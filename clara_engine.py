import uuid
import json
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from anthropic import Anthropic

from models import (
    ClarificationQuestion,
    ClarificationResponse,
    AnswerResponse,
    RetrievedDocument,
    QueryRequest
)
from vector_store import VectorStore
from config import settings


class ClaRAEngine:
    """
    ClaRA (Clarifying Retrieval-Augmented) Engine

    Implements Apple's ClaRA approach:
    1. Analyze query for ambiguity
    2. Generate clarifying questions if needed
    3. Refine retrieval based on clarifications
    4. Generate improved answers
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.conversations: Dict[str, Dict] = {}

        # Initialize LLM client
        if settings.openai_api_key:
            self.llm_client = OpenAI(api_key=settings.openai_api_key)
            self.llm_provider = "openai"
        elif settings.anthropic_api_key:
            self.llm_client = Anthropic(api_key=settings.anthropic_api_key)
            self.llm_provider = "anthropic"
        else:
            raise ValueError("No LLM API key provided. Set either OPENAI_API_KEY or ANTHROPIC_API_KEY")

    def process_query(self, query_request: QueryRequest) -> Tuple[Optional[ClarificationResponse], Optional[AnswerResponse]]:
        """
        Process a query using ClaRA approach

        Returns:
            - ClarificationResponse if clarifications are needed
            - AnswerResponse if query can be answered directly
        """

        # Get or create conversation
        conv_id = query_request.conversation_id or str(uuid.uuid4())

        if conv_id not in self.conversations:
            self.conversations[conv_id] = {
                "query": query_request.query,
                "clarifications": {},
                "history": []
            }

        # Update clarifications if provided
        if query_request.clarifications:
            self.conversations[conv_id]["clarifications"].update(query_request.clarifications)

        # Step 1: Check if we need clarifications
        if settings.enable_clarifications and not query_request.clarifications:
            needs_clarification, clarification_response = self._analyze_query_ambiguity(
                query_request.query,
                conv_id
            )

            if needs_clarification:
                return clarification_response, None

        # Step 2: Perform retrieval (refined if we have clarifications)
        refined_query = self._refine_query_with_clarifications(
            query_request.query,
            self.conversations[conv_id]["clarifications"]
        )

        retrieved_docs = self.vector_store.search(
            query=refined_query,
            top_k=settings.top_k_documents
        )

        # Check if we found any documents
        if not retrieved_docs:
            # No documents in database
            answer_response = AnswerResponse(
                conversation_id=conv_id,
                answer="I don't have any documents to search through yet. Please upload some documents first using the upload section on the left.",
                sources=[],
                confidence_score=0.0,
                used_clarifications=False
            )
            return None, answer_response

        # Step 3: Generate answer
        answer_response = self._generate_answer(
            query=query_request.query,
            retrieved_docs=retrieved_docs,
            clarifications=self.conversations[conv_id]["clarifications"],
            conv_id=conv_id
        )

        return None, answer_response

    def _analyze_query_ambiguity(
        self,
        query: str,
        conv_id: str
    ) -> Tuple[bool, Optional[ClarificationResponse]]:
        """Analyze if query needs clarification"""

        prompt = f"""You are an AI assistant analyzing user queries for ambiguity in a RAG system.

Query: "{query}"

IMPORTANT: Only request clarification if the query is TRULY ambiguous with multiple completely different meanings.
Simple, clear questions should NOT need clarification even if they're broad.

Examples of queries that DON'T need clarification:
- "What is this document about?"
- "Summarize the main points"
- "What are the key findings?"
- "Tell me about X" (where X is a clear topic)

Examples that DO need clarification:
- "What about performance?" (could be system/financial/employee performance)
- "How did it go?" (too vague, unclear what "it" refers to)

Analyze this query and determine if it TRULY needs clarification.

Respond in JSON format:
{{
    "needs_clarification": true/false,
    "reasoning": "why clarification is/isn't needed",
    "questions": [
        {{
            "question_text": "the clarifying question",
            "question_type": "open" or "multiple_choice",
            "suggested_options": ["option1", "option2"] (only for multiple_choice)
        }}
    ]
}}

Be conservative - when in doubt, set needs_clarification to false.
"""

        response_text = self._call_llm(prompt)

        try:
            # Parse JSON response
            response_json = json.loads(response_text)

            if response_json.get("needs_clarification", False):
                questions = []
                for idx, q in enumerate(response_json.get("questions", [])):
                    question = ClarificationQuestion(
                        question_id=f"{conv_id}_q{idx}",
                        question_text=q["question_text"],
                        question_type=q.get("question_type", "open"),
                        suggested_options=q.get("suggested_options")
                    )
                    questions.append(question)

                clarification_response = ClarificationResponse(
                    conversation_id=conv_id,
                    needs_clarification=True,
                    questions=questions,
                    reasoning=response_json.get("reasoning")
                )

                return True, clarification_response

        except json.JSONDecodeError:
            # If parsing fails, assume no clarification needed
            pass

        return False, None

    def _refine_query_with_clarifications(
        self,
        original_query: str,
        clarifications: Dict[str, str]
    ) -> str:
        """Refine query using clarifications"""

        if not clarifications:
            return original_query

        # Combine original query with clarifications
        refined_query = original_query

        for question_id, answer in clarifications.items():
            refined_query += f"\n{answer}"

        return refined_query

    def _generate_answer(
        self,
        query: str,
        retrieved_docs: List[RetrievedDocument],
        clarifications: Dict[str, str],
        conv_id: str
    ) -> AnswerResponse:
        """Generate final answer using retrieved documents"""

        # Prepare context from retrieved documents
        context = "\n\n".join([
            f"[Document {i+1}] (Relevance: {doc.relevance_score:.2f})\n{doc.chunk.content}"
            for i, doc in enumerate(retrieved_docs)
        ])

        # Prepare clarifications text
        clarifications_text = ""
        if clarifications:
            clarifications_text = "\n\nUser Clarifications:\n"
            for q_id, answer in clarifications.items():
                clarifications_text += f"- {answer}\n"

        prompt = f"""You are a helpful AI assistant answering questions based on provided documents.

User Query: {query}
{clarifications_text}

Retrieved Context:
{context}

Instructions:
1. Answer the query using the information from the retrieved context above
2. Be helpful, clear, and specific in your answer
3. If the context contains relevant information, provide a comprehensive answer
4. If the context doesn't fully answer the question, provide what information is available and mention what's missing
5. Provide a confidence score based on how well the context answers the question:
   - 0.9-1.0: Excellent coverage, clear answer
   - 0.7-0.9: Good coverage, mostly answered
   - 0.5-0.7: Partial information available
   - 0.0-0.5: Limited or no relevant information

Respond in JSON format:
{{
    "answer": "your detailed, helpful answer",
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation of your confidence level"
}}

IMPORTANT: Be helpful and provide useful answers. Don't be overly restrictive.
"""

        response_text = self._call_llm(prompt)

        try:
            response_json = json.loads(response_text)

            answer_response = AnswerResponse(
                conversation_id=conv_id,
                answer=response_json.get("answer", response_text),
                sources=retrieved_docs,
                confidence_score=response_json.get("confidence_score", 0.5),
                used_clarifications=bool(clarifications)
            )

            return answer_response

        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return AnswerResponse(
                conversation_id=conv_id,
                answer=response_text,
                sources=retrieved_docs,
                confidence_score=0.5,
                used_clarifications=bool(clarifications)
            )

    def _call_llm(self, prompt: str) -> str:
        """Call LLM API"""

        if self.llm_provider == "openai":
            response = self.llm_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.llm_temperature,
                max_tokens=settings.max_tokens
            )
            return response.choices[0].message.content

        elif self.llm_provider == "anthropic":
            response = self.llm_client.messages.create(
                model=settings.llm_model.replace("gpt-4-turbo-preview", "claude-3-opus-20240229"),
                max_tokens=settings.max_tokens,
                temperature=settings.llm_temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    def clear_conversation(self, conv_id: str) -> None:
        """Clear a conversation history"""
        if conv_id in self.conversations:
            del self.conversations[conv_id]

    def get_conversation(self, conv_id: str) -> Optional[Dict]:
        """Get conversation data"""
        return self.conversations.get(conv_id)
