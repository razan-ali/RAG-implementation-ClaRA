# ClaRA RAG System - Complete Setup Guide

## Quick Start (5 minutes)

### For Linux/Mac:

```bash
# 1. Clone and navigate
cd RAG-implementation-ClaRA

# 2. Make run script executable
chmod +x run.sh

# 3. Run the startup script
./run.sh

# 4. Edit .env file when prompted
nano .env  # or use your preferred editor

# Add your API key:
# OPENAI_API_KEY=sk-your-key-here

# 5. Run again
./run.sh
```

### For Windows:

```cmd
# 1. Navigate to folder
cd RAG-implementation-ClaRA

# 2. Run the startup script
run.bat

# 3. Edit .env file when prompted
notepad .env

# Add your API key:
# OPENAI_API_KEY=sk-your-key-here

# 4. Run again
run.bat
```

## Detailed Step-by-Step Guide

### Step 1: Prerequisites

Ensure you have:
- ✅ Python 3.8 or higher
- ✅ pip (Python package manager)
- ✅ OpenAI API key OR Anthropic API key

Check Python version:
```bash
python --version  # Should show 3.8+
```

### Step 2: Get API Keys

#### Option A: OpenAI (Recommended)

1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

#### Option B: Anthropic

1. Go to https://console.anthropic.com/
2. Sign in or create account
3. Navigate to API Keys
4. Create and copy your key

### Step 3: Install Dependencies

#### Automatic (Recommended):
```bash
./run.sh  # Linux/Mac
run.bat   # Windows
```

#### Manual:
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

### Step 4: Configure Environment

1. **Copy example config:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file:**
   ```bash
   nano .env  # or use any text editor
   ```

3. **Add your API key:**
   ```env
   # For OpenAI:
   OPENAI_API_KEY=sk-your-actual-key-here

   # OR for Anthropic:
   ANTHROPIC_API_KEY=your-anthropic-key-here
   ```

4. **Optional settings:**
   ```env
   # Change these if needed:
   PORT=8000
   DEBUG=True
   ENABLE_CLARIFICATIONS=True
   MAX_CLARIFICATION_QUESTIONS=3
   TOP_K_DOCUMENTS=5
   ```

### Step 5: Run the Application

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Access the Interface

Open your browser to:
- **Main Interface:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc

## First Time Usage

### 1. Upload a Document

- Click "Click to select a file"
- Choose a PDF, DOCX, TXT, CSV, or XLSX file
- Click "Upload Document"
- Wait for processing (usually 5-30 seconds)

### 2. Ask Questions

Simple question:
```
Q: "What is this document about?"
```

Potentially ambiguous question:
```
Q: "What improvements were made?"

ClaRA will ask: "What type of improvements?"
- Technical improvements
- Process improvements
- Product improvements

You select: "Technical improvements"

ClaRA provides targeted answer about technical improvements
```

## Troubleshooting

### Issue: Port 8000 already in use

**Solution:** Change port in `.env`:
```env
PORT=8080
```

Then access at http://localhost:8080

### Issue: "No module named 'fastapi'"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "No LLM API key provided"

**Solution:** Check `.env` file has:
```env
OPENAI_API_KEY=sk-your-key-here
```

### Issue: ChromaDB errors

**Solution:** Delete and recreate vector database:
```bash
rm -rf vector_db
python main.py
```

### Issue: Document upload fails

**Possible causes:**
1. File too large (>50MB)
2. Corrupted file
3. Unsupported format

**Solution:** Try a smaller, different file first.

### Issue: Slow responses

**Causes:**
- Large documents
- Many chunks
- LLM API latency

**Solutions:**
1. Reduce `TOP_K_DOCUMENTS` in `.env`
2. Use smaller documents
3. Check API quota/limits

## Testing Your Setup

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### 2. Upload Test Document

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test.txt"
```

### 3. Query Test

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this about?"}'
```

## Advanced Configuration

### Using Different Embedding Models

In `.env`:
```env
# Fast, smaller model (default):
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Better quality, slower:
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# Multilingual:
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### Using Different LLM Models

```env
# OpenAI:
LLM_MODEL=gpt-4-turbo-preview
LLM_MODEL=gpt-3.5-turbo

# Anthropic (requires ANTHROPIC_API_KEY):
LLM_MODEL=claude-3-opus-20240229
LLM_MODEL=claude-3-sonnet-20240229
```

### Adjusting Chunking

Edit `main.py`:
```python
document_processor = DocumentProcessor(
    chunk_size=1000,    # Increase for longer chunks
    chunk_overlap=200   # Increase for more context
)
```

## Production Deployment

### Using Gunicorn (Production Server)

```bash
pip install gunicorn

gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t clara-rag .
docker run -p 8000:8000 --env-file .env clara-rag
```

## Next Steps

1. ✅ Upload your documents
2. ✅ Try asking questions
3. ✅ Experience ClaRA's clarifications
4. ✅ Explore API documentation at `/docs`
5. ✅ Customize settings in `.env`
6. ✅ Integrate with your applications

## Getting Help

- Check README.md for detailed documentation
- Review API docs at http://localhost:8000/docs
- Check logs for error messages
- Ensure API keys are valid and have quota

## Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **ChromaDB Documentation:** https://docs.trychroma.com/
- **OpenAI API:** https://platform.openai.com/docs
- **Anthropic API:** https://docs.anthropic.com/

---

**You're all set! Enjoy using ClaRA RAG System! 🚀**
