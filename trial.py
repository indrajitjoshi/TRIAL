import streamlit as st
import json
import time
import requests
import pandas as pd
from datetime import datetime
from fpdf import FPDF  # Requires: pip install fpdf

# --- CONFIGURATION ---
ST_PAGE_TITLE = "GenAI SOW Architect"
ST_PAGE_ICON = "📄"
GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"

# --- CONSTANTS & DROPDOWNS ---
SOLUTION_TYPES = [
    "Multi Agent Store Advisor", "Intelligent Search", "Recommendation", 
    "AI Agents Demand Forecasting", "Banner Audit using LLM", "Image Enhancement", 
    "Virtual Try-On", "Agentic AI L1 Support", "Product Listing Standardization", 
    "AI Agents Based Pricing Module", "Cost, Margin Visibility & Insights using LLM", 
    "AI Trend Simulator", "Virtual Data Analyst (Text to SQL)", "Multilingual Call Analysis", 
    "Customer Review Analysis", "Sales Co-Pilot", "Research Co-Pilot", 
    "Product Copy Generator", "Multi-agent e-KYC & Onboarding", "Document / Report Audit", 
    "RBI Circular Scraping & Insights Bot", "Visual Inspection", "AIoT based CCTV Surveillance", 
    "Multilingual Voice Bot", "SOP Creation", "Other"
]

INDUSTRIES = [
    "Retail / E-commerce", "BFSI", "Manufacturing", "Telecom", "Healthcare", 
    "Energy / Utilities", "Logistics", "Media", "Government", "Other"
]

ENGAGEMENT_TYPES = ["Proof of Concept (PoC)", "Pilot", "MVP", "Production Rollout", "Assessment / Discovery"]
AWS_ML_SERVICES = ["Amazon Bedrock", "Amazon SageMaker", "Amazon Rekognition", "Amazon Textract", "Amazon Comprehend", "Amazon Transcribe", "Amazon Translate"]

# --- PDF GENERATION CLASS ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Statement of Work (SOW)', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, body)
        self.ln()

def clean_text(text):
    """Helper to remove/replace characters incompatible with latin-1 PDF encoding."""
    replacements = {
        '\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'", 
        '\u201c': '"', '\u201d': '"', '●': '-', '•': '-'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

# --- API UTILITIES ---
def call_gemini_json(prompt, schema, system_instruction="You are a professional solution architect."):
    """Calls Gemini with a structured JSON output requirement."""
    api_key = "" # Provided by environment
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    for i in range(5):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                result = response.json()
                text_content = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "{}")
                return json.loads(text_content)
            else:
                time.sleep(2**i)
        except Exception as e:
            if i == 4: st.error(f"API Connection Error: {str(e)}")
            time.sleep(2**i)
    return None

def call_gemini_text(prompt, system_instruction="You are a professional solution architect."):
    """Standard text generation call."""
    api_key = ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    
    for i in range(5):
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "")
            else:
                time.sleep(2**i)
        except Exception:
            time.sleep(2**i)
    return "AI model busy. Please try clicking the button again."

# --- SESSION STATE INITIALIZATION ---
if "autofill_data" not in st.session_state:
    st.session_state.autofill_data = {}
if "autofill_done" not in st.session_state:
    st.session_state.autofill_done = False

# --- PAGE SETUP ---
st.set_page_config(page_title=ST_PAGE_TITLE, page_icon=ST_PAGE_ICON, layout="wide")

st.title(f"{ST_PAGE_ICON} {ST_PAGE_TITLE}")
st.markdown("Create end-to-end professional SOWs tailored to specific AWS GenAI solutions.")

tabs = st.tabs([
    "1. High-Level Context", 
    "2. Project Overview", 
    "3. Data & Dependencies", 
    "4. Scope & Architecture", 
    "5. Timeline & Costs",
    "6. Review & Export (PDF)"
])

# --- TAB 1: CONTEXT ---
with tabs[0]:
    col1, col2 = st.columns(2)
    with col1:
        sol_type = st.selectbox("1.1 Solution Type", SOLUTION_TYPES)
        if sol_type == "Other":
            sol_type = st.text_input("Specify Solution Type")
        
        engagement = st.selectbox("1.2 Engagement Type", ENGAGEMENT_TYPES)
        
    with col2:
        industry = st.selectbox("1.3 Industry / Domain", INDUSTRIES)
        if industry == "Other":
            industry = st.text_input("Specify Industry")
        
        customer_name = st.text_input("Customer Name", "Acme Global")

    st.divider()
    if st.button("✨ GENERATE COMPLETE SOW DRAFT (SECTION-BY-SECTION)", use_container_width=True, type="primary"):
        # Initialize dictionary to hold all parts
        generated_sow = {}
        
        # System instruction for high specificity
        sys_instruct = f"You are a specialized Solution Architect for the {industry} industry. You are writing a Statement of Work for a '{sol_type}' solution. All content generated MUST be highly specific to '{sol_type}'. Do NOT use generic project management boilerplate. Use technical terms relevant to {sol_type}."
        
        # Progress status bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. Objective
            status_text.text(f"1/8 Generating Specific Objective for {sol_type}...")
            obj_schema = {
                "type": "OBJECT",
                "properties": {
                    "objective": {"type": "STRING"}
                }
            }
            # Strictly use sol_type for objective generation
            res = call_gemini_json(f"Generate a concise, 1-2 sentence formal business objective specifically for a '{sol_type}' solution. Focus on the core value proposition of {sol_type} (e.g. accuracy, automation, speed). Do not reference generic goals.", obj_schema, sys_instruct)
            if res: generated_sow.update(res)
            progress_bar.progress(12)

            # 2. Stakeholders
            status_text.text("2/8 Generating Stakeholder information...")
            stk_schema = {
                "type": "OBJECT",
                "properties": {
                    "stakeholders": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "role": {"type": "STRING"},
                                "name": {"type": "STRING"},
                                "title": {"type": "STRING"},
                                "email": {"type": "STRING"}
                            }
                        }
                    }
                }
            }
            
            prompt_stakeholders = f"""
            Generate a list of project stakeholders for a {sol_type} project at {customer_name}. 
            Required Roles:
            1. Partner Executive Sponsor: Name "Ram Joshi", Title "Head of Analytics & ML", Email "ram.joshi@oneture.com".
            2. Customer Executive Sponsor: Create a realistic name and title relevant to {industry}.
            3. AWS Executive Sponsor: Create a realistic name and title "AWS Account Executive".
            4. Project Escalation Contacts: Generate TWO distinct people (Partner & Customer side).
            """
            res = call_gemini_json(prompt_stakeholders, stk_schema, sys_instruct)
            if res: generated_sow.update(res)
            progress_bar.progress(25)

            # 3. Dependencies & Assumptions
            status_text.text(f"3/8 Generating Specific Dependencies for {sol_type}...")
            deps_schema = {
                 "type": "OBJECT",
                 "properties": {
                     "dependencies": {"type": "ARRAY", "items": {"type": "STRING"}},
                     "assumptions": {"type": "ARRAY", "items": {"type": "STRING"}}
                 }
            }
            prompt_deps = f"""
            Generate a list of Assumptions and Dependencies SPECIFIC to a '{sol_type}' project. 
            - Dependencies: List exactly 6 items. Cover data availability (specific to {sol_type} data), AWS quotas, API access, and SME availability.
            - Assumptions: List exactly 6 items. Cover POC limitations, language/format support, data quality, and existing infra.
            """
            res = call_gemini_json(prompt_deps, deps_schema, sys_instruct)
            if res: generated_sow.update(res)
            progress_bar.progress(37)

            # 4. Data Characteristics
            status_text.text("4/8 Analyzing Data Characteristics...")
            data_schema = {
                "type": "OBJECT",
                "properties": {
                    "data_characteristics": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "type": {"type": "STRING"},
                                "size": {"type": "STRING"},
                                "format": {"type": "STRING"},
                                "volume": {"type": "STRING"}
                            }
                        }
                    }
                }
            }
            res = call_gemini_json(f"Identify 3 realistic data types required for a '{sol_type}'. Provide realistic size (MB/GB) and volume.", data_schema, sys_instruct)
            if res: generated_sow.update(res)
            progress_bar.progress(50)

            # 5. Success Criteria
            status_text.text("5/8 Defining Technical Success Criteria...")
            success_schema = {
                "type": "OBJECT",
                "properties": {
                    "success_criteria": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "heading": {"type": "STRING"},
                                "points": {"type": "ARRAY", "items": {"type": "STRING"}}
                            }
                        }
                    }
                }
            }
            prompt_success = f"""
            Generate detailed PoC Success Criteria for a '{sol_type}' solution. 
            Structure:
            1. Demonstrations: List 3 specific user flows to demo.
            2. Results: List 3 specific metric-based outcomes (e.g. Accuracy %, Latency ms).
            3. Usability: List 2 points about user experience.
            """
            res = call_gemini_json(prompt_success, success_schema, sys_instruct)
            if res: generated_sow.update(res)
            progress_bar.progress(62)

            # 6. Technical Scope
            status_text.text(f"6/8 Architecting Technical Scope for {sol_type}...")
            scope_schema = {
                "type": "OBJECT",
                "properties": {
                    "technical_phases": {
                        "type": "OBJECT",
                        "properties": {
                            "infrastructure_setup": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "core_workflows": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "backend_components": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "feedback_testing": {"type": "ARRAY", "items": {"type": "STRING"}}
                        }
                    }
                }
            }
            prompt_scope = f"""
            Write a comprehensive Technical Project Plan for a '{sol_type}' project. 
            1. Infrastructure Setup: AWS services specific to {sol_type}.
            2. Create Core Workflows: Ingestion, processing, inference steps.
            3. Backend Components: APIs, Databases, Logic layers.
            4. Feedback & Testing: UAT steps.
            """
            res = call_gemini_json(prompt_scope, scope_schema, sys_instruct)
            if res: generated_sow.update(res)
            progress_bar.progress(75)

            # 7. Architecture
            status_text.text("7/8 Selecting AWS Services...")
            arch_schema = {
                "type": "OBJECT",
                "properties": {
                    "architecture": {
                        "type": "OBJECT",
                        "properties": {
                            "compute": {"type": "STRING"},
                            "storage": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "ml_services": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "ui": {"type": "STRING"}
                        }
                    }
                }
            }
            res = call_gemini_json(f"Design an AWS architecture for '{sol_type}'. Suggest best-practice Compute, Storage, and AI Services.", arch_schema, sys_instruct)
            if res: generated_sow.update(res)
            progress_bar.progress(87)

            # 8. Timeline & Costs
            status_text.text("8/8 Finalizing Timeline & Costing...")
            time_schema = {
                "type": "OBJECT",
                "properties": {
                    "timeline": {
                        "type": "ARRAY", 
                        "items": {
                            "type": "OBJECT", 
                            "properties": {
                                "phase": {"type": "STRING"}, 
                                "task": {"type": "STRING"},
                                "weeks": {"type": "STRING"}
                            }
                        }
                    },
                    "usage_users": {"type": "NUMBER"},
                    "usage_requests": {"type": "NUMBER"}
                }
            }
            res = call_gemini_json(f"Create a high-level timeline for a '{engagement}' of a '{sol_type}'. Include Phase, Task Description, and Week duration (e.g. Wk1-Wk2).", time_schema, sys_instruct)
            if res: generated_sow.update(res)
            progress_bar.progress(100)
            
            # Finalize
            st.session_state.autofill_data = generated_sow
            st.session_state.autofill_done = True
            status_text.success("Complete SOW Draft Generated Successfully!")
            st.toast("Check Tab 6 for the Final PDF Report.")

        except Exception as e:
            st.error(f"An error occurred during part-by-part generation: {str(e)}")
            status_text.text("Generation paused due to an error.")

# --- TAB 2: PROJECT OVERVIEW ---
with tabs[1]:
    data = st.session_state.autofill_data
    st.header("2. PROJECT OVERVIEW")
    
    # Auto-generated Objective is displayed here
    st.subheader("2.1 OBJECTIVE")
    st.info("This objective is automatically generated based on the Solution Type selected.")
    final_objective = st.text_area("Edit Objective", value=data.get("objective", ""), height=100)
    # Update state if edited
    st.session_state.autofill_data["objective"] = final_objective

    st.subheader("2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM")
    
    # Defaults if empty
    default_stakeholders = [
        {"role": "Partner Executive Sponsor", "name": "Ram Joshi", "title": "Head of Analytics & ML", "email": "ram.joshi@oneture.com"},
        {"role": "Customer Executive Sponsor", "name": "TBD", "title": "Head of Product", "email": "client@example.com"},
        {"role": "AWS Executive Sponsor", "name": "Anubhav Sood", "title": "AWS Account Executive", "email": "anbhsood@amazon.com"},
        {"role": "Project Escalation Contacts", "name": "Omkar Dhavalikar", "title": "AI/ML Lead", "email": "omkar.dhavalikar@oneture.com"}
    ]
    
    current_stakeholders = data.get("stakeholders", default_stakeholders)
    
    updated_stakeholders = []
    for i, s in enumerate(current_stakeholders):
        st.markdown(f"**{s.get('role', 'Stakeholder')}**")
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("Name", s.get('name', ''), key=f"s_n_{i}")
        t = c2.text_input("Title", s.get('title', ''), key=f"s_t_{i}")
        e = c3.text_input("Email", s.get('email', ''), key=f"s_e_{i}")
        updated_stakeholders.append({"role": s.get('role'), "name": n, "title": t, "email": e})
    
    if st.button("+ Add Stakeholder"):
        updated_stakeholders.append({"role": "New Role", "name": "", "title": "", "email": ""})
        st.session_state.autofill_data["stakeholders"] = updated_stakeholders
        st.rerun()

    # Save back to session state
    st.session_state.autofill_data["stakeholders"] = updated_stakeholders

# --- TAB 3: DATA & DEPENDENCIES ---
with tabs[2]:
    st.header("2.3 ASSUMPTIONS & DEPENDENCIES")
    
    col_d, col_a = st.columns(2)
    
    with col_d:
        st.subheader("Dependencies")
        deps_list = data.get("dependencies", ["Data access provided", "AWS access provided"])
        deps_text = st.text_area("List dependencies (one per line)", value="\n".join(deps_list), height=200)
    
    with col_a:
        st.subheader("Assumptions")
        assump_list = data.get("assumptions", ["POC is not production ready", "English language only"])
        assump_text = st.text_area("List assumptions (one per line)", value="\n".join(assump_list), height=200)

    st.divider()
    st.subheader("Data Characteristics (Internal Use)")
    raw_data_chars = data.get("data_characteristics", [])
    
    processed_data = []
    for i, item in enumerate(raw_data_chars):
        c1, c2, c3, c4 = st.columns(4)
        d_type = c1.text_input("Data Type", value=item.get("type", ""), key=f"dt_t_{i}")
        d_size = c2.text_input("Avg Size", value=item.get("size", ""), key=f"dt_s_{i}")
        d_fmt = c3.text_input("Format", value=item.get("format", ""), key=f"dt_f_{i}")
        d_vol = c4.text_input("Volume", value=item.get("volume", ""), key=f"dt_v_{i}")
        processed_data.append({"type": d_type, "size": d_size, "format": d_fmt, "volume": d_vol})

# --- TAB 4: SCOPE & ARCHITECTURE ---
with tabs[3]:
    st.header("2.4 PoC Success Criteria")
    
    sc_data = data.get("success_criteria", [])
    formatted_sc_text = ""
    for item in sc_data:
        formatted_sc_text += f"**{item.get('heading', 'Criteria')}**\n"
        for point in item.get('points', []):
            formatted_sc_text += f"- {point}\n"
        formatted_sc_text += "\n"
        
    final_sc_text = st.text_area("Edit Success Criteria", value=formatted_sc_text, height=300)

    st.divider()
    st.header("3 SCOPE OF WORK - TECHNICAL PROJECT PLAN")
    
    tech_phases = data.get("technical_phases", {})
    
    st.subheader("1. Infrastructure Setup")
    p1 = st.text_area("Tasks", value="\n".join(tech_phases.get("infrastructure_setup", [])), height=100, key="ph1")
    
    st.subheader("2. Create Core Workflows")
    p2 = st.text_area("Tasks", value="\n".join(tech_phases.get("core_workflows", [])), height=150, key="ph2")
    
    st.subheader("3. Backend Components")
    p3 = st.text_area("Tasks", value="\n".join(tech_phases.get("backend_components", [])), height=100, key="ph3")
    
    st.subheader("4. Feedback & Testing")
    p4 = st.text_area("Tasks", value="\n".join(tech_phases.get("feedback_testing", [])), height=100, key="ph4")

    st.divider()
    st.header("4 SOLUTION ARCHITECTURE")
    arch = data.get("architecture", {})
    col_arch1, col_arch2 = st.columns(2)
    with col_arch1:
        comp_val = arch.get("compute", "AWS Lambda + Step Functions")
        compute = st.selectbox("Compute", ["AWS Lambda + Step Functions", "ECS / EKS", "Hybrid"], index=0 if "Lambda" in str(comp_val) else 1)
        storage = st.multiselect("Storage & Search", ["Amazon S3", "DynamoDB", "OpenSearch", "RDS", "Vector DB (Aurora PG)"], default=arch.get("storage", ["Amazon S3"]))
    with col_arch2:
        ml_services = st.multiselect("GenAI / ML Services", AWS_ML_SERVICES, default=arch.get("ml_services", ["Amazon Bedrock"]))
        ui_val = arch.get("ui", "Streamlit on S3")
        ui_layer = st.selectbox("UI Layer", ["Streamlit on S3", "CloudFront + Static UI", "Internal demo only", "No UI (API only)"], index=0 if "Streamlit" in str(ui_val) else 1)

# --- TAB 5: TIMELINE & COSTS ---
with tabs[4]:
    st.header("Development Timelines")
    raw_timeline = data.get("timeline", [{"phase": "Setup", "task": "Initial Setup", "weeks": "Wk1"}])
    
    final_timeline = []
    for i, step in enumerate(raw_timeline):
        c1, c2, c3 = st.columns([1, 2, 1])
        p_name = c1.text_input("Phase", value=step.get("phase", ""), key=f"p_{i}")
        p_task = c2.text_input("Task", value=step.get("task", ""), key=f"t_{i}")
        p_weeks = c3.text_input("Weeks", value=step.get("weeks", ""), key=f"w_{i}")
        final_timeline.append({"Phase": p_name, "Task": p_task, "Weeks": p_weeks})

    st.divider()
    st.header("5 RESOURCES & COST ESTIMATES")
    c1, c2, c3 = st.columns(3)
    n_users = c1.number_input("Est. Daily Users", value=int(data.get("usage_users", 100)))
    n_reqs = c2.number_input("Requests/User/Day", value=int(data.get("usage_requests", 5)))
    ownership = c3.selectbox("Cost Ownership", ["Funded by AWS", "Funded by Partner", "Funded by Customer", "Shared"])

# --- TAB 6: REVIEW & EXPORT ---
with tabs[5]:
    st.header("Final SOW Report (PDF)")
    
    def create_pdf():
        pdf = PDF()
        pdf.add_page()
        
        # 1. Project Overview
        pdf.chapter_title("2. PROJECT OVERVIEW")
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, "2.1 OBJECTIVE", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 5, clean_text(final_objective))
        pdf.ln(5)
        
        # 2.2 Stakeholders Table
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, "2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S)", 0, 1)
        
        pdf.set_font('Arial', 'B', 10)
        # Table Header
        col_w = [40, 50, 50, 50]
        pdf.cell(col_w[0], 7, "Role", 1)
        pdf.cell(col_w[1], 7, "Name", 1)
        pdf.cell(col_w[2], 7, "Title", 1)
        pdf.cell(col_w[3], 7, "Email", 1, 1)
        
        pdf.set_font('Arial', '', 9)
        for s in updated_stakeholders:
            pdf.cell(col_w[0], 7, clean_text(s.get('role', '')[:20]), 1)
            pdf.cell(col_w[1], 7, clean_text(s.get('name', '')[:25]), 1)
            pdf.cell(col_w[2], 7, clean_text(s.get('title', '')[:25]), 1)
            pdf.cell(col_w[3], 7, clean_text(s.get('email', '')[:25]), 1, 1)
        pdf.ln(5)
        
        # 2.3 Dependencies
        pdf.chapter_title("2.3 ASSUMPTIONS & DEPENDENCIES")
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, "Dependencies:", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 5, clean_text(deps_text))
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, "Assumptions:", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 5, clean_text(assump_text))
        pdf.ln(5)
        
        # 2.4 Success Criteria
        pdf.chapter_title("2.4 PoC SUCCESS CRITERIA")
        pdf.multi_cell(0, 5, clean_text(final_sc_text))
        pdf.ln(5)
        
        # 3. Scope of Work
        pdf.chapter_title("3. SCOPE OF WORK - TECHNICAL PROJECT PLAN")
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, "Phase 1: Infrastructure Setup", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 5, clean_text(p1))
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, "Phase 2: Core Workflows", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 5, clean_text(p2))
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, "Phase 3: Backend Components", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 5, clean_text(p3))
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, "Phase 4: Feedback & Testing", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 5, clean_text(p4))
        pdf.ln(5)
        
        # Timeline Table
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, "Development Timelines", 0, 1)
        t_col_w = [40, 110, 40]
        pdf.cell(t_col_w[0], 7, "Phase", 1)
        pdf.cell(t_col_w[1], 7, "Task", 1)
        pdf.cell(t_col_w[2], 7, "Weeks", 1, 1)
        
        pdf.set_font('Arial', '', 9)
        for t in final_timeline:
            pdf.cell(t_col_w[0], 7, clean_text(t['Phase'][:20]), 1)
            pdf.cell(t_col_w[1], 7, clean_text(t['Task'][:60]), 1)
            pdf.cell(t_col_w[2], 7, clean_text(t['Weeks'][:20]), 1, 1)
        pdf.ln(5)
        
        # 4. Architecture
        pdf.chapter_title("4. SOLUTION ARCHITECTURE")
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Compute: {clean_text(str(compute))}", 0, 1)
        pdf.cell(0, 6, f"Storage: {clean_text(', '.join(storage))}", 0, 1)
        pdf.cell(0, 6, f"ML Services: {clean_text(', '.join(ml_services))}", 0, 1)
        pdf.cell(0, 6, f"UI Layer: {clean_text(str(ui_layer))}", 0, 1)
        pdf.ln(5)
        
        # 5. Resources
        pdf.chapter_title("5. RESOURCES & COST ESTIMATES")
        pdf.cell(0, 6, f"Cost Ownership: {clean_text(ownership)}", 0, 1)
        pdf.cell(0, 6, f"Usage Estimates: {n_users} users, {n_reqs} requests/day", 0, 1)
        
        return pdf.output(dest='S').encode('latin-1')

    # Preview Text
    st.markdown("### Preview (Text Version)")
    st.text_area("Objective", value=final_objective, disabled=True)
    st.write("---")
    st.write("Click below to download the official PDF.")

    if st.session_state.autofill_done:
        try:
            pdf_bytes = create_pdf()
            st.download_button(
                label="📥 Download SOW (PDF)",
                data=pdf_bytes,
                file_name=f"{customer_name.replace(' ', '_')}_SOW.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}. Make sure 'fpdf' is installed.")
            st.info("pip install fpdf")
    else:
        st.warning("Please generate the SOW in Tab 1 first.")
