import streamlit as st
import json
import boto3
import google.generativeai as genai
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import pandas as pd
from datetime import datetime, timedelta
import io
import os

# --- CONFIGURATION & INITIALIZATION ---
st.set_page_config(page_title="GenAI SOW Agent", layout="wide", page_icon="📝")

# Gemini API Setup (Fallback/Primary LLM)
# The system environment provides the key at runtime for the preview environment
apiKey = "" 
genai.configure(api_key=apiKey)

# Constants
APP_ID = "sow-generator-v1"
MODELS = ["gemini-1.5-pro", "gemini-1.5-flash"]

# --- UI STATE MANAGEMENT ---
if 'sow_data' not in st.session_state:
    st.session_state.sow_data = {}
if 'generated_sections' not in st.session_state:
    st.session_state.generated_sections = {}

# --- HELPER FUNCTIONS ---

def call_llm(prompt, system_instruction):
    """Orchestrates section-wise prompt invocation with exponential backoff logic."""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025",
            system_instruction=system_instruction
        )
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1000,
            )
        )
        return response.text
    except Exception as e:
        st.error(f"LLM Error: {str(e)}")
        return "Content generation failed. Please refine inputs and retry."

def save_to_s3(data, filename):
    """Mock S3 storage logic for the artifact environment."""
    # In a real AWS environment, use boto3.client('s3').put_object(...)
    # For this demo, we store in session state to simulate persistence
    st.session_state.sow_data[filename] = data
    return True

def calculate_costs(volumes, solution_type):
    """Deterministic cost calculator based on solution tiers."""
    base_costs = {
        "Generative AI Chatbot": 500,
        "Document Intelligence": 800,
        "Agentic Workflow": 1200,
        "Image/Multimodal": 1500
    }
    unit_cost = base_costs.get(solution_type, 500)
    total = volumes * unit_cost * 0.01 # Mock logic
    return round(total, 2)

# --- UI COMPONENTS ---

def sidebar_navigation():
    with st.sidebar:
        st.title("SOW Control Center")
        st.info("Fill out the project parameters to generate a production-ready Statement of Work.")
        if st.button("Reset Form", type="secondary"):
            st.session_state.sow_data = {}
            st.rerun()

def main_form():
    st.title("🚀 GenAI Scope of Work (SOW) Agent")
    
    # --- 1. SOLUTION SELECTION & CONTEXT ---
    with st.expander("1. Solution Selection & High-Level Context", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            sol_type = st.selectbox("Solution Type", [
                "Generative AI Chatbot", 
                "Document Intelligence / RAG", 
                "Agentic Workflow Automation", 
                "Multi-modal Content Generation",
                "Code Transformation",
                "Other"
            ])
            eng_type = st.selectbox("Engagement Type", ["Proof of Concept (PoC)", "Production Pilot", "Migration", "Advisory"])
        with col2:
            industry = st.selectbox("Industry", ["Financial Services", "Healthcare", "Manufacturing", "Retail", "Public Sector", "Other"])
            if industry == "Other":
                industry_custom = st.text_input("Specify Industry")
            
    # --- 2. PROJECT OVERVIEW ---
    with st.expander("2. Project Overview"):
        biz_obj = st.text_area("Business Objective", placeholder="Describe the problem being solved...")
        outcomes = st.multiselect("Key Outcomes Expected", [
            "Increased Efficiency", "Reduced Operational Cost", "Improved Customer Experience", 
            "Data Extraction Accuracy", "Faster Time-to-Market", "Scalability Compliance"
        ])
        
        st.write("**Stakeholder Matrix**")
        col_s1, col_s2, col_s3 = st.columns(3)
        partner_sponsor = col_s1.text_input("Partner Exec Sponsor")
        customer_sponsor = col_s2.text_input("Customer Exec Sponsor")
        escalation_contact = col_s3.text_input("Escalation Contact")

    # --- 3. ASSUMPTIONS & DEPENDENCIES ---
    with st.expander("3. Assumptions & Dependencies"):
        cust_deps = st.multiselect("Customer Dependencies", [
            "Data Access Provided within 48 hours",
            "SME availability for testing",
            "AWS Account access with Admin permissions",
            "Cleaned dataset availability",
            "Single Sign-On (SSO) integration access"
        ])
        
        data_types = st.multiselect("Data Characteristics", ["Structured (SQL)", "Unstructured (PDF/DOC)", "Semi-structured (JSON)", "Image/Video"])
        
        # Conditional follow-up
        if "Unstructured (PDF/DOC)" in data_types:
            st.warning("OCR and Chunking strategies will be required.")
            chunk_size = st.slider("Target Chunk Size (Tokens)", 256, 1024, 512)

    # --- 4. POC SUCCESS CRITERIA ---
    with st.expander("4. PoC Success Criteria"):
        success_dims = st.multiselect("Success Dimensions", ["Accuracy", "Latency", "User Satisfaction", "Cost per Inference", "Security Compliance"])
        validation_req = st.radio("User Validation Requirement", ["Required", "Not Required", "Optional"])

    # --- 5. SCOPE OF WORK (TECHNICAL) ---
    with st.expander("5. Scope of Work – Technical Components"):
        core_caps = st.text_area("Core Capabilities", value=f"Generic {sol_type} capabilities including authentication and API endpoints.")
        integrations = st.multiselect("Integrations Required", ["Salesforce", "ServiceNow", "Slack/Teams", "Internal Database", "Custom REST API"])

    # --- 6. ARCHITECTURE & SERVICES ---
    with st.expander("6. Architecture & AWS Services"):
        c1, c2, c3 = st.columns(3)
        compute = c1.selectbox("Compute", ["AWS Lambda", "Amazon ECS (Fargate)", "Amazon SageMaker Endpoints"])
        genai_svc = c2.multiselect("GenAI Services", ["Amazon Bedrock", "Amazon SageMaker", "AWS HealthScribe"])
        storage = c3.multiselect("Storage & Search", ["Amazon OpenSearch", "Amazon Aurora", "Amazon S3", "Pinecone"])

    # --- 8. TIMELINE & COSTING ---
    with st.expander("8. Timeline & Costing"):
        duration = st.selectbox("PoC Duration", ["4 Weeks", "6 Weeks", "8 Weeks", "12 Weeks"])
        vol_input = st.number_input("Expected Monthly Transaction Volume", min_value=0, value=1000)
        
        estimated_cost = calculate_costs(vol_input, sol_type)
        st.metric("Estimated Implementation Cost (Credits/USD)", f"${estimated_cost}")

    # --- ASSEMBLY LOGIC ---
    if st.button("Assemble & Generate SOW", type="primary"):
        with st.status("Generating SOW Sections via LLM...") as status:
            # Prepare data for LLM
            context = f"Solution: {sol_type}, Engagement: {eng_type}, Industry: {industry}"
            
            # 1. Generate Business Objective Section
            st.write("Refining Project Overview...")
            obj_prompt = f"Context: {context}. User input: {biz_obj}. Expected Outcomes: {', '.join(outcomes)}. Refine this into a professional 'Project Objective' section for a Statement of Work."
            st.session_state.generated_sections['objective'] = call_llm(obj_prompt, "You are a professional AWS Solutions Architect writing a Statement of Work.")
            
            # 2. Generate Assumptions Section
            st.write("Expanding Assumptions...")
            assump_prompt = f"List these dependencies as formal SOW clauses: {', '.join(cust_deps)}. Mention {', '.join(data_types)} data handling requirements."
            st.session_state.generated_sections['assumptions'] = call_llm(assump_prompt, "Write formal business assumptions for an AI project. Use professional consulting tone.")

            # 3. Generate Technical Scope
            st.write("Structuring Technical Plan...")
            scope_prompt = f"Develop a technical scope of work for a {sol_type} using {compute} and {', '.join(genai_svc)}. Integrations: {', '.join(integrations)}."
            st.session_state.generated_sections['technical_scope'] = call_llm(scope_prompt, "Generate a detailed technical work plan with 'Infrastructure', 'Workflows', and 'Testing' subsections.")

            # 4. Success Criteria
            st.write("Defining Success Criteria...")
            success_prompt = f"Create measurable success criteria for: {', '.join(success_dims)} based on a {sol_type} PoC."
            st.session_state.generated_sections['success'] = call_llm(success_prompt, "You are a Quality Assurance engineer. Create measurable KPIs.")

            status.update(label="SOW Generated Successfully!", state="complete")
            st.success("All sections generated. Review below and download.")

    # --- PREVIEW AND EDITING ---
    if st.session_state.generated_sections:
        st.divider()
        st.subheader("Review Generated Content")
        
        # Make the LLM outputs editable before final docx generation
        st.session_state.generated_sections['objective'] = st.text_area("Objective (Editable)", st.session_state.generated_sections.get('objective'))
        st.session_state.generated_sections['assumptions'] = st.text_area("Assumptions (Editable)", st.session_state.generated_sections.get('assumptions'))
        st.session_state.generated_sections['technical_scope'] = st.text_area("Technical Scope (Editable)", st.session_state.generated_sections.get('technical_scope'))
        
        # FINAL EXPORT
        doc_buffer = generate_docx(st.session_state.generated_sections, {
            "solution": sol_type, 
            "industry": industry, 
            "duration": duration, 
            "cost": estimated_cost,
            "services": f"{compute}, {', '.join(genai_svc)}"
        })
        
        st.download_button(
            label="📥 Download SOW (DOCX)",
            data=doc_buffer,
            file_name=f"SOW_{sol_type.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

def generate_docx(sections, meta):
    """Assembles the final DOCX document with professional styling."""
    doc = Document()
    
    # Title Section
    title = doc.add_heading('Statement of Work (SOW)', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.add_run(f"Solution: {meta['solution']}\n").bold = True
    p.add_run(f"Industry: {meta['industry']}\n")
    p.add_run(f"Duration: {meta['duration']}\n")
    p.add_run(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
    
    # 1. PROJECT OVERVIEW
    doc.add_heading('1. PROJECT OVERVIEW', level=1)
    doc.add_heading('Objective', level=2)
    doc.add_paragraph(sections.get('objective', ''))
    
    doc.add_heading('Assumptions & Dependencies', level=2)
    doc.add_paragraph(sections.get('assumptions', ''))
    
    doc.add_heading('PoC Success Criteria', level=2)
    doc.add_paragraph(sections.get('success', ''))
    
    # 2. SCOPE OF WORK
    doc.add_heading('2. SCOPE OF WORK – TECHNICAL PROJECT PLAN', level=1)
    doc.add_paragraph(sections.get('technical_scope', ''))
    
    # 3. INFRASTRUCTURE & PRICING (Deterministic)
    doc.add_heading('3. INFRASTRUCTURE & COSTING', level=1)
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Component'
    hdr_cells[1].text = 'Details'
    
    row1 = table.add_row().cells
    row1[0].text = 'AWS Services'
    row1[1].text = meta['services']
    
    row2 = table.add_row().cells
    row2[0].text = 'Estimated Cost'
    row2[1].text = f"${meta['cost']} USD (Credits)"

    # Footer
    doc.add_paragraph("\n\nConfidential - Internal Use Only")
    
    # Save to buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- RUN APP ---
if __name__ == "__main__":
    sidebar_navigation()
    main_form()