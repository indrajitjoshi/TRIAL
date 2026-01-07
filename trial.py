import streamlit as st
import json
import io
import pandas as pd
import time
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="GenAI SOW Agent", layout="wide", page_icon="📝")

# Gemini API Initialization
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
    """
    Generates all SOW sections in a single structured call.
    Uses Gemini 2.5 Flash for high speed and reliability.
    """
    meta = st.session_state.sow_data["metadata"]
    context = f"Solution: {meta['solution_type']}, Industry: {meta['industry']}, Type: {meta['engagement_type']}"
    
    status_placeholder = st.empty()
    status_placeholder.info("⚡ Agentic workflow initiated: Drafting professional SOW components...")
    
    system_prompt = """
    You are an expert AI Solutions Architect. Generate a professional Statement of Work.
    Return the response ONLY in a structured JSON format with the following keys:
    'objective', 'assumptions', 'success_criteria', 'infra_setup', 'core_workflows'.
    Use professional consulting tone. Ensure content is specific to the industry and solution provided.
    """
    
    user_prompt = f"""
    Context: {context} for {meta['customer_name']}.
    Please provide:
    1. A 2-paragraph business objective (string).
    2. A bulleted list of 5 assumptions and 3 dependencies (string).
    3. 4 measurable success KPIs (string).
    4. Detailed AWS Infrastructure setup including VPC, Lambda, and Bedrock (string).
    5. Description of the core RAG or Agentic data flow logic (string).
    """

    max_retries = 5
    retry_delays = [1, 2, 4, 8, 16]

    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-preview-09-2025",
                system_instruction=system_prompt
            )
            
            response = model.generate_content(
                user_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
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
                
                # Pre-fill deterministic sections
                st.session_state.sow_data["sections"]["backend_components"] = f"Standard {meta['industry']} security adapters, Vector database (Amazon OpenSearch Serverless), and data ingestion pipelines."
                st.session_state.sow_data["sections"]["testing_feedback"] = "Functional testing, prompt optimization, performance benchmarking, and UAT cycles."
                
                status_placeholder.success("✅ Drafting complete! Review your sections below.")
                time.sleep(1.5)
                status_placeholder.empty()
                return True
            else:
                raise Exception("Model returned empty content.")
                
        except Exception as e:
            if attempt < max_retries - 1:
                status_placeholder.warning(f"Drafting in progress... (Retrying {attempt + 1}/{max_retries})")
                time.sleep(retry_delays[attempt])
                continue
            else:
                status_placeholder.error(f"Drafting failed after retries: {str(e)}")
                return False

# --- EXPORT UTILS ---

def create_docx(data):
    doc = Document()
    
    # Header styling
    title = doc.add_heading('Statement of Work (SOW)', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Metadata Table
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Project Parameter'
    hdr_cells[1].text = 'Description'
    
    params = [
        ("Customer", data['metadata']['customer_name']),
        ("Solution", data['metadata']['solution_type']),
        ("Industry", data['metadata']['industry']),
        ("Duration", data['metadata']['duration']),
        ("Date Created", datetime.now().strftime('%Y-%m-%d'))
    ]
    
    for param, val in params:
        row = table.add_row().cells
        row[0].text = param
        row[1].text = val

    # Project Overview
    doc.add_heading('1. PROJECT OVERVIEW', level=1)
    doc.add_heading('Objective', level=2)
    doc.add_paragraph(data['sections']['objective'])
    doc.add_heading('Assumptions & Dependencies', level=2)
    doc.add_paragraph(data['sections']['assumptions'])
    doc.add_heading('Success Criteria', level=2)
    doc.add_paragraph(data['sections']['success_criteria'])

    # Scope of Work
    doc.add_heading('2. TECHNICAL PROJECT PLAN', level=1)
    doc.add_heading('Infrastructure Setup', level=2)
    doc.add_paragraph(data['sections']['infra_setup'])
    doc.add_heading('Core Workflows', level=2)
    doc.add_paragraph(data['sections']['core_workflows'])
    doc.add_heading('Backend Components', level=2)
    doc.add_paragraph(data['sections']['backend_components'])
    doc.add_heading('Testing & Feedback', level=2)
    doc.add_paragraph(data['sections']['testing_feedback'])

    # Costing
    doc.add_heading('3. ESTIMATED PRICING', level=1)
    p_table = doc.add_table(rows=1, cols=3)
    p_table.style = 'Table Grid'
    h_cells = p_table.rows[0].cells
    h_cells[0].text = 'Service Item'
    h_cells[1].text = 'Volume (Est)'
    h_cells[2].text = 'Total Cost'
    
    r = p_table.add_row().cells
    r[0].text = f"{data['metadata']['solution_type']} Implementation"
    r[1].text = str(data['costing']['volume'])
    r[2].text = f"${data['costing']['total']:,.2f}"

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- MAIN UI ---

def main():
    st.sidebar.title("🛠️ SOW Configuration")
    
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
        if st.button("🪄 Auto-Draft SOW Sections", type="primary", use_container_width=True):
            if fast_generate_sow():
                st.rerun()

    st.title("📄 AI Statement of Work Architect")
    st.markdown("Draft and customize production-ready SOWs using high-fidelity LLMs.")

    tabs = st.tabs(["📋 Overview", "⚙️ Tech Plan", "💰 Pricing & Export"])

    with tabs[0]:
        st.subheader("Section 1: Project Foundations")
        st.session_state.sow_data["sections"]["objective"] = st.text_area("Business Objective", 
            value=st.session_state.sow_data["sections"]["objective"], height=180, key="edit_obj")
        
        st.session_state.sow_data["sections"]["assumptions"] = st.text_area("Assumptions & Dependencies", 
            value=st.session_state.sow_data["sections"]["assumptions"], height=180, key="edit_ass")
        
        st.session_state.sow_data["sections"]["success_criteria"] = st.text_area("Success Criteria (KPIs)", 
            value=st.session_state.sow_data["sections"]["success_criteria"], height=150, key="edit_succ")

    with tabs[1]:
        st.subheader("Section 2: Technical Execution")
        st.session_state.sow_data["sections"]["infra_setup"] = st.text_area("Infrastructure (Cloud)", 
            value=st.session_state.sow_data["sections"]["infra_setup"], height=120, key="edit_infra")
        
        st.session_state.sow_data["sections"]["core_workflows"] = st.text_area("Logical Workflows", 
            value=st.session_state.sow_data["sections"]["core_workflows"], height=150, key="edit_flow")
        
        c1, c2 = st.columns(2)
        st.session_state.sow_data["sections"]["backend_components"] = c1.text_area("Backend & Integrations", 
            value=st.session_state.sow_data["sections"]["backend_components"], height=100, key="edit_back")
        st.session_state.sow_data["sections"]["testing_feedback"] = c2.text_area("QA & Validation", 
            value=st.session_state.sow_data["sections"]["testing_feedback"], height=100, key="edit_qa")

    with tabs[2]:
        st.subheader("Section 3: Cost Modeling")
        col1, col2, col3 = st.columns(3)
        vol = col1.number_input("Transaction/Token Volume", value=int(st.session_state.sow_data["costing"]["volume"]))
        unit = col2.number_input("Unit Cost ($)", value=float(st.session_state.sow_data["costing"]["unit_cost"]), format="%.4f")
        total = vol * unit
        st.session_state.sow_data["costing"]["volume"] = vol
        st.session_state.sow_data["costing"]["unit_cost"] = unit
        st.session_state.sow_data["costing"]["total"] = total
        col3.metric("Project Total", f"${total:,.2f}")

        st.divider()
        st.subheader("Finalize Document")
        
        d_col1, d_col2 = st.columns(2)
        
        docx_bytes = create_docx(st.session_state.sow_data)
        d_col1.download_button(
            label="📥 Download Professional SOW (Word)",
            data=docx_bytes,
            file_name=f"SOW_{st.session_state.sow_data['metadata']['customer_name']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

        backup_json = json.dumps(st.session_state.sow_data, indent=4)
        d_col2.download_button(
            label="💾 Export Project State (JSON)",
            data=backup_json,
            file_name="sow_archive.json",
            mime="application/json",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
