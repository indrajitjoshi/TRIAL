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
    if st.button("✨ GENERATE COMPLETE SOW DRAFT (LLM AUTOFILL)", use_container_width=True, type="primary"):
        sow_schema = {
            "type": "OBJECT",
            "properties": {
                "objective": {"type": "STRING"},
                "outcomes": {"type": "ARRAY", "items": {"type": "STRING"}},
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
                },
                "dependencies": {"type": "STRING"},
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
                },
                "success_criteria": {"type": "STRING"},
                "technical_scope": {"type": "STRING"},
                "architecture": {
                    "type": "OBJECT",
                    "properties": {
                        "compute": {"type": "STRING"},
                        "storage": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "ml_services": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "ui": {"type": "STRING"}
                    }
                },
                "timeline": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "phase": {"type": "STRING"},
                            "weeks": {"type": "STRING"}
                        }
                    }
                },
                "usage_users": {"type": "NUMBER"},
                "usage_requests": {"type": "NUMBER"}
            }
        }
        
        prompt = f"""Generate a complete, professional SOW dataset for building a '{sol_type}' solution for a '{industry}' client named '{customer_name}'. 
        The engagement type is a '{engagement}'.
        - Objective: Formal and business-aligned.
        - Outcomes: 4-5 strategic goals.
        - Stakeholders: Generate 4 realistic placeholder stakeholders (Partner Exec, Customer Exec, AWS Exec, Escalation).
        - Dependencies: Formal bulleted list of 6-8 critical data/env needs.
        - Data: Realistic metrics for relevant data types (e.g. text for LLMs, images for CV).
        - Success Criteria: Specific metrics like '90% accuracy', '<2s latency'.
        - Technical Scope: Detailed breakdown of tasks (Ingestion, Inference, App dev).
        - Architecture: Choose best AWS services.
        - Timeline: Logical week mapping for {engagement}."""
        
        with st.spinner("GenAI is architecting your SOW..."):
            result = call_gemini_json(prompt, sow_schema)
            if result:
                st.session_state.autofill_data = result
                st.session_state.autofill_done = True
                st.toast("Success! Entire SOW Draft Generated.")
            else:
                st.error("Failed to generate content. The API might be under heavy load.")

# --- TAB 2: PROJECT OVERVIEW ---
with tabs[1]:
    data = st.session_state.autofill_data
    st.header("2. Project Overview")
    
    col_obj, col_refined = st.columns([1, 1])
    with col_obj:
        raw_obj = st.text_area("2.1 Business Objective (Input)", placeholder="Refine manual effort, improve ROI...")
        if st.button("Refine Single Objective"):
            with st.spinner("Refining..."):
                st.session_state.autofill_data["objective"] = call_gemini_text(f"Refine this into a professional SOW objective: {raw_obj}")
    
    with col_refined:
        final_objective = st.text_area("Objective (Editable)", value=data.get("objective", ""), height=200)

    st.divider()
    outcome_options = ["Reduce manual effort", "Improve accuracy / quality", "Faster turnaround time", "Cost reduction", "Revenue uplift", "Compliance improvement", "Better customer experience", "Scalability validation"]
    outcomes = st.multiselect("2.2 Key Outcomes Expected", outcome_options, default=data.get("outcomes", outcome_options[:2]))

    st.subheader("2.3 Stakeholders Information")
    stakeholders = data.get("stakeholders", [
        {"role": "Partner Executive Sponsor", "name": "", "title": "", "email": ""},
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
    st.header("3. Assumptions & Dependencies")
    deps_text = st.text_area("3.1 Customer Dependencies", value=data.get("dependencies", ""), height=200)

    st.divider()
    st.subheader("3.2 Data Characteristics")
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
    st.header("4. PoC Success Criteria")
    success_text = st.text_area("4.1 Success Criteria", value=data.get("success_criteria", ""), height=150)

    st.divider()
    st.header("5. Scope of Work (Technical)")
    sow_text = st.text_area("Detailed Project Tasks", value=data.get("technical_scope", ""), height=300)

    st.divider()
    st.header("6. Architecture & AWS Services")
    arch = data.get("architecture", {})
    col_arch1, col_arch2 = st.columns(2)
    with col_arch1:
        comp_val = arch.get("compute", "AWS Lambda + Step Functions")
        compute = st.selectbox("Compute", ["AWS Lambda + Step Functions", "ECS / EKS", "Hybrid"], index=0 if "Lambda" in comp_val else 1)
        storage = st.multiselect("Storage & Search", ["Amazon S3", "DynamoDB", "OpenSearch", "RDS", "Vector DB (Aurora PG)"], default=arch.get("storage", ["Amazon S3"]))
    with col_arch2:
        ml_services = st.multiselect("GenAI / ML Services", AWS_ML_SERVICES, default=arch.get("ml_services", ["Amazon Bedrock"]))
        ui_val = arch.get("ui", "Streamlit on S3")
        ui_layer = st.selectbox("UI Layer", ["Streamlit on S3", "CloudFront + Static UI", "Internal demo only", "No UI (API only)"], index=0 if "Streamlit" in ui_val else 1)

# --- TAB 5: TIMELINE & COSTS ---
with tabs[4]:
    st.header("8. Timeline & Phasing")
    raw_timeline = data.get("timeline", [{"phase": "Setup", "weeks": "Week 1"}])
    
    final_timeline = []
    for i, step in enumerate(raw_timeline):
        c1, c2 = st.columns([3, 1])
        p_name = c1.text_input("Phase", value=step.get("phase", ""), key=f"p_{i}")
        p_weeks = c2.text_input("Weeks", value=step.get("weeks", ""), key=f"w_{i}")
        final_timeline.append({"phase": p_name, "weeks": p_weeks})

    st.divider()
    st.header("9. Costing & Usage")
    c1, c2, c3 = st.columns(3)
    n_users = c1.number_input("Est. Daily Users", value=int(data.get("usage_users", 100)))
    n_reqs = c2.number_input("Requests/User/Day", value=int(data.get("usage_requests", 5)))
    ownership = c3.selectbox("Cost Ownership", ["Funded by AWS", "Funded by Partner", "Funded by Customer", "Shared"])

# --- TAB 6: REVIEW & EXPORT ---
with tabs[5]:
    st.header("Final SOW Review")
    
    doc_markdown = f"""# {sol_type} {engagement} SOW
**Customer:** {customer_name} | **Industry:** {industry}
**Date:** {datetime.now().strftime('%d %B %Y')}

---

## 2. PROJECT OVERVIEW
### 2.1 OBJECTIVE
{data.get('objective', 'TBD')}

### 2.2 KEY OUTCOMES
{', '.join(outcomes)}

### 2.3 STAKEHOLDERS
| Role | Name | Title | Email |
|---|---|---|---|
"""
    for s in final_stakeholders:
        doc_markdown += f"| {s['Role']} | {s['Name']} | {s['Title']} | {s['Email']} |\n"

    doc_markdown += f"""
---

## 3. ASSUMPTIONS & DEPENDENCIES
{deps_text}

### 3.2 DATA CHARACTERISTICS
"""
    for d in processed_data:
        doc_markdown += f"- **{d['type']}**: {d['size']} ({d['format']}), ~{d['volume']} volume\n"

    doc_markdown += f"""
---

## 4. PoC SUCCESS CRITERIA
{success_text}

---

## 5. SCOPE OF WORK - TECHNICAL
{sow_text}

---

## 6. ARCHITECTURE
- **Compute:** {compute}
- **Storage:** {', '.join(storage)}
- **ML Services:** {', '.join(ml_services)}
- **UI:** {ui_layer}

---

## 8. TIMELINE
"""
    for t in final_timeline:
        doc_markdown += f"- **{t['phase']}**: {t['weeks']}\n"

    st.markdown(doc_markdown)
    
    st.download_button(
        label="📥 Download SOW Document (.md)",
        data=doc_markdown,
        file_name=f"{customer_name.replace(' ', '_')}_{sol_type.replace(' ', '_')}_SOW.md",
        mime="text/markdown"
    )

st.sidebar.markdown(f"**Current Solution:**\n{sol_type}")
st.sidebar.markdown(f"**Target Industry:**\n{industry}")
st.sidebar.info("Use Tab 1 'Autofill' for a full baseline, then edit individual sections as needed.")
