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
def call_gemini(prompt, system_instruction="You are a professional solution architect at an AWS Partner."):
    api_key = "" # Execution environment provides this
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
    return "Error generating content. Please try again."

# --- UI STATE ---
if "sow_data" not in st.session_state:
    st.session_state.sow_data = {}

# --- PAGE SETUP ---
st.set_page_config(page_title=ST_PAGE_TITLE, page_icon=ST_PAGE_ICON, layout="wide")

st.title(f"{ST_PAGE_ICON} {ST_PAGE_TITLE}")
st.markdown("Generate high-quality, professional SOW documents using GenAI and AWS best practices.")

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
            sol_type = st.text_input("Please specify solution type")
        
        engagement = st.selectbox("1.2 Engagement Type", ENGAGEMENT_TYPES)
        
    with col2:
        industry = st.selectbox("1.3 Industry / Domain", INDUSTRIES)
        if industry == "Other":
            industry = st.text_input("Please specify industry")
        
        customer_name = st.text_input("Customer Name", "Acme Corp")

# --- TAB 2: PROJECT OVERVIEW ---
with tabs[1]:
    st.header("2. Project Overview")
    
    col_obj, col_refined = st.columns([1, 1])
    with col_obj:
        raw_objective = st.text_area("2.1 Business Objective (Input)", placeholder="e.g. Reduce manual effort in audit, improve accuracy, enable faster decisions...")
        if st.button("Refine with LLM"):
            with st.spinner("Refining..."):
                prompt = f"Rewrite this business objective into a formal project objective for a {sol_type} project in the {industry} industry. Input: {raw_objective}"
                st.session_state.refined_objective = call_gemini(prompt)
    
    with col_refined:
        final_objective = st.text_area("Refined Objective (Editable)", value=st.session_state.get("refined_objective", ""))

    st.divider()
    outcomes = st.multiselect("2.2 Key Outcomes Expected", ["Reduce manual effort", "Improve accuracy / quality", "Faster turnaround time", "Cost reduction", "Revenue uplift", "Compliance improvement", "Better customer experience", "Scalability validation"])

    st.subheader("2.3 Stakeholders Information")
    stakeholder_data = []
    for role in ["Partner Executive Sponsor", "Customer Executive Sponsor", "AWS Executive Sponsor", "Escalation Contact"]:
        st.markdown(f"**{role}**")
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Name", key=f"name_{role}")
        title = c2.text_input("Title", key=f"title_{role}")
        email = c3.text_input("Email", key=f"email_{role}")
        stakeholder_data.append({"Role": role, "Name": name, "Title": title, "Email": email})

# --- TAB 3: DATA & DEPENDENCIES ---
with tabs[2]:
    st.header("3. Assumptions & Dependencies")
    
    deps = st.multiselect("3.1 Customer Dependencies", ["Sample data availability", "Historical data availability", "Design / business guidelines finalized", "API access provided", "User access to AWS account", "SME availability for validation", "Network / VPC access", "Security approvals"])
    
    if st.button("Expand Dependencies"):
        with st.spinner("Expanding..."):
            prompt = f"Expand the following list of project dependencies into formal statements for a SOW: {', '.join(deps)}. Ensure they are specific to a {sol_type} implementation."
            st.session_state.expanded_deps = call_gemini(prompt)
    
    expanded_deps_text = st.text_area("Formal Dependency Statements", value=st.session_state.get("expanded_deps", ""), height=200)

    st.divider()
    st.subheader("3.2 Data Characteristics")
    data_types = st.multiselect("Data Types Involved", ["Images", "Text", "PDFs / Documents", "Audio", "Video", "Structured tables", "APIs / Streams"])
    
    data_details = {}
    for dt in data_types:
        st.markdown(f"**Details for {dt}**")
        c1, c2, c3 = st.columns(3)
        size = c1.text_input("Avg Size / Payload", key=f"size_{dt}")
        fmt = c2.text_input("Formats (e.g. PNG, JSON)", key=f"fmt_{dt}")
        vol = c3.text_input("Approx Daily Volume", key=f"vol_{dt}")
        data_details[dt] = {"size": size, "format": fmt, "volume": vol}

# --- TAB 4: SCOPE & ARCHITECTURE ---
with tabs[3]:
    st.header("4. PoC Success Criteria")
    dimensions = st.multiselect("Success Dimensions", SUCCESS_DIMENSIONS, default=["Accuracy", "Usability"])
    
    if st.button("Generate Success Criteria"):
        with st.spinner("Generating..."):
            prompt = f"Generate measurable success criteria for a {sol_type} POC in the {industry} sector based on these dimensions: {', '.join(dimensions)}. Provide specific metrics (e.g., >=85% accuracy)."
            st.session_state.success_crit = call_gemini(prompt)
    
    final_success_crit = st.text_area("Measurable Success Criteria", value=st.session_state.get("success_crit", ""), height=150)

    st.divider()
    st.header("5. Scope of Work (Technical)")
    flows = st.multiselect("Functional Flows to Include", ["Upload / Ingestion", "Processing / Inference", "Metadata extraction", "Scoring / Recommendation", "Feedback loop", "UI display"], default=["Upload / Ingestion", "Processing / Inference", "UI display"])
    
    if st.button("Generate SOW Text"):
        with st.spinner("Generating..."):
            prompt = f"Convert the following functional steps into a formal Technical Scope of Work section for a {sol_type}: {', '.join(flows)}."
            st.session_state.sow_text = call_gemini(prompt)
    
    final_sow_text = st.text_area("Detailed Scope of Work", value=st.session_state.get("sow_text", ""), height=250)

    st.divider()
    st.header("6. Architecture & Services")
    col_arch1, col_arch2 = st.columns(2)
    with col_arch1:
        compute = st.radio("Compute & Orchestration", ["AWS Lambda + Step Functions", "ECS / EKS", "Hybrid"], index=0)
        storage = st.multiselect("Storage & Search", ["Amazon S3", "DynamoDB", "OpenSearch", "RDS", "Vector DB (Aurora PG)"], default=["Amazon S3", "OpenSearch"])
    with col_arch2:
        ml_services = st.multiselect("GenAI / ML Services", AWS_ML_SERVICES, default=["Amazon Bedrock"])
        ui_layer = st.selectbox("UI Layer", ["Streamlit on S3", "CloudFront + Static UI", "Internal demo only", "No UI (API only)"])

# --- TAB 5: TIMELINE & COSTS ---
with tabs[4]:
    st.header("8. Timeline & Phasing")
    duration = st.selectbox("PoC Duration", ["2 weeks", "4 weeks", "6 weeks", "Custom"])
    
    phases = ["Infra setup", "Core workflows", "Testing & validation", "Demo & feedback"]
    phase_mapping = {}
    for p in phases:
        phase_mapping[p] = st.text_input(f"Timeline for {p}", "Week 1-2")

    st.divider()
    st.header("9. Costing & Usage")
    c1, c2, c3 = st.columns(3)
    num_users = c1.number_input("Est. Daily Users", 1, 10000, 100)
    req_per_day = c2.number_input("Requests/User/Day", 1, 1000, 5)
    cost_ownership = c3.selectbox("Cost Ownership", ["Funded by AWS", "Funded by Partner", "Funded by Customer", "Shared"])

# --- TAB 6: REVIEW & EXPORT ---
with tabs[5]:
    st.header("Review & Export")
    
    # Assembly logic
    doc_content = f"""# {sol_type} {engagement} Scope of Work
**Customer:** {customer_name}
**Industry:** {industry}
**Date:** {datetime.now().strftime('%d %B %Y')}

---

## 2. PROJECT OVERVIEW

### 2.1 OBJECTIVE
{final_objective}

### 2.2 PROJECT STAKEHOLDERS
| Role | Name | Title | Email |
|------|------|-------|-------|
"""
    for s in stakeholder_data:
        doc_content += f"| {s['Role']} | {s['Name']} | {s['Title']} | {s['Email']} |\n"

    doc_content += f"""
### 2.3 KEY OUTCOMES
{", ".join(outcomes)}

---

## 3. ASSUMPTIONS & DEPENDENCIES

### 3.1 CUSTOMER DEPENDENCIES
{expanded_deps_text}

### 3.2 DATA CHARACTERISTICS
"""
    for k, v in data_details.items():
        doc_content += f"- **{k}**: {v['size']} ({v['format']}), ~{v['volume']} volume.\n"

---

doc_content += f"""
## 4. PoC SUCCESS CRITERIA
{final_success_crit}

---

## 5. SCOPE OF WORK - TECHNICAL PROJECT PLAN
{final_sow_text}

---

## 6. ARCHITECTURE & AWS SERVICES
- **Compute:** {compute}
- **Storage:** {", ".join(storage)}
- **ML Services:** {", ".join(ml_services)}
- **UI:** {ui_layer}

---

## 8. TIMELINE & PHASING
**Total Duration:** {duration}
"""
    for p, t in phase_mapping.items():
        doc_content += f"- {p}: {t}\n"

    st.markdown(doc_content)
    
    st.download_button(
        label="Download SOW (Markdown)",
        data=doc_content,
        file_name=f"{customer_name.replace(' ', '_')}_{sol_type.replace(' ', '_')}_SOW.md",
        mime="text/markdown"
    )

st.sidebar.info("Fill out the tabs sequentially. Use the 'Refine/Expand' buttons to leverage GenAI for professional phrasing.")
