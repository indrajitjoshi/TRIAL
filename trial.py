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
            "solution_name": "WIMO Bot",
            "industry": "Retail / QSR",
            "customer_name": "Customer Name",
            "partner_name": "Partner Name",
            "raw_objective": ""
        },
        "sections": {
            "2.1 OBJECTIVE": "",
            "2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM": "",
            "2.3 ASSUMPTIONS & DEPENDENCIES": "",
            "2.4 PROJECT SUCCESS CRITERIA": "",
            "3 SCOPE OF WORK - TECHNICAL PROJECT PLAN": "",
            "4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM": "",
            "6 RESOURCES & COST ESTIMATES": ""
        }
    }

# -------------------------------------------------
# LLM CALL
# -------------------------------------------------
def call_llm(prompt: str) -> str:
    try:
        result = pipe(
            prompt,
            max_new_tokens=500,
            temperature=0.2
        )
        return result[0]["generated_text"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------------------------
# GENERATION ENGINE (STRICT SOW FORMAT)
# -------------------------------------------------
def generate_sow():
    meta = st.session_state.sow_data["metadata"]
    sec = st.session_state.sow_data["sections"]

    status = st.empty()
    status.info("⏳ Generating enterprise-grade SOW...")

    # 2.1 OBJECTIVE
    sec["2.1 OBJECTIVE"] = call_llm(f"""
Write ONLY the Objective section in a formal SOW tone.

Context:
- Solution: {meta['solution_name']}
- Industry: {meta['industry']}
- Business Problem: {meta['raw_objective']}

Constraints:
- 2–3 sentences
- Consulting-style language
- No headings, no bullets
""")

    # 2.2 STAKEHOLDERS
    sec["2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM"] = call_llm(f"""
Create a structured stakeholder section for a POC SOW.

Include:
- Partner Executive Sponsor
- Customer Executive Sponsor
- Cloud / Technology Sponsor
- Project Escalation Contacts

Use table-like bullet formatting with:
Name | Title | Responsibility
""")

    # 2.3 ASSUMPTIONS & DEPENDENCIES
    sec["2.3 ASSUMPTIONS & DEPENDENCIES"] = call_llm(f"""
Write this section exactly in the following structure:

Dependencies:
- List 2–3 customer dependencies required before POC start

Assumptions:
- List 2–3 delivery assumptions by the implementation partner

Tone: Formal, contractual, POC-specific
""")

    # 2.4 SUCCESS CRITERIA
    sec["2.4 PROJECT SUCCESS CRITERIA"] = call_llm(f"""
Create Project Success Criteria in this exact format:

1. Demonstrations:
- Bullet points of demo capabilities

2. Results:
- Bullet points of expected technical outcomes

Context: {meta['solution_name']} GenAI POC
""")

    # 3 SCOPE OF WORK
    sec["3 SCOPE OF WORK - TECHNICAL PROJECT PLAN"] = call_llm(f"""
Write Scope of Work using this structure:

1. Requirements Gathering & Design (Estimated Time: 1 week)
- Bulleted activities

2. Model / Bot Development (Estimated Time: 1 week)
- Bulleted activities

3. Integration & UI (Estimated Time: 1 week)
- Bulleted activities

4. Delivery & Demonstration (Estimated Time: 1 week)
- Bulleted activities

Tone: Consulting SOW
""")

    # 4 ARCHITECTURE
    sec["4 SOLUTION ARCHITECTURE / ARCHITECTURAL DIAGRAM"] = call_llm(f"""
Describe high-level solution architecture for a GenAI POC.

Include:
- UI layer
- API / orchestration layer
- LLM / embeddings
- Data sources
- Security considerations

Do NOT include diagrams, only text.
""")

    # 6 COMMERCIALS
    sec["6 RESOURCES & COST ESTIMATES"] = call_llm(f"""
Write a short commercial section stating:

- POC is a one-time investment
- Jointly funded or exploratory in nature
- Costs indicative and subject to post-POC decisions

Tone: Enterprise SOW
""")

    status.success("✅ SOW Generated Successfully")
    time.sleep(1)
    status.empty()

# -------------------------------------------------
# DOCX EXPORT
# -------------------------------------------------
def create_docx(data):
    doc = Document()
    title = doc.add_heading("Scope of Work (SOW)", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    p.add_run(f"Customer: {data['metadata']['customer_name']}\n").bold = True
    p.add_run(f"Solution: {data['metadata']['solution_name']}\n")
    p.add_run(f"Date: {datetime.now().strftime('%d %B %Y')}")

    for section, content in data["sections"].items():
        doc.add_heading(section, level=1)
        doc.add_paragraph(content)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# -------------------------------------------------
# UI
# -------------------------------------------------
def main():
    st.sidebar.title("🛠️ SOW Inputs")

    meta = st.session_state.sow_data["metadata"]

    meta["customer_name"] = st.sidebar.text_input("Customer Name", meta["customer_name"])
    meta["solution_name"] = st.sidebar.text_input("Solution Name", meta["solution_name"])
    meta["industry"] = st.sidebar.text_input("Industry", meta["industry"])

    meta["raw_objective"] = st.sidebar.text_area(
        "Business Objective",
        placeholder="Describe the business problem the POC is solving..."
    )

    if st.sidebar.button("🪄 Generate SOW", use_container_width=True):
        generate_sow()
        st.rerun()

    st.title("📄 Generated Statement of Work")

    for section in st.session_state.sow_data["sections"]:
        st.text_area(
            section,
            st.session_state.sow_data["sections"][section],
            height=220
        )

    st.divider()
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
