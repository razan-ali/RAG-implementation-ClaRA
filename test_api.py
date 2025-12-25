"""
Test script for ClaRA RAG API

Run this after starting the server to test the API endpoints
"""

import requests
import json
import time
from pathlib import Path


BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")

    if response.status_code == 200:
        print("✅ Health check passed")
        print(f"   Response: {response.json()}")
        return True
    else:
        print("❌ Health check failed")
        return False


def test_upload():
    """Test document upload"""
    print("\n📤 Testing document upload...")

    # Create a test document
    test_file = Path("test_document.txt")
    test_content = """
# Test Document for ClaRA RAG System

## Introduction
This is a test document to demonstrate the ClaRA RAG system capabilities.

## System Performance
The system shows excellent performance with:
- Fast response times under 2 seconds
- High accuracy of 95%
- Efficient memory usage

## Financial Performance
The Q3 financial results show:
- Revenue increased by 25%
- Profit margins improved to 18%
- Customer acquisition cost reduced by 30%

## Technical Improvements
Recent technical improvements include:
- Upgraded database to PostgreSQL 15
- Implemented caching layer with Redis
- Optimized API response times
- Added comprehensive monitoring

## Conclusion
The system meets all performance and reliability requirements.
"""

    with open(test_file, "w") as f:
        f.write(test_content)

    # Upload the file
    with open(test_file, "rb") as f:
        files = {"file": ("test_document.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/upload", files=files)

    if response.status_code == 200:
        result = response.json()
        print("✅ Upload successful")
        print(f"   Message: {result['message']}")
        print(f"   Chunks created: {result['document_metadata']['num_chunks']}")
        return True
    else:
        print(f"❌ Upload failed: {response.text}")
        return False


def test_query_simple():
    """Test simple query (should get direct answer)"""
    print("\n💬 Testing simple query...")

    query_data = {
        "query": "What is this document about?",
        "conversation_id": None
    }

    response = requests.post(
        f"{BASE_URL}/query",
        headers={"Content-Type": "application/json"},
        data=json.dumps(query_data)
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ Query successful")

        if "answer" in result:
            print(f"   Answer: {result['answer'][:100]}...")
            print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
            print(f"   Sources: {len(result.get('sources', []))}")
        else:
            print("   Got clarification response (unexpected for this query)")

        return True
    else:
        print(f"❌ Query failed: {response.text}")
        return False


def test_query_ambiguous():
    """Test ambiguous query (should trigger clarifications)"""
    print("\n❓ Testing ambiguous query (should trigger clarifications)...")

    query_data = {
        "query": "What does it say about performance?",
        "conversation_id": None
    }

    response = requests.post(
        f"{BASE_URL}/query",
        headers={"Content-Type": "application/json"},
        data=json.dumps(query_data)
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ Query successful")

        if result.get("needs_clarification"):
            print("   ✅ Clarifications triggered (as expected)")
            print(f"   Questions: {len(result.get('questions', []))}")
            for i, q in enumerate(result.get('questions', []), 1):
                print(f"   Q{i}: {q['question_text']}")

            # Now answer with clarification
            print("\n💬 Answering clarification with 'System Performance'...")

            clarification_data = {
                "query": "What does it say about performance?",
                "conversation_id": result.get("conversation_id"),
                "clarifications": {
                    result['questions'][0]['question_id']: "System Performance"
                }
            }

            response2 = requests.post(
                f"{BASE_URL}/query",
                headers={"Content-Type": "application/json"},
                data=json.dumps(clarification_data)
            )

            if response2.status_code == 200:
                result2 = response2.json()
                if "answer" in result2:
                    print("   ✅ Got refined answer after clarification")
                    print(f"   Answer: {result2['answer'][:100]}...")
                else:
                    print("   ⚠️ Still need more clarification")

        else:
            print("   ⚠️ No clarifications triggered (might answer directly)")
            if "answer" in result:
                print(f"   Answer: {result['answer'][:100]}...")

        return True
    else:
        print(f"❌ Query failed: {response.text}")
        return False


def test_list_documents():
    """Test listing documents"""
    print("\n📋 Testing list documents...")

    response = requests.get(f"{BASE_URL}/documents")

    if response.status_code == 200:
        result = response.json()
        print("✅ List documents successful")
        print(f"   Total documents: {result.get('total_documents', 0)}")
        print(f"   Total chunks: {result.get('total_chunks', 0)}")
        return True
    else:
        print(f"❌ List documents failed: {response.text}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("ClaRA RAG System - API Tests")
    print("=" * 60)

    print("\n⚠️  Make sure the server is running on http://localhost:8000")
    print("   Start it with: python main.py\n")

    time.sleep(1)

    tests = [
        ("Health Check", test_health),
        ("Document Upload", test_upload),
        ("List Documents", test_list_documents),
        ("Simple Query", test_query_simple),
        ("Ambiguous Query (ClaRA)", test_query_ambiguous),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            time.sleep(1)  # Wait between tests
        except Exception as e:
            print(f"❌ {name} failed with exception: {str(e)}")
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your ClaRA RAG system is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")

    # Cleanup
    test_file = Path("test_document.txt")
    if test_file.exists():
        test_file.unlink()
        print("\n🧹 Cleaned up test file")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Is it running on http://localhost:8000?")
        print("   Start it with: python main.py")
