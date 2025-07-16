import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import pipeline
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    chunks = text.split("\n\n")  # Split into paragraphs
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
def retrieve_relevant_chunks(query, chunks, embeddings, index, model, k=3):
    query_embedding = model.encode([query])[0]
    distances, indices = index.search(np.array([query_embedding]), k)
    return [chunks[i] for i in indices[0]]

# Step 5: Decision and Output Generation
def generate_response(query, chunks, embeddings=None, index=None, model_st=None, llm_model="gemini-1.5-flash"):
    # Configure Gemini API
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel(llm_model)
    
    parsed_query = parse_query(query)
    relevant_chunks = retrieve_relevant_chunks(query, chunks, embeddings, index, model_st)
    
    # Construct prompt for LLM
    prompt = f"""Based on the following insurance policy document chunks, answer the user's query in JSON format.

Query: {query}

Relevant Document Chunks:
{chr(10).join([f"Chunk {i+1}: {chunk}" for i, chunk in enumerate(relevant_chunks)])}

Please provide your response in the following JSON format:
{{
    "decision": "Covered" or "Not Covered" or "Partially Covered",
    "amount": "maximum coverage amount if applicable, otherwise null",
    "justification": "detailed explanation based on the document chunks"
}}

Only base your answer on the information provided in the document chunks. If the information is not sufficient to make a determination, state that clearly in the justification."""

    try:
        # Generate response using Gemini
        response = model.generate_content(prompt)
        
        # Try to parse as JSON, if it fails, format it properly
        try:
            # Extract JSON from response if it's wrapped in markdown
            response_text = response.text
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
                "justification": f"LLM Response: {response.text}"
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
            response = generate_response(user_query, chunks)
            
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
    
    # Load and process PDF
    pdf_path = "EDLHLGA23009V012223.pdf"
    
    try:
        print("📖 Extracting text from PDF...")
        text = extract_text_from_pdf(pdf_path)
        
        print("🧠 Creating document embeddings...")
        chunks, embeddings, index = create_document_embeddings(text)
        model_st = SentenceTransformer('all-MiniLM-L6-v2')
        
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
            response = generate_response(query, chunks)
            print("\n📋 Test Response:")
            print(response)
            
    except FileNotFoundError:
        print(f"❌ Error: PDF file '{pdf_path}' not found!")
        print("Please make sure the PDF file exists in the current directory.")
    except Exception as e:
        print(f"❌ An error occurred during PDF processing: {str(e)}")
        print("Please check your setup and try again.")