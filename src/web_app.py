from flask import Flask, request, jsonify, render_template_string, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from .app import extract_text_from_document, create_document_embeddings, generate_response
import tempfile
import traceback
import time
import gc
import requests
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

ALL_ALLOWED_EXTENSIONS = {'pdf', 'docx', 'eml'}
MAX_FILE_SIZE = 16 * 1024 * 1024

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

current_document = {
    'chunks': None,
    'embeddings': None,
    'index': None,
    'model_st': None,
    'source_url': None,
    'filename': None,
    'upload_time': None,
    'chunk_count': 0,
    'questions': [],
    'answers': []
}

def allowed_file_extension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALL_ALLOWED_EXTENSIONS

# HTML Template as string (Modified for simplified output and API endpoint)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Document API Test Client</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .app-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 800px;
            overflow: hidden;
            animation: slideUp 0.6s ease-out;
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 3s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            position: relative;
            z-index: 2;
        }
        
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-weight: 300;
            position: relative;
            z-index: 2;
        }
        
        .content {
            padding: 0;
        }
        
        .input-section {
            padding: 40px;
            text-align: center;
        }
        
        textarea {
            width: 100%;
            height: 300px;
            padding: 15px;
            border: 2px solid #e0e7ff;
            border-radius: 15px;
            font-family: 'Poppins', sans-serif;
            font-size: 0.95rem;
            color: #4a5568;
            background-color: #f8fafc;
            resize: vertical;
            outline: none;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        }

        textarea:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .input-group {
            margin-bottom: 15px;
            text-align: left;
        }

        .input-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #4a5568;
        }

        .input-group input[type="text"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #e0e7ff;
            border-radius: 8px;
            font-family: 'Poppins', sans-serif;
            font-size: 0.9rem;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
            font-size: 1rem;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        
        .chat-section {
            height: auto;
            min-height: 400px;
            display: flex;
            flex-direction: column;
        }
        
        .document-info {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .doc-details h3 {
            color: #1e40af;
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .doc-details p {
            color: #64748b;
            margin: 5px 0 0 0;
            font-size: 0.9rem;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            animation: blink 2s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        .new-doc-btn {
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .new-doc-btn:hover {
            background: #667eea;
            color: white;
            transform: scale(1.05);
        }
        
        .output-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #fafafa;
        }

        .output-json-block {
            background: #2d3748;
            color: #f7fafc;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Consolas', 'Monaco', monospace;
            white-space: pre-wrap;
            word-break: break-all;
            font-size: 0.9rem;
            text-align: left;
            overflow-x: auto;
        }

        .output-json-block pre {
            margin: 0;
            padding: 0;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #64748b;
            display: none;
        }
        
        .spinner {
            width: 30px;
            height: 30px;
            border: 3px solid #e2e8f0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #64748b;
        }
        
        .empty-icon {
            font-size: 3rem;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 10px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }
        
        .notification.success { background: #10b981; }
        .notification.error { background: #ef4444; }
        .notification.warning { background: #f59e0b; }
        
        @keyframes slideIn {
            from { transform: translateX(100%); }
            to { transform: translateX(0); }
        }
        
        .flash-message {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            color: #1e40af;
            padding: 15px 20px;
            margin: 20px;
            border-radius: 10px;
            border-left: 4px solid #3b82f6;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .app-container { margin: 10px; }
            .header h1 { font-size: 2rem; }
            .input-section { padding: 20px; }
            .chat-section { height: auto; min-height: 400px; }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header">
            <h1>🤖 AI Document API Test Client</h1>
            <p>Interact with your AI Document Analysis API</p>
        </div>

        <div class="content">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="flash-message">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p>AI is processing your document and questions...</p>
            </div>

            {% if not document_loaded %}
            <div class="input-section">
                <form onsubmit="submitApiRequest(event)" id="jsonForm"> {# Changed function name #}
                    <div class="input-group">
                        <label for="baseUrlInput">API Base URL:</label>
                        <input type="text" id="baseUrlInput" value="http://localhost:5000" placeholder="e.g., http://localhost:5000">
                    </div>
                    <div class="input-group">
                        <label for="authHeaderInput">Authorization Header (Bearer Token):</label>
                        <input type="text" id="authHeaderInput" value="Bearer fd4d7c6b3d2f4441c504368af8eafd59025b77053a8123fd9946501c5ae23612" placeholder="e.g., Bearer your_token_here">
                    </div>
                    <div class="input-group">
                        <label for="jsonInput">JSON Request Body:</label>
                        <textarea id="jsonInput" placeholder='Paste your JSON request here, e.g.:
{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for pre-existing diseases (PED) to be covered?",
        "Does this policy cover maternity expenses, and what are the conditions?"
    ]
}'></textarea>
                    </div>
                    <button type="submit" class="btn">✨ Send API Request</button> {# Changed button text #}
                </form>
            </div>
            {% endif %}

            {% if document_loaded %}
            <div class="chat-section">
                <div class="document-info">
                    <div class="doc-details">
                        <h3><span class="status-dot"></span>{{ filename }}</h3>
                        <p>Source: {{ source_url }}</p>
                        <p>Uploaded at {{ upload_time }} • {{ chunk_count }} sections processed</p>
                    </div>
                    <button class="new-doc-btn" onclick="clearDocument()">📎 Send New API Request</button> {# Changed button text #}
                </div>

                <div class="output-container" id="outputContainer">
                    {% if answers %}
                        <div class="output-json-block">
<pre>
{
    "answers": [
{% for answer in answers %}
        "{{ answer | e }}"{% if not loop.last %},{% endif %} {# Added | e for HTML escaping #}
{% endfor %}
    ]
}
</pre>
                        </div>
                    {% else %}
                        <div class="empty-state">
                            <div class="empty-icon">💬</div>
                            <h3>Waiting for API input...</h3> {# Changed text #}
                            <p>Once processed, results will appear here.</p>
                        </div>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const jsonInput = document.getElementById('jsonInput');
            if (jsonInput) {
                // Pre-populate with the exact sample from the image
                jsonInput.value = JSON.stringify({
                    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
                    "questions": [
                        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
                        "What is the waiting period for pre-existing diseases (PED) to be covered?",
                        "Does this policy cover maternity expenses, and what are the conditions?",
                        "What is the waiting period for cataract surgery?",
                        "Are the medical expenses for an organ donor covered under this policy?",
                        "What is the No Claim Discount (NCD) offered in this policy?",
                        "Is there a benefit for preventive health check-ups?",
                        "How does the policy define a 'Hospital'?",
                        "What is the extent of coverage for AYUSH treatments?",
                        "Are there any sub-limits on room rent and ICU charges for Plan A?"
                    ]
                }, null, 4);
            }
        });

        async function submitApiRequest(event) { {# Changed function name #}
            event.preventDefault();
            console.log("submitApiRequest called.");
            
            const baseUrlInput = document.getElementById('baseUrlInput');
            const authHeaderInput = document.getElementById('authHeaderInput');
            const jsonInput = document.getElementById('jsonInput');
            const jsonString = jsonInput.value.trim();
            const submitBtn = document.querySelector('#jsonForm .btn');
            const loadingDiv = document.getElementById('loading');

            const baseUrl = baseUrlInput.value.trim();
            const authHeader = authHeaderInput.value.trim();

            if (!baseUrl) {
                showNotification('Please enter the API Base URL.', 'warning');
                return;
            }
            if (!jsonString) {
                showNotification('Please enter your JSON request.', 'warning');
                return;
            }
            // Authorization header is optional for local dev, but if present, validate format
            if (authHeader && !authHeader.toLowerCase().startsWith('bearer ')) {
                showNotification('Authorization header must start with "Bearer "', 'warning');
                return;
            }

            try {
                JSON.parse(jsonString);
                console.log("JSON parsed successfully, attempting API call.");
            } catch (e) {
                showNotification('Invalid JSON format. Please check your input.', 'error');
                console.error("JSON parsing error:", e);
                return;
            }

            if (loadingDiv) {
                loadingDiv.style.display = 'block';
            }
            submitBtn.disabled = true;
            submitBtn.innerHTML = '⏳ Sending Request...'; {# Changed button text #}

            try {
                // Construct the full API URL based on the image
                const apiUrl = `${baseUrl}/hackrx/run`; {# Modified API URL #}

                const headers = { 'Content-Type': 'application/json' };
                if (authHeader) {
                    headers['Authorization'] = authHeader;
                }

                const response = await fetch(apiUrl, { {# Changed URL #}
                    method: 'POST',
                    headers: headers, {# Added headers #}
                    body: jsonString
                });
                const data = await response.json();
                console.log("API response received:", data);

                if (data.success) {
                    showNotification('API request processed successfully!', 'success');
                    setTimeout(() => location.reload(), 500); 
                } else {
                    showNotification('Error from API: ' + (data.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                console.error('Network or API call error:', error);
                showNotification('Network or API call error: ' + error.message, 'error');
            } finally {
                if (loadingDiv) {
                    loadingDiv.style.display = 'none';
                }
                submitBtn.disabled = false;
                submitBtn.innerHTML = '✨ Send API Request'; {# Changed button text #}
                console.log("API request finished.");
            }
        }

        function clearDocument() {
            if (confirm('Send a new API request? This will clear current results.')) { {# Changed text #}
                fetch('/clear', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Current results cleared!', 'success'); {# Changed text #}
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        showNotification('Error: ' + data.error, 'error');
                    }
                })
                .catch(error => showNotification('Error: ' + error.message, 'error'));
            }
        }

        function showNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    response = app.response_class(
        render_template_string(HTML_TEMPLATE, 
                              document_loaded=current_document['chunks'] is not None,
                              filename=current_document['filename'],
                              source_url=current_document['source_url'],
                              upload_time=current_document.get('upload_time', 'Unknown'),
                              chunk_count=current_document.get('chunk_count', 0),
                              answers=current_document['answers'])
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# MODIFIED: Changed endpoint to /hackrx/run as per the image
@app.route('/hackrx/run', methods=['POST'])
def run_hackrx_request(): # Renamed function for clarity
    try:
        # Check for Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Unauthorized: Bearer token missing or malformed.'}), 401
        
        # You could add token validation here, e.g., if token == "your_expected_token":
        # For now, we just check its presence and format.
        token = auth_header.split(' ')[1]
        print(f"Received Authorization Token: {token}") # For debugging

        req_data = request.get_json()
        if not req_data:
            return jsonify({'success': False, 'error': 'Invalid JSON payload.'}), 400

        document_url = req_data.get('documents')
        questions = req_data.get('questions', [])

        if not document_url:
            return jsonify({'success': False, 'error': 'Document URL is missing in the JSON payload.'}), 400
        if not isinstance(questions, list) or not questions:
            return jsonify({'success': False, 'error': 'Questions array is missing or empty in the JSON payload.'}), 400

        current_document.update({
            'chunks': None,
            'embeddings': None,
            'index': None,
            'model_st': None,
            'source_url': None,
            'filename': None,
            'upload_time': None,
            'chunk_count': 0,
            'questions': [],
            'answers': []
        })

        temp_file_path = None
        try:
            parsed_url = urlparse(document_url)
            path_segments = parsed_url.path.split('/')
            
            base_filename = path_segments[-1] if path_segments[-1] else 'document' 

            if '.' not in base_filename:
                return jsonify({'success': False, 'error': f'Could not determine file type from URL: {document_url}. URL must contain a file extension.'}), 400
            
            file_extension = base_filename.rsplit('.', 1)[1].lower()

            if not allowed_file_extension(base_filename):
                return jsonify({'success': False, 'error': f'Unsupported document type from URL: .{file_extension}. Only PDF, DOCX, EML are supported.'}), 400

            print(f"Attempting to download document from: {document_url}")
            response = requests.get(document_url, stream=True)
            response.raise_for_status()

            if int(response.headers.get('content-length', 0)) > MAX_FILE_SIZE:
                return jsonify({'success': False, 'error': f'Downloaded file size exceeds limit ({MAX_FILE_SIZE / (1024*1024)}MB)'}), 413

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}')
            temp_file_path = temp_file.name
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            temp_file.close()

            print(f"Successfully downloaded {base_filename} to {temp_file_path}")

            text = extract_text_from_document(temp_file_path, file_extension)
            chunks, embeddings, index, model_st = create_document_embeddings(text)

            current_document.update({
                'chunks': chunks,
                'embeddings': embeddings,
                'index': index,
                'model_st': model_st,
                'source_url': document_url,
                'filename': base_filename,
                'upload_time': time.strftime('%H:%M:%S'),
                'chunk_count': len(chunks),
                'questions': questions
            })
            
            print(f"Document '{base_filename}' processed with {len(chunks)} chunks. Now answering questions...")

            collected_answers = []
            for q_text in questions:
                try:
                    answer_string = generate_response(
                        q_text, 
                        current_document['chunks'],
                        current_document['embeddings'],
                        current_document['index'],
                        current_document['model_st']
                    )
                    collected_answers.append(answer_string)
                except Exception as question_e:
                    collected_answers.append(f"Error answering question '{q_text}': {str(question_e)}")
                print(f"Answered '{q_text}'")

            current_document['answers'] = collected_answers

            print("All questions answered.")
            # Return JSON in the exact format shown in your sample response image (image_ee6ae5.png)
            return jsonify({'answers': collected_answers}) # Modified: Simpler JSON response
            
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        time.sleep(0.1 * (attempt + 1))
                        os.unlink(temp_file_path)
                        break
                    except PermissionError as e:
                        if attempt == max_retries - 1:
                            print(f"Warning: Could not delete temp file after {max_retries} attempts: {temp_file_path}")
                        else:
                            print(f"Retry {attempt + 1}/{max_retries} to delete temp file: {e}")
                            gc.collect()
                    except Exception as cleanup_error:
                        print(f"Warning: Unexpected error deleting temp file {temp_file_path}: {cleanup_error}")
                        break
        
    except requests.exceptions.RequestException as re:
        error_msg = f"Network or download error: {str(re)}"
        print(f"Download error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500
    except json.JSONDecodeError:
        error_msg = 'Invalid JSON format in request body.'
        print(f"JSON parsing error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 400
    except Exception as e:
        error_msg = f'Error processing request: {str(e)}'
        print(f"Processing error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/clear', methods=['POST'])
def clear_document():
    try:
        current_document.update({
            'chunks': None, 'embeddings': None, 'index': None, 
            'model_st': None, 'source_url': None, 'filename': None, 
            'upload_time': None, 'chunk_count': 0,
            'questions': [], 'answers': []
        })
        return jsonify({'success': True, 'message': 'Document and answers cleared successfully'})
    except Exception as e:
        return jsonify({'error': f'Error clearing document: {str(e)}'}), 500

@app.route('/status')
def get_status():
    return jsonify({
        'document_loaded': current_document['chunks'] is not None,
        'filename': current_document['filename'],
        'source_url': current_document['source_url'],
        'chunks_count': len(current_document['chunks']) if current_document['chunks'] else 0,
        'upload_time': current_document.get('upload_time', None),
        'model_ready': current_document['model_st'] is not None,
        'questions_count': len(current_document['questions']),
        'answers_count': len(current_document['answers'])
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)