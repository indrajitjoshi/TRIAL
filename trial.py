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
            "solution_type": "Multi Agent Store Advisor",
            "other_solution": "",
            "selected_sections": [],
            "industry": "Financial Services",
            "customer_name": "Acme Corp",
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
    Uses Gemini 2.5 Flash for professional SOW drafting.
    """
    meta = st.session_state.sow_data["metadata"]
    solution = meta["other_solution"] if meta["solution_type"] == "Other (Please specify)" else meta["solution_type"]
    selected = meta["selected_sections"]
    
    if not selected:
        st.error("Please select at least one section to generate.")
        return False

    status_placeholder = st.empty()
    status_placeholder.info(f"🚀 Drafting {len(selected)} sections for {solution}...")
    
    # Mapping keys to descriptive prompts
    prompt_map = {
        "2.1 OBJECTIVE": "Write a 2-paragraph professional business objective for this solution.",
        "2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM": "Describe the ideal project team structure including Sponsor, Tech Lead, and SME roles.",
        "2.3 ASSUMPTIONS & DEPENDENCIES": "List 5 technical assumptions and 3 customer dependencies (e.g. data access, API keys).",
        "2.4 PoC Success Criteria": "Define 4 measurable KPIs for this PoC (e.g. Accuracy, Latency, Adoption).",
        "3 SCOPE OF WORK - TECHNICAL PROJECT PLAN": "Detail the technical work plan phases: Discovery, Infra, Development, and Testing.",
        "4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM": "Describe the high-level AWS architecture components (Bedrock, Lambda, OpenSearch) required.",
        "5 RESOURCES & COST ESTIMATES": "Provide a high-level estimate of resource hours and cloud consumption costs."
    }

    # Filter prompts for selected sections only
    targeted_prompts = {k: prompt_map[k] for k in selected}

    system_prompt = """
    You are a Senior AI Solutions Architect. Generate professional consulting content for a Statement of Work.
    Return the response ONLY in a structured JSON format where the keys match the section names provided.
    Tone: Professional, Factual, Fomal. No conversational filler.
    """
    
    user_prompt = f"""
    Solution: {solution}
    Industry: {meta['industry']}
    Sections to generate: {json.dumps(targeted_prompts)}
    """

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
            generated_data = json.loads(res_text)
            
            # Update Session State only for what was generated
            for section in selected:
                st.session_state.sow_data["sections"][section] = generated_data.get(section, "Generation failed for this section.")
            
            status_placeholder.success("✅ SOW Content Ready! Review the sections below.")
            time.sleep(1.5)
            status_placeholder.empty()
            return True
    except Exception as e:
        status_placeholder.error(f"Drafting failed: {str(e)}")
        return False

# --- EXPORT UTILS ---

def create_docx(data):
    doc = Document()
    
    # Header
    title = doc.add_heading('Statement of Work (SOW)', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Metadata
    sol = data['metadata']['other_solution'] if data['metadata']['solution_type'] == "Other (Please specify)" else data['metadata']['solution_type']
    p = doc.add_paragraph()
    p.add_run(f"Customer: {data['metadata']['customer_name']}\n").bold = True
    p.add_run(f"Solution: {sol}\n")
    p.add_run(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")

    # Content Sections
    for section_name, content in data['sections'].items():
        if content: # Only include non-empty sections
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
        
        # 1. Solution Type Selection (Pre-seeded list)
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
        
        # 2. Section Selection Checklist
        st.write("### 2. Select Sections to Generate")
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
            if st.checkbox(section, value=True):
                st.session_state.sow_data["metadata"]["selected_sections"].append(section)

        st.divider()
        if st.button("🪄 Auto-Draft Selected Sections", type="primary", use_container_width=True):
            if generate_selected_content():
                st.rerun()

    st.title("📄 GenAI SOW Architect")
    st.markdown("Automate professional Statements of Work for enterprise AI solutions.")

    # TABS FOR CONTENT REVIEW & EDITING
    tab_list = ["Project Foundations", "Technical & Architecture", "Resource & Export"]
    tabs = st.tabs(tab_list)

    with tabs[0]:
        st.subheader("Heading 2: Project Overview")
        st.session_state.sow_data["sections"]["2.1 OBJECTIVE"] = st.text_area("2.1 OBJECTIVE", value=st.session_state.sow_data["sections"]["2.1 OBJECTIVE"], height=150)
        st.session_state.sow_data["sections"]["2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM"] = st.text_area("2.2 STAKEHOLDERS", value=st.session_state.sow_data["sections"]["2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM"], height=150)
        st.session_state.sow_data["sections"]["2.3 ASSUMPTIONS & DEPENDENCIES"] = st.text_area("2.3 ASSUMPTIONS", value=st.session_state.sow_data["sections"]["2.3 ASSUMPTIONS & DEPENDENCIES"], height=150)
        st.session_state.sow_data["sections"]["2.4 PoC Success Criteria"] = st.text_area("2.4 SUCCESS CRITERIA", value=st.session_state.sow_data["sections"]["2.4 PoC Success Criteria"], height=150)

    with tabs[1]:
        st.subheader("Heading 3 & 4: Execution")
        st.session_state.sow_data["sections"]["3 SCOPE OF WORK - TECHNICAL PROJECT PLAN"] = st.text_area("3 SCOPE OF WORK", value=st.session_state.sow_data["sections"]["3 SCOPE OF WORK - TECHNICAL PROJECT PLAN"], height=250)
        st.session_state.sow_data["sections"]["4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM"] = st.text_area("4 SOLUTION ARCHITECTURE", value=st.session_state.sow_data["sections"]["4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM"], height=200)

    with tabs[2]:
        st.subheader("Heading 5: Financials")
        st.session_state.sow_data["sections"]["5 RESOURCES & COST ESTIMATES"] = st.text_area("5 RESOURCES & COSTS", value=st.session_state.sow_data["sections"]["5 RESOURCES & COST ESTIMATES"], height=200)

        st.divider()
        st.subheader("Finalize & Download")
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
