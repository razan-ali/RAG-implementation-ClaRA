"""
Example usage of ClaRA RAG System

This script demonstrates how to use the ClaRA RAG system programmatically
"""

import requests
import json
from pathlib import Path


class ClaRAClient:
    """Simple client for ClaRA RAG API"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.conversation_id = None

    def upload_document(self, file_path):
        """Upload a document"""
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            response = requests.post(f"{self.base_url}/upload", files=files)
            response.raise_for_status()
            return response.json()

    def query(self, question, clarifications=None):
        """Ask a question"""
        data = {
            "query": question,
            "conversation_id": self.conversation_id,
            "clarifications": clarifications
        }

        response = requests.post(
            f"{self.base_url}/query",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        response.raise_for_status()
        result = response.json()

        # Save conversation ID for follow-up queries
        if "conversation_id" in result:
            self.conversation_id = result["conversation_id"]

        return result

    def list_documents(self):
        """List all uploaded documents"""
        response = requests.get(f"{self.base_url}/documents")
        response.raise_for_status()
        return response.json()

    def clear_documents(self):
        """Clear all documents"""
        response = requests.delete(f"{self.base_url}/documents")
        response.raise_for_status()
        return response.json()


def example_basic_usage():
    """Example: Basic document upload and query"""
    print("\n" + "="*60)
    print("Example 1: Basic Usage")
    print("="*60)

    client = ClaRAClient()

    # Create a sample document
    sample_doc = "sample_doc.txt"
    with open(sample_doc, "w") as f:
        f.write("""
        Product Manual - SmartWidget Pro

        Overview:
        SmartWidget Pro is an advanced widget with AI capabilities.
        Price: $299
        Weight: 1.2 kg
        Battery life: 48 hours

        Features:
        - Voice control
        - Wireless charging
        - Water resistant (IP67)
        - 5-year warranty

        Setup Instructions:
        1. Charge for 4 hours before first use
        2. Download the SmartWidget app
        3. Pair via Bluetooth
        4. Follow in-app setup wizard
        """)

    # Upload document
    print("\n📤 Uploading document...")
    result = client.upload_document(sample_doc)
    print(f"✅ {result['message']}")

    # Ask a question
    print("\n💬 Asking: 'How much does it cost?'")
    response = client.query("How much does it cost?")

    if "answer" in response:
        print(f"\n🤖 Answer: {response['answer']}")
        print(f"📊 Confidence: {response['confidence_score']:.0%}")
    else:
        print("❓ ClaRA needs clarification")

    # Cleanup
    Path(sample_doc).unlink()


def example_clarification_workflow():
    """Example: Handling clarifications"""
    print("\n" + "="*60)
    print("Example 2: ClaRA Clarification Workflow")
    print("="*60)

    client = ClaRAClient()

    # Create document with ambiguous content
    sample_doc = "company_report.txt"
    with open(sample_doc, "w") as f:
        f.write("""
        Q3 Company Report

        Technical Performance:
        - API response time: 150ms
        - System uptime: 99.9%
        - Bug fix rate improved by 40%

        Financial Performance:
        - Revenue: $5.2M
        - Profit margin: 22%
        - Growth rate: 35% YoY

        Team Performance:
        - Employee satisfaction: 4.2/5
        - Retention rate: 92%
        - New hires: 15 engineers
        """)

    # Upload
    print("\n📤 Uploading company report...")
    result = client.upload_document(sample_doc)
    print(f"✅ {result['message']}")

    # Ask ambiguous question
    print("\n💬 Asking: 'What was the performance like?'")
    response = client.query("What was the performance like?")

    if response.get("needs_clarification"):
        print("\n❓ ClaRA needs clarification:")

        # Display clarifying questions
        for i, question in enumerate(response["questions"], 1):
            print(f"\nQuestion {i}: {question['question_text']}")
            if question.get("suggested_options"):
                for j, option in enumerate(question["suggested_options"], 1):
                    print(f"  {j}. {option}")

        # Answer the clarification
        print("\n💬 Answering: 'Financial Performance'")

        clarifications = {
            response["questions"][0]["question_id"]: "Financial Performance"
        }

        response = client.query(
            "What was the performance like?",
            clarifications=clarifications
        )

        if "answer" in response:
            print(f"\n🤖 Refined Answer: {response['answer']}")
            print(f"📊 Confidence: {response['confidence_score']:.0%}")
            print(f"✅ Used clarifications: {response['used_clarifications']}")

    # Cleanup
    Path(sample_doc).unlink()


def example_multiple_documents():
    """Example: Working with multiple documents"""
    print("\n" + "="*60)
    print("Example 3: Multiple Documents")
    print("="*60)

    client = ClaRAClient()

    # Clear existing documents
    print("\n🧹 Clearing existing documents...")
    client.clear_documents()

    # Create multiple documents
    docs = {
        "policy.txt": "Company Policy: All employees must submit timesheets by Friday. Remote work is allowed 3 days per week.",
        "benefits.txt": "Benefits Package: Health insurance, 401k matching up to 6%, 20 days PTO, gym membership.",
        "handbook.txt": "Employee Handbook: Dress code is business casual. Office hours are 9 AM - 6 PM."
    }

    # Upload all documents
    print("\n📤 Uploading multiple documents...")
    for filename, content in docs.items():
        with open(filename, "w") as f:
            f.write(content)

        result = client.upload_document(filename)
        print(f"✅ Uploaded: {filename}")

        # Cleanup
        Path(filename).unlink()

    # List documents
    print("\n📋 Current documents:")
    doc_list = client.list_documents()
    print(f"Total: {doc_list['total_documents']} documents, {doc_list['total_chunks']} chunks")

    # Query across all documents
    print("\n💬 Asking: 'What are the benefits?'")
    response = client.query("What are the benefits?")

    if "answer" in response:
        print(f"\n🤖 Answer: {response['answer']}")

        if response.get("sources"):
            print(f"\n📚 Sources ({len(response['sources'])}):")
            for i, source in enumerate(response['sources'][:3], 1):
                print(f"  {i}. {source['chunk']['metadata']['source_file']}")
                print(f"     Relevance: {source['relevance_score']:.0%}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("ClaRA RAG System - Usage Examples")
    print("="*60)
    print("\n⚠️  Make sure the server is running: python main.py")

    try:
        input("\nPress Enter to continue...")

        example_basic_usage()
        input("\nPress Enter for next example...")

        example_clarification_workflow()
        input("\nPress Enter for next example...")

        example_multiple_documents()

        print("\n" + "="*60)
        print("✅ All examples completed!")
        print("="*60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Is it running?")
        print("   Start it with: python main.py")
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
