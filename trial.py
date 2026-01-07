import streamlit as st
import io
import time
from datetime import datetime
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from transformers import pipeline

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="GenAI SOW Agent",
    layout="wide",
    page_icon="📝"
)

# ---------------- LOAD LLM (ONCE) ----------------
@st.cache_resource
def load_llm():
    return pipeline(
        "text-generation",
        model="MiniMaxAI/MiniMax-M2.1",
        trust_remote_code=True,
        device_map="auto"
    )

pipe = load_llm()

# ---------------- SESSION STATE ----------------
if "sow_data" not in st.session_state:
    st.session_state.sow_data = {
        "metadata": {
            "solution_type": "Multi Agent Store Advisor",
            "other_solution": "",
            "selected_sections": [],
            "industry": "Financial Services",
            "customer_name": "Acme Corp",
            "raw_objective_input": ""
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

# ---------------- LLM CALL ----------------
def call_llm(prompt: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional SOW Architect. "
                "Write formal, enterprise-grade, concise content. "
                "No greetings. No filler. No explanations."
            )
        },
        {"role": "user", "content": prompt}
    ]

    try:
        output = pipe(
            messages,
            max_new_tokens=700,
            temperature=0.3,
            do_sample=True
        )

        return output[0]["generated_text"][-1]["content"].strip()

    except Exception as e:
        return f"Error: {str(e)}"

# ---------------- GENERATION ENGINE ----------------
def generate_selected_content():
    meta = st.session_state.sow_data["metadata"]
    solution = meta["other_solution"] if meta["solution_type"] == "Other (Please specify)" else meta["solution_type"]
    selected = meta["selected_sections"]

    if not selected:
        st.error("Select at least one section.")
        return False

    prompt_map = {
        "2.1 OBJECTIVE":
            f"Rewrite this into a formal SOW Objective for a {solution} project: {meta['raw_objective_input']}",

        "2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM":
            f"Define governance structure, sponsors, stakeholders, and delivery roles for {solution}.",

        "2.3 ASSUMPTIONS & DEPENDENCIES":
            f"List 5 technical assumptions and 3 customer dependencies for {solution}.",

        "2.4 PoC Success Criteria":
            f"Define 4 measurable KPIs to validate a {solution} Proof of Concept.",

        "3 SCOPE OF WORK - TECHNICAL PROJECT PLAN":
            f"Describe Discovery, Design, Development, Testing, and UAT phases for {solution}.",

        "4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM":
            f"Describe a cloud-native architecture using LLMs, APIs, orchestration, and security layers for {solution}.",

        "5 RESOURCES & COST ESTIMATES":
            f"Estimate team roles, effort assumptions, and cost drivers for {solution}."
    }

    status = st.empty()

    for i, section in enumerate(selected):
        status.info(f"⏳ Generating {section} ({i+1}/{len(selected)})")
        prompt = f"Industry: {meta['industry']}\nTask: {prompt_map[section]}"
        result = call_llm(prompt)

        if not result.startswith("Error"):
            st.session_state.sow_data["sections"][section] = result
        else:
            st.error(result)

    status.success("✅ SOW Generated")
    time.sleep(1)
    status.empty()
    return True

# ---------------- DOCX EXPORT ----------------
def create_docx(data):
    doc = Document()
    title = doc.add_heading("Statement of Work (SOW)", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sol = data["metadata"]["other_solution"] if data["metadata"]["solution_type"] == "Other (Please specify)" else data["metadata"]["solution_type"]

    p = doc.add_paragraph()
    p.add_run(f"Customer: {data['metadata']['customer_name']}\n").bold = True
    p.add_run(f"Solution: {sol}\n")
    p.add_run(f"Date: {datetime.now().strftime('%Y-%m-%d')}")

    for section, content in data["sections"].items():
        if content:
            doc.add_heading(section, level=1)
            doc.add_paragraph(content)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# ---------------- UI ----------------
def main():
    st.sidebar.title("🛠️ SOW Designer")

    with st.sidebar:
        meta = st.session_state.sow_data["metadata"]

        meta["customer_name"] = st.text_input("Customer Name", meta["customer_name"])

        solutions = [
            "Multi Agent Store Advisor", "Intelligent Search", "Recommendation",
            "Virtual Data Analyst (Text to SQL)", "Sales Co-Pilot",
            "Document / Report Audit", "SOP Creation", "Other (Please specify)"
        ]

        meta["solution_type"] = st.selectbox("Solution Type", solutions)

        if meta["solution_type"] == "Other (Please specify)":
            meta["other_solution"] = st.text_input("Specify Solution")

        meta["industry"] = st.selectbox("Industry", ["Retail", "Financial Services", "Healthcare", "Manufacturing"])

        meta["raw_objective_input"] = st.text_area("Business Problem")

        sections = list(st.session_state.sow_data["sections"].keys())
        meta["selected_sections"] = []

        for sec in sections:
            if st.checkbox(sec, value=True):
                meta["selected_sections"].append(sec)

        if st.button("🪄 Auto-Generate SOW", use_container_width=True):
            if generate_selected_content():
                st.rerun()

    st.title("📄 AI Statement of Work Architect")

    for sec in st.session_state.sow_data["sections"]:
        st.session_state.sow_data["sections"][sec] = st.text_area(
            sec,
            st.session_state.sow_data["sections"][sec],
            height=200
        )

    st.divider()
    docx = create_docx(st.session_state.sow_data)

    st.download_button(
        "📥 Download SOW (DOCX)",
        docx,
        file_name=f"SOW_{meta['customer_name'].replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if __name__ == "__main__":
    main()

