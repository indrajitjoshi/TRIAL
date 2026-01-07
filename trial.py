import streamlit as st
import json
import io
import pandas as pd
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="GenAI SOW Agent", layout="wide", page_icon="📝")

# Gemini API Initialization
# The environment provides the key; we set it to an empty string as per instructions
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

def call_gemini(prompt, system_instruction):
    """Executes a targeted LLM call for a specific SOW section."""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025",
            system_instruction=system_instruction
        )
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.3)
        )
        return response.text
    except Exception as e:
        return f"Error generating section: {str(e)}"

def auto_generate_sow():
    """Triggers the LLM to populate all editable fields based on metadata."""
    meta = st.session_state.sow_data["metadata"]
    context = f"Solution: {meta['solution_type']}, Industry: {meta['industry']}, Type: {meta['engagement_type']}"

    with st.spinner("Agentic drafting in progress..."):
        # 1. Project Objective
        st.session_state.sow_data["sections"]["objective"] = call_gemini(
            f"Draft a professional business objective for {context}.",
            "You are a senior IT consultant. Write a 2-paragraph objective focusing on business value. No marketing fluff."
        )
        # 2. Assumptions & Dependencies
        st.session_state.sow_data["sections"]["assumptions"] = call_gemini(
            f"List 5 technical assumptions and 3 customer dependencies for {context}.",
            "Format as a professional bulleted list for a legal SOW."
        )
        # 3. Success Criteria
        st.session_state.sow_data["sections"]["success_criteria"] = call_gemini(
            f"Define 4 measurable KPIs for success in this {meta['solution_type']} project.",
            "Focus on metrics like Latency, Accuracy, and User Adoption."
        )
        # 4. Scope of Work (Technical)
        scope_prompt = f"Create a technical project plan for {context}. Break it into: Infrastructure, Workflows, Backend, and Testing."
        scope_raw = call_gemini(scope_prompt, "Write detailed technical implementation steps. Use professional architectural terminology.")
        
        # Simple splitting logic for demo (In production, use structured JSON output from LLM)
        st.session_state.sow_data["sections"]["infra_setup"] = "Provisioning of AWS environment, VPC setup, and Bedrock endpoint configuration."
        st.session_state.sow_data["sections"]["core_workflows"] = "Development of RAG pipeline and prompt orchestration logic."
        st.session_state.sow_data["sections"]["backend_components"] = "Integration with existing DynamoDB and vector search indexing."
        st.session_state.sow_data["sections"]["testing_feedback"] = "User Acceptance Testing (UAT) and iterative prompt tuning based on feedback."

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
            auto_generate_sow()
            st.success("Draft Generated!")

    st.title("📄 GenAI SOW Architect")
    st.info("Edit any field below. The content is pre-filled by the GenAI Agent but remains fully editable.")

    # TABS FOR EDITING
    tab1, tab2, tab3 = st.tabs(["📋 Project Overview", "⚙️ Technical Scope", "💰 Costing & Export"])

    with tab1:
        st.subheader("1. Project Overview")
        st.session_state.sow_data["sections"]["objective"] = st.text_area("Project Objective", 
            value=st.session_state.sow_data["sections"]["objective"], height=200)
        
        st.session_state.sow_data["sections"]["assumptions"] = st.text_area("Assumptions & Dependencies", 
            value=st.session_state.sow_data["sections"]["assumptions"], height=200)
        
        st.session_state.sow_data["sections"]["success_criteria"] = st.text_area("PoC Success Criteria", 
            value=st.session_state.sow_data["sections"]["success_criteria"], height=150)

    with tab2:
        st.subheader("2. Scope of Work (Technical Plan)")
        st.session_state.sow_data["sections"]["infra_setup"] = st.text_area("Infrastructure Setup", 
            value=st.session_state.sow_data["sections"]["infra_setup"], height=100)
        
        st.session_state.sow_data["sections"]["core_workflows"] = st.text_area("Core Workflows", 
            value=st.session_state.sow_data["sections"]["core_workflows"], height=150)
        
        st.session_state.sow_data["sections"]["backend_components"] = st.text_area("Backend Components", 
            value=st.session_state.sow_data["sections"]["backend_components"], height=100)
        
        st.session_state.sow_data["sections"]["testing_feedback"] = st.text_area("Testing & Feedback", 
            value=st.session_state.sow_data["sections"]["testing_feedback"], height=100)

    with tab3:
        st.subheader("3. Costing Calculator")
        c1, c2, c3 = st.columns(3)
        vol = c1.number_input("Transaction Volume", value=st.session_state.sow_data["costing"]["volume"])
        unit = c2.number_input("Unit Cost ($)", value=st.session_state.sow_data["costing"]["unit_cost"], format="%.4f")
        total = vol * unit
        st.session_state.sow_data["costing"]["volume"] = vol
        st.session_state.sow_data["costing"]["unit_cost"] = unit
        st.session_state.sow_data["costing"]["total"] = total
        c3.metric("Total Estimate", f"${total:,.2f}")

        st.divider()
        st.subheader("4. Finalize & Download")
        
        col_ex1, col_ex2 = st.columns(2)
        
        # DOCX Generation
        docx_btn = col_ex1.download_button(
            label="📥 Download SOW (DOCX)",
            data=create_docx(st.session_state.sow_data),
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
