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

def call_gemini(prompt, system_instruction):
    """Executes a targeted LLM call for a specific SOW section with exponential backoff."""
    max_retries = 5
    for i in range(max_retries):
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-preview-09-2025",
                system_instruction=system_instruction
            )
            # Use non-streaming generate_content
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1000
                )
            )
            if response and response.candidates:
                text = response.candidates[0].content.parts[0].text
                if text:
                    return text.strip()
            raise Exception("Empty or invalid response from API")
        except Exception as e:
            if i == max_retries - 1:
                return f"Error generating section after {max_retries} attempts: {str(e)}"
            # Exponential backoff: 1s, 2s, 4s, 8s, 16s
            time.sleep(2**i)
    return "Generation failed."

def auto_generate_sow():
    """Triggers the LLM to populate all editable fields based on metadata."""
    meta = st.session_state.sow_data["metadata"]
    context = f"Solution: {meta['solution_type']}, Industry: {meta['industry']}, Type: {meta['engagement_type']}"

    # UI tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 1. Project Objective
        status_text.text("Drafting Project Objective...")
        st.session_state.sow_data["sections"]["objective"] = call_gemini(
            f"Draft a professional business objective for {context}.",
            "You are a senior IT consultant. Write a 2-paragraph objective focusing on business value. No marketing language."
        )
        progress_bar.progress(20)

        # 2. Assumptions & Dependencies
        status_text.text("Expanding Assumptions...")
        st.session_state.sow_data["sections"]["assumptions"] = call_gemini(
            f"List 5 technical assumptions and 3 customer dependencies for {context}.",
            "Format as a professional bulleted list for a legal SOW. Do not include introductory text."
        )
        progress_bar.progress(40)

        # 3. Success Criteria
        status_text.text("Defining Success Criteria...")
        st.session_state.sow_data["sections"]["success_criteria"] = call_gemini(
            f"Define 4 measurable KPIs for success in this {meta['solution_type']} project.",
            "Focus on metrics like Latency, Accuracy, and User Adoption. Use a bulleted list."
        )
        progress_bar.progress(60)

        # 4. Technical Scope (Infra/Workflows)
        status_text.text("Structuring Technical Infrastructure...")
        st.session_state.sow_data["sections"]["infra_setup"] = call_gemini(
            f"Detail the Infrastructure Setup requirements for a {meta['solution_type']} on AWS.",
            "Describe VPC, compute (Lambda/ECS), and LLM endpoint (Bedrock) requirements professionally."
        )
        progress_bar.progress(80)

        # 5. Core Workflows & Backend
        status_text.text("Finalizing Core Workflows...")
        st.session_state.sow_data["sections"]["core_workflows"] = call_gemini(
            f"Describe the core logical workflows for {context}, specifically RAG or Agentic flows.",
            "Write a professional description of the data flow and orchestration logic."
        )
        
        # Pre-filling static components for reliability
        st.session_state.sow_data["sections"]["backend_components"] = f"Integration with {meta['industry']}-specific data sources, vector database (OpenSearch/Pinecone), and identity management systems."
        st.session_state.sow_data["sections"]["testing_feedback"] = "Execution of comprehensive UAT, prompt engineering optimization cycles, and performance benchmarking against latency targets."
        
        progress_bar.progress(100)
        status_text.text("SOW Draft Completed.")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
    except Exception as e:
        st.error(f"An unexpected error occurred during generation: {e}")

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
            st.rerun() # Ensure the main UI refreshes with new state

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
