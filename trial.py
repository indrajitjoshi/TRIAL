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
# SESSION STATE
# -------------------------------------------------
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
            "partner_sponsor": [],
            "customer_sponsor": [],
            "cloud_sponsor": [],
            "escalation_contacts": []
        },
        "sections": {
            "objective": "",
            "assumptions": "",
            "dependencies": "",
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
# GENERATION ENGINE
# -------------------------------------------------
def generate_sow():
    meta = st.session_state.sow_data["metadata"]
    sec = st.session_state.sow_data["sections"]
    tbl = st.session_state.sow_data["tables"]

    solution = meta["other_solution"] if meta["solution_type"] == "Other (Please specify)" else meta["solution_type"]

    sec["objective"] = call_llm(
        f"Write a formal 2–3 sentence SOW objective for a {solution} POC in the {meta['industry']} industry."
    )

    def gen_table(role):
        text = call_llm(
            f"Generate 2 stakeholders for {role}. "
            f"Return each row on a new line in this format: Name | Title | Email"
        )
        rows = []
        for line in text.split("\n"):
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3:
                    rows.append(parts)
        return rows

    tbl["partner_sponsor"] = gen_table("Partner Executive Sponsor")
    tbl["customer_sponsor"] = gen_table("Customer Executive Sponsor")
    tbl["cloud_sponsor"] = gen_table("Cloud Executive Sponsor")
    tbl["escalation_contacts"] = gen_table("Project Escalation Contact")

    sec["dependencies"] = call_llm(f"List 2 customer dependencies for a {solution} POC.")
    sec["assumptions"] = call_llm(f"List 2 delivery assumptions for a {solution} POC.")
    sec["success_demo"] = call_llm(f"List 3 demo capabilities for a {solution} POC.")
    sec["success_results"] = call_llm(f"List 2 expected outcomes for a {solution} POC.")
    sec["scope"] = call_llm(f"Describe a 4-phase technical delivery plan with timelines for a {solution} POC.")
    sec["architecture"] = call_llm(f"Describe high-level cloud and GenAI architecture for a {solution} POC.")
    sec["commercials"] = call_llm(f"Write a short POC commercial note (one-time, exploratory investment).")

# -------------------------------------------------
# DOCX EXPORT (FIXED TABLE HANDLING)
# -------------------------------------------------
def add_table(doc, title, rows):
    doc.add_heading(title, level=2)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"

    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Name"
    hdr_cells[1].text = "Title"
    hdr_cells[2].text = "Email / Contact Info"

    for r in rows:
        row_cells = table.add_row().cells
        row_cells[0].text = r[0]
        row_cells[1].text = r[1]
        row_cells[2].text = r[2]

def create_docx(data):
    doc = Document()
    doc.add_heading("Scope of Work (SOW)", 0)

    meta = data["metadata"]
    doc.add_paragraph(f"Customer: {meta['customer_name']}")
    doc.add_paragraph(f"Solution: {meta['solution_type']}")
    doc.add_paragraph(f"Date: {datetime.now().strftime('%d %B %Y')}")

    doc.add_heading("2.1 OBJECTIVE", 1)
    doc.add_paragraph(data["sections"]["objective"])

    doc.add_heading("2.2 PROJECT SPONSORS / STAKEHOLDERS", 1)
    add_table(doc, "Partner Executive Sponsor", data["tables"]["partner_sponsor"])
    add_table(doc, "Customer Executive Sponsor", data["tables"]["customer_sponsor"])
    add_table(doc, "Cloud Executive Sponsor", data["tables"]["cloud_sponsor"])
    add_table(doc, "Project Escalation Contacts", data["tables"]["escalation_contacts"])

    doc.add_heading("2.3 ASSUMPTIONS & DEPENDENCIES", 1)
    doc.add_paragraph("Dependencies:\n" + data["sections"]["dependencies"])
    doc.add_paragraph("Assumptions:\n" + data["sections"]["assumptions"])

    doc.add_heading("2.4 PROJECT SUCCESS CRITERIA", 1)
    doc.add_paragraph("Demonstrations:\n" + data["sections"]["success_demo"])
    doc.add_paragraph("Results:\n" + data["sections"]["success_results"])

    doc.add_heading("3 SCOPE OF WORK - TECHNICAL PROJECT PLAN", 1)
    doc.add_paragraph(data["sections"]["scope"])

    doc.add_heading("4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM", 1)
    doc.add_paragraph(data["sections"]["architecture"])

    doc.add_heading("6 RESOURCES & COST ESTIMATES", 1)
    doc.add_paragraph(data["sections"]["commercials"])

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

    if st.sidebar.button("🪄 Generate SOW"):
        generate_sow()
        st.rerun()

    st.title("📄 Generated SOW")
    docx = create_docx(st.session_state.sow_data)

    st.download_button(
        "📥 Download SOW (DOCX)",
        docx,
        file_name="Generated_SOW.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if __name__ == "__main__":
    main()
