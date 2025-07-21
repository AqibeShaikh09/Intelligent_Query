import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import pipeline
import json
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_api_key():
    """
    Get API key with fallback support for different naming conventions
    Supports both OPENROUTER_API_KEY and OPENAI_API_KEY for backward compatibility
    """
    # Primary key name (preferred)
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key:
        return api_key
    
    # Fallback key name for backward compatibility
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print("⚠️  Using OPENAI_API_KEY - Consider renaming to OPENROUTER_API_KEY")
        return api_key
    
    # No key found
    raise ValueError("❌ No API key found! Please set OPENROUTER_API_KEY in your .env file")

# Step 1: Document Ingestion
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    # Clean text (e.g., remove OCR errors)
    text = text.replace("iviviv", "").replace("Air Ambulasce", "Air Ambulance")
    return text

# Step 2: Text Chunking and Embedding
def create_document_embeddings(text):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Split into smaller chunks to manage token limits better
    # First split by paragraphs, then further split if needed
    paragraphs = text.split("\n\n")
    chunks = []
    
    for paragraph in paragraphs:
        # If paragraph is too long, split it into smaller chunks
        if len(paragraph) > 800:
            # Split long paragraphs into sentences and group them
            sentences = paragraph.split(". ")
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk + sentence) < 800:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
        else:
            if paragraph.strip():
                chunks.append(paragraph.strip())
    
    # Filter out very short chunks
    chunks = [chunk for chunk in chunks if len(chunk) > 50]
    
    embeddings = model.encode(chunks)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return chunks, embeddings, index, model

# Step 3: Query Parsing
def parse_query(query):
    nlp = pipeline("ner", model="dslim/bert-base-NER")
    entities = nlp(query)
    parsed = {"care_type": None, "beneficiary": None, "period": None}
    for entity in entities:
        if "mother" in query.lower():
            parsed["beneficiary"] = "mother"
        if "preventive care" in query.lower():
            parsed["care_type"] = "routine preventive care"
        if "just delivered" in query.lower():
            parsed["period"] = "postpartum"
    return parsed

# Step 4: Semantic Retrieval
def retrieve_relevant_chunks(query, chunks, embeddings, index, model, k=2):
    query_embedding = model.encode([query])[0]
    distances, indices = index.search(np.array([query_embedding]), k)
    # Limit chunk size to prevent token overflow
    relevant_chunks = []
    for i in indices[0]:
        chunk = chunks[i]
        # Limit each chunk to 500 characters to stay within token limits
        if len(chunk) > 500:
            chunk = chunk[:500] + "..."
        relevant_chunks.append(chunk)
    return relevant_chunks

# Step 5: Decision and Output Generation
def generate_response(query, chunks, embeddings=None, index=None, model_st=None, llm_model="anthropic/claude-3-haiku"):
    # Configure OpenRouter API using new OpenAI client
    from openai import OpenAI
    
    try:
        api_key = get_api_key()
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    except ValueError as e:
        print(f"API Key Error: {e}")
        return json.dumps({
            "answer": "❌ API key not configured. Please set OPENROUTER_API_KEY in your .env file.",
            "justification": "Cannot process query without API key.",
            "confidence": 0.0
        })
    
    parsed_query = parse_query(query)
    relevant_chunks = retrieve_relevant_chunks(query, chunks, embeddings, index, model_st)
    
    # Construct prompt for LLM
    prompt = f"""Based on these document excerpts, answer the query in JSON format.

Query: {query}

Document excerpts:
{chr(10).join([f"{i+1}. {chunk}" for i, chunk in enumerate(relevant_chunks)])}

Response format:
{{
    "decision": "Covered/Not Covered/Partially Covered/Unable to determine",
    "amount": "coverage amount or null",
    "justification": "brief explanation based on excerpts"
}}

Base answer only on provided excerpts."""
    
    # Estimate token count (rough approximation: 1 token ≈ 4 characters)
    estimated_tokens = len(prompt) // 4
    print(f"Estimated prompt tokens: {estimated_tokens}")
    
    # If prompt is too long, use only the first chunk
    if estimated_tokens > 8000:  # Conservative limit for free tier
        print("Prompt too long, using only first chunk")
        relevant_chunks = relevant_chunks[:1]
        # Recreate shorter prompt
        prompt = f"""Based on this document excerpt, answer in JSON format.

Query: {query}

Excerpt: {relevant_chunks[0][:300]}...

Format: {{"decision": "...", "amount": "...", "justification": "..."}}"""

    try:
        # Generate response using OpenRouter with new API
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": "You are an AI assistant that analyzes documents and provides JSON responses."},
                {"role": "user", "content": prompt}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "PDF Q&A System"
            }
        )
        
        response_text = response.choices[0].message.content
        
        # Try to parse as JSON, if it fails, format it properly
        try:
            # Extract JSON from response if it's wrapped in markdown
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Validate JSON format
            parsed_response = json.loads(response_text)
            return json.dumps(parsed_response, indent=2)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response
            return json.dumps({
                "decision": "Unable to determine",
                "amount": None,
                "justification": f"AI Response: {response_text}"
            }, indent=2)
            
    except Exception as e:
        # Fallback response in case of API errors
        return json.dumps({
            "decision": "Error",
            "amount": None,
            "justification": f"Error generating response: {str(e)}"
        }, indent=2)

# Interactive Question-Answer Function
def interactive_qa_session(chunks, embeddings, index, model_st):
    print("=" * 60)
    print("📄 PDF Question-Answer System")
    print("=" * 60)
    print("You can now ask questions about the PDF document!")
    print("Type 'quit', 'exit', or 'q' to stop.")
    print("-" * 60)
    
    while True:
        try:
            # Get user input
            user_query = input("\n🤔 Ask your question: ").strip()
            
            # Check for exit commands
            if user_query.lower() in ['quit', 'exit', 'q', '']:
                print("\n👋 Thank you for using the PDF Q&A system!")
                break
            
            # Process the query
            print("\n🔍 Processing your question...")
            response = generate_response(user_query, chunks, embeddings, index, model_st)
            
            # Display the response
            print("\n📋 Response:")
            print("-" * 40)
            
            # Parse and display JSON response nicely
            try:
                response_data = json.loads(response)
                print(f"Decision: {response_data.get('decision', 'N/A')}")
                if response_data.get('amount'):
                    print(f"Amount: {response_data.get('amount')}")
                print(f"Justification: {response_data.get('justification', 'N/A')}")
            except:
                print(response)
            
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n\n👋 Session ended by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            print("Please try asking your question again.")

# Main Execution
if __name__ == "__main__":
    print("🚀 Starting PDF Analysis System...")
    
    # Get PDF file path from user
    while True:
        pdf_path = input("\n📁 Enter the path to your PDF file (or drag and drop the file here): ").strip().strip('"')
        
        if os.path.exists(pdf_path) and pdf_path.lower().endswith('.pdf'):
            break
        else:
            print("❌ File not found or not a PDF file. Please try again.")
            print("Make sure to provide the full path to your PDF file.")
    
    try:
        print(f"📖 Extracting text from PDF: {os.path.basename(pdf_path)}...")
        text = extract_text_from_pdf(pdf_path)
        
        print("🧠 Creating document embeddings...")
        chunks, embeddings, index, model_st = create_document_embeddings(text)
        
        print("✅ PDF processing complete!")
        
        # Ask user for interaction mode
        print("\nChoose an option:")
        print("1. Interactive Q&A session")
        print("2. Run single test query")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            # Start interactive session
            interactive_qa_session(chunks, embeddings, index, model_st)
        else:
            # Run test query
            print("\n🧪 Running test query...")
            query = "Is routine preventive care covered for a mother who has just delivered a newborn under this policy?"
            response = generate_response(query, chunks, embeddings, index, model_st)
            print("\n📋 Test Response:")
            print(response)
            
    except FileNotFoundError:
        print(f"❌ Error: PDF file '{os.path.basename(pdf_path)}' not found!")
        print("Please make sure the PDF file exists and the path is correct.")
    except Exception as e:
        print(f"❌ An error occurred during PDF processing: {str(e)}")
        print("Please check your PDF file and try again.")