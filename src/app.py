import pdfplumber
import fitz  # PyMuPDF for fast PDF extraction
import requests
import tempfile
import mimetypes
from docx import Document
import email
import email.policy
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
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    # Clean text (e.g., remove OCR errors)
    text = text.replace("iviviv", "").replace("Air Ambulasce", "Air Ambulance")
    return text

# DOCX extraction
def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Email extraction (.eml)
def extract_text_from_email(email_path):
    with open(email_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)
    text = msg.get_body(preferencelist=('plain')).get_content() if msg.get_body(preferencelist=('plain')) else ''
    return text

# Download file from URL and auto-detect type
def download_and_extract_text(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download file: {url}")
    # Guess file type from headers or URL
    content_type = response.headers.get('content-type', '')
    ext = mimetypes.guess_extension(content_type) or url.split('.')[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
    # Dispatch to correct extractor
    if ext in ['.pdf', 'pdf']:
        return extract_text_from_pdf(tmp_path)
    elif ext in ['.docx', 'docx']:
        return extract_text_from_docx(tmp_path)
    elif ext in ['.eml', 'msg']:
        return extract_text_from_email(tmp_path)
    else:
        raise Exception(f"Unsupported file type: {ext}")

# Step 2: Text Chunking and Embedding
def create_document_embeddings(text):
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    
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
        if not api_key:
            raise ValueError("No API key found")
            
        # Set the API key in environment for OpenAI client
        os.environ['OPENAI_API_KEY'] = api_key
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        print(f"✅ OpenAI client initialized with API key: {api_key[:20]}...")
        
    except ValueError as e:
        print(f"API Key Error: {e}")
        return json.dumps({
            "answer": "❌ API key not configured. Please set OPENROUTER_API_KEY in your .env file.",
            "justification": "Cannot process query without API key.",
            "confidence": 0.0
        })
    except Exception as e:
        print(f"Client initialization error: {e}")
        return json.dumps({
            "answer": "❌ Failed to initialize AI client.",
            "justification": f"Error: {str(e)}",
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
        system_prompt = (
            "You are an expert insurance analyst AI. "
            "Always answer strictly based on the provided document excerpts. "
            "If the answer is not present, reply 'Unable to determine'. "
            "Return your answer in the specified JSON format. "
            "Do not hallucinate or make assumptions."
        )
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=256,  # Lower this value
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

from fastapi import FastAPI, UploadFile, File, Form, Request, Header, Body
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Optional


app = FastAPI()

def verify_bearer_token(authorization: str):
    """
    Verifies Bearer token from Authorization header.
    Replace 'YOUR_HACKRX_TOKEN' with your actual token or use env variable.
    """
    required_token = os.getenv('HACKRX_BEARER_TOKEN', 'YOUR_HACKRX_TOKEN')
    if not authorization or not authorization.startswith('Bearer '):
        return False, "Missing or invalid Authorization header."
    token = authorization.split('Bearer ')[-1].strip()
    if token != required_token:
        return False, "Invalid Bearer token."
    return True, None

# HackRx 6.0 compliant endpoint


@app.post("/hackrx/run")
async def hackrx_run(
    request: Request,
    authorization: str = Header(None),
    documents: Optional[str] = Body(None),
    questions: Optional[List[str]] = Body(None)
):
    # Verify Bearer token
    ok, err = verify_bearer_token(authorization)
    if not ok:
        return JSONResponse({"success": False, "error": err}, status_code=401)

    # Check if documents and questions are provided
    if not documents or not questions:
        return JSONResponse({"success": False, "error": "No valid input provided."}, status_code=400)

    try:
        # Download and extract text from the document URL
        text = download_and_extract_text(documents)
        chunks, embeddings, index, model_st = create_document_embeddings(text)

        # Generate answers for each question
        answers = []
        for q in questions:
            response = generate_response(q, chunks, embeddings, index, model_st)
            try:
                result = json.loads(response)
                answer = result.get('justification') or str(result)
            except Exception:
                answer = response
            answers.append(answer)

        # Add processing_info for leaderboard compliance
        processing_info = {
            "response_time": None,  # You can set actual timing if needed
            "token_usage": None    # Set if available from LLM response
        }
        return JSONResponse({
            "success": True,
            "answers": answers,
            "processing_info": processing_info
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get API key and set it for OpenAI client
    api_key = get_api_key()
    openai.api_key = api_key
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=3000)