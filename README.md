# ClaRA RAG System

A Retrieval-Augmented Generation (RAG) system implementing Apple's **ClaRA (Clarifying Retrieval-Augmented)** approach, built with Python and FastAPI.

## Features

- **Intelligent Clarifications**: Automatically detects ambiguous queries and asks clarifying questions
- **Multi-Format Support**: PDF, DOCX, TXT, CSV, XLSX
- **Vector-Based Retrieval**: Fast and accurate document retrieval using ChromaDB
- **Modern Web Interface**: Clean, responsive UI for document upload and Q&A
- **RESTful API**: Well-documented FastAPI endpoints
- **Confidence Scoring**: AI provides confidence levels for answers

## What is ClaRA?

ClaRA (Clarifying Retrieval-Augmented Generation) improves traditional RAG by:

1. **Analyzing Query Ambiguity**: Determines if user queries need clarification
2. **Generating Clarifying Questions**: Asks targeted questions to better understand intent
3. **Iterative Refinement**: Uses clarifications to improve document retrieval
4. **Better Answers**: Provides more accurate responses based on refined context

## Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  FastAPI Server │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│Document │ │ ClaRA Engine │
│Processor│ └──────┬───────┘
└────┬────┘        │
     │             │
     ▼             ▼
┌──────────────────────┐
│   Vector Store       │
│   (ChromaDB)         │
└──────────────────────┘
          │
          ▼
    ┌──────────┐
    │   LLM    │
    │(GPT/Claude)│
    └──────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key or Anthropic API key

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RAG-implementation-ClaRA
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   # OR
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Access the interface**
   Open your browser to: `http://localhost:8000`

## Usage

### Web Interface

1. **Upload Documents**
   - Click "Click to select a file" in the left panel
   - Choose a supported document (PDF, DOCX, TXT, CSV, XLSX)
   - Click "Upload Document"

2. **Ask Questions**
   - Type your question in the chat input
   - Press Enter or click "Send"
   - If your question is ambiguous, ClaRA will ask clarifying questions
   - Answer the clarifications to get a better response

### API Endpoints

#### Upload Document
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"
```

#### Query with ClaRA
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main findings?",
    "conversation_id": null
  }'
```

#### List Documents
```bash
curl "http://localhost:8000/documents"
```

#### Delete Document
```bash
curl -X DELETE "http://localhost:8000/documents/{document_id}"
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

Edit `.env` to customize settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `LLM_MODEL` | LLM model to use | `gpt-4-turbo-preview` |
| `TOP_K_DOCUMENTS` | Number of docs to retrieve | `5` |
| `ENABLE_CLARIFICATIONS` | Enable ClaRA clarifications | `True` |
| `MAX_CLARIFICATION_QUESTIONS` | Max clarifying questions | `3` |
| `SIMILARITY_THRESHOLD` | Relevance threshold | `0.7` |

## Project Structure

```
RAG-implementation-ClaRA/
├── main.py                 # FastAPI application
├── config.py               # Configuration settings
├── models.py               # Pydantic models
├── document_processor.py   # Document parsing and chunking
├── vector_store.py         # Vector database interface
├── clara_engine.py         # ClaRA implementation
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── static/
│   └── index.html          # Web interface
├── uploads/                # Uploaded documents (auto-created)
└── vector_db/              # Vector database (auto-created)
```

## How ClaRA Works

### 1. Query Analysis
```python
# User asks: "What does it say about performance?"

# ClaRA analyzes and determines this is ambiguous
# Multiple aspects could be "performance":
# - System performance
# - Financial performance
# - Employee performance
```

### 2. Clarification Generation
```python
# ClaRA generates targeted questions:
{
  "needs_clarification": true,
  "questions": [
    {
      "question_text": "What type of performance are you interested in?",
      "suggested_options": ["System Performance", "Financial Performance", "Employee Performance"]
    }
  ]
}
```

### 3. Refined Retrieval
```python
# User responds: "Financial Performance"

# ClaRA refines the query:
# Original: "What does it say about performance?"
# Refined: "What does it say about performance? Financial Performance"

# Retrieval now focuses on financial metrics
```

### 4. Better Answer
```python
# ClaRA provides accurate answer with sources
{
  "answer": "According to the Q3 report, financial performance...",
  "confidence_score": 0.92,
  "sources": [...]
}
```

## Example Queries

### Without Clarification
```
Q: "Tell me about the results"
A: [Direct answer if documents clearly show one type of results]
```

### With Clarification
```
Q: "What improvements were made?"
ClaRA: "What kind of improvements are you asking about?"
       - Technical improvements
       - Process improvements
       - Product improvements

User: "Technical improvements"
A: [Targeted answer about technical improvements with high confidence]
```

## Development

### Running Tests
```bash
pytest tests/
```

### Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Issue: "No LLM API key provided"
**Solution**: Add either `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` to your `.env` file

### Issue: "Error processing document"
**Solution**: Ensure the document is in a supported format and not corrupted

### Issue: "ChromaDB error"
**Solution**: Delete the `vector_db` folder and restart the application

## Technologies Used

- **FastAPI**: Modern web framework
- **ChromaDB**: Vector database
- **Sentence Transformers**: Document embeddings
- **LangChain**: Text processing
- **OpenAI/Anthropic**: LLM integration
- **PyPDF2, python-docx, pandas**: Document parsing

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Citation

If you use this implementation in your research, please cite:

```bibtex
@software{clara_rag_2024,
  title={ClaRA RAG System},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/RAG-implementation-ClaRA}
}
```

## Acknowledgments

- Inspired by Apple's ClaRA approach to retrieval-augmented generation
- Built with modern Python RAG stack

## Support

For issues and questions:
- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review example queries above

---

**Happy querying with ClaRA!**
