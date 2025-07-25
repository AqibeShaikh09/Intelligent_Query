import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import pipeline
import json
import openai
import os
from dotenv import load_dotenv
import docx
from email import policy
from email.parser import BytesParser
import requests

load_dotenv()

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    text = text.replace("iviviv", "").replace("Air Ambulasce", "Air Ambulance")
    return text

def extract_text_from_docx(docx_path):
    document = docx.Document(docx_path)
    text = []
    for paragraph in document.paragraphs:
        text.append(paragraph.text)
    return "\n".join(text).strip()

def extract_text_from_email(email_path):
    with open(email_path, 'rb') as fp:
        msg = BytesParser(policy=policy.default).parse(fp)

    text_content = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = part.get('Content-Disposition')

            if ctype == 'text/plain' and 'attachment' not in (cdisp or ''):
                text_content.append(part.get_content())
                break
    else:
        if msg.get_content_type() == 'text/plain':
            text_content.append(msg.get_content())
    
    headers = []
    for header_name in ['Subject', 'From', 'To', 'Date']:
        if msg[header_name]:
            headers.append(f"{header_name}: {msg[header_name]}")

    full_text = "\n".join(headers) + "\n\n" + "\n".join(text_content)
    return full_text.strip()


def extract_text_from_document(file_path, file_extension):
    if file_extension == 'pdf':
        print(f"Extracting text from PDF: {file_path}")
        return extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        print(f"Extracting text from DOCX: {file_path}")
        return extract_text_from_docx(file_path)
    elif file_extension == 'eml':
        print(f"Extracting text from Email (.eml): {file_path}")
        return extract_text_from_email(file_path)
    else:
        raise ValueError(f"Unsupported file type: .{file_extension}")

def create_document_embeddings(text):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    paragraphs = text.split("\n\n")
    chunks = []
    
    for paragraph in paragraphs:
        if len(paragraph) > 800:
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
    
    chunks = [chunk for chunk in chunks if len(chunk) > 50]
    
    embeddings = model.encode(chunks)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return chunks, embeddings, index, model

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

def retrieve_relevant_chunks(query, chunks, embeddings, index, model, k=2):
    query_embedding = model.encode([query])[0]
    distances, indices = index.search(np.array([query_embedding]), k)
    relevant_chunks = []
    for i in indices[0]:
        chunk = chunks[i]
        if len(chunk) > 500:
            chunk = chunk[:500] + "..."
        relevant_chunks.append(chunk)
    return relevant_chunks

def generate_response(query, chunks, embeddings=None, index=None, model_st=None, llm_model="anthropic/claude-3-haiku"):
    from openai import OpenAI
    
    client = OpenAI(
        api_key=os.getenv('OPENROUTER_API_KEY'),
        base_url="https://openrouter.ai/api/v1"
    )
    
    parsed_query = parse_query(query)
    relevant_chunks = retrieve_relevant_chunks(query, chunks, embeddings, index, model_st)
    
    # MODIFIED PROMPT: Ask for a direct answer string
    prompt = f"""Based on these document excerpts, directly answer the query as a single string.
Do NOT use JSON format. Do NOT include any preamble like "The document states...".
Just provide the concise answer directly from the excerpts. If the information is not in the excerpts, state "Unable to determine from provided document."

Query: {query}

Document excerpts:
{chr(10).join([f"{i+1}. {chunk}" for i, chunk in enumerate(relevant_chunks)])}

Direct Answer:""" # Added "Direct Answer:" to guide the model

    estimated_tokens = len(prompt) // 4
    print(f"Estimated prompt tokens: {estimated_tokens}")
    
    if estimated_tokens > 8000:
        print("Prompt too long, using only first chunk")
        relevant_chunks = relevant_chunks[:1]
        prompt = f"""Based on this document excerpt, directly answer the query as a single string.
Do NOT use JSON format. Do NOT include any preamble like "The document states...".
Just provide the concise answer directly from the excerpt. If the information is not in the excerpt, state "Unable to determine from provided document."

Query: {query}

Excerpt: {relevant_chunks[0][:300]}...

Direct Answer:"""

    try:
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": "You are an AI assistant that analyzes documents and provides concise string responses based ONLY on provided excerpts."},
                {"role": "user", "content": prompt}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "PDF Q&A System"
            }
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # We expect a string, but sometimes LLMs might still wrap it or add extra text.
        # Let's try to clean it up a bit if needed.
        if response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text.strip("`") # Remove markdown code blocks
        
        return response_text # Return the direct string response
            
    except Exception as e:
        # Fallback response in case of API errors
        return f"Error generating response: {str(e)}" # Return error as a string