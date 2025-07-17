# PDF Question-Answer System

A web application that allows users to upload PDF documents and ask questions about their content using AI.

## Features

- 📄 **PDF Upload**: Drag & drop PDF files up to 16MB
- 🤖 **AI-Powered Q&A**: Ask questions and get intelligent answers
- 🎨 **Beautiful UI**: Modern, responsive web interface
- ⚡ **Fast Processing**: Quick document analysis and response generation
- 🔒 **Secure**: Files are processed temporarily and not stored permanently

## Technologies Used

- **Backend**: Flask, Python
- **AI**: OpenRouter API for accessing multiple AI models (Claude, GPT, etc.)
- **Document Processing**: pdfplumber for PDF text extraction
- **Search**: FAISS for semantic similarity search
- **ML**: Sentence Transformers for embeddings
- **Frontend**: Bootstrap 5, vanilla JavaScript

## Project Structure

```
pdf-qa-system/
├── src/                    # Source code
│   ├── app.py             # Core AI/PDF processing
│   └── web_app.py         # Flask web application
├── scripts/               # Setup and utility scripts
├── docs/                  # Documentation
├── .github/workflows/     # CI/CD workflows
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Multi-container setup
├── CONTRIBUTING.md       # Contribution guidelines
└── README.md             # This file
```

## Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd pdf-qa-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

4. **Run the application**
```bash
python src/web_app.py
```

5. **Open browser**
```
http://localhost:5000
```

## Docker Deployment

### Local Docker

1. **Build and run with Docker**
```bash
docker build -t pdf-qa-system .
docker run -p 5000:5000 --env-file .env pdf-qa-system
```

2. **Or use Docker Compose**
```bash
docker-compose up -d
```

## Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `SECRET_KEY`: Flask secret key (optional, auto-generated if not set)
- `PORT`: Port number (default: 5000)

## API Endpoints

- `GET /`: Main application interface
- `POST /upload`: Upload and process PDF file
- `POST /ask`: Ask questions about uploaded PDF
- `POST /clear`: Clear current document from memory

## Usage

1. **Upload PDF**: Click "Upload & Process PDF" and select your file
2. **Ask Questions**: Type questions in the chat interface
3. **Get Answers**: Receive AI-powered responses with justification
4. **Clear Document**: Remove current PDF and start fresh

## Example Questions

- "What is this document about?"
- "Summarize the key points"
- "What are the main requirements?"
- "Is [specific topic] covered in this document?"

## Limitations

- Maximum file size: 16MB
- Supported format: PDF only
- Files are processed temporarily (not stored permanently)
- Free tier limitations apply for OpenRouter API

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.
