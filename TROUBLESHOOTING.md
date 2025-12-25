# Troubleshooting Guide

## Issue: Chatbot can't answer simple questions

### Most Common Causes:

#### 1. **No Documents Uploaded Yet** ❌
**Problem:** The system has no documents to search
**Solution:**
- Upload at least one document using the web interface
- The chatbot needs documents to answer questions!

#### 2. **API Key Not Set** ❌
**Problem:** No LLM API key configured
**Symptoms:** Errors in console, no responses
**Solution:**
```bash
# Check if .env file exists
cat .env

# If not, copy from example
cp .env.example .env

# Edit and add your API key
nano .env  # or use any text editor

# Add one of these:
OPENAI_API_KEY=sk-your-actual-key-here
# OR
ANTHROPIC_API_KEY=your-anthropic-key-here
```

#### 3. **Clarifications Too Aggressive** ❌
**Problem:** System asks clarifying questions for everything
**Solution:** Disable clarifications in `.env`:
```bash
ENABLE_CLARIFICATIONS=False
```

#### 4. **Poor Document Retrieval** ❌
**Problem:** Vector search not finding relevant chunks
**Solution:** Lower the similarity threshold in `.env`:
```bash
SIMILARITY_THRESHOLD=0.3  # Lower = more lenient
TOP_K_DOCUMENTS=10        # Get more results
```

#### 5. **LLM Model Issues** ❌
**Problem:** Using wrong or unavailable model
**Solution:** Check your model in `.env`:
```bash
# For OpenAI:
LLM_MODEL=gpt-3.5-turbo  # Cheaper, faster (try this first!)
# OR
LLM_MODEL=gpt-4-turbo-preview  # Better quality

# For Anthropic:
LLM_MODEL=claude-3-sonnet-20240229  # Good balance
# OR
LLM_MODEL=claude-3-opus-20240229  # Best quality
```

---

## Quick Diagnostic Checklist

Run through this checklist:

### ✓ Step 1: Check Server is Running
```bash
# Should see: "Uvicorn running on http://0.0.0.0:8000"
# If not running, start it:
python main.py
```

### ✓ Step 2: Check API Key
```bash
cat .env | grep API_KEY
# Should show your API key (not "your_openai_api_key_here")
```

### ✓ Step 3: Upload a Test Document
1. Go to http://localhost:8000
2. Upload ANY document (PDF, TXT, etc.)
3. Wait for "Upload successful" message

### ✓ Step 4: Check Documents Are Stored
```bash
# Run in Python:
python -c "
from vector_store import VectorStore
vs = VectorStore()
stats = vs.get_collection_stats()
print(f'Documents: {stats[\"total_documents\"]}')
print(f'Chunks: {stats[\"total_chunks\"]}')
"
```

Should show at least 1 document and multiple chunks!

### ✓ Step 5: Try Simple Query
Ask: **"What is this document about?"**

**Expected:** Clear answer
**If you get:** "I need clarification..." → Disable clarifications in `.env`

---

## Recommended Settings for Best Performance

Edit your `.env` file:

```bash
# Use GPT-3.5 for faster, cheaper responses
LLM_MODEL=gpt-3.5-turbo

# Disable clarifications initially
ENABLE_CLARIFICATIONS=False

# More lenient retrieval
SIMILARITY_THRESHOLD=0.3
TOP_K_DOCUMENTS=8

# Slightly higher temperature for more natural responses
LLM_TEMPERATURE=0.8
```

---

## Testing the System

### Test 1: Simple Question
```
Upload: Any document
Ask: "What is this document about?"
Expected: Clear summary
```

### Test 2: Specific Question
```
Upload: Company report
Ask: "What is the revenue?"
Expected: Specific answer with numbers
```

### Test 3: Clarification (if enabled)
```
Upload: Technical document
Ask: "What about performance?"
Expected: Clarifying question OR direct answer
```

---

## Common Error Messages

### "No LLM API key provided"
**Fix:** Add API key to `.env` file

### "Error processing document"
**Fix:**
- Check file format is supported (PDF, DOCX, TXT, CSV, XLSX)
- Try a smaller file first
- Check file isn't corrupted

### "ChromaDB error"
**Fix:**
```bash
rm -rf vector_db/
# Restart server
python main.py
```

### Empty or "I don't know" responses
**Fix:**
1. Make sure documents are uploaded
2. Lower `SIMILARITY_THRESHOLD` to 0.3
3. Increase `TOP_K_DOCUMENTS` to 10
4. Try `gpt-3.5-turbo` model

---

## Debug Mode

Add print statements to see what's happening:

Edit `clara_engine.py`, add this after line 85:

```python
print(f"DEBUG: Found {len(retrieved_docs)} documents")
print(f"DEBUG: Top relevance score: {retrieved_docs[0].relevance_score if retrieved_docs else 'N/A'}")
```

Restart server and watch console output!

---

## Still Not Working?

### Get Detailed Logs:

```python
# Create debug_test.py
from clara_engine import ClaRAEngine
from vector_store import VectorStore
from models import QueryRequest

vs = VectorStore()
clara = ClaRAEngine(vs)

# Check stats
stats = vs.get_collection_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"Total chunks: {stats['total_chunks']}")

# Try a search
results = vs.search("test query", top_k=5)
print(f"Search results: {len(results)}")
for i, r in enumerate(results):
    print(f"  {i+1}. Relevance: {r.relevance_score:.2f}")
    print(f"     Content: {r.chunk.content[:100]}...")
```

Run: `python debug_test.py`

---

## Best Practices

1. **Start Simple:**
   - Disable clarifications
   - Use gpt-3.5-turbo
   - Upload small test document first

2. **Test Incrementally:**
   - One document → test
   - Add more → test again
   - Enable clarifications → test

3. **Monitor Costs:**
   - gpt-3.5-turbo = ~$0.001 per query
   - gpt-4 = ~$0.03 per query
   - Start with 3.5!

4. **Document Quality:**
   - Clear, well-formatted documents work best
   - PDFs with actual text (not scanned images)
   - Reasonable size (< 10MB)

---

## Need More Help?

Check the logs in your terminal where the server is running. Errors will show there!
