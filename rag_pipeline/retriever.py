import json
import logging
import google.generativeai as genai
from typing import List, Dict

logger = logging.getLogger(__name__)

class RAGRetriever:
    def __init__(self, db_session):
        self.db_session = db_session
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def retrieve_context(self, query: str) -> str:
        # Mock retrieval from DB/Knowledge sources based on keyword matches
        # Production would use Vector DB like Pinecone or pgvector
        context = []
        if "Block B" in query or "14" in query:
            context.append("Inverter 14: Block B. Telemetry: efficiency=0.82, voltage imbalance=high. Risk score: 0.82 (Shutdown Risk). Status: Active warning.")
            context.append("Inverter 12: Block B. Risk score: 0.45 (Degradation Risk).")
            context.append("Inverter 18: Block B. Risk score: 0.50 (Degradation Risk).")
        
        return " | ".join(context) if context else "None"

    def ask_question(self, query: str) -> str:
        context = self.retrieve_context(query)
        
        # Hallucination Guardrail: Reject if no context
        if not context or context == "None":
            return "Requested inverter data is not available in the system."
        
        prompt = f"""
        Answer the following user question using ONLY the provided context. If the context does not answer the question, say "Requested inverter data is not available in the system." do not make up any information.
        
        Context:
        {context}
        
        Question:
        {query}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"GenAI Error in RAG: {e}")
            return "An error occurred while answering your question."
