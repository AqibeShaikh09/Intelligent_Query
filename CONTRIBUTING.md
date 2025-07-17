# Contributing to PDF Q&A System

Thank you for your interest in contributing to the PDF Q&A System! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pdf-qa-system.git
   cd pdf-qa-system
   ```

3. **Set up the development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Copy environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

## Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** in the appropriate directories:
   - `src/` - Core application code
   - `scripts/` - Utility scripts
   - `docs/` - Documentation

3. **Test your changes**:
   ```bash
   python src/web_app.py  # Test locally
   docker-compose up      # Test with Docker
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: brief description of your changes"
   ```

5. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small

## Testing

- Test your changes locally before submitting
- Ensure Docker build works: `docker build -t test-image .`
- Verify the web interface loads correctly
- Test PDF upload and Q&A functionality

## Pull Request Guidelines

- **Title**: Use a clear, descriptive title
- **Description**: Explain what your PR does and why
- **Testing**: Describe how you tested your changes
- **Screenshots**: Include screenshots for UI changes

## Types of Contributions

### Bug Fixes
- Fix issues with PDF processing
- Improve error handling
- Fix UI/UX problems

### Features
- Add new AI model support
- Improve document processing
- Enhance user interface
- Add new deployment options (Docker, cloud platforms)

### Documentation
- Improve setup instructions
- Add troubleshooting guides
- Update API documentation

### Infrastructure
- Improve Docker configuration
- Add CI/CD workflows
- Optimize deployment scripts

## Reporting Issues

When reporting bugs, please include:

1. **Environment details**: OS, Python version, browser
2. **Steps to reproduce**: Clear, step-by-step instructions
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Screenshots**: If applicable
6. **Logs**: Any error messages or console output

## Questions?

Feel free to open an issue for:
- Questions about the codebase
- Suggestions for improvements
- Discussion about new features

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).
