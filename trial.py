import streamlit as st
import json
import io
import time
import os
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="GenAI SOW Agent", layout="wide", page_icon="📝")

# --- STABILITY OVERRIDES ---
# Disable client certificate checks which often cause 503/504 hangs in sandboxed environments
os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
os.environ["GRPC_DNS_RESOLVER"] = "native"

# --- API INITIALIZATION ---
# The environment provides the key at runtime. We use an empty string for the default configuration.
# Note: In this environment, gemini-2.5-flash-preview-09-2025 is the primary supported model for generation.
apiKey = "" 
genai.configure(api_key=apiKey, transport='rest')

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

# --- LLM ENGINE ---

def call_genai_service(prompt):
    """
    Stable call wrapper using gemini-2.5-flash-preview-09-2025 with REST transport and aggressive retries.
    """
    try:
        # Reverting to the primary supported model for this environment for maximum stability
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025",
            system_instruction="You are a professional SOW Architect. Write formal, technical, and concise document content. No greetings, no intros, no conversational filler."
        )
        
        # Mandatory Exponential Backoff
        max_retries = 5
        retry_delays = [2, 4, 8, 16, 32]
        
        for attempt in range(max_retries):
            try:
                # Use generateContent (non-streaming)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=2048,
                    ),
                    request_options={"timeout": 120}
                )
                
                if response and response.text:
                    return response.text.strip()
                else:
                    raise Exception("Model returned empty content.")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"Error: {str(e)}"
                time.sleep(retry_delays[attempt])
    except Exception as e:
        return f"Initialization Error: {str(e)}"
    
    return "Error: Unknown failure in AI service."

def generate_selected_content():
    """
    Iterative drafting engine. Processes sections one-by-one to ensure stability.
    """
    meta = st.session_state.sow_data["metadata"]
    solution = meta["other_solution"] if meta["solution_type"] == "Other (Please specify)" else meta["solution_type"]
    selected = meta["selected_sections"]
    raw_input = meta["raw_objective_input"]
    
    if not selected:
        st.error("Please select at least one section to generate.")
        return False

    status_placeholder = st.empty()
    
    prompt_map = {
        "2.1 OBJECTIVE": f"Rewrite this business problem into a formal SOW Objective section for a {solution} project: '{raw_input}'.",
        "2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM": f"Describe the project team structure and professional roles required for a {solution} implementation.",
        "2.3 ASSUMPTIONS & DEPENDENCIES": f"List 5 specific technical assumptions and 3 critical customer dependencies for a {solution} deployment.",
        "2.4 PoC Success Criteria": f"Define 4 measurable and realistic KPIs to validate the success of a {solution} PoC.",
        "3 SCOPE OF WORK - TECHNICAL PROJECT PLAN": f"Detail the technical implementation phases (Discovery, Design, Development, and UAT) for {solution}.",
        "4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM": f"Describe the high-level AWS architecture components (e.g., Bedrock, Lambda, OpenSearch) for {solution}.",
        "5 RESOURCES & COST ESTIMATES": f"Estimate resource roles (e.g., Data Engineer, ML Ops) and cloud consumption cost drivers for {solution}."
    }

    for i, section_key in enumerate(selected):
        status_placeholder.info(f"⏳ AI Agent drafting {section_key} ({i+1}/{len(selected)})...")
        
        prompt = f"Context: {meta['industry']} industry.\nTask: {prompt_map[section_key]}"
        
        generated_text = call_genai_service(prompt)
        
        if "Error:" not in generated_text:
            st.session_state.sow_data["sections"][section_key] = generated_text
        else:
            st.error(f"❌ Failed to draft {section_key}: {generated_text}")

    status_placeholder.success("✅ Drafting complete!")
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
    st.sidebar.title("🛠️ SOW Designer")
    
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
            st.session_state.sow_data["metadata"]["other_solution"] = st.text_input("Specify Solution Name")

        st.session_state.sow_data["metadata"]["industry"] = st.selectbox("Industry", ["Retail", "Financial Services", "Healthcare", "Manufacturing", "Legal"])
        
        st.divider()
        st.write("### 2. Business Context")
        st.session_state.sow_data["metadata"]["raw_objective_input"] = st.text_area(
            "What problem are we solving?", 
            placeholder="e.g. Automate manual document review to reduce turnaround time...",
            help="AI will transform this into the formal Objective section."
        )

        st.divider()
        st.write("### 3. SOW Structure")
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
        if st.button("🪄 Auto-Generate SOW", type="primary", use_container_width=True):
            if generate_selected_content():
                st.rerun()

    st.title("📄 AI Statement of Work Architect")
    st.markdown("Automate enterprise-grade SOW drafting.")

    tabs = st.tabs(["Project Overview", "Technical Plan", "Financials & Export"])

    with tabs[0]:
        st.session_state.sow_data["sections"]["2.1 OBJECTIVE"] = st.text_area("2.1 OBJECTIVE", value=st.session_state.sow_data["sections"]["2.1 OBJECTIVE"], height=200, key="area_21")
        st.session_state.sow_data["sections"]["2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM"] = st.text_area("2.2 STAKEHOLDERS", value=st.session_state.sow_data["sections"]["2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM"], height=200, key="area_22")
        st.session_state.sow_data["sections"]["2.3 ASSUMPTIONS & DEPENDENCIES"] = st.text_area("2.3 ASSUMPTIONS", value=st.session_state.sow_data["sections"]["2.3 ASSUMPTIONS & DEPENDENCIES"], height=200, key="area_23")
        st.session_state.sow_data["sections"]["2.4 PoC Success Criteria"] = st.text_area("2.4 SUCCESS CRITERIA", value=st.session_state.sow_data["sections"]["2.4 PoC Success Criteria"], height=200, key="area_24")

    with tabs[1]:
        st.session_state.sow_data["sections"]["3 SCOPE OF WORK - TECHNICAL PROJECT PLAN"] = st.text_area("3 SCOPE OF WORK", value=st.session_state.sow_data["sections"]["3 SCOPE OF WORK - TECHNICAL PROJECT PLAN"], height=300, key="area_3")
        st.session_state.sow_data["sections"]["4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM"] = st.text_area("4 SOLUTION ARCHITECTURE", value=st.session_state.sow_data["sections"]["4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM"], height=250, key="area_4")

    with tabs[2]:
        st.session_state.sow_data["sections"]["5 RESOURCES & COST ESTIMATES"] = st.text_area("5 RESOURCES & COSTS", value=st.session_state.sow_data["sections"]["5 RESOURCES & COST ESTIMATES"], height=250, key="area_5")

        st.divider()
        docx_bytes = create_docx(st.session_state.sow_data)
        st.download_button(
            label="📥 Download SOW (DOCX)",
            data=docx_bytes,
            file_name=f"SOW_{st.session_state.sow_data['metadata']['customer_name'].replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
