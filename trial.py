import streamlit as st
import json
import io
import pandas as pd
import time
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="GenAI SOW Agent", layout="wide", page_icon="📝")

# Gemini API Initialization
# The execution environment provides the key at runtime.
apiKey = "" 
genai.configure(api_key=apiKey)

# --- SESSION STATE INITIALIZATION ---
if 'sow_data' not in st.session_state:
    st.session_state.sow_data = {
        "metadata": {
            "solution_type": "Generative AI Chatbot",
            "engagement_type": "Proof of Concept (PoC)",
            "industry": "Financial Services",
            "customer_name": "Acme Corp",
            "duration": "6 Weeks"
        },
        "sections": {
            "objective": "",
            "assumptions": "",
            "success_criteria": "",
            "infra_setup": "",
            "core_workflows": "",
            "backend_components": "",
            "testing_feedback": ""
        },
        "costing": {
            "volume": 10000,
            "unit_cost": 0.05,
            "total": 500.0
        }
    }

# --- LLM UTILS ---

def fast_generate_sow():
    """Generates all SOW sections in a single structured call with increased timeout to handle 504 errors."""
    meta = st.session_state.sow_data["metadata"]
    context = f"Solution: {meta['solution_type']}, Industry: {meta['industry']}, Type: {meta['engagement_type']}"
    
    status_text = st.empty()
    status_text.warning("⚡ AI is drafting the entire SOW... Please wait (est. 15-20 seconds).")
    
    system_prompt = """
    You are a senior AI Solutions Architect. Generate a professional Statement of Work.
    Return the response in a structured JSON format with the following keys:
    'objective', 'assumptions', 'success_criteria', 'infra_setup', 'core_workflows'.
    Use professional consulting tone. No marketing fluff.
    """
    
    user_prompt = f"""
    Context: {context} for {meta['customer_name']}.
    Please provide:
    1. A 2-paragraph business objective.
    2. A bulleted list of 5 assumptions and 3 dependencies.
    3. 4 measurable success KPIs.
    4. Detailed AWS Infrastructure setup (VPC, Lambda, Bedrock).
    5. Description of the core RAG or Agentic data flow logic.
    """

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025",
            system_instruction=system_prompt
        )
        
        # Adding request_options to increase the timeout to 60 seconds to avoid 504 Gateway/Deadline issues
        response = model.generate_content(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            ),
            request_options={"timeout": 60}
        )
        
        if response and response.candidates:
            res_text = response.candidates[0].content.parts[0].text
            data = json.loads(res_text)
            
            # Update Session State
            st.session_state.sow_data["sections"]["objective"] = data.get("objective", "")
            st.session_state.sow_data["sections"]["assumptions"] = data.get("assumptions", "")
            st.session_state.sow_data["sections"]["success_criteria"] = data.get("success_criteria", "")
            st.session_state.sow_data["sections"]["infra_setup"] = data.get("infra_setup", "")
            st.session_state.sow_data["sections"]["core_workflows"] = data.get("core_workflows", "")
            
            # Static pre-fills for reliability
            st.session_state.sow_data["sections"]["backend_components"] = f"Integration with {meta['industry']}-specific data sources and vector stores."
            st.session_state.sow_data["sections"]["testing_feedback"] = "Comprehensive UAT and prompt optimization cycles."
            
            status_text.success("✅ SOW Generated Successfully!")
            time.sleep(1)
            status_text.empty()
            return True
        else:
            status_text.error("AI returned an empty response. Please try again.")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "504" in error_msg or "Deadline Exceeded" in error_msg:
            status_text.error("⌛ The request timed out (504). The AI model is taking longer than expected. Please try clicking 'Auto-Generate' again.")
        else:
            status_text.error(f"Generation failed: {error_msg}")
        return False

# --- EXPORT UTILS ---

def create_docx(data):
    doc = Document()
    
    # Title
    title = doc.add_heading('Statement of Work (SOW)', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Meta Info
    p = doc.add_paragraph()
    p.add_run(f"Customer: {data['metadata']['customer_name']}\n").bold = True
    p.add_run(f"Project: {data['metadata']['solution_type']}\n")
    p.add_run(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")

    # Section 1
    doc.add_heading('1. PROJECT OVERVIEW', level=1)
    doc.add_heading('Objective', level=2)
    doc.add_paragraph(data['sections']['objective'])
    doc.add_heading('Assumptions & Dependencies', level=2)
    doc.add_paragraph(data['sections']['assumptions'])
    doc.add_heading('PoC Success Criteria', level=2)
    doc.add_paragraph(data['sections']['success_criteria'])

    # Section 2
    doc.add_heading('2. SCOPE OF WORK – TECHNICAL PROJECT PLAN', level=1)
    doc.add_heading('Infrastructure Setup', level=2)
    doc.add_paragraph(data['sections']['infra_setup'])
    doc.add_heading('Core Workflows', level=2)
    doc.add_paragraph(data['sections']['core_workflows'])
    doc.add_heading('Backend Components', level=2)
    doc.add_paragraph(data['sections']['backend_components'])
    doc.add_heading('Testing & Feedback', level=2)
    doc.add_paragraph(data['sections']['testing_feedback'])

    # Section 3: Costing Table
    doc.add_heading('3. PROJECT COSTING', level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Item description'
    hdr_cells[1].text = 'Unit Volume'
    hdr_cells[2].text = 'Total Cost'
    
    row = table.add_row().cells
    row[0].text = f"{data['metadata']['solution_type']} Implementation"
    row[1].text = str(data['costing']['volume'])
    row[2].text = f"${data['costing']['total']:,.2f}"

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- MAIN UI ---

def main():
    st.sidebar.title("🛠️ SOW Configuration")
    
    # Sidebar Metadata
    with st.sidebar:
        st.session_state.sow_data["metadata"]["customer_name"] = st.text_input("Customer Name", value=st.session_state.sow_data["metadata"]["customer_name"])
        st.session_state.sow_data["metadata"]["solution_type"] = st.selectbox("Solution Type", 
            ["Generative AI Chatbot", "Document Intelligence", "Agentic Workflow", "Code Refactoring", "Custom ML"],
            index=0)
        st.session_state.sow_data["metadata"]["industry"] = st.selectbox("Industry", 
            ["Financial Services", "Healthcare", "Manufacturing", "Retail", "Energy"],
            index=0)
        st.session_state.sow_data["metadata"]["engagement_type"] = st.selectbox("Engagement Type", 
            ["Proof of Concept (PoC)", "Production Pilot", "Strategy Phase"], index=0)
        
        st.divider()
        if st.button("🪄 Auto-Generate All Content", type="primary", use_container_width=True):
            if fast_generate_sow():
                st.rerun()

    st.title("📄 GenAI SOW Architect")
    st.info("Edit any field below. Click 'Auto-Generate' in the sidebar to populate content using Gemini Pro.")

    # TABS FOR EDITING
    tab1, tab2, tab3 = st.tabs(["📋 Project Overview", "⚙️ Technical Scope", "💰 Costing & Export"])

    with tab1:
        st.subheader("1. Project Overview")
        st.session_state.sow_data["sections"]["objective"] = st.text_area("Project Objective", 
            value=st.session_state.sow_data["sections"]["objective"], height=200, key="ta_objective")
        
        st.session_state.sow_data["sections"]["assumptions"] = st.text_area("Assumptions & Dependencies", 
            value=st.session_state.sow_data["sections"]["assumptions"], height=200, key="ta_assumptions")
        
        st.session_state.sow_data["sections"]["success_criteria"] = st.text_area("PoC Success Criteria", 
            value=st.session_state.sow_data["sections"]["success_criteria"], height=150, key="ta_success")

    with tab2:
        st.subheader("2. Scope of Work (Technical Plan)")
        st.session_state.sow_data["sections"]["infra_setup"] = st.text_area("Infrastructure Setup", 
            value=st.session_state.sow_data["sections"]["infra_setup"], height=120, key="ta_infra")
        
        st.session_state.sow_data["sections"]["core_workflows"] = st.text_area("Core Workflows", 
            value=st.session_state.sow_data["sections"]["core_workflows"], height=150, key="ta_workflows")
        
        st.session_state.sow_data["sections"]["backend_components"] = st.text_area("Backend Components", 
            value=st.session_state.sow_data["sections"]["backend_components"], height=100, key="ta_backend")
        
        st.session_state.sow_data["sections"]["testing_feedback"] = st.text_area("Testing & Feedback", 
            value=st.session_state.sow_data["sections"]["testing_feedback"], height=100, key="ta_testing")

    with tab3:
        st.subheader("3. Costing Calculator")
        c1, c2, c3 = st.columns(3)
        vol = c1.number_input("Transaction Volume", value=int(st.session_state.sow_data["costing"]["volume"]))
        unit = c2.number_input("Unit Cost ($)", value=float(st.session_state.sow_data["costing"]["unit_cost"]), format="%.4f")
        total = vol * unit
        st.session_state.sow_data["costing"]["volume"] = vol
        st.session_state.sow_data["costing"]["unit_cost"] = unit
        st.session_state.sow_data["costing"]["total"] = total
        c3.metric("Total Estimate", f"${total:,.2f}")

        st.divider()
        st.subheader("4. Finalize & Download")
        
        col_ex1, col_ex2 = st.columns(2)
        
        # DOCX Generation
        docx_data = create_docx(st.session_state.sow_data)
        col_ex1.download_button(
            label="📥 Download SOW (DOCX)",
            data=docx_data,
            file_name=f"SOW_{st.session_state.sow_data['metadata']['customer_name']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

        # JSON State Download (Local Storage)
        json_str = json.dumps(st.session_state.sow_data, indent=4)
        col_ex2.download_button(
            label="💾 Backup SOW State (JSON)",
            data=json_str,
            file_name="sow_data.json",
            mime="application/json",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
