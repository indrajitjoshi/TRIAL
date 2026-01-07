import streamlit as st
import io
import time
from datetime import datetime
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

# -------------------------------------------------
# LLM CALL
# -------------------------------------------------
def call_llm(prompt: str) -> str:
    try:
        result = pipe(
            prompt,
            max_new_tokens=400,
            temperature=0.3
        )
        return result[0]["generated_text"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------------------------
# CONTENT GENERATION
# -------------------------------------------------
def generate_selected_content():
    meta = st.session_state.sow_data["metadata"]
    solution = meta["other_solution"] if meta["solution_type"] == "Other (Please specify)" else meta["solution_type"]
    selected = meta["selected_sections"]

    if not selected:
        st.error("Please select at least one section.")
        return False

    prompt_map = {
        "2.1 OBJECTIVE":
            f"Rewrite the following business problem into a formal SOW Objective section for a {solution} project:\n{meta['raw_objective_input']}",

        "2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM":
            f"Describe project sponsors, stakeholders, governance, and delivery team roles for a {solution} implementation.",

        "2.3 ASSUMPTIONS & DEPENDENCIES":
            f"List 5 technical assumptions and 3 customer dependencies for implementing {solution}.",

        "2.4 PoC Success Criteria":
            f"Define 4 measurable KPIs to evaluate the success of a {solution} Proof of Concept.",

        "3 SCOPE OF WORK - TECHNICAL PROJECT PLAN":
            f"Describe the Discovery, Design, Development, Testing, and UAT phases for delivering {solution}.",

        "4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM":
            f"Describe a high-level cloud-based solution architecture for {solution}, including data flow, security, and AI components.",

        "5 RESOURCES & COST ESTIMATES":
            f"Estimate delivery roles, effort assumptions, and primary cost drivers for a {solution} project."
    }

    status = st.empty()

    for i, section in enumerate(selected):
        status.info(f"⏳ Generating {section} ({i+1}/{len(selected)})")
        prompt = f"Industry: {meta['industry']}\n\nTask:\n{prompt_map[section]}"
        content = call_llm(prompt)

        if not content.startswith("Error"):
            st.session_state.sow_data["sections"][section] = content
        else:
            st.error(content)

    status.success("✅ SOW generation completed")
    time.sleep(1)
    status.empty()
    return True

# -------------------------------------------------
# DOCX EXPORT
# -------------------------------------------------
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

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# -------------------------------------------------
# UI
# -------------------------------------------------
def main():
    st.sidebar.title("🛠️ SOW Designer")

    meta = st.session_state.sow_data["metadata"]

    with st.sidebar:
        meta["customer_name"] = st.text_input("Customer Name", meta["customer_name"])

        solution_options = [
            "Multi Agent Store Advisor",
            "Intelligent Search",
            "Recommendation",
            "Sales Co-Pilot",
            "Virtual Data Analyst (Text to SQL)",
            "Document / Report Audit",
            "SOP Creation",
            "Other (Please specify)"
        ]

        meta["solution_type"] = st.selectbox("Solution Type", solution_options)

        if meta["solution_type"] == "Other (Please specify)":
            meta["other_solution"] = st.text_input("Specify Solution Name")

        meta["industry"] = st.selectbox(
            "Industry",
            ["Retail", "Financial Services", "Healthcare", "Manufacturing", "Legal"]
        )

        meta["raw_objective_input"] = st.text_area(
            "Business Problem",
            placeholder="Describe the problem this solution will address..."
        )

        st.divider()
        st.write("### SOW Sections")

        meta["selected_sections"] = []
        for section in st.session_state.sow_data["sections"].keys():
            if st.checkbox(section, value=True):
                meta["selected_sections"].append(section)

        if st.button("🪄 Auto-Generate SOW", use_container_width=True):
            if generate_selected_content():
                st.rerun()

    st.title("📄 AI Statement of Work Architect")

    for section in st.session_state.sow_data["sections"]:
        st.session_state.sow_data["sections"][section] = st.text_area(
            section,
            st.session_state.sow_data["sections"][section],
            height=200
        )

    st.divider()
    docx = create_docx(st.session_state.sow_data)

    st.download_button(
        "📥 Download SOW (DOCX)",
        docx,
        file_name=f"SOW_{meta['customer_name'].replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------
if __name__ == "__main__":
    main()
