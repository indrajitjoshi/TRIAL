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
# LOAD LLM (BETTER MODEL)
# -------------------------------------------------
@st.cache_resource
def load_llm():
    return pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        device="cpu"
    )

llm = load_llm()

def call_llm(prompt):
    response = llm(
        prompt,
        max_new_tokens=400,
        temperature=0.4,
        do_sample=True
    )[0]["generated_text"]

    # Remove prompt echo
    return response.replace(prompt, "").strip()

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
def empty_row():
    return {"Name": "", "Title": "", "Email": ""}

if "sow_data" not in st.session_state:
    st.session_state.sow_data = {
        "metadata": {
            "customer_name": "",
            "industry": "Retail",
            "solution_type": "Multi Agent Store Advisor",
            "other_solution": "",
            "business_problem": ""
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
        },
        "tables": {
            "partner": [empty_row()],
            "customer": [empty_row()],
            "cloud": [empty_row()],
            "escalation": [empty_row()]
        }
    }

# -------------------------------------------------
# GENERATION ENGINE (FIXED)
# -------------------------------------------------
def generate_sow():
    d = st.session_state.sow_data
    m = d["metadata"]
    s = d["sections"]

    solution = m["other_solution"] if m["solution_type"] == "Other (Please specify)" else m["solution_type"]

    s["objective"] = call_llm(f"""
Write a formal SOW OBJECTIVE section.
Context:
- Industry: {m['industry']}
- Solution: {solution}
- Business Problem: {m['business_problem']}

Rules:
- 2 short paragraphs
- No definitions
- Consulting tone
""")

    s["dependencies"] = call_llm(f"""
List CUSTOMER DEPENDENCIES for a {solution} POC.
Rules:
- Minimum 5 bullet points
- Technical + business mix
""")

    s["assumptions"] = call_llm(f"""
List DELIVERY ASSUMPTIONS for a {solution} POC.
Rules:
- Minimum 5 bullet points
- Enterprise assumptions only
""")

    s["success_demo"] = call_llm(f"""
Define DEMONSTRATION SUCCESS CRITERIA.
Rules:
- Minimum 4 bullet points
- Measurable outcomes
""")

    s["success_results"] = call_llm(f"""
Define EXPECTED BUSINESS RESULTS.
Rules:
- Minimum 4 bullet points
- Business value focused
""")

    s["scope"] = call_llm(f"""
Write TECHNICAL SCOPE OF WORK.
Rules:
- Use phases: Discovery, Design, Build, Test, Demo
- Bullet points per phase
""")

    s["architecture"] = call_llm(f"""
Describe HIGH-LEVEL SOLUTION ARCHITECTURE.
Rules:
- Logical flow
- Cloud-native
- GenAI components
""")

    s["commercials"] = call_llm(f"""
Write COMMERCIAL & RESOURCE ESTIMATE NOTES.
Rules:
- Roles
- Duration
- Cost drivers
""")

# -------------------------------------------------
# DOCX EXPORT
# -------------------------------------------------
def add_table(doc, title, rows):
    doc.add_heading(title, level=2)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"

    h = table.rows[0].cells
    h[0].text = "Name"
    h[1].text = "Title"
    h[2].text = "Email / Contact"

    for r in rows:
        if any(r.values()):
            c = table.add_row().cells
            c[0].text = r["Name"]
            c[1].text = r["Title"]
            c[2].text = r["Email"]

def create_docx(data):
    doc = Document()
    doc.add_heading("Statement of Work (SOW)", 0)

    m = data["metadata"]
    s = data["sections"]

    doc.add_paragraph(f"Customer: {m['customer_name']}")
    doc.add_paragraph(f"Industry: {m['industry']}")
    doc.add_paragraph(f"Solution: {m['solution_type']}")
    doc.add_paragraph(f"Date: {datetime.now().strftime('%d %B %Y')}")

    for k, title in [
        ("objective", "2.1 Objective"),
        ("dependencies", "Dependencies"),
        ("assumptions", "Assumptions"),
        ("success_demo", "Success Demonstration"),
        ("success_results", "Expected Results"),
        ("scope", "Scope of Work"),
        ("architecture", "Architecture"),
        ("commercials", "Commercials")
    ]:
        doc.add_heading(title, 1)
        doc.add_paragraph(s[k])

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# -------------------------------------------------
# UI
# -------------------------------------------------
def main():
    d = st.session_state.sow_data
    m = d["metadata"]
    s = d["sections"]

    st.sidebar.title("🛠 Inputs")

    m["customer_name"] = st.sidebar.text_input("Customer Name", m["customer_name"])
    m["industry"] = st.sidebar.text_input("Industry", m["industry"])
    m["solution_type"] = st.sidebar.text_input("Solution Type", m["solution_type"])
    m["business_problem"] = st.sidebar.text_area("Business Problem")

    if st.sidebar.button("🪄 Generate SOW"):
        generate_sow()
        st.success("SOW content generated")

    st.title("📄 Editable SOW")

    for k, label in [
        ("objective", "Objective"),
        ("dependencies", "Dependencies"),
        ("assumptions", "Assumptions"),
        ("success_demo", "Success Demonstration"),
        ("success_results", "Expected Results"),
        ("scope", "Scope of Work"),
        ("architecture", "Architecture"),
        ("commercials", "Commercials")
    ]:
        s[k] = st.text_area(label, s[k], height=150)

    st.download_button(
        "📥 Download DOCX",
        create_docx(d),
        "Generated_SOW.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if __name__ == "__main__":
    main()
