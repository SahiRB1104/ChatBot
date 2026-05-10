from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

import streamlit as st

API_BASE_URL = os.getenv("CHATBOT_API_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
APP_TITLE = "Education AI Assistant"


def api_request(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> Any:
    body = None
    headers = {"Content-Type": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    req = urlrequest.Request(
        f"{API_BASE_URL}{path}",
        data=body,
        method=method,
        headers=headers,
    )

    with urlrequest.urlopen(req, timeout=60) as response:
        data = response.read().decode("utf-8")
        return json.loads(data) if data else {}


def fetch_history() -> list[dict[str, Any]]:
    try:
        data = api_request("/history")
    except Exception:
        return []

    return data if isinstance(data, list) else []


def ask_single(question: str) -> dict[str, Any]:
    return api_request("/ask", method="POST", payload={"userInput": question})


def ask_batch(questions: list[str]) -> dict[str, Any]:
    return api_request("/ask-batch", method="POST", payload={"userInputs": questions})


def extract_answer(data: dict[str, Any]) -> str:
    return str(data.get("answer") or data.get("response") or "").strip()


def extract_answer_html(data: dict[str, Any]) -> str:
    return str(data.get("answer_html") or data.get("response_html") or "").strip()


def format_timestamp(value: Any) -> str:
    if not value:
        return ""

    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(value)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
          .stApp {
            background:
              radial-gradient(circle at top left, rgba(17, 94, 89, 0.12), transparent 28%),
              radial-gradient(circle at top right, rgba(15, 23, 42, 0.08), transparent 24%),
              linear-gradient(180deg, #f8fafc 0%, #eef4f7 100%);
            color: #0f172a;
            font-family: "Manrope", "Segoe UI", sans-serif;
          }
          .hero {
            padding: 1.2rem 1.3rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(15, 118, 110, 0.92));
            color: white;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
            margin-bottom: 1rem;
          }
          .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.1;
          }
          .hero p {
            margin: 0.55rem 0 0;
            color: rgba(255, 255, 255, 0.86);
            font-size: 0.98rem;
          }
          .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.85rem;
          }
          .chip {
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.18);
            font-size: 0.82rem;
          }
          .panel {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 1rem 1.05rem;
            background: rgba(255, 255, 255, 0.88);
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
          }
          .subtle {
            color: #475569;
            font-size: 0.95rem;
          }
          .history-card {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 16px;
            padding: 0.85rem 0.95rem;
            background: #fff;
            margin-bottom: 0.75rem;
          }
          .history-meta {
            color: #64748b;
            font-size: 0.8rem;
            margin-bottom: 0.45rem;
          }
          .history-question {
            font-weight: 700;
            margin-bottom: 0.4rem;
          }
          .history-answer {
            color: #0f172a;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def seed_session_history() -> None:
    if st.session_state.get("history_seeded"):
        return

    messages: list[dict[str, str]] = []
    history = fetch_history()

    for item in reversed(history):
        question = str(item.get("userInput") or "").strip()
        answer = str(item.get("aiResponse") or "").strip()

        if question:
            messages.append({"role": "user", "content": question})
        if answer:
            messages.append({"role": "assistant", "content": answer})

    st.session_state.messages = messages
    st.session_state.history_seeded = True


def render_header() -> None:
    st.markdown(
        f"""
        <div class="hero">
          <h1>{APP_TITLE}</h1>
          <p>Streamlit frontend with compact, structured answers for education questions.</p>
          <div class="chip-row">
            <span class="chip">Concise answers</span>
            <span class="chip">Markdown formatting</span>
            <span class="chip">Saved history</span>
            <span class="chip">Batch mode</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_single_tab() -> None:
    st.markdown("<div class='panel'>Ask one question and get a concise, structured answer.</div>", unsafe_allow_html=True)

    seed_session_history()

    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask a question about education, careers, or study topics")

    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                data = ask_single(question)
                answer = extract_answer(data)
                answer_html = extract_answer_html(data)
            except urlerror.URLError as exc:
                st.error(f"Backend request failed: {exc.reason if hasattr(exc, 'reason') else exc}")
                return
            except Exception as exc:
                st.error(f"Could not get a response: {exc}")
                return

        if answer:
            st.markdown(answer)
        elif answer_html:
            st.markdown(answer_html, unsafe_allow_html=True)
        else:
            st.warning("The backend returned an empty answer.")

    if answer:
        st.session_state.messages.append({"role": "assistant", "content": answer})


def render_batch_tab() -> None:
    st.markdown("<div class='panel'>Enter one question per line. Empty lines are ignored.</div>", unsafe_allow_html=True)

    raw_questions = st.text_area(
        "Batch questions",
        height=220,
        placeholder="What is the best way to prepare for board exams?\nHow do I improve concentration while studying?",
        label_visibility="collapsed",
    )

    submit = st.button("Run batch", type="primary")

    if not submit:
        return

    questions = [line.strip() for line in raw_questions.splitlines() if line.strip()]

    if not questions:
        st.info("Add at least one question before running the batch.")
        return

    try:
        data = ask_batch(questions)
    except urlerror.URLError as exc:
        st.error(f"Backend request failed: {exc.reason if hasattr(exc, 'reason') else exc}")
        return
    except Exception as exc:
        st.error(f"Could not get batch responses: {exc}")
        return

    items = data.get("items") if isinstance(data, dict) else None

    if isinstance(items, list) and items:
        for index, item in enumerate(items, start=1):
            question = str(item.get("question") or questions[index - 1]).strip()
            answer = str(item.get("answer") or "").strip()
            answer_html = str(item.get("answer_html") or "").strip()
            with st.container(border=True):
                st.markdown(f"**{index}. {question}**")
                if answer:
                    st.markdown(answer)
                elif answer_html:
                    st.markdown(answer_html, unsafe_allow_html=True)
                else:
                    st.warning("No answer returned for this question.")
        return

    responses = data.get("responses") if isinstance(data, dict) else []
    if not isinstance(responses, list):
        st.warning("The batch response did not contain structured results.")
        return

    for index, (question, answer) in enumerate(zip(questions, responses), start=1):
        with st.container(border=True):
            st.markdown(f"**{index}. {question}**")
            st.markdown(str(answer))


def render_recent_history() -> None:
    history = fetch_history()
    if not history:
        st.info("No saved history yet.")
        return

    for item in history[:8]:
        question = str(item.get("userInput") or "").strip()
        answer = str(item.get("aiResponse") or "").strip()
        timestamp = format_timestamp(item.get("timestamp"))

        with st.container():
            st.markdown(
                f"""
                <div class="history-card">
                  <div class="history-meta">{timestamp}</div>
                  <div class="history-question">Q: {question}</div>
                  <div class="history-answer">A: {answer}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="💬", layout="wide")
    inject_styles()

    with st.sidebar:
        st.title("Controls")
        st.caption(f"Backend: {API_BASE_URL}")
        if st.button("Clear local chat"):
            st.session_state.messages = []
            st.session_state.history_seeded = True
            st.rerun()

        st.markdown("### Tips")
        st.markdown("- Ask one focused question at a time.")
        st.markdown("- Use the batch tab for multiple prompts.")
        st.markdown("- Answers are tuned to stay concise and structured.")

    render_header()

    single_tab, batch_tab, history_tab = st.tabs(["Single Q&A", "Batch Q&A", "Recent History"])

    with single_tab:
        render_single_tab()

    with batch_tab:
        render_batch_tab()

    with history_tab:
        render_recent_history()


if __name__ == "__main__":
    main()