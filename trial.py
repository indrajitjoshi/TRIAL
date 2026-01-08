import streamlit as st
import json
import time
import requests
import pandas as pd
from datetime import datetime

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
SUCCESS_DIMENSIONS = ["Accuracy", "Latency", "Usability", "Explainability", "Coverage", "Cost efficiency", "Integration readiness"]
AWS_ML_SERVICES = ["Amazon Bedrock", "Amazon SageMaker", "Amazon Rekognition", "Amazon Textract", "Amazon Comprehend", "Amazon Transcribe", "Amazon Translate"]

# --- API UTILITIES ---
def call_gemini_json(prompt, schema):
    """Calls Gemini with a structured JSON output requirement."""
    api_key = "" # Provided by environment
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
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
    "6. Review & Export"
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
        
        # Progress status bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. Objective
            status_text.text("1/8 Generating Concise Project Objective...")
            obj_schema = {
                "type": "OBJECT",
                "properties": {
                    "objective": {"type": "STRING"}
                }
            }
            res = call_gemini_json(f"Generate a concise, 1-2 sentence formal business objective for a '{sol_type}' solution for '{customer_name}' in the '{industry}' industry. Engagement: {engagement}.", obj_schema)
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
            # Note: Partner sponsor is hardcoded later per user request
            res = call_gemini_json(f"Generate 3 placeholder stakeholders for a {sol_type} project at {customer_name}: Customer Executive Sponsor, AWS Executive Sponsor, and Escalation Contact.", stk_schema)
            
            # HARDCODED PARTNER SPONSOR PER REQUEST
            fixed_partner = {
                "role": "Partner Executive Sponsor",
                "name": "Ram Joshi",
                "title": "Head of Analytics & ML",
                "email": "Gaurav.kankaria@oneture.com"
            }
            if res and "stakeholders" in res:
                res["stakeholders"].insert(0, fixed_partner)
            else:
                generated_sow["stakeholders"] = [fixed_partner]
            
            if res: generated_sow.update(res)
            progress_bar.progress(25)

            # 3. Dependencies & Assumptions
            status_text.text("3/8 Generating Generalized Assumptions & Dependencies...")
            deps_schema = {
                 "type": "OBJECT",
                 "properties": {
                     "dependencies": {"type": "STRING"},
                     "assumptions": {"type": "STRING"}
                 }
            }
            res = call_gemini_json(f"Generate list of general Assumptions and Dependencies for a {sol_type} project. Dependencies should cover data access and environment. Assumptions should cover POC scope.", deps_schema)
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
            res = call_gemini_json(f"Identify 2-3 realistic data types and volumes required for a '{sol_type}' implementation in the '{industry}' sector.", data_schema)
            if res: generated_sow.update(res)
            progress_bar.progress(50)

            # 5. Success Criteria
            status_text.text("5/8 Defining Detailed Success Criteria...")
            success = call_gemini_text(f"Provide a detailed list of PoC Success Criteria for a '{sol_type}'. Format as bullet points with specific metrics like accuracy, latency, and business outcomes.")
            generated_sow["success_criteria"] = success
            progress_bar.progress(62)

            # 6. Technical Scope
            status_text.text("6/8 Architecting Technical Scope...")
            scope = call_gemini_text(f"Write a comprehensive 'SCOPE OF WORK - TECHNICAL PROJECT PLAN' for a '{sol_type}' project. Structure it into phases like 'Infrastructure Setup', 'Core Workflows', 'Backend Components', and 'Testing'.")
            generated_sow["technical_scope"] = scope
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
            res = call_gemini_json(f"Design an AWS architecture for '{sol_type}'. Suggest compute, storage, Bedrock/SageMaker services, and UI layer.", arch_schema)
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
            res = call_gemini_json(f"Create a high-level timeline for a '{engagement}' of a '{sol_type}'. Include Phase, Task Description, and Week duration (e.g. Wk1-Wk2).", time_schema)
            if res: generated_sow.update(res)
            progress_bar.progress(100)
            
            # Finalize
            st.session_state.autofill_data = generated_sow
            st.session_state.autofill_done = True
            status_text.success("Complete SOW Draft Generated Successfully!")
            st.toast("Check Tab 6 for the Final Report.")

        except Exception as e:
            st.error(f"An error occurred during part-by-part generation: {str(e)}")
            status_text.text("Generation paused due to an error.")

# --- TAB 2: PROJECT OVERVIEW ---
with tabs[1]:
    data = st.session_state.autofill_data
    st.header("2. PROJECT OVERVIEW")
    
    col_obj, col_refined = st.columns([1, 1])
    with col_obj:
        raw_obj = st.text_area("2.1 Business Objective (Input)", placeholder="Refine manual effort, improve ROI...")
        if st.button("Refine Single Objective"):
            with st.spinner("Refining..."):
                st.session_state.autofill_data["objective"] = call_gemini_text(f"Refine this into a concise 1-2 sentence formal business objective: {raw_obj}")
    
    with col_refined:
        final_objective = st.text_area("2.1 OBJECTIVE (Editable)", value=data.get("objective", ""), height=100)

    st.subheader("2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM")
    stakeholders = data.get("stakeholders", [
        {"role": "Partner Executive Sponsor", "name": "Ram Joshi", "title": "Head of Analytics & ML", "email": "Gaurav.kankaria@oneture.com"},
        {"role": "Customer Executive Sponsor", "name": "", "title": "", "email": ""},
        {"role": "AWS Executive Sponsor", "name": "", "title": "", "email": ""},
        {"role": "Escalation Contact", "name": "", "title": "", "email": ""}
    ])
    
    final_stakeholders = []
    for i, s in enumerate(stakeholders):
        st.markdown(f"**{s.get('role', f'Stakeholder {i}')}**")
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Name", key=f"name_{i}", value=s.get("name", ""))
        title = c2.text_input("Title", key=f"title_{i}", value=s.get("title", ""))
        email = c3.text_input("Email", key=f"email_{i}", value=s.get("email", ""))
        final_stakeholders.append({"Role": s.get('role'), "Name": name, "Title": title, "Email": email})

# --- TAB 3: DATA & DEPENDENCIES ---
with tabs[2]:
    st.header("2.3 ASSUMPTIONS & DEPENDENCIES")
    deps_text = st.text_area("Dependencies & Assumptions", value=f"Dependencies:\n{data.get('dependencies', '')}\n\nAssumptions:\n{data.get('assumptions', '')}", height=300)

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
    success_text = st.text_area("Success Criteria", value=data.get("success_criteria", ""), height=200)

    st.divider()
    st.header("3 SCOPE OF WORK - TECHNICAL PROJECT PLAN")
    sow_text = st.text_area("Detailed Scope", value=data.get("technical_scope", ""), height=400)

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
    st.header("Final SOW Report")
    
    doc_markdown = f"""# {sol_type} POC SOW
**Date:** {datetime.now().strftime('%d %B %Y')}

---

# 2 PROJECT OVERVIEW

## 2.1 OBJECTIVE
{data.get('objective', 'TBD')}

## 2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM
| Name | Title | Email/Contact Info |
|---|---|---|
"""
    for s in final_stakeholders:
        doc_markdown += f"| {s['Name']} | {s['Title']} | {s['Email']} |\n"

    doc_markdown += f"""
## 2.3 ASSUMPTIONS & DEPENDENCIES
{deps_text}

## 2.4 PoC Success Criteria
{success_text}

---

# 3 SCOPE OF WORK - TECHNICAL PROJECT PLAN
{sow_text}

### Development Timelines
| Phase | Task | Timeline |
|---|---|---|
"""
    for t in final_timeline:
        doc_markdown += f"| {t['Phase']} | {t['Task']} | {t['Weeks']} |\n"

    doc_markdown += f"""
---

# 4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM
- **Compute:** {compute}
- **Storage:** {', '.join(storage)}
- **ML Services:** {', '.join(ml_services)}
- **UI:** {ui_layer}

*(Architecture diagram to be inserted here)*

---

# 5 RESOURCES & COST ESTIMATES
- **Cost Ownership:** {ownership}
- **Usage Estimates:** {n_users} users, {n_reqs} requests/day.
- **Infrastructure Costs:** (Calculated via AWS Pricing Calculator)
"""

    st.markdown(doc_markdown)
    
    st.download_button(
        label="📥 Download SOW Document (.md)",
        data=doc_markdown,
        file_name=f"{customer_name.replace(' ', '_')}_{sol_type.replace(' ', '_')}_SOW.md",
        mime="text/markdown"
    )

st.sidebar.markdown(f"**Current Solution:**\n{sol_type}")
st.sidebar.markdown(f"**Target Industry:**\n{industry}")
st.sidebar.info("Generation updated to match Nykaa SOW format.")
