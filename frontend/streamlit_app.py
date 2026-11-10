"""A small home for the studio outside Slack (Lab 3).

A brief form that sends requests to the deployed agent, and a gallery of
everything it has published. Streamlit runs on your server, so the LangSmith
API key never reaches the browser.

Run it:
    DEPLOYMENT_API_URL=... LANGSMITH_API_KEY=... uv run --group frontend streamlit run frontend/streamlit_app.py
"""

import base64
import os

import streamlit as st
from langgraph_sdk import get_sync_client

ASSISTANT_ID = "design-studio"  # the agent's name in agent.py
FORMATS = ["social-card", "square", "story", "slide"]

client = get_sync_client(url=os.environ["DEPLOYMENT_API_URL"], api_key=os.environ["LANGSMITH_API_KEY"])

st.set_page_config(page_title="Design Studio", layout="wide")
st.title("Design Studio")
brief_tab, gallery_tab = st.tabs(["New request", "Gallery"])

with brief_tab:
    with st.form("brief"):
        ask = st.text_area("What do you need?", placeholder="A launch card for our newest product")
        copy = st.text_input("Exact headline (optional)")
        fmt = st.selectbox("Format", FORMATS)
        submitted = st.form_submit_button("Send to the studio")

    if submitted and ask:
        message = f"{ask}\n\nFormat: {fmt}" + (f'\nHeadline, exactly: "{copy}"' if copy else "")
        thread = client.threads.create()
        with st.spinner("Designing…"):
            state = client.runs.wait(
                thread["thread_id"],
                ASSISTANT_ID,
                input={"messages": [{"role": "user", "content": message}]},
            )
        messages = state.get("messages", []) if isinstance(state, dict) else []
        reply = messages[-1]["content"] if messages else "No reply."
        if isinstance(reply, list):
            reply = "\n".join(part.get("text", "") for part in reply if isinstance(part, dict))
        st.markdown(reply)
        st.caption("Ask the studio to publish a design, and it appears in the Gallery once it's approved.")

with gallery_tab:
    items = client.store.search_items(("gallery",), limit=50).get("items", [])
    if not items:
        st.info("Nothing published yet.")
    columns = st.columns(3)
    for i, item in enumerate(sorted(items, key=lambda it: it["value"]["published_at"], reverse=True)):
        value = item["value"]
        with columns[i % 3]:
            st.image(base64.b64decode(value["png_base64"]), caption=value["caption"] or value["name"])
