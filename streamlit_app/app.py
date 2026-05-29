"""Enterprise EV troubleshooting chat UI (Streamlit) — ChatGPT-style layout."""

import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
import streamlit.components.v1 as components

API_URL = os.getenv("STREAMLIT_API_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"

USER_AVATAR = "🧑‍🔧"
ASSISTANT_AVATAR = "⚡"


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


def inject_chatgpt_styles() -> None:
    st.markdown(
        """
        <style>
        /* Hide Streamlit chrome for a cleaner chat surface */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {
            background: transparent;
            box-shadow: none;
        }

        /* Centered chat column (ChatGPT-like width) */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 6rem;
            max-width: 52rem;
        }

        /* Chat history scrolls; input stays pinned at bottom */
        [data-testid="stMainBlockContainer"] {
            min-height: calc(100vh - 5rem);
        }

        /* User bubbles — subtle right emphasis */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background-color: #f7f7f8;
            border-radius: 12px;
            padding: 0.25rem 0.5rem;
            margin-bottom: 0.75rem;
        }

        /* Assistant bubbles */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            background-color: #ffffff;
            border: 1px solid #ececf1;
            border-radius: 12px;
            padding: 0.25rem 0.5rem;
            margin-bottom: 0.75rem;
        }

        /* Room above Streamlit's bottom-pinned chat input */
        [data-testid="stChatInput"] textarea {
            border-radius: 1.25rem !important;
            border: 1px solid #d1d5db !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        }

        .chat-welcome {
            text-align: center;
            color: #6b7280;
            padding: 3rem 1rem 2rem;
            font-size: 0.95rem;
        }

        .chat-welcome h2 {
            color: #111827;
            font-weight: 600;
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }

        .msg-meta {
            font-size: 0.75rem;
            color: #9ca3af;
            margin-top: 0.5rem;
        }

        .citation-list {
            font-size: 0.85rem;
            color: #374151;
            margin-top: 0.75rem;
            padding-top: 0.5rem;
            border-top: 1px solid #ececf1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def scroll_chat_to_bottom() -> None:
    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;
            const main = doc.querySelector('section.main');
            if (main) {
                main.scrollTop = main.scrollHeight;
            }
            const chatMessages = doc.querySelectorAll('[data-testid="stChatMessage"]');
            if (chatMessages.length) {
                chatMessages[chatMessages.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
        })();
        </script>
        """,
        height=0,
    )


def init_state() -> None:
    st.session_state.setdefault("session_id", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("last_sources", [])
    st.session_state.setdefault("last_citations", [])


def render_welcome() -> None:
    st.markdown(
        """
        <div class="chat-welcome">
            <h2>EV Troubleshooting Assistant</h2>
            <p>Ask about charging, battery DTCs, OTA updates, or HV service procedures.<br>
            Answers are grounded in your indexed EV documentation with citations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_assistant_extras(msg: Dict[str, Any]) -> None:
    citations: List[str] = msg.get("citations") or []
    if citations:
        st.markdown("**Sources**")
        for cite in citations:
            st.markdown(f"- {cite}")

    sources: List[Dict[str, Any]] = msg.get("sources") or []
    if sources:
        with st.expander(f"View {len(sources)} retrieved chunks", expanded=False):
            for idx, src in enumerate(sources, start=1):
                st.markdown(
                    f"**[{idx}] {src.get('source_file', 'unknown')}** "
                    f"(score {src.get('score', 0):.3f})"
                )
                st.markdown(src.get("text", ""))
                meta = src.get("metadata")
                if meta:
                    st.caption(str(meta))

    meta = msg.get("meta")
    if meta:
        st.markdown(
            f'<p class="msg-meta">{meta}</p>',
            unsafe_allow_html=True,
        )


def render_message(msg: Dict[str, Any]) -> None:
    role = msg["role"]
    avatar = USER_AVATAR if role == "user" else ASSISTANT_AVATAR
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.get("content", ""))
        if role == "assistant":
            render_assistant_extras(msg)


def fetch_assistant_reply(query: str) -> Optional[Dict[str, Any]]:
    payload = {
        "query": query,
        "session_id": st.session_state.session_id,
        "use_hybrid": True,
        "use_rerank": True,
        "include_sources": True,
    }
    return api_post("/chat", payload)


def build_assistant_message(result: Dict[str, Any]) -> Dict[str, Any]:
    citations = result.get("citations", [])
    sources: List[Dict[str, Any]] = result.get("sources", [])
    st.session_state.session_id = result.get("session_id")
    st.session_state.last_sources = sources
    st.session_state.last_citations = citations
    return {
        "role": "assistant",
        "content": result.get("answer", ""),
        "citations": citations,
        "sources": sources,
        "meta": (
            f"Latency: {result.get('latency_ms', 0):.0f} ms · "
            f"Grounded: {result.get('grounded', False)}"
        ),
    }


def generate_pending_reply(messages: List[Dict[str, Any]]) -> None:
    """Fetch assistant reply above the input bar, then rerun with full history."""
    query = messages[-1]["content"]
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.spinner("Thinking..."):
            try:
                result = fetch_assistant_reply(query)
            except Exception as exc:
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"Sorry, I could not reach the API: {exc}",
                        "citations": [],
                        "sources": [],
                    }
                )
                st.rerun()
                return
            if result is None:
                messages.append(
                    {
                        "role": "assistant",
                        "content": "Sorry, I did not receive a response from the server.",
                        "citations": [],
                        "sources": [],
                    }
                )
                st.rerun()
                return

    messages.append(build_assistant_message(result))
    st.rerun()


def render_chat() -> None:
    """
    Streamlit draws widgets top-to-bottom. Order must be:
      1) message history (oldest → newest)
      2) in-flight assistant reply (if any)
      3) chat input (always last — Streamlit pins it to the bottom)
    """
    messages: List[Dict[str, Any]] = st.session_state.messages

    with st.container():
        if not messages:
            render_welcome()
        else:
            for msg in messages:
                render_message(msg)

        if messages and messages[-1]["role"] == "user":
            generate_pending_reply(messages)

    scroll_chat_to_bottom()

    prompt = st.chat_input("Message EV Troubleshooting Assistant...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt.strip()})
        st.rerun()


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

    if st.sidebar.button("New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.last_sources = []
        st.session_state.last_citations = []
        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="EV RAG Troubleshooting",
        page_icon="⚡",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    inject_chatgpt_styles()
    init_state()
    sidebar()
    render_chat()


if __name__ == "__main__":
    main()
