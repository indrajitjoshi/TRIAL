import streamlit as st
import io
from datetime import datetime
from docx import Document
from transformers import pipeline

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="GenAI SOW Agent",
    layout="wide",
    page_icon="📝"
)

# -------------------------------------------------
# LOAD LLM (STREAMLIT CLOUD SAFE)
# -------------------------------------------------
@st.cache_resource
def load_llm():
    return pipeline(
        task="text2text-generation",
        model="google/flan-t5-base",
        device="cpu"
    )

pipe = load_llm()

# -------------------------------------------------
# INITIAL DATA
# -------------------------------------------------
def empty_row():
    return {"Name": "", "Title": "", "Email": ""}

if "sow_data" not in st.session_state:
    st.session_state.sow_data = {
        "metadata": {
            "customer_name": "Customer Name",
            "industry": "Retail",
            "solution_type": "Multi Agent Store Advisor",
            "other_solution": "",
            "raw_objective": ""
        },
        "tables": {
            "partner": [empty_row()],
            "customer": [empty_row()],
            "cloud": [empty_row()],
            "escalation": [empty_row()]
        },
        "sections": {
            "objective": "",
            "dependencies": "",
            "assumptions": "",
            "success_demo": "",
            "success_results": "",
            "scope": "",
            "architecture": "",
            "commercials": ""
        }
    }

# -------------------------------------------------
# LLM HELPER
# -------------------------------------------------
def call_llm(prompt: str) -> str:
    result = pipe(prompt, max_new_tokens=300, temperature=0.2)
    return result[0]["generated_text"].strip()

# -------------------------------------------------
# GENERATE INITIAL CONTENT
# -------------------------------------------------
def generate_sow():
    meta = st.session_state.sow_data["metadata"]
    sec = st.session_state.sow_data["sections"]

    solution = meta["other_solution"] if meta["solution_type"] == "Other (Please specify)" else meta["solution_type"]

    sec["objective"] = call_llm(
        f"Write a formal 2–3 sentence SOW objective for a {solution} POC in the {meta['industry']} industry."
    )
    sec["dependencies"] = call_llm(f"List 2 customer dependencies for a {solution} POC.")
    sec["assumptions"] = call_llm(f"List 2 delivery assumptions for a {solution} POC.")
    sec["success_demo"] = call_llm(f"List 3 demonstration capabilities for a {solution} POC.")
    sec["success_results"] = call_llm(f"List 2 expected outcomes for a {solution} POC.")
    sec["scope"] = call_llm(f"Describe a 4-phase technical delivery plan with timelines.")
    sec["architecture"] = call_llm(f"Describe high-level GenAI solution architecture.")
    sec["commercials"] = call_llm(f"Write a short POC commercial note.")

# -------------------------------------------------
# TABLE EDITOR
# -------------------------------------------------
def editable_table(title, key):
    st.subheader(title)
    rows = st.session_state.sow_data["tables"][key]

    for i, row in enumerate(rows):
        cols = st.columns(3)
        row["Name"] = cols[0].text_input("Name", row["Name"], key=f"{key}_name_{i}")
        row["Title"] = cols[1].text_input("Title", row["Title"], key=f"{key}_title_{i}")
        row["Email"] = cols[2].text_input("Email / Contact Info", row["Email"], key=f"{key}_email_{i}")

    if st.button(f"➕ Add row to {title}", key=f"add_{key}"):
        rows.append(empty_row())
        st.rerun()

# -------------------------------------------------
# DOCX EXPORT
# -------------------------------------------------
def add_docx_table(doc, title, rows):
    doc.add_heading(title, level=2)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"

    hdr = table.rows[0].cells
    hdr[0].text = "Name"
    hdr[1].text = "Title"
    hdr[2].text = "Email / Contact Info"

    for r in rows:
        if r["Name"] or r["Title"] or r["Email"]:
            row = table.add_row().cells
            row[0].text = r["Name"]
            row[1].text = r["Title"]
            row[2].text = r["Email"]

def create_docx(data):
    doc = Document()
    doc.add_heading("Scope of Work (SOW)", 0)

    meta = data["metadata"]
    doc.add_paragraph(f"Customer: {meta['customer_name']}")
    doc.add_paragraph(f"Solution: {meta['solution_type']}")
    doc.add_paragraph(f"Date: {datetime.now().strftime('%d %B %Y')}")

    sec = data["sections"]

    doc.add_heading("2.1 OBJECTIVE", 1)
    doc.add_paragraph(sec["objective"])

    doc.add_heading("2.2 PROJECT SPONSORS / STAKEHOLDERS", 1)
    add_docx_table(doc, "Partner Executive Sponsor", data["tables"]["partner"])
    add_docx_table(doc, "Customer Executive Sponsor", data["tables"]["customer"])
    add_docx_table(doc, "Cloud Executive Sponsor", data["tables"]["cloud"])
    add_docx_table(doc, "Project Escalation Contacts", data["tables"]["escalation"])

    doc.add_heading("2.3 ASSUMPTIONS & DEPENDENCIES", 1)
    doc.add_paragraph("Dependencies:\n" + sec["dependencies"])
    doc.add_paragraph("Assumptions:\n" + sec["assumptions"])

    doc.add_heading("2.4 PROJECT SUCCESS CRITERIA", 1)
    doc.add_paragraph("Demonstrations:\n" + sec["success_demo"])
    doc.add_paragraph("Results:\n" + sec["success_results"])

    doc.add_heading("3 SCOPE OF WORK - TECHNICAL PROJECT PLAN", 1)
    doc.add_paragraph(sec["scope"])

    doc.add_heading("4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM", 1)
    doc.add_paragraph(sec["architecture"])

    doc.add_heading("6 RESOURCES & COST ESTIMATES", 1)
    doc.add_paragraph(sec["commercials"])

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# -------------------------------------------------
# UI
# -------------------------------------------------
def main():
    meta = st.session_state.sow_data["metadata"]

    st.sidebar.title("🛠️ SOW Inputs")

    meta["customer_name"] = st.sidebar.text_input("Customer Name", meta["customer_name"])
    meta["industry"] = st.sidebar.selectbox(
        "Industry",
        ["Retail", "Financial Services", "Healthcare", "Manufacturing", "Legal"]
    )

    solution_options = [
        "Multi Agent Store Advisor",
        "Intelligent Search",
        "Recommendation",
        "AI Agents Demand Forecasting",
        "Banner Audit using LLM",
        "Image Enhancement",
        "Virtual Try-On",
        "Agentic AI L1 Support",
        "Product Listing Standardization",
        "AI Agents Based Pricing Module",
        "Cost, Margin Visibility & Insights using LLM",
        "AI Trend Simulator",
        "Virtual Data Analyst (Text to SQL)",
        "Multilingual Call Analysis",
        "Customer Review Analysis",
        "Sales Co-Pilot",
        "Research Co-Pilot",
        "Product Copy Generator",
        "Multi-agent e-KYC & Onboarding",
        "Document / Report Audit",
        "RBI Circular Scraping & Insights Bot",
        "Visual Inspection",
        "AIoT based CCTV Surveillance",
        "Multilingual Voice Bot",
        "SOP Creation",
        "Other (Please specify)"
    ]

    meta["solution_type"] = st.sidebar.selectbox("Solution Type", solution_options)

    if meta["solution_type"] == "Other (Please specify)":
        meta["other_solution"] = st.sidebar.text_input("Specify Solution")

    meta["raw_objective"] = st.sidebar.text_area("Business Objective")

    if st.sidebar.button("🪄 Generate Initial Draft"):
        generate_sow()
        st.rerun()

    st.title("📄 Editable SOW")

    st.text_area("2.1 OBJECTIVE", st.session_state.sow_data["sections"]["objective"], height=150, key="obj")

    editable_table("Partner Executive Sponsor", "partner")
    editable_table("Customer Executive Sponsor", "customer")
    editable_table("Cloud Executive Sponsor", "cloud")
    editable_table("Project Escalation Contacts", "escalation")

    for label, key in [
        ("Dependencies", "dependencies"),
        ("Assumptions", "assumptions"),
        ("Demonstrations", "success_demo"),
        ("Results", "success_results"),
        ("Scope of Work", "scope"),
        ("Solution Architecture", "architecture"),
        ("Commercials", "commercials")
    ]:
        st.text_area(label, st.session_state.sow_data["sections"][key], height=150, key=key)

    docx = create_docx(st.session_state.sow_data)
    st.download_button(
        "📥 Download SOW (DOCX)",
        docx,
        file_name="Generated_SOW.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

if __name__ == "__main__":
    main()
