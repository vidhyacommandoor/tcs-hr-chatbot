import streamlit as st
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load locally saved or platform-level environment secrets
load_dotenv()

st.set_page_config(page_title="TCS HR Assistant", page_icon="🤖", layout="centered")

# ====================== TCS GENAILAB SETUP ======================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
# Fetch the custom internal URL provided by the portal instructions
BASE_URL = os.getenv("GOOGLE_GEMINI_BASE_URL") or st.secrets.get("GOOGLE_GEMINI_BASE_URL") or "https://genailab.tcs.in"

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY is missing from configuration parameters.")
    st.stop()

# Tell the Google SDK to talk to the tcs.in LiteLLM Gateway instead of public Google servers
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'base_url': BASE_URL}
)

# ====================== SYSTEM PROMPT ======================
# Tailored to match evaluation themes: empathetic tone, dependency handoffs, and avoiding false timeline promises
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

# ====================== SYNTHETIC DATABASE ======================
# Business-realistic synthetic context generated in accordance with exercise requirements
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
st.caption("Multi-Process AI HR Support | Onboarding • Leave • Exit | Powered by Gemini 2.5 Flash")

# Initialize Chat Session State 
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "Hello! I am your TCS HR Assistant. How can I help resolve your core process or tracking queries today?\n\nYou can query me regarding **Onboarding**, **Leave Management**, or **Exit Formalities**."
    }]

# ====================== SIDEBAR SETUP ======================
with st.sidebar:
    st.header("🏢 Process Configuration")
    process = st.selectbox("Active Track Focus", ["General Inquiries", "Onboarding Track", "Leave Management", "Exit Formalities"])
    
    st.markdown("---")
    st.info("💡 **Workbook Tip:** Provide your Candidate ID or Employee ID (e.g., `CAND-2026-4782`) to trace live database profile changes.")
    
    # Hidden utility window allowing evaluators to verify backend simulation state
    with st.expander("🔍 View Synthetic Database Context"):
        st.json(CANDIDATES)
        
    if st.button("🧹 Clear Conversation History"):
        st.session_state.messages = []
        st.rerun()

# Render Conversational History UI Layout Elements
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ====================== CHAT EXECUTION LOGIC ======================
if prompt := st.chat_input("Type your HR question here..."):
    # Append and show user query block
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Trigger Assistant Generation Block
    with st.chat_message("assistant"):
        with st.spinner("Analyzing internal HR documentation and policy workflows..."):
            
            # Dynamic Context Retrieval and Handoff Processing 
            matched_context = "No specific tracking identifier or personal profile was referenced in this input sequence."
            for profile_id, data in CANDIDATES.items():
                if profile_id in prompt:
                    matched_context = (
                        f"Active User Found: ID {profile_id} maps to {data['name']} within the '{data['process']}' track. "
                        f"Current State: {data['status']}. Structural Dependency Handoff: {data['dependency']}."
                    )
                    break
            
            # Construct clear chat sequences matching the official SDK types format
            gemini_contents = []
            for m in st.session_state.messages:
                # Map standard role strings to Gemini's expected values ('user' / 'model')
                sdk_role = "model" if m["role"] == "assistant" else "user"
                gemini_contents.append(
                    types.Content(
                        role=sdk_role,
                        parts=[types.Part.from_text(text=m["content"])]
                    )
                )
            
            try:
                # Establish Generation Config payload mapping system prompts and hyperparameters
                config = types.GenerateContentConfig(
                    system_instruction=f"{HR_SYSTEM_PROMPT}\n\n[INTERNAL PROFILE CONTEXT]: {matched_context}",
                    temperature=0.2,  # Low temperature for precise policy alignment and rule adherence
                    max_output_tokens=900
                )
                
                # Execute generation using the designated SDK target model name
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=gemini_contents,
                    config=config
                )
                assistant_reply = response.text
                
            except Exception as e:
                assistant_reply = f"⚠️ **Connection Alert:** Unable to safely retrieve information from the core evaluation endpoint.\n\n*Log Details:* `{str(e)}`"

            st.markdown(assistant_reply)
    
    # Store history loop data points for correct turn context preservation
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
