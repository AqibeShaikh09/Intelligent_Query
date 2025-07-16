from flask import Flask, request, jsonify, render_template_string, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from app import extract_text_from_pdf, create_document_embeddings, generate_response
import tempfile
import traceback

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Global variables to store processed document data
current_document = {
    'chunks': None,
    'embeddings': None,
    'index': None,
    'model_st': None,
    'filename': None
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML Template as string (for Render compatibility)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Question-Answer System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .main-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        .chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 1rem;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 1rem;
            padding: 0.75rem;
            border-radius: 10px;
            max-width: 80%;
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: auto;
            margin-right: 0;
        }
        .bot-message {
            background: white;
            border: 1px solid #e9ecef;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .loading {
            display: none;
        }
        .file-upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 3rem 2rem;
            text-align: center;
            transition: all 0.3s;
            background: rgba(102, 126, 234, 0.05);
        }
        .file-upload-area:hover {
            border-color: #764ba2;
            background: rgba(118, 75, 162, 0.1);
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 25px;
            padding: 0.75rem 2rem;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        .card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px 15px 0 0 !important;
            border: none;
        }
        .alert {
            border-radius: 10px;
            border: none;
        }
        .spinner-border {
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container-fluid py-4">
        <div class="row justify-content-center">
            <div class="col-lg-10 col-xl-8">
                <div class="main-container p-4">
                    <div class="text-center mb-4">
                        <h1 class="display-4 fw-bold">
                            <i class="fas fa-file-pdf text-danger me-3"></i>
                            PDF Q&A System
                        </h1>
                        <p class="lead text-muted">Upload a PDF document and ask questions about its content</p>
                    </div>

                    <!-- Flash Messages -->
                    {% with messages = get_flashed_messages() %}
                        {% if messages %}
                            {% for message in messages %}
                                <div class="alert alert-info alert-dismissible fade show" role="alert">
                                    <i class="fas fa-info-circle me-2"></i>{{ message }}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                </div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}

                    {% if not document_loaded %}
                    <!-- File Upload Section -->
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="mb-0"><i class="fas fa-upload me-2"></i>Upload PDF Document</h5>
                        </div>
                        <div class="card-body">
                            <form action="/upload" method="post" enctype="multipart/form-data" id="uploadForm">
                                <div class="file-upload-area">
                                    <div class="mb-3">
                                        <i class="fas fa-cloud-upload-alt fa-4x text-primary mb-3"></i>
                                        <h5>Drag & Drop or Click to Upload</h5>
                                        <p class="text-muted mb-3">Select a PDF file to analyze (Max 16MB)</p>
                                    </div>
                                    <input type="file" name="file" accept=".pdf" class="form-control mb-3" id="fileInput" required>
                                    <button type="submit" class="btn btn-primary btn-lg">
                                        <i class="fas fa-upload me-2"></i>Upload & Process PDF
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>

                    <!-- Features Section -->
                    <div class="row text-center">
                        <div class="col-md-4 mb-3">
                            <div class="card h-100">
                                <div class="card-body">
                                    <i class="fas fa-search fa-2x text-primary mb-3"></i>
                                    <h6>Smart Search</h6>
                                    <p class="text-muted small">AI-powered semantic search through your documents</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-3">
                            <div class="card h-100">
                                <div class="card-body">
                                    <i class="fas fa-robot fa-2x text-success mb-3"></i>
                                    <h6>AI Assistant</h6>
                                    <p class="text-muted small">Get intelligent answers powered by Gemini AI</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-3">
                            <div class="card h-100">
                                <div class="card-body">
                                    <i class="fas fa-bolt fa-2x text-warning mb-3"></i>
                                    <h6>Instant Results</h6>
                                    <p class="text-muted small">Fast processing and real-time responses</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endif %}

                    {% if document_loaded %}
                    <!-- Question-Answer Section -->
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">
                                <i class="fas fa-comments me-2"></i>Chat with: {{ filename }}
                            </h5>
                            <button class="btn btn-outline-light btn-sm" onclick="clearDocument()">
                                <i class="fas fa-trash me-1"></i>Clear Document
                            </button>
                        </div>
                        <div class="card-body">
                            <!-- Chat Container -->
                            <div id="chatContainer" class="chat-container mb-3">
                                <div class="text-center text-muted">
                                    <i class="fas fa-comments fa-2x mb-2"></i>
                                    <p>Start by asking a question about your PDF document!</p>
                                </div>
                            </div>

                            <!-- Question Input -->
                            <div class="input-group">
                                <input type="text" id="questionInput" class="form-control form-control-lg" 
                                       placeholder="Ask a question about the PDF..." 
                                       onkeypress="handleKeyPress(event)">
                                <button class="btn btn-primary" onclick="askQuestion()">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </div>

                            <!-- Loading Indicator -->
                            <div id="loading" class="loading mt-3">
                                <div class="text-center">
                                    <div class="spinner-border" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p class="mt-2 text-muted">Processing your question...</p>
                                </div>
                            </div>

                            <!-- Example Questions -->
                            <div class="mt-3">
                                <small class="text-muted">Try asking:</small>
                                <div class="mt-2">
                                    <button class="btn btn-outline-secondary btn-sm me-2 mb-2" onclick="askSampleQuestion('What is this document about?')">
                                        What is this document about?
                                    </button>
                                    <button class="btn btn-outline-secondary btn-sm me-2 mb-2" onclick="askSampleQuestion('Summarize the key points')">
                                        Summarize the key points
                                    </button>
                                    <button class="btn btn-outline-secondary btn-sm me-2 mb-2" onclick="askSampleQuestion('What are the main requirements?')">
                                        What are the main requirements?
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                askQuestion();
            }
        }

        function askSampleQuestion(question) {
            document.getElementById('questionInput').value = question;
            askQuestion();
        }

        function askQuestion() {
            const questionInput = document.getElementById('questionInput');
            const question = questionInput.value.trim();
            
            if (!question) {
                alert('Please enter a question');
                return;
            }

            addMessageToChat(question, 'user');
            questionInput.value = '';
            document.getElementById('loading').style.display = 'block';
            questionInput.disabled = true;

            fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                questionInput.disabled = false;
                if (data.success) {
                    addResponseToChat(data.response);
                } else {
                    addMessageToChat(`Error: ${data.error}`, 'bot');
                }
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                questionInput.disabled = false;
                addMessageToChat(`Error: ${error.message}`, 'bot');
            });
        }

        function addMessageToChat(message, sender) {
            const chatContainer = document.getElementById('chatContainer');
            
            // Clear the initial message if it exists
            if (chatContainer.querySelector('.text-center')) {
                chatContainer.innerHTML = '';
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'AI Assistant'}:</strong><br>${message}`;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function addResponseToChat(response) {
            const chatContainer = document.getElementById('chatContainer');
            
            // Clear the initial message if it exists
            if (chatContainer.querySelector('.text-center')) {
                chatContainer.innerHTML = '';
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot-message';
            
            let responseHtml = '<strong>AI Assistant:</strong><br>';
            responseHtml += `<div class="mt-2">`;
            responseHtml += `<strong>Decision:</strong> <span class="badge bg-primary">${response.decision}</span><br>`;
            if (response.amount && response.amount !== 'null') {
                responseHtml += `<strong>Amount:</strong> ${response.amount}<br>`;
            }
            responseHtml += `<strong>Explanation:</strong><br>${response.justification}`;
            responseHtml += `</div>`;
            
            messageDiv.innerHTML = responseHtml;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function clearDocument() {
            if (confirm('Are you sure you want to clear the current document?')) {
                fetch('/clear', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                .then(response => response.json())
                .then(data => {
                    if (data.success) location.reload();
                    else alert(`Error: ${data.error}`);
                })
                .catch(error => alert(`Error: ${error.message}`));
            }
        }

        // File upload enhancements
        document.addEventListener('DOMContentLoaded', function() {
            const fileInput = document.getElementById('fileInput');
            const uploadForm = document.getElementById('uploadForm');
            
            if (fileInput) {
                fileInput.addEventListener('change', function() {
                    const file = this.files[0];
                    if (file) {
                        if (file.type !== 'application/pdf') {
                            alert('Please select a PDF file');
                            this.value = '';
                            return;
                        }
                        if (file.size > 16 * 1024 * 1024) {
                            alert('File size must be less than 16MB');
                            this.value = '';
                            return;
                        }
                    }
                });
                
                uploadForm.addEventListener('submit', function() {
                    const submitBtn = this.querySelector('button[type="submit"]');
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                    submitBtn.disabled = true;
                });
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                document_loaded=current_document['chunks'] is not None,
                                filename=current_document['filename'])

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(url_for('index'))
        
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            flash('Please upload a valid PDF file')
            return redirect(url_for('index'))
        
        # Save file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            
            # Process the PDF
            text = extract_text_from_pdf(temp_file.name)
            chunks, embeddings, index, model_st = create_document_embeddings(text)
            
            # Store in global variables
            current_document.update({
                'chunks': chunks,
                'embeddings': embeddings,
                'index': index,
                'model_st': model_st,
                'filename': secure_filename(file.filename)
            })
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
        flash(f'✅ PDF "{file.filename}" uploaded and processed successfully! You can now ask questions.')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'❌ Error processing file: {str(e)}')
        print(f"Upload error: {traceback.format_exc()}")
        return redirect(url_for('index'))

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Please enter a question'}), 400
        
        if current_document['chunks'] is None:
            return jsonify({'error': 'Please upload a PDF first'}), 400
        
        # Generate response
        response = generate_response(
            question, 
            current_document['chunks'],
            current_document['embeddings'],
            current_document['index'],
            current_document['model_st']
        )
        
        # Parse the JSON response
        try:
            response_data = json.loads(response)
            return jsonify({'success': True, 'response': response_data})
        except json.JSONDecodeError:
            return jsonify({
                'success': True,
                'response': {
                    'decision': 'Response received',
                    'amount': None,
                    'justification': response
                }
            })
            
    except Exception as e:
        print(f"Question processing error: {traceback.format_exc()}")
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_document():
    try:
        current_document.update({
            'chunks': None, 'embeddings': None, 'index': None, 
            'model_st': None, 'filename': None
        })
        return jsonify({'success': True, 'message': 'Document cleared successfully'})
    except Exception as e:
        return jsonify({'error': f'Error clearing document: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
