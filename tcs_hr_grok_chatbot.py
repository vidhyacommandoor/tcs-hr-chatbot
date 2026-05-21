import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="TCS HR Assistant", page_icon="🤖", layout="centered")

# ====================== GROK SETUP ======================
XAI_API_KEY = os.getenv("XAI_API_KEY") or st.secrets.get("XAI_API_KEY")

client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

# ====================== SYSTEM PROMPT ======================
HR_SYSTEM_PROMPT = """
You are TCS HR Assistant, a professional, empathetic HR chatbot for Tata Consultancy Services.

You specialize in three areas:
1. **Employee Onboarding**
2. **Leave Management**
3. **Exit Formalities**

Always respond in a warm, professional, and helpful tone. 
Be accurate with policies. Never give false promises on timelines.
Offer escalation when the query is complex or sensitive.
"""

# Mock Data
CANDIDATES = {
    "CAND-2026-4782": {"name": "Priya Sharma", "process": "Onboarding", "status": "BGV Pending"}
}

st.title("🤖 TCS HR Assistant")
st.caption("Multi-Process AI HR Support | Onboarding • Leave • Exit | Powered by Grok")

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm TCS HR Assistant. How can I help you today?\n\nYou can ask about **Onboarding**, **Leave**, or **Exit** processes."}]

# Sidebar - Quick Options
with st.sidebar:
    st.header("Quick Actions")
    process = st.selectbox("Select Process", ["General", "Onboarding", "Leave Management", "Exit Formalities"])
    
    st.divider()
    st.info("💡 Tip: Mention your Candidate ID or Employee ID for personalized help.")

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="grok-4",
                    messages=[
                        {"role": "system", "content": HR_SYSTEM_PROMPT},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
                assistant_reply = response.choices[0].message.content
            except Exception as e:
                assistant_reply = f"⚠️ I'm unable to connect to Grok right now. Please try again later. Error: {str(e)}"

            st.markdown(assistant_reply)
    
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})