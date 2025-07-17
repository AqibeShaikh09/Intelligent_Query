# Project Structure

```
pdf-qa-system/
├── src/                          # Source code
│   ├── __init__.py              # Package initialization
│   ├── app.py                   # Core AI/PDF processing logic
│   └── web_app.py               # Flask web application
├── scripts/                     # Utility scripts
│   ├── setup-docker.bat        # Docker setup (Windows)
│   ├── setup-ngrok.bat         # Ngrok setup (Windows)
│   ├── start-ngrok.bat         # Start ngrok tunnel
│   ├── start-server.bat        # Start server (Windows)
│   ├── test_openai_docker.py   # OpenAI API test
│   ├── test_openrouter.py      # OpenRouter API test
│   └── simple_test.py          # Simple functionality test
├── docs/                        # Documentation
│   ├── DOCKER_README.md        # Docker setup guide
│   ├── NGROK-SETUP.md          # Ngrok setup guide
│   └── README-DOCKERHUB.md     # Docker Hub deployment guide
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── .gitattributes              # Git attributes for line endings
├── .dockerignore               # Docker ignore rules
├── Dockerfile                   # Docker container definition
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt             # Python dependencies
└── README.md                    # Main project documentation
```

## Key Files

### Source Code (`src/`)
- **app.py**: Core AI and PDF processing functionality
- **web_app.py**: Flask web application with UI

### Configuration
- **.env.example**: Template for environment variables
- **requirements.txt**: Python package dependencies
- **Dockerfile**: Container configuration
- **docker-compose.yml**: Multi-container setup

### Documentation (`docs/`)
- Deployment guides
- Setup instructions
- API documentation
