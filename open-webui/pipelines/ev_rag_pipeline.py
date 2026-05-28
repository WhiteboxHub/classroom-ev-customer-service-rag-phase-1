"""
ev_rag_pipeline.py
Open-WebUI pipeline adapter for the EV RAG Platform.
Bridges Open-WebUI to the EV RAG FastAPI backend.
"""

import json
from typing import Any, Dict, Generator, Iterator, List, Optional, Union

import httpx


class Pipeline:
    """
    Open-WebUI pipeline for EV RAG troubleshooting assistant.
    Routes queries to the EV RAG FastAPI backend and streams responses.
    """

    class Valves:
        def __init__(self):
            self.ev_rag_api_url = "http://api:8000"
            self.default_session_id: Optional[str] = None
            self.use_hybrid_retrieval = True
            self.use_reranking = True
            self.top_k = 5

    def __init__(self):
        self.name = "EV RAG Troubleshooting Pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"EV RAG Pipeline starting up. API: {self.valves.ev_rag_api_url}")

    async def on_shutdown(self):
        print("EV RAG Pipeline shutting down.")

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[Dict],
        body: Dict,
    ) -> Union[str, Generator, Iterator]:
        """
        Main pipeline handler — routes EV query to RAG API.
        """
        try:
            # Extract session ID from conversation if available
            session_id = body.get("session_id") or self.valves.default_session_id

            # Call EV RAG chat endpoint
            response = httpx.post(
                f"{self.valves.ev_rag_api_url}/api/v1/chat",
                json={
                    "query": user_message,
                    "session_id": session_id,
                    "top_k": self.valves.top_k,
                    "use_hybrid": self.valves.use_hybrid_retrieval,
                    "use_rerank": self.valves.use_reranking,
                },
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()

            # Format response with sources
            answer = result.get("answer", "No answer generated.")
            sources = result.get("sources", [])
            latency_ms = result.get("latency_ms", 0)
            grounded = result.get("grounded", False)

            # Append source citations
            if sources:
                answer += "\n\n**Sources Retrieved:**"
                for idx, src in enumerate(sources[:5], 1):
                    source_file = src.get("source_file", "unknown")
                    score = src.get("score", 0)
                    answer += f"\n- [{idx}] `{source_file}` (relevance: {score:.2f})"

            answer += f"\n\n*Retrieval latency: {latency_ms:.0f}ms | Grounded: {'Yes' if grounded else 'No'}*"
            return answer

        except Exception as exc:
            return f"EV RAG Pipeline error: {str(exc)}. Please check that the EV RAG API is running."
