import streamlit as st
import json
import io
import pandas as pd
import time
import os
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
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
            "solution_type": "Multi Agent Store Advisor",
            "other_solution": "",
            "selected_sections": [],
            "industry": "Financial Services",
            "customer_name": "Acme Corp",
            "raw_objective_input": "", 
        },
        "sections": {
            "2.1 OBJECTIVE": "",
            "2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM": "",
            "2.3 ASSUMPTIONS & DEPENDENCIES": "",
            "2.4 PoC Success Criteria": "",
            "3 SCOPE OF WORK - TECHNICAL PROJECT PLAN": "",
            "4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM": "",
            "5 RESOURCES & COST ESTIMATES": ""
        }
    }

# --- LLM UTILS ---

def generate_selected_content():
    """
    Generates content only for the sections selected by the user.
    Uses an iterative approach (one call per section) for maximum reliability.
    """
    meta = st.session_state.sow_data["metadata"]
    solution = meta["other_solution"] if meta["solution_type"] == "Other (Please specify)" else meta["solution_type"]
    selected = meta["selected_sections"]
    raw_input = meta["raw_objective_input"]
    
    if not selected:
        st.error("Please select at least one section to generate.")
        return False

    status_placeholder = st.empty()
    
    # Prompt helper mapping
    prompt_map = {
        "2.1 OBJECTIVE": f"Rewrite the following business problem into a formal Statement of Work Objective section: '{raw_input}'. Align it strictly to the '{solution}' solution type.",
        "2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM": "Describe the ideal project team structure including Sponsor, Tech Lead, and SME roles for this project.",
        "2.3 ASSUMPTIONS & DEPENDENCIES": "List 5 technical assumptions and 3 customer dependencies (e.g. data access, API keys). Use bullets.",
        "2.4 PoC Success Criteria": "Define 4 measurable KPIs for this PoC (e.g. Accuracy, Latency, Adoption). Use bullets.",
        "3 SCOPE OF WORK - TECHNICAL PROJECT PLAN": "Detail the technical work plan phases: Discovery, Infrastructure Setup, Development, and Testing/UAT.",
        "4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM": "Describe the high-level AWS architecture components (Bedrock, Lambda, OpenSearch) required for this solution.",
        "5 RESOURCES & COST ESTIMATES": "Provide a high-level estimate of resource roles needed and potential cloud consumption costs/credits."
    }

    # Iterate through selected sections and generate content for each
    for i, section_key in enumerate(selected):
        status_placeholder.info(f"⏳ AI Agent drafting section ({i+1}/{len(selected)}): {section_key}...")
        
        system_prompt = "You are a Senior AI Solutions Architect. Write professional, formal, and authoritative SOW content. Do not use conversational filler, greetings, or markdown headers. Ensure the output is ready to be pasted directly into a legal document."
        
        user_prompt = f"""
        Solution Type: {solution}
        Industry/Domain: {meta['industry']}
        Customer: {meta['customer_name']}
        Task: {prompt_map[section_key]}
        """

        max_retries = 3
        retry_delays = [2, 4, 8]
        
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash-preview-09-2025",
                    system_instruction=system_prompt
                )
                
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=1500,
                    ),
                    request_options={"timeout": 60} 
                )
                
                if response and response.text:
                    st.session_state.sow_data["sections"][section_key] = response.text.strip()
                    break
                else:
                    raise Exception("Empty response from model.")
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delays[attempt])
                else:
                    st.error(f"Failed to generate {section_key}: {str(e)}")

    status_placeholder.success("✅ Drafting complete! Review your sections below.")
    time.sleep(1)
    status_placeholder.empty()
    return True

# --- EXPORT UTILS ---

def create_docx(data):
    doc = Document()
    title = doc.add_heading('Statement of Work (SOW)', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    sol = data['metadata']['other_solution'] if data['metadata']['solution_type'] == "Other (Please specify)" else data['metadata']['solution_type']
    p = doc.add_paragraph()
    p.add_run(f"Customer: {data['metadata']['customer_name']}\n").bold = True
    p.add_run(f"Solution: {sol}\n")
    p.add_run(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")

    for section_name, content in data['sections'].items():
        if content:
            doc.add_heading(section_name, level=1)
            doc.add_paragraph(content)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- MAIN UI ---

def main():
    st.sidebar.title("🛠️ SOW Configuration")
    
    with st.sidebar:
        st.session_state.sow_data["metadata"]["customer_name"] = st.text_input("Customer Name", value=st.session_state.sow_data["metadata"]["customer_name"])
        
        solution_options = [
            "Multi Agent Store Advisor", "Intelligent Search", "Recommendation", 
            "AI Agents Demand Forecasting", "Banner Audit using LLM", "Image Enhancement", 
            "Virtual Try-On", "Agentic AI L1 Support", "Product Listing Standardization", 
            "AI Agents Based Pricing Module", "Cost, Margin Visibility & Insights using LLM", 
            "AI Trend Simulator", "Virtual Data Analyst (Text to SQL)", "Multilingual Call Analysis", 
            "Customer Review Analysis", "Sales Co-Pilot", "Research Co-Pilot", 
            "Product Copy Generator", "Multi-agent e-KYC & Onboarding", "Document / Report Audit", 
            "RBI Circular Scraping & Insights Bot", "Visual Inspection", "AIoT based CCTV Surveillance", 
            "Multilingual Voice Bot", "SOP Creation", "Other (Please specify)"
        ]
        
        st.session_state.sow_data["metadata"]["solution_type"] = st.selectbox("1. Select Solution Type", solution_options)
        
        if st.session_state.sow_data["metadata"]["solution_type"] == "Other (Please specify)":
            st.session_state.sow_data["metadata"]["other_solution"] = st.text_input("Please specify solution name")

        st.session_state.sow_data["metadata"]["industry"] = st.selectbox("Industry", ["Financial Services", "Retail", "Healthcare", "Manufacturing", "Legal", "Public Sector"])
        
        st.divider()
        
        # --- BUSINESS OBJECTIVE INPUT ---
        st.write("### 2. Project Overview Inputs")
        st.session_state.sow_data["metadata"]["raw_objective_input"] = st.text_area(
            "What business problem is the customer solving?", 
            placeholder="Example: Reduce manual effort, improve accuracy, enable faster decision-making, improve conversion, etc.",
            help="This input will be refined by the LLM into the formal '2.1 OBJECTIVE' section."
        )

        st.divider()
        st.write("### 3. Select Sections to Generate")
        section_list = [
            "2.1 OBJECTIVE", 
            "2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM", 
            "2.3 ASSUMPTIONS & DEPENDENCIES", 
            "2.4 PoC Success Criteria", 
            "3 SCOPE OF WORK - TECHNICAL PROJECT PLAN", 
            "4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM", 
            "5 RESOURCES & COST ESTIMATES"
        ]
        
        st.session_state.sow_data["metadata"]["selected_sections"] = []
        for section in section_list:
            if st.checkbox(section, value=True, key=f"check_{section}"):
                st.session_state.sow_data["metadata"]["selected_sections"].append(section)

        st.divider()
        if st.button("🪄 Auto-Draft Selected Sections", type="primary", use_container_width=True):
            if generate_selected_content():
                st.rerun()

    st.title("📄 GenAI SOW Architect")
    st.markdown("Automate professional enterprise SOW creation with AI agents.")

    # Simplified Tab Names
    tabs = st.tabs(["Project Overview", "Technical Execution", "Financials"])

    with tabs[0]:
        st.subheader("Project Overview")
        st.session_state.sow_data["sections"]["2.1 OBJECTIVE"] = st.text_area("2.1 OBJECTIVE", value=st.session_state.sow_data["sections"]["2.1 OBJECTIVE"], height=200, key="area_21")
        st.session_state.sow_data["sections"]["2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM"] = st.text_area("2.2 STAKEHOLDERS", value=st.session_state.sow_data["sections"]["2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM"], height=200, key="area_22")
        st.session_state.sow_data["sections"]["2.3 ASSUMPTIONS & DEPENDENCIES"] = st.text_area("2.3 ASSUMPTIONS", value=st.session_state.sow_data["sections"]["2.3 ASSUMPTIONS & DEPENDENCIES"], height=200, key="area_23")
        st.session_state.sow_data["sections"]["2.4 PoC Success Criteria"] = st.text_area("2.4 SUCCESS CRITERIA", value=st.session_state.sow_data["sections"]["2.4 PoC Success Criteria"], height=200, key="area_24")

    with tabs[1]:
        st.subheader("Technical Execution")
        st.session_state.sow_data["sections"]["3 SCOPE OF WORK - TECHNICAL PROJECT PLAN"] = st.text_area("3 SCOPE OF WORK", value=st.session_state.sow_data["sections"]["3 SCOPE OF WORK - TECHNICAL PROJECT PLAN"], height=300, key="area_3")
        st.session_state.sow_data["sections"]["4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM"] = st.text_area("4 SOLUTION ARCHITECTURE", value=st.session_state.sow_data["sections"]["4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM"], height=250, key="area_4")

    with tabs[2]:
        st.subheader("Financials")
        st.session_state.sow_data["sections"]["5 RESOURCES & COST ESTIMATES"] = st.text_area("5 RESOURCES & COSTS", value=st.session_state.sow_data["sections"]["5 RESOURCES & COST ESTIMATES"], height=250, key="area_5")

        st.divider()
        st.subheader("Finalize & Download")
        docx_bytes = create_docx(st.session_state.sow_data)
        st.download_button(
            label="📥 Download SOW (Word)",
            data=docx_bytes,
            file_name=f"SOW_{st.session_state.sow_data['metadata']['customer_name'].replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
