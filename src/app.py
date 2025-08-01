import os
import logging
import gc
import time
from dotenv import load_dotenv

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

import pdfplumber
try:
    import fitz  # PyMuPDF for fast PDF extraction
    # Verify it's the correct PyMuPDF module
    if not hasattr(fitz, 'open'):
        raise ImportError("Wrong fitz module loaded")
except (ImportError, AttributeError):
    # Fallback: Try importing PyMuPDF directly
    try:
        import pymupdf as fitz
    except ImportError:
        # Final fallback: use pdfplumber only
        fitz = None
        logger.warning("PyMuPDF not available, will use pdfplumber only")

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

# Load environment variables
load_dotenv()

# Global model cache to prevent reloading
_model_cache = {
    'sentence_transformer': None,
    'ner_pipeline': None
}

# Document cache to avoid reprocessing same documents
_document_cache = {}
MAX_CACHE_SIZE = 5  # Keep last 5 documents cached

def get_document_cache_key(url):
    """Generate cache key for document URL"""
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()

def get_cached_document(url):
    """Get document from cache if available"""
    cache_key = get_document_cache_key(url)
    return _document_cache.get(cache_key)

def cache_document(url, chunks, embeddings, index, model):
    """Cache document processing results"""
    cache_key = get_document_cache_key(url)
    
    # Implement LRU-style cache by removing oldest if at capacity
    if len(_document_cache) >= MAX_CACHE_SIZE:
        # Remove the first (oldest) entry
        oldest_key = next(iter(_document_cache))
        del _document_cache[oldest_key]
        logger.info(f"Removed oldest document from cache")
    
    _document_cache[cache_key] = {
        'chunks': chunks,
        'embeddings': embeddings, 
        'index': index,
        'model': model
    }
    logger.info(f"Cached document processing results for {url[:50]}...")

def get_sentence_transformer():
    """Get cached sentence transformer model"""
    if _model_cache['sentence_transformer'] is None:
        logger.info("Loading SentenceTransformer model (first time only)...")
        _model_cache['sentence_transformer'] = SentenceTransformer('BAAI/bge-large-en-v1.5')
        logger.info("SentenceTransformer model loaded and cached")
    return _model_cache['sentence_transformer']

def get_ner_pipeline():
    """Get cached NER pipeline"""
    if _model_cache['ner_pipeline'] is None:
        logger.info("Loading NER pipeline (first time only)...")
        _model_cache['ner_pipeline'] = pipeline("ner", model="dslim/bert-base-NER")
        logger.info("NER pipeline loaded and cached")
    return _model_cache['ner_pipeline']

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
        logger.warning("Using OPENAI_API_KEY - Consider renaming to OPENROUTER_API_KEY")
        return api_key
    
    # No key found
    raise ValueError("❌ No API key found! Please set OPENROUTER_API_KEY in your .env file")

# Step 1: Document Ingestion
def extract_text_from_pdf(pdf_path):
    if fitz is not None:
        # Use PyMuPDF (faster)
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        # Clean text (e.g., remove OCR errors)
        text = text.replace("iviviv", "").replace("Air Ambulasce", "Air Ambulance")
        return text
    else:
        # Fallback to pdfplumber
        logger.info("Using pdfplumber for PDF extraction")
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
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
    # Use cached model instead of creating new one
    model = get_sentence_transformer()
    
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
    
    logger.info(f"Encoding {len(chunks)} chunks with cached model...")
    embeddings = model.encode(chunks)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return chunks, embeddings, index, model

def estimate_tokens(text: str) -> int:
    """
    More accurate token estimation for various text types
    Based on OpenAI's tokenization patterns
    """
    # Basic character-based estimation with adjustments
    chars = len(text)
    
    # Count specific patterns that affect tokenization
    words = len(text.split())
    punctuation_count = sum(1 for c in text if c in '.,;:!?()[]{}"\'-')
    numbers_count = len([w for w in text.split() if w.isdigit()])
    
    # Estimate tokens based on multiple factors
    # English text averages ~4 characters per token
    # But punctuation, numbers, and special chars can affect this
    base_tokens = chars / 4.0
    
    # Adjustments
    if words > 0:
        avg_word_length = chars / words
        if avg_word_length > 6:  # Longer words tend to be split more
            base_tokens *= 1.2
    
    # Add extra tokens for punctuation and numbers
    estimated_tokens = base_tokens + (punctuation_count * 0.5) + (numbers_count * 0.3)
    
    return int(estimated_tokens)

# Step 3: Query Parsing
def parse_query(query):
    # Use cached NER pipeline instead of creating new one
    nlp = get_ner_pipeline()
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
        
        logger.info(f"OpenAI client initialized with API key: {api_key[:20]}...")
        
    except ValueError as e:
        logger.error(f"API Key Error: {e}")
        return json.dumps({
            "answer": "❌ API key not configured. Please set OPENROUTER_API_KEY in your .env file.",
            "justification": "Cannot process query without API key.",
            "confidence": 0.0
        })
    except Exception as e:
        logger.error(f"Client initialization error: {e}")
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
    
    # Estimate token count using improved function
    estimated_tokens = estimate_tokens(prompt)
    logger.info(f"Estimated prompt tokens: {estimated_tokens}")
    
    # If prompt is too long, use only the first chunk
    if estimated_tokens > 8000:  # Conservative limit for free tier
        logger.warning("Prompt too long, using only first chunk")
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
    logger.info("Starting interactive Q&A session")
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
            logger.info("Session ended by user")
            print("\n\n👋 Session ended by user. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error during Q&A session: {str(e)}")
            print(f"\n❌ An error occurred: {str(e)}")
            print("Please try asking your question again.")

# Main Execution

from fastapi import FastAPI, UploadFile, File, Form, Request, Header, Body, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Optional
import time
from collections import defaultdict

# Simple rate limiting (in-memory)
request_counts = defaultdict(list)
RATE_LIMIT_REQUESTS = 10  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

def check_rate_limit(client_ip: str) -> bool:
    """Simple rate limiting - 10 requests per minute per IP"""
    now = time.time()
    # Clean old requests
    request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] 
                                if now - req_time < RATE_LIMIT_WINDOW]
    
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    request_counts[client_ip].append(now)
    return True


app = FastAPI()

# Preload models at startup to avoid delays on first request
@app.on_event("startup")
async def startup_event():
    logger.info("Preloading ML models at startup...")
    try:
        # Preload sentence transformer
        get_sentence_transformer()
        # Preload NER pipeline  
        get_ner_pipeline()
        logger.info("All models preloaded successfully!")
    except Exception as e:
        logger.error(f"Error preloading models: {e}")

def verify_bearer_token(authorization: str):
    """
    Verifies Bearer token from Authorization header.
    Requires HACKRX_BEARER_TOKEN environment variable to be set.
    """
    required_token = os.getenv('HACKRX_BEARER_TOKEN')
    if not required_token:
        return False, "HACKRX_BEARER_TOKEN environment variable is not configured."
    
    if not authorization or not authorization.startswith('Bearer '):
        return False, "Missing or invalid Authorization header."
    
    token = authorization.split('Bearer ')[-1].strip()
    if token != required_token:
        return False, "Invalid Bearer token."
    return True, None

# HackRx 6.0 compliant endpoint

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and Docker health checks"""
    try:
        api_key = get_api_key()
        if not api_key:
            return JSONResponse({
                "status": "unhealthy",
                "error": "API key not configured"
            }, status_code=503)
        
        return JSONResponse({
            "status": "healthy",
            "service": "Intelligent Query PDF Q&A System",
            "version": "1.0.0",
            "api_configured": True
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=503)

@app.post("/hackrx/run")
async def hackrx_run(
    request: Request,
    authorization: str = Header(None),
    documents: Optional[str] = Body(None),
    questions: Optional[List[str]] = Body(None)
):
    # Rate limiting check
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    # Verify Bearer token
    ok, err = verify_bearer_token(authorization)
    if not ok:
        logger.warning(f"Bearer token verification failed: {err}")
        return JSONResponse({"success": False, "error": err}, status_code=401)

    # Validate input parameters
    if not documents:
        logger.warning("Request missing documents parameter")
        return JSONResponse({
            "success": False, 
            "error": "Missing 'documents' parameter. Please provide a URL to the document."
        }, status_code=400)
    
    if not questions:
        logger.warning("Request missing questions parameter")
        return JSONResponse({
            "success": False, 
            "error": "Missing 'questions' parameter. Please provide a list of questions."
        }, status_code=400)
    
    if not isinstance(questions, list) or len(questions) == 0:
        logger.warning("Invalid questions format")
        return JSONResponse({
            "success": False, 
            "error": "Questions must be a non-empty list."
        }, status_code=400)
    
    # Validate URL format
    if not documents.startswith(('http://', 'https://')):
        logger.warning(f"Invalid document URL format: {documents}")
        return JSONResponse({
            "success": False, 
            "error": "Documents parameter must be a valid URL."
        }, status_code=400)

    try:
        # Download and extract text from the document URL
        logger.info(f"Processing document URL: {documents}")
        
        # Check cache first
        cached_doc = get_cached_document(documents)
        if cached_doc:
            logger.info("Using cached document processing results")
            chunks = cached_doc['chunks']
            embeddings = cached_doc['embeddings']
            index = cached_doc['index']
            model_st = cached_doc['model']
        else:
            # Process document if not cached
            text = download_and_extract_text(documents)
            logger.info(f"Extracted {len(text)} characters from document")
            
            chunks, embeddings, index, model_st = create_document_embeddings(text)
            logger.info(f"Created {len(chunks)} chunks for processing")
            
            # Cache the results
            cache_document(documents, chunks, embeddings, index, model_st)

        # Generate answers for each question
        answers = []
        for i, q in enumerate(questions):
            logger.info(f"Processing question {i+1}/{len(questions)}: {q[:50]}...")
            response = generate_response(q, chunks, embeddings, index, model_st)
            try:
                result = json.loads(response)
                answer = result.get('justification') or str(result)
            except Exception:
                answer = response
            answers.append(answer)
            
            # Force garbage collection after each question to manage memory
            if i % 3 == 0:  # Every 3 questions
                gc.collect()

        # Add processing_info for leaderboard compliance
        processing_info = {
            "response_time": None,  # You can set actual timing if needed
            "token_usage": None,    # Set if available from LLM response
            "chunks_processed": len(chunks),
            "questions_answered": len(questions),
            "cache_hit": cached_doc is not None
        }
        
        logger.info(f"Successfully processed {len(questions)} questions")
        
        # Final cleanup (but don't delete cached items)
        if not cached_doc:  # Only cleanup if we didn't use cache
            del chunks, embeddings, index, model_st
        gc.collect()
        
        return JSONResponse({
            "success": True,
            "answers": answers,
            "processing_info": processing_info
        })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        # Cleanup on error
        gc.collect()
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get API key and set it for OpenAI client
    api_key = get_api_key()
    openai.api_key = api_key
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 3000))
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=port)