import streamlit as st
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

# ====================== CORPORATE NETWORK SAFEGUARDS ======================
# Bypasses strict internal corporate SSL proxy interception errors
os.environ["CURL_CA_BUNDLE"] = ""

# Load local environment secrets if available
load_dotenv()

st.set_page_config(page_title="TCS HR Assistant", page_icon="🤖", layout="centered")

# ====================== TCS LITELLM GATEWAY SETUP ======================
# Safely pull from Streamlit cloud secrets or local environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
BASE_URL = os.getenv("GOOGLE_GEMINI_BASE_URL") or st.secrets.get("GOOGLE_GEMINI_BASE_URL") or "https://genailab.tcs.in/v1"

if not GEMINI_API_KEY:
    st.error("❌ Configuration Error: API Key missing from environment settings/secrets.")
    st.stop()

# Initialize LangChain ChatOpenAI configured directly for the TCS LiteLLM endpoint
# NOTE: If gemini-2.5-flash gives an RBAC 403 access error, swap the model parameter string
# to "azure/genailab-maas-gpt-4o-mini" which has a highly inclusive access tier.
llm = ChatOpenAI(
    api_key=GEMINI_API_KEY,
    base_url=BASE_URL,
    model="azure/genailab-maas-gpt-5-mini", 
    temperature=0.2, # Low temperature ensures safe policy adherence and minimizes hallucinations
    max_tokens=900
)

# ====================== HR POLICY SYSTEM INSTRUCTIONS ======================
HR_SYSTEM_PROMPT = """
You are TCS HR Assistant, a professional, empathetic HR chatbot for Tata Consultancy Services.

You specialize in three key operational process areas matching the workbook scope:
1. **Employee Onboarding** (Background Verification tracking, document follow-ups, manager escalations)
2. **Leave Management** (Leave policy queries, leave discrepancies, exception rules)
3. **Exit Formalities** (Notice period guidelines, Full-and-Final settlement timelines, asset clearance)

Rules for response generation (Strict Evaluation Criteria):
- Maintain a warm, empathetic, yet strictly professional HR corporate tone throughout the exchange.
- Extensively use clean formatting structures such as bold title cards, markdown tables, and clear bulleted itemizations.
- Review and apply data provided in the [INTERNAL PROFILE CONTEXT] block. If an ID tracking request doesn't match our data, explain it gently and provide standard ticket escalation paths.
- Under no circumstances make absolute timeline promises unless explicitly validated within the internal context dataset.
- Protect data boundaries. Strictly ensure no real employee personally identifiable information (PII) is exposed.
- Clearly note dependency boundaries (e.g., dependencies on Payroll, IT, Background Verification Vendors, or Admin teams) when answering status requests.
"""

# ====================== SYNTHETIC INTERNAL DATABASE ======================
# Realistic fictional data generated to fulfill workbook simulation guidelines
CANDIDATES = {
    "CAND-2026-4782": {
        "name": "Priya Sharma", 
        "process": "Onboarding Track", 
        "status": "BGV Pending - Awaiting University Transcript Authentication",
        "dependency": "External BGV Vendor Group"
    },
    "EMP-2026-1102": {
        "name": "Amit Patel", 
        "process": "Leave Management", 
        "status": "Exception Leave Request Submitted - Under Manager Review Workflow",
        "dependency": "Reporting Manager Approval Portal"
    },
    "EMP-2026-9055": {
        "name": "Rahul Verma", 
        "process": "Exit Formalities", 
        "status": "Notice Period Progress (Day 45 of 90) - Asset Clearance Incomplete",
        "dependency": "Internal Corporate IT Operations Desk"
    }
}

st.title("🤖 TCS HR Assistant")
st.caption("Multi-Process AI HR Support | Powered by LangChain & GenAILab Gateway")

# Initialize Chat History Session State if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "Hello! I am your TCS HR Assistant. How can I help resolve your core process or tracking queries today?\n\nYou can query me regarding **Onboarding**, **Leave Management**, or **Exit Formalities**."
    }]

# ====================== SIDEBAR CONFIGURATION ======================
with st.sidebar:
    st.header("🏢 Process Controls")
    process = st.selectbox("Active Track Focus", ["General Inquiries", "Onboarding Track", "Leave Management", "Exit Formalities"])
    
    st.markdown("---")
    st.info("💡 **Workbook Tip:** Provide your Candidate ID or Employee ID (e.g., `CAND-2026-4782`) to trace live database profile changes.")
    
    # Hidden utility expander allowing evaluators to verify backend simulation state
    with st.expander("🔍 View Synthetic Database Context"):
        st.json(CANDIDATES)
        
    if st.button("🧹 Clear Conversation History"):
        st.session_state.messages = []
        st.rerun()

# Render Conversational History UI elements
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ====================== CHAT EXECUTION FLOW ======================
if prompt := st.chat_input("Type your HR question here..."):
    # Append and show user query block instantly
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Trigger Assistant Generation Block
    with st.chat_message("assistant"):
        with st.spinner("Analyzing internal HR documentation and policy workflows..."):
            
            # Unstructured Text Search -> Structured Database Profile Mapping
            matched_context = "No specific tracking identifier or personal profile was referenced in this input sequence."
            for profile_id, data in CANDIDATES.items():
                if profile_id in prompt:
                    matched_context = (
                        f"Active User Found: ID {profile_id} maps to {data['name']} within the '{data['process']}' track. "
                        f"Current State: {data['status']}. Structural Dependency Handoff: {data['dependency']}."
                    )
                    break
            
            # Map the running Streamlit history array into standard LangChain Message objects
            langchain_messages = [
                SystemMessage(content=f"{HR_SYSTEM_PROMPT}\n\n[INTERNAL PROFILE CONTEXT]: {matched_context}")
            ]
            
            for m in st.session_state.messages:
                if m["role"] == "user":
                    langchain_messages.append(HumanMessage(content=m["content"]))
                else:
                    langchain_messages.append(AIMessage(content=m["content"]))
            
            # Invoke the gateway model via LangChain
            try:
                response = llm.invoke(langchain_messages)
                assistant_reply = response.content
            except Exception as e:
                assistant_reply = f"⚠️ **Gateway Communication Issue:** Unable to safely retrieve information from the core evaluation endpoint.\n\n*Log Details:* `{str(e)}`"

            st.markdown(assistant_reply)
    
    # Store history loop data points for correct turn context preservation
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
