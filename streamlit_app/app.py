"""Enterprise EV troubleshooting chat UI (Streamlit)."""

import os
from typing import Any, Dict, List

import requests
import streamlit as st

API_URL = os.getenv("STREAMLIT_API_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"


def api_post(path: str, payload: Dict[str, Any], files=None) -> Dict[str, Any]:
    url = f"{API_URL}{API_PREFIX}{path}"
    if files:
        response = requests.post(url, files=files, data=payload, timeout=120)
    else:
        response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def api_get(path: str) -> Dict[str, Any]:
    url = f"{API_URL}{API_PREFIX}{path}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def init_state() -> None:
    st.session_state.setdefault("session_id", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("last_sources", [])
    st.session_state.setdefault("last_citations", [])


def sidebar() -> None:
    st.sidebar.title("EV Knowledge Base")
    st.sidebar.caption("Upload service manuals, firmware notes, and diagnostic PDFs")

    with st.sidebar.expander("Metadata filters", expanded=False):
        vehicle_model = st.text_input("Vehicle model")
        firmware_version = st.text_input("Firmware version")
        charging_type = st.text_input("Charging type")
        diagnostic_category = st.selectbox(
            "Diagnostic category",
            ["", "charging", "battery", "firmware", "infotainment", "diagnostics", "general"],
        )

    uploaded = st.sidebar.file_uploader(
        "Upload EV document",
        type=["pdf", "md", "txt"],
        accept_multiple_files=False,
    )

    if st.sidebar.button("Ingest uploaded document", use_container_width=True):
        if not uploaded:
            st.sidebar.warning("Select a file first.")
        else:
            with st.spinner("Ingesting document..."):
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                data = {
                    k: v
                    for k, v in {
                        "vehicle_model": vehicle_model,
                        "firmware_version": firmware_version,
                        "charging_type": charging_type,
                        "diagnostic_category": diagnostic_category,
                    }.items()
                    if v
                }
                result = api_post("/ingest/upload", payload=data, files=files)
            st.sidebar.success(result.get("message", "Ingested"))

    if st.sidebar.button("Ingest sample dataset", use_container_width=True):
        with st.spinner("Indexing sample EV docs..."):
            result = api_post("/ingest/path", {"source_path": "sample_ev_docs"})
        st.sidebar.success(
            f"Indexed {result.get('chunks_indexed', 0)} chunks from sample corpus"
        )

    st.sidebar.divider()
    try:
        docs = api_get("/ingest/documents").get("documents", [])
        st.sidebar.subheader(f"Indexed documents ({len(docs)})")
        for doc in docs[:15]:
            st.sidebar.text(f"• {doc.get('source_file', 'unknown')}")
    except Exception as exc:
        st.sidebar.error(f"API unavailable: {exc}")

    if st.sidebar.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.last_sources = []
        st.session_state.last_citations = []


def render_chat() -> None:
    st.title("EV Troubleshooting Assistant")
    st.caption("Grounded RAG responses with hybrid retrieval, reranking, and source citations")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    query = st.chat_input("Describe the EV issue (charging, battery DTC, OTA, etc.)")
    if not query:
        return

    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving context and generating grounded answer..."):
            try:
                payload = {
                    "query": query,
                    "session_id": st.session_state.session_id,
                    "use_hybrid": True,
                    "use_rerank": True,
                    "include_sources": True,
                }
                result = api_post("/chat", payload)
            except Exception as exc:
                st.error(f"Chat failed: {exc}")
                return

        st.session_state.session_id = result.get("session_id")
        answer = result.get("answer", "")
        st.markdown(answer)

        citations = result.get("citations", [])
        if citations:
            st.markdown("**Source citations**")
            for cite in citations:
                st.markdown(f"- {cite}")

        sources: List[Dict[str, Any]] = result.get("sources", [])
        st.session_state.last_sources = sources
        st.session_state.last_citations = citations
        st.session_state.messages.append({"role": "assistant", "content": answer})

        st.caption(
            f"Latency: {result.get('latency_ms', 0):.0f} ms | "
            f"Grounded: {result.get('grounded', False)}"
        )


def render_sources_panel() -> None:
    st.subheader("Retrieved source chunks")
    sources = st.session_state.get("last_sources", [])
    if not sources:
        st.info("Ask a question to see retrieved troubleshooting chunks.")
        return

    for idx, src in enumerate(sources, start=1):
        with st.expander(
            f"[{idx}] {src.get('source_file', 'unknown')} — score {src.get('score', 0):.3f}"
        ):
            st.markdown(src.get("text", ""))
            st.json(src.get("metadata", {}))


def main() -> None:
    st.set_page_config(
        page_title="EV RAG Troubleshooting",
        page_icon="⚡",
        layout="wide",
    )
    init_state()
    sidebar()

    col_chat, col_sources = st.columns([2, 1])
    with col_chat:
        render_chat()
    with col_sources:
        render_sources_panel()


if __name__ == "__main__":
    main()
