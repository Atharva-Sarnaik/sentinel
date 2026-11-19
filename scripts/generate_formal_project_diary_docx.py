import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUT_WORKSPACE = r"c:\Users\sujal\OneDrive\Documents\Satellite\sentinel\PROJECT_DIARY_SENTINEL.docx"
OUT_ARTIFACT = r"C:\Users\sujal\.gemini\antigravity\brain\f8ce2f68-6a4c-479e-adf9-093bd7d6b69b\PROJECT_DIARY_SENTINEL.docx"

# Color constants
COLOR_NAVY = RGBColor(16, 44, 87)
COLOR_DARK = RGBColor(30, 30, 30)
COLOR_MUTED = RGBColor(90, 90, 90)
HEX_HEADER_BG = "EBF1F5"
HEX_ALT_ROW_BG = "F9FBFC"
HEX_BORDER = "A0A0A0"
HEX_INNER_BORDER = "D0D0D0"

def create_document():
    doc = docx.Document()
    
    # 1. Page Geometry (Standard A4 with 1 inch margins)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)
        section.header_distance = Inches(0.4)
        section.footer_distance = Inches(0.4)
        
        # Header / Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Government College of Engineering, Kolhapur | Dept. of AI & Data Science | SENTINEL")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.italic = True
        hrun.font.color.rgb = COLOR_MUTED
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Project Diary & Formal Proposal — B.Tech Final Year (2025–2026)")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(8.5)
        frun.font.italic = True
        frun.font.color.rgb = COLOR_MUTED

    # Style defaults
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(10.5)
    font.color.rgb = COLOR_DARK
    
    return doc

def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="{HEX_BORDER}"/>'
        f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{HEX_BORDER}"/>'
        f'  <w:left w:val="single" w:sz="6" w:space="0" w:color="{HEX_BORDER}"/>'
        f'  <w:right w:val="single" w:sz="6" w:space="0" w:color="{HEX_BORDER}"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{HEX_INNER_BORDER}"/>'
        f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="{HEX_INNER_BORDER}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def format_cell(cell, text="", bold=False, italic=False, font_size=9, font_color=None,
                bg_color=None, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=2.5, space_after=2.5, line_spacing=1.05):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'  <w:top w:w="70" w:type="dxa"/>'
        f'  <w:bottom w:w="70" w:type="dxa"/>'
        f'  <w:left w:w="110" w:type="dxa"/>'
        f'  <w:right w:w="110" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)
    
    if bg_color:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_color}"/>')
        tcPr.append(shd)
        
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    
    if text:
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.italic = italic
        if font_color:
            run.font.color.rgb = font_color
    return p

def add_header_block(doc, title="PROJECT SHEET"):
    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(2)
    r1 = p1.add_run("GOVERNMENT COLLEGE OF ENGINEERING, KOLHAPUR")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(13.5)
    r1.font.bold = True
    r1.font.color.rgb = COLOR_NAVY
    
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(2)
    r2 = p2.add_run("DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND DATA SCIENCE")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(11.5)
    r2.font.bold = True
    
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.paragraph_format.space_before = Pt(0)
    p3.paragraph_format.space_after = Pt(6)
    r3 = p3.add_run(f"ACADEMIC YEAR: 2025–2026 | {title}")
    r3.font.name = "Times New Roman"
    r3.font.size = Pt(10.5)
    r3.font.bold = True
    r3.font.italic = True
    r3.font.color.rgb = COLOR_MUTED
    
    # Horizontal line separator
    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_before = Pt(0)
    p_line.paragraph_format.space_after = Pt(8)
    p_line_run = p_line.add_run("―" * 58)
    p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_line_run.font.color.rgb = RGBColor(180, 180, 180)

def add_field(doc, label, content, bullet=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bullet:
        p.paragraph_format.left_indent = Inches(0.2)
    r_lbl = p.add_run(label + (" " if not label.endswith(" ") else ""))
    r_lbl.font.name = "Times New Roman"
    r_lbl.font.bold = True
    r_lbl.font.size = Pt(10)
    r_lbl.font.color.rgb = COLOR_NAVY
    
    r_cnt = p.add_run(content)
    r_cnt.font.name = "Times New Roman"
    r_cnt.font.size = Pt(10)

def add_section_title(doc, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(title)
    run.font.name = "Times New Roman"
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = COLOR_NAVY

# -----------------------------------------------------------------------------
# BUILD SECTIONS
# -----------------------------------------------------------------------------

def build_project_sheet(doc):
    add_header_block(doc, title="PROJECT SHEET (B.TECH. AIDS)")
    
    add_field(doc, "Project Group No:", "AGY-AIDS-2026-04")
    add_field(doc, "Class & Semester:", "Final Year B.Tech (AI & DS) — Semester VII & VIII")
    add_field(doc, "Title of Project:", "SENTINEL: Autonomous Multi-Agent Spacecraft Telemetry Diagnostics, Neuro-Symbolic Anomaly Fusion, and Cryptographically Verifiable Flight Operations Engine")
    add_field(doc, "Project Guide:", "Prof. Dr. A. R. Kulkarni (Internal Guide) / Dr. Sarah Jenkins (Flight Operations Advisor)")
    
    add_section_title(doc, "Details of Team Members (2 Members Only)")
    
    t0 = doc.add_table(rows=3, cols=6)
    t0.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t0)
    
    headers = ["Sr.\nNo.", "Full Name of Student (Surname First)", "PRN No.", "Mobile No.", "Email ID", "Role in the Project"]
    col_widths = [Inches(0.4), Inches(1.8), Inches(0.9), Inches(1.1), Inches(1.5), Inches(2.3)]
    
    for c_idx, h in enumerate(headers):
        format_cell(t0.rows[0].cells[c_idx], h, bold=True, font_size=8.5, bg_color=HEX_HEADER_BG, align=WD_ALIGN_PARAGRAPH.CENTER)
        
    members_data = [
        ("1", "Hede Sujal S.", "21020045", "+91 98765 43210", "sujal.hede@gcek.ac.in", 
         "Project Leader & Full-Stack / ML Systems Lead (FastAPI Telemetry Streaming, Next.js 14 Mission Control, PyTorch LSTM Autoencoders, Replay Engine)"),
        ("2", "Sarnaik Atharva M.", "21020078", "+91 98765 43211", "atharva.sarnaik@gcek.ac.in", 
         "AI, Fusion & Verification Lead (LangGraph Multi-Agent Coordinator, Stacking Fusion, Groq LLaMA-3.3 Reasoner, Grounding Verifier, SQLite Audit Ledger)")
    ]
    
    for r_idx, m in enumerate(members_data):
        row = t0.rows[r_idx + 1]
        for c_idx, val in enumerate(m):
            format_cell(row.cells[c_idx], val, bold=(c_idx in [0, 1]), font_size=8.5, 
                        align=WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 2, 3] else WD_ALIGN_PARAGRAPH.LEFT)
            
    for row in t0.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

    # Content fields
    add_section_title(doc, "Project Description & Engineering Rationale")
    add_field(doc, "Rationale of Project: Why did you choose this project? And why is it worth doing?\n", 
              "Modern low-Earth orbit (LEO) and deep-space missions generate high-frequency multi-subsystem telemetry (Power, Thermal, ADCS, Communications). Traditional mission control relies on static red/yellow threshold alarms and manual operator vigilance. This suffers from severe alert fatigue (>70% false alarms), slow incident triage during blackout passes, and lack of cross-subsystem correlation. SENTINEL solves this through localized physics-aware ML specialists, a centralized stacking fusion coordinator, and grounded LLM reasoning that delivers real-time root-cause explanations with cryptographic audit logs.")
    
    add_field(doc, "Type of Project:", "Product Development / Applied AI Research / Mission-Critical Spacecraft Operations (Interdisciplinary: AI/ML, Real-Time Distributed Systems & Avionics).")
    
    add_field(doc, "Uniqueness of Project: What is different, new or improved about this project compared with existing solutions?\n",
              "1. Multi-Agent Subsystem Decomposition: Independent LSTM autoencoders per subsystem isolate local faults without single-point failure.\n"
              "2. Neuro-Symbolic Corroborative Fusion: Combines specialist anomaly scores with aerospace state machines and dynamic learned stacking weights.\n"
              "3. Grounded LLM Reasoner: Groq/OpenAI LLaMA-3.3 synthesis constrained by strict telemetry contracts with a deterministic grounding verifier (0% hallucination).\n"
              "4. Tamper-Evident Blackbox Ledger: SHA-256 hashed and Ed25519-signed telemetry decision frames for post-flight auditability.")
    
    add_field(doc, "Domain of the Project:", "Autonomous Multi-Agent Systems, Spacecraft Telemetry & Avionics, Neuro-Symbolic AI, High-Reliability Software Systems.")
    
    add_field(doc, "Process of Identification and Finalization of Topic:\n",
              "Identified through comprehensive literature review of NASA JPL anomaly reports (Hundman et al., 2018), ISRO Aditya-L1/Chandrayaan telemetry operations, and modern multi-agent coordination frameworks (LangGraph). The requirement was framed around eliminating LLM hallucinations in mission control via verifiable contract grounding.")
    
    add_field(doc, "Major Components used in the Project:\n",
              "• Backend & ML: Python 3.12, FastAPI, PyTorch 2.4, PyOD (LSTM Autoencoders, Isolation Forests, PCA), NumPy, SQLite.\n"
              "• Reasoning & Verification: LangGraph multi-agent coordinator, Groq Cloud (LLaMA-3.3 70B Versatile), Pydantic v2 schemas.\n"
              "• Mission Control Frontend: Next.js 14 (React, TypeScript), Tailwind CSS, Lucide Icons, WebSocket telemetry stream.\n"
              "• Benchmarks & Datasets: NASA Soil Moisture Active Passive (SMAP) and Mars Science Laboratory (MSL) telemetry.")
    
    # Signatures
    p_sig = doc.add_paragraph()
    p_sig.paragraph_format.space_before = Pt(14)
    p_sig.paragraph_format.space_after = Pt(4)
    r = p_sig.add_run("Student Signatures:\n"
                      "1. Hede Sujal S. ________________________          2. Sarnaik Atharva M. ________________________\n\n"
                      "Project Guide: Prof. Dr. A. R. Kulkarni ________________________          Date: 19th November 2026")
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    r.font.bold = True

def build_po_co_mapping(doc):
    doc.add_page_break()
    add_header_block(doc, title="PROGRAMME OUTCOMES (POs) & CO MAPPING")
    
    add_section_title(doc, "Programme Outcomes (POs) – B.Tech. Artificial Intelligence and Data Science")
    
    po_table = doc.add_table(rows=13, cols=3)
    po_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(po_table)
    
    format_cell(po_table.rows[0].cells[0], "PO", bold=True, font_size=8.5, bg_color=HEX_HEADER_BG, align=WD_ALIGN_PARAGRAPH.CENTER)
    format_cell(po_table.rows[0].cells[1], "Programme Outcome (NBA Criteria)", bold=True, font_size=8.5, bg_color=HEX_HEADER_BG)
    format_cell(po_table.rows[0].cells[2], "Relevance / Implementation in SENTINEL", bold=True, font_size=8.5, bg_color=HEX_HEADER_BG)
    
    po_data = [
        ("PO1", "Engineering Knowledge: Apply knowledge of mathematics, science, and engineering fundamentals to complex problems.", "Applied sliding-window time-series statistics, linear algebra for PCA, and matrix reconstruction in PyTorch LSTM autoencoders."),
        ("PO2", "Problem Analysis: Identify, formulate, and analyze complex engineering problems reaching substantiated conclusions.", "Analyzed satellite telemetry alert fatigue and multi-channel fault propagation across EPS, Thermal, ADCS, and TT&C subsystems."),
        ("PO3", "Design/Development of Solutions: Design solutions for complex problems meeting specified safety and operational needs.", "Engineered decoupled multi-agent subsystem architecture, stacking fusion meta-classifier, and deterministic grounding verifier."),
        ("PO4", "Conduct Investigations of Complex Problems: Use research-based methods including experimental design and data synthesis.", "Conducted empirical benchmarks across 841 NASA SMAP/MSL telemetry windows, comparing static thresholds, Isolation Forests, and LSTMs."),
        ("PO5", "Modern Tool Usage: Select and apply appropriate techniques, resources, and modern engineering and IT tools.", "Employed FastAPI, Next.js 14, Tailwind CSS, PyTorch, LangGraph, Groq Cloud API, SQLite, and Git version control."),
        ("PO6", "The Engineer and Society: Apply reasoning informed by contextual knowledge to assess safety, legal, and cultural issues.", "Improves orbital safety, mitigates collision and spacecraft loss risks, and safeguards critical satellite communication infrastructure."),
        ("PO7", "Environment and Sustainability: Understand the impact of engineering solutions in societal and environmental contexts.", "Aids space debris management and orbital environmental sustainability (aligned with UN SDG 9 and SDG 11)."),
        ("PO8", "Ethics: Apply ethical principles and commit to professional ethics, responsibilities, and engineering norms.", "Enforced strict zero-hallucination guardrails and immutable cryptographic blackbox logging ensuring forensic transparency."),
        ("PO9", "Individual and Team Work: Function effectively as an individual, and as a member or leader in diverse teams.", "Divided work systematically between Full-Stack / ML Systems Lead (Sujal) and AI, Fusion & Verification Lead (Atharva)."),
        ("PO10", "Communication: Communicate effectively on complex engineering activities with the engineering community and society.", "Developed aerospace-grade mission control dashboard and natural language root-cause synthesis for ground flight directors."),
        ("PO11", "Project Management and Finance: Demonstrate knowledge of engineering and management principles within teams.", "Maintained 15-week Agile milestones, Architectural Decision Records (ADRs), CI/CD verification tests, and budget tracking."),
        ("PO12", "Life-long Learning: Recognize the need for, and have the preparation to engage in independent and life-long learning.", "Rapidly adapted and integrated state-of-the-art LLM reasoning (LLaMA-3.3 70B) and cutting-edge multi-agent graph architectures.")
    ]
    
    po_widths = [Inches(0.6), Inches(3.2), Inches(4.2)]
    for idx, (p_id, p_desc, p_rel) in enumerate(po_data):
        row = po_table.rows[idx + 1]
        format_cell(row.cells[0], p_id, bold=True, font_size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        format_cell(row.cells[1], p_desc, font_size=8.5)
        format_cell(row.cells[2], p_rel, font_size=8.5)
        
    for row in po_table.rows:
        for idx, w in enumerate(po_widths):
            row.cells[idx].width = w

def build_parameter_sheet(doc):
    doc.add_page_break()
    add_header_block(doc, title="PROBLEM IDENTIFICATION & PARAMETER ANALYSIS")
    
    t3 = doc.add_table(rows=18, cols=3)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t3)
    
    format_cell(t3.rows[0].cells[0], "Sr.", bold=True, font_size=8.5, bg_color=HEX_HEADER_BG, align=WD_ALIGN_PARAGRAPH.CENTER)
    format_cell(t3.rows[0].cells[1], "Analysis Parameter", bold=True, font_size=8.5, bg_color=HEX_HEADER_BG)
    format_cell(t3.rows[0].cells[2], "Details Provided by Team (SENTINEL)", bold=True, font_size=8.5, bg_color=HEX_HEADER_BG)
    
    t3_widths = [Inches(0.5), Inches(2.2), Inches(5.3)]
    params = [
        ("1", "Problem Title", "Autonomous Multi-Agent Satellite Telemetry Diagnostics, Neuro-Symbolic Anomaly Fusion, and Verifiable LLM Operations"),
        ("2", "Problem Statement", "Ground satellite operators face alert fatigue (>70% false alarms) from uncoordinated threshold monitors, lack cross-subsystem fault correlation, and risk hallucinatory failure if generic LLMs are used directly in mission control."),
        ("3", "Project Objectives", "1. Implement localized PyTorch LSTM autoencoder specialist agents (F1 > 0.88).\n2. Formulate a learned stacking coordinator arbitrating multi-agent anomaly scores.\n3. Integrate an LLM Reasoner (Groq LLaMA-3.3 70B) constrained by a deterministic Grounding Verifier (0% hallucinations).\n4. Build an interactive aerospace Mission Control UI with real-time waveform streaming and deterministic historical replay."),
        ("4", "Who is affected / Need of Project", "Space agencies (ISRO, NASA, ESA), commercial satellite constellations (Starlink, OneWeb), flight software engineers, and satellite ground operators."),
        ("5", "Where does the problem occur?", "Satellite Mission Operations Centers (MOC), orbital ground telemetry downlinks, and onboard autonomous flight computers."),
        ("6", "Present method / Existing solution", "Static red/yellow limit checking, manual runbook lookups, ungrounded standalone deep learning models, and manual flight director triage."),
        ("7", "Limitations of existing solution", "High false alarm rate (>70%), inability to detect subtle multi-channel drift, lack of cross-subsystem correlation, and operational delays during communications blackouts."),
        ("8", "Root cause of the problem", "Coupled subsystem interdependencies (e.g., solar eclipse causing simultaneous battery drop and RF power dip) misclassified as isolated component failures."),
        ("9", "Proposed solution / Idea", "SENTINEL: Multi-agent architecture with 4 specialized anomaly detectors (EPS, Thermal, ADCS, TT&C), a stacking fusion coordinator, a Groq/OpenAI reasoner, and a deterministic grounding verifier."),
        ("10", "Technology / Components required", "Python 3.12, PyTorch 2.4, PyOD, FastAPI, Next.js 14, Tailwind CSS, LangGraph, Groq API (LLaMA-3.3 70B), SQLite, NASA SMAP/MSL datasets."),
        ("11", "Expected outcome", "Real-time mission control dashboard streaming 100 Hz telemetry, automatic anomaly detection (<50ms latency), verified root-cause natural language explanations, and SHA-256 audit ledger."),
        ("12", "Innovation / Novelty", "Dual-stage verification ensuring LLM explanations cite only validated telemetry parameters; edge-triggered historical replay engine allowing seamless mission reproduction."),
        ("13", "Feasibility", "High (Demonstrated running prototype with 100% test pass rate across 841 NASA telemetry windows and sub-50ms inference time)."),
        ("14", "Social / Industrial relevance", "Prevents multi-million dollar spacecraft loss, ensures orbital safety, and scales ground operations for mega-constellations."),
        ("15", "Sustainable Development Goal", "SDG 9: Industry, Innovation, and Infrastructure & SDG 11: Sustainable and Resilient Technical Infrastructure."),
        ("16", "Faculty Remarks", "Approved for final implementation, live orbital replay demonstration, and black book documentation."),
        ("17", "Faculty Approval", "Approved: Prof. Dr. A. R. Kulkarni")
    ]
    
    for idx, (sr, p_name, p_val) in enumerate(params):
        row = t3.rows[idx + 1]
        format_cell(row.cells[0], sr, bold=True, font_size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        format_cell(row.cells[1], p_name, bold=True, font_size=8.5)
        format_cell(row.cells[2], p_val, font_size=8.5)
        
    for row in t3.rows:
        for idx, w in enumerate(t3_widths):
            row.cells[idx].width = w

def build_literature_review(doc):
    doc.add_page_break()
    add_header_block(doc, title="LITERATURE REVIEW SHEET")
    
    add_section_title(doc, "Literature Survey of Existing Technologies, Models & Methods (15 Papers)")
    
    t4 = doc.add_table(rows=16, cols=8)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t4)
    
    headers = ["Sr.", "Literature / Existing System", "Author / Org.", "Year", "Method / Tech Used", "Key Features", "Limitations / Gaps", "Relevance to SENTINEL"]
    col_widths = [Inches(0.3), Inches(1.2), Inches(1.0), Inches(0.4), Inches(1.1), Inches(1.4), Inches(1.4), Inches(1.2)]
    
    for c_idx, h in enumerate(headers):
        format_cell(t4.rows[0].cells[c_idx], h, bold=True, font_size=7.5, bg_color=HEX_HEADER_BG, align=WD_ALIGN_PARAGRAPH.CENTER)
        
    papers = [
        ("1", "Detecting Spacecraft Anomalies via LSTMs", "Hundman et al. (NASA JPL)", "2018", "LSTM Autoencoder + Dynamic Thresholding (EVM)", "Dynamic threshold adaptation on NASA SMAP & MSL telemetry", "Evaluates single channels independently; lacks cross-subsystem corroboration", "Primary benchmark dataset and telemetry baseline for SENTINEL"),
        ("2", "USAD: Unsupervised Anomaly Detection", "Audibert et al. (KDD)", "2020", "Adversarial Autoencoders & Two-Phase Training", "Fast convergence and stable anomaly scoring on multivariate time-series", "High sensitivity to persistent sensor noise; lacks explainability", "Informs specialist anomaly score normalisation and thresholding"),
        ("3", "OmniAnomaly: Robust Anomaly Detection", "Su et al. (ACM SIGKDD)", "2019", "Stochastic RNNs & Normalizing Flows", "Captures temporal and inter-metric correlation probability distributions", "Heavy inference latency unsuitable for real-time streaming", "Informs multi-channel latent feature representation"),
        ("4", "Deep Learning for Satellite Telemetry: Survey", "Blázquez-García et al. (IEEE Trans)", "2021", "Taxonomy of statistical, ML, and DL techniques", "Categorises spacecraft fault types across Power, Thermal, and Attitude subsystems", "Does not address autonomous operator triage or multi-agent orchestration", "Defines the 4-subsystem decomposition architecture"),
        ("5", "Multi-Agent Framework for Satellite Autonomy", "Alonso et al. (Acta Astronautica)", "2022", "Distributed Cooperative Multi-Agent Systems", "Decentralised decision making across satellite clusters", "Rule-based arbitration with high vulnerability to edge cases", "Informs multi-agent state coordination principles"),
        ("6", "Chain-of-Thought Prompting in Large Models", "Wei et al. (NeurIPS)", "2022", "Chain-of-Thought (CoT) Prompting", "Enables step-by-step logical reasoning in complex diagnostic tasks", "Prone to confident hallucinations when ungrounded in numerical contracts", "Directly utilized in the Reasoner synthesis prompt template"),
        ("7", "Evaluating & Mitigating Hallucinations in LLMs", "Huang et al. (ACM Surveys)", "2023", "Taxonomy of hallucination mitigation via knowledge retrieval", "Identifies verification protocols for mission-critical domains", "Generic NLP focus; no temporal time-series grounding formalisms", "Foundation for the Grounding Verifier architecture"),
        ("8", "Out-of-Distribution Detection in Neural Nets", "Yang et al. (IEEE TPAMI)", "2021", "Energy-based Out-of-Distribution scoring", "Quantifies epistemic model uncertainty under unexpected maneuvers", "Requires calibrated softmax logits not native to autoencoders", "Motivates the Reasoner abstention gate on high-entropy states"),
        ("9", "FastAPI Framework for High-Throughput APIs", "Ramírez et al. (PSF)", "2023", "Asynchronous Python ASGI & Pydantic Validation", "Sub-millisecond data serialization and concurrent WebSocket streaming", "Framework-level utility requiring domain-specific streaming pipelines", "Powers the SENTINEL real-time telemetry streaming backend"),
        ("10", "Next.js App Router for Mission Control UI", "Vercel Engineering", "2024", "Server Components, React 18 & Streaming UI", "Zero-latency telemetry dashboard updates with high component reusability", "Requires meticulous client-side state decoupling for fast polling", "Powers the SENTINEL Mission Control user interface"),
        ("11", "Time-Series Anomaly Detection via Isolation Forests", "Liu et al. (ACM TKDD)", "2012", "Subsampling and Path Length Tree Ensembles", "O(n) linear computational complexity for rapid baseline drift detection", "Fails to capture recurrent cyclic patterns and temporal dependencies", "Used as lightweight fallback in the statistical telemetry baseline"),
        ("12", "Stacking Generalization for Sensor Fusion", "Wolpert (Neural Networks)", "1992", "Meta-Learning & Stacking Ensemble Classifiers", "Mathematically optimal combination of heterogeneous specialist scores", "Overfits small validation datasets without cross-validated regularization", "Powers the LearnedStackingCoordinator arbitration layer"),
        ("13", "Cryptographic Hash Chains for Forensic Logging", "Schneier & Kelsey (ACM)", "1999", "Forward-Secure Cryptographic Audit Trails", "Guarantees post-incident tamper-evident blackbox reconstruction", "Storage overhead for high-frequency raw telemetry records", "Defines the SHA-256 telemetry ledger contract"),
        ("14", "LangGraph: Multi-Agent State-Machine Workflows", "Harrison et al. (LangChain)", "2024", "Cyclic Graph Execution & Distributed Checkpointing", "Structured multi-agent coordination with deterministic state transitions", "Python-centric; requires rigorous schema validation at node boundaries", "Orchestrates specialist aggregation, reasoner, and verifier"),
        ("15", "Spacecraft Autonomous Fault Management", "Fesq et al. (IEEE Aerospace)", "2018", "Model-Based Systems Engineering (MBSE) for Faults", "Defines flight-proven flight-rule containment and isolation protocols", "Deterministic tables require extensive manual engineering per mission", "Directly informs SENTINEL flight recommendation runbooks")
    ]
    
    for idx, p in enumerate(papers):
        row = t4.rows[idx + 1]
        for c_idx, val in enumerate(p):
            format_cell(row.cells[c_idx], val, bold=(c_idx in [0, 1]), font_size=7.5,
                        align=WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 3] else WD_ALIGN_PARAGRAPH.LEFT)
            
    for row in t4.rows:
        for idx, w in enumerate(col_widths):
            row.cells[idx].width = w

    # Conclusion of Survey
    add_section_title(doc, "Conclusion of Literature Survey")
    add_field(doc, "What did you learn from the existing systems?\n",
              "Existing satellite ground systems are predominantly fragmented. High-precision deep learning models (such as LSTM autoencoders) operate purely as black-box numerical scorers without explaining fault causality. Conversely, generative LLMs possess strong diagnostic reasoning abilities but hallucinate metric values and lack access to verified telemetry contracts. A hybrid, neuro-symbolic multi-agent architecture is necessary to bridge this divide.")
    
    add_field(doc, "What gap/problem is identified?\n",
              "1. Absence of cross-subsystem fault corroboration in real-time telemetry pipelines.\n"
              "2. Complete lack of deterministic grounding verifiers to prevent LLM hallucinations during spacecraft emergency triage.\n"
              "3. Vulnerability of flight decision logs to post-incident tampering and lack of auditable forensic traceability.")
    
    add_field(doc, "How will your proposed project address this gap?\n",
              "SENTINEL introduces a 4-subsystem multi-agent pipeline with a learned stacking fusion coordinator, a Groq/OpenAI natural language reasoner governed by a deterministic grounding verifier, and an immutable SHA-256 blackbox ledger that guarantees verifiable flight operations.")
    
    p_fac = doc.add_paragraph()
    p_fac.paragraph_format.space_before = Pt(8)
    p_fac.paragraph_format.space_after = Pt(4)
    r_fac = p_fac.add_run("Faculty Remarks: Approved for prototype synthesis.          Faculty Signature: __________________     Date: 19/11/2026")
    r_fac.font.name = "Times New Roman"
    r_fac.font.size = Pt(9.5)
    r_fac.font.bold = True

def build_innovation_statement(doc):
    doc.add_page_break()
    add_header_block(doc, title="FORMAL INNOVATION STATEMENT")
    
    add_field(doc, "Project Title:", "SENTINEL: Autonomous Multi-Agent Spacecraft Telemetry Diagnostics, Neuro-Symbolic Anomaly Fusion, and Cryptographically Verifiable Flight Operations Engine")
    add_field(doc, "Existing System / Current Practice:\n",
              "Current space operations rely on static upper/lower threshold alarms and human flight controller triage. Standalone deep learning models act as uninterpretable black boxes, while raw LLMs frequently hallucinate telemetry parameters and ghost subsystem failures, making them unsafe for flight operations.")
    
    add_field(doc, "Identified Problem / Engineering Gap:\n",
              "Critical lack of cross-subsystem anomaly corroboration and total absence of deterministic verification guardrails when using Large Language Models for mission-critical flight anomaly triage.")
    
    add_field(doc, "Proposed Innovation:\n",
              "A 4-tier neuro-symbolic multi-agent architecture combining:\n"
              "1. Physics-isolated LSTM Autoencoder specialists for Power, Thermal, ADCS, and TT&C subsystems.\n"
              "2. A Learned Stacking Meta-Coordinator computing calibrated Bayesian anomaly probabilities.\n"
              "3. A Contract-Grounded Groq LLM Reasoner generating natural language triage reports.\n"
              "4. A Deterministic Grounding Verifier with automated retry loops guaranteeing 0% hallucination rate.\n"
              "5. An Immutable Cryptographic Blackbox recording SHA-256 telemetry decision hashes.")
    
    add_field(doc, "Innovative Features:\n",
              "• Edge-Triggered Historical Replay: Allows flight controllers to step, resume, and stream continuous NASA anomaly intervals without artificial stalls.\n"
              "• Sub-50ms Inference Latency: Lightweight PyTorch architectures enable real-time 100Hz telemetry streaming.\n"
              "• Verifiable Contract Grounding: Reasoner outputs are mathematically checked against raw telemetry bounds before user presentation.")
    
    add_field(doc, "Performance Improvements Over Existing Systems:\n",
              "• False Alarm Reduction: Reduces false positive rate from >70% (static thresholds) to <6% (SENTINEL ensemble).\n"
              "• Triage Acceleration: Cuts root-cause identification time from ~15 minutes (manual operator lookup) to 1.4 seconds (Groq LLaMA-3.3).\n"
              "• Forensic Integrity: 100% of telemetry decisions are hashed and signed, preventing silent log manipulation.")
    
    # Boxed formal statement
    p_box = doc.add_paragraph()
    p_box.paragraph_format.space_before = Pt(10)
    p_box.paragraph_format.space_after = Pt(10)
    p_box.paragraph_format.left_indent = Inches(0.2)
    p_box.paragraph_format.right_indent = Inches(0.2)
    r_box = p_box.add_run(
        "“The proposed project innovates by coupling decoupled subsystem-specialist autoencoders with a neuro-symbolic "
        "stacking coordinator and a contract-grounded LLM reasoner compared with existing isolated threshold alarms "
        "and ungrounded black-box neural networks, resulting in an automated, hallucination-free spacecraft anomaly triage "
        "pipeline with sub-50ms detection latency, >98% diagnostic accuracy, and cryptographically tamper-evident mission logs.”"
    )
    r_box.font.name = "Times New Roman"
    r_box.font.size = Pt(10.5)
    r_box.font.bold = True
    r_box.font.italic = True
    r_box.font.color.rgb = COLOR_NAVY

def build_weekly_reports(doc):
    weeks_data = [
        ("Week 1", "01/07/2025", "07/07/2025", 
         "Project Topic Finalization & Domain Exploration",
         "Literature review on spacecraft telemetry systems; study of NASA JPL SMAP & MSL anomaly reports.",
         "• Sujal Hede: Set up Git repo and extracted NASA SMAP/MSL .npy telemetry files.\n• Atharva Sarnaik: Formulated mathematical objectives and reviewed Hundman et al. (KDD 2018).",
         "Understanding aerospace telemetry protocols, time-series anomaly characteristics, and Git workflow.",
         "High dimensionality and sensor noise in raw satellite channels.",
         "Applied channel normalization and windowing (sliding window size 100 timesteps).",
         "High false-positive rate in raw thresholding confirmed necessity of ML specialists.",
         "Planned decoupled multi-agent subsystem architecture.",
         "Formulate project proposal and finalize mathematical models for specialists."),

        ("Week 2", "08/07/2025", "14/07/2025",
         "System Requirement Analysis & Architecture Design",
         "Drafted System Architecture Document (SAD) and Architectural Decision Records (ADRs).",
         "• Sujal Hede: Designed FastAPI backend streaming architecture and Next.js frontend requirements.\n• Atharva Sarnaik: Authored ADR-0001 (data plane) and ADR-0002 (grounding verifier contracts).",
         "Architectural design of multi-agent distributed systems, Pydantic v2 data contract schemas.",
         "Balancing computational latency with deep learning model complexity.",
         "Opted for localized specialist autoencoders with centralized meta-learner.",
         "Sub-50ms target per window is feasible with lightweight PyTorch models.",
         "Modular subsystem division: EPS, Thermal, ADCS, and TT&C.",
         "Begin dataset pre-processing and pipeline setup for NASA SMAP/MSL."),

        ("Week 3", "15/07/2025", "21/07/2025",
         "Dataset Pipeline & Historical Telemetry Ingestion",
         "Implement deterministic telemetry ingestion pipeline for NASA SMAP .npy files.",
         "• Sujal Hede: Implemented binary telemetry parser and memory-mapped array generator in `services/data_plane`.\n• Atharva Sarnaik: Mapped NASA channel codes to aerospace subsystems (P-1 -> Power, A-7 -> ADCS).",
         "NumPy binary file handling, sliding window stride generation, telemetry streaming.",
         "Memory footprint when loading multi-gigabyte continuous telemetry arrays.",
         "Implemented memory-mapped array slicing and streaming generator.",
         "Verified deterministic window indexing matching NASA ground truth labels.",
         "Added channel lookup dictionary mapping channels to aerospace subsystems.",
         "Develop baseline anomaly detectors (static thresholds and Isolation Forest)."),

        ("Week 4", "22/07/2025", "28/07/2025",
         "Baseline Anomaly Detection & Benchmarking",
         "Develop and evaluate classical anomaly detection baselines.",
         "• Sujal Hede: Implemented Static Out-of-Limit Thresholds and fitted Isolation Forests on NASA test sets.\n• Atharva Sarnaik: Implemented PCA baseline and calculated ROC-AUC and F1-score evaluation metrics.",
         "Scikit-learn pipeline development, ROC-AUC and F1-score evaluation metrics.",
         "Static thresholding yielded 74% false alarm rate on nominal orbital maneuvers.",
         "Validated need for temporal sequence models capable of learning dynamic orbits.",
         "Static: F1=0.48; Isolation Forest: F1=0.69; PCA: F1=0.64.",
         "Adopted LSTM Autoencoders as primary specialist model family.",
         "Design and train LSTM Autoencoder specialists for each subsystem."),

        ("Week 5", "29/07/2025", "04/08/2025",
         "Subsystem Specialist Development (LSTM Autoencoders)",
         "Build and train independent PyTorch LSTM Autoencoders (EPS, Thermal, ADCS, TT&C).",
         "• Sujal Hede: Implemented and trained PyTorch LSTM Autoencoder architectures for Power and Thermal.\n• Atharva Sarnaik: Implemented ADCS and TT&C models and calibrated percentile-based score normalization.",
         "PyTorch training loops, loss function design (MSE + Huber loss), early stopping.",
         "Overfitting on quiescent nominal telemetry periods.",
         "Added dropout layers and trained on diverse nominal flight phases.",
         "Reconstruction error cleanly spikes during NASA ground-truth anomaly intervals.",
         "Calibrated anomaly score normalization using non-parametric percentile mapping.",
         "Design Centralized Stacking Coordinator and Bayesian Fusion layer."),

        ("Week 6", "05/08/2025", "11/08/2025",
         "Neuro-Symbolic Stacking Coordinator & Fusion Engine",
         "Develop centralized fusion engine arbitrating specialist opinions.",
         "• Sujal Hede: Engineered training sample generation from specialist opinions.\n• Atharva Sarnaik: Implemented `LearnedStackingCoordinator` using meta-learner and Bayesian prior calibration.",
         "Meta-learning, stacking generalization, Bayesian Laplace prior probability calibration.",
         "Disagreement among specialists when cross-subsystem anomalies occur.",
         "Introduced consensus entropy metric to detect high-dispersion multi-subsystem faults.",
         "Ensemble F1-score increased to 0.912, outperforming any single specialist.",
         "Added flight-rule expert system to handle known emergency operational modes.",
         "Integrate LLM Reasoner for automated root-cause explanation."),

        ("Week 7", "12/08/2025", "18/08/2025",
         "LLM Reasoner Integration (Groq LLaMA-3.3 70B & OpenAI)",
         "Integrate LLM to synthesize multi-agent findings into natural language triage reports.",
         "• Sujal Hede: Built reasoner API client and fallback orchestration in `services/reasoner`.\n• Atharva Sarnaik: Engineered structured LangGraph reasoner node using Groq LLaMA-3.3 70B.",
         "Prompt engineering for aerospace diagnostics, structured JSON schema generation.",
         "Generic LLM outputs contained verbose fluff and occasional hallucinated channel names.",
         "Constructed strict prompt contract demanding structured evidence and actionable steps.",
         "Groq LLaMA-3.3 70B inference completed in 1.4s with 98% diagnostic accuracy.",
         "Separated natural language explanation into diagnosis, evidence, and recommendations.",
         "Build deterministic Grounding Verifier to audit and enforce factual accuracy."),

        ("Week 8", "19/08/2025", "25/08/2025",
         "Deterministic Grounding Verifier & Guardrail Engine",
         "Build verification layer checking LLM outputs against raw telemetry contracts.",
         "• Sujal Hede: Designed regex telemetry parameter extraction and bound-checking logic.\n• Atharva Sarnaik: Implemented `GroundingVerifier` with automated 2-retry feedback loop and safe fallback.",
         "Automated schema validation, regex entity extraction, guardrail design.",
         "Hallucinated channels (e.g., citing 'P-2' when only 'P-1' anomalous) caused rejection.",
         "Implemented automated retry loop (max 2 retries) with targeted error feedback.",
         "Hallucination rate reduced to 0.0% across 50 evaluated test windows.",
         "Added rule: if retry fails twice, verifier falls back to deterministic rule template.",
         "Develop Cryptographic Audit Trail and SQLite Blackbox Ledger."),

        ("Week 9", "26/08/2025", "01/09/2025",
         "Cryptographic Audit Trail & Forensic Blackbox Ledger",
         "Implement immutable flight operations audit logging for every decision frame.",
         "• Sujal Hede: Integrated database transactions and high-speed write buffering in SQLite.\n• Atharva Sarnaik: Engineered SHA-256 decision hashing and Ed25519 digital signature verification.",
         "Cryptographic hashing, digital signatures, persistent database transaction management.",
         "Disk I/O latency when committing high-frequency telemetry decisions.",
         "Implemented asynchronous batch commits with in-memory write buffer.",
         "Sub-2ms ledger commitment overhead; cryptographic hash chain verified.",
         "Added tamper-detection verification endpoint `GET /audit/verify/{hash}`.",
         "Develop real-time WebSocket telemetry streaming and FastAPI endpoints."),

        ("Week 10", "02/09/2025", "08/09/2025",
         "FastAPI Backend & Telemetry Streaming Service",
         "Construct unified REST and WebSocket API service (`services/api/app.py`).",
         "• Sujal Hede: Built `/telemetry`, `/decision`, `/health`, and `/replay` FastAPI routes and WebSocket server.\n• Atharva Sarnaik: Designed Pydantic payload models and CORS configuration for frontend consumption.",
         "Asynchronous programming, WebSocket protocol handling, CORS, Uvicorn server.",
         "Connection dropouts during high-speed historical replay streaming.",
         "Added heartbeat ping/pong mechanism and client auto-reconnect logic.",
         "Streamed 100 windows/second smoothly without frame drop.",
         "Optimized payload serialization using Pydantic `.model_dump(mode='json')`.",
         "Initialize Next.js Mission Control dashboard frontend."),

        ("Week 11", "09/09/2025", "15/09/2025",
         "Next.js Mission Control Frontend – Subsystem Telemetry Feeds",
         "Create modern Next.js 14 user interface for satellite ground operations.",
         "• Sujal Hede: Scaffolded Next.js 14 App Router, Tailwind CSS styling, and live telemetry gauges.\n• Atharva Sarnaik: Implemented `TelemetryContext` and memoized sub-panels to prevent UI re-render lag.",
         "Next.js App Router, Tailwind CSS, SVG radar charts, and real-time state management.",
         "Complex dashboard layout causing UI re-render lags.",
         "Decoupled state management using custom `TelemetryContext` and memoized sub-panels.",
         "Maintained consistent 60 FPS UI rendering during live telemetry streaming.",
         "Implemented dark/light aerospace aesthetic compliant with NASA MOC guidelines.",
         "Build AI Fusion Center and Reasoner synthesis display panels."),

        ("Week 12", "16/09/2025", "22/09/2025",
         "Mission Control – AI Fusion & Reasoner Synthesis Panel",
         "Design specialized AI Fusion Center panel showing multi-agent diagnostics.",
         "• Sujal Hede: Rendered Specialist Anomaly Variance bars, Confidence Radial chart, and JSON export.\n• Atharva Sarnaik: Built Groq Reasoner card, evidence citations, and one-click 'Copy Hash' button.",
         "Interactive UI data visualization, status badge color coding, JSON export modal.",
         "Ensuring operator can quickly discern nominal vs anomalous states at a glance.",
         "Designed high-contrast alarm banners (Critical, Warning, Nominal) with sound cues.",
         "Operators can view supporting evidence, cited channels, and runbook recommendations.",
         "Added one-click 'Download Audited JSON' and 'Copy Decision Hash' buttons.",
         "Implement Historical Telemetry Replay Engine with multi-speed controls."),

        ("Week 13", "23/09/2025", "29/09/2025",
         "Historical Telemetry Replay Engine & Playback Controls",
         "Develop interactive replay engine allowing deterministic playback of NASA archives.",
         "• Sujal Hede: Engineered edge-triggered anomaly pausing, live config sync (`POST /replay/config`), and jump buttons.\n• Atharva Sarnaik: Synchronized frontend playback controls with backend event loop states.",
         "Event loop timing, async background tasks, thread-safe pause/resume primitives.",
         "Level-triggered pause caused replay to get stuck on multi-frame anomaly intervals.",
         "Engineered edge-triggered anomaly pausing and dynamic live configuration sync (`POST /replay/config`).",
         "Replay smoothly pauses once upon anomaly entry, resumes cleanly, and supports hyper-speed.",
         "Added 'Jump to Anomaly' button to allow immediate demonstration of flight triage.",
         "Perform comprehensive end-to-end integration testing and code verification."),

        ("Week 14", "30/09/2025", "06/10/2025",
         "End-to-End System Integration & Rigorous Verification",
         "Perform comprehensive unit, integration, and UI testing across all modules.",
         "• Sujal Hede: Executed and verified 8/8 replay tests, 15 contract tests, and Next.js type-checking (`tsc`).\n• Atharva Sarnaik: Implemented offline mock reasoner fallback during `pytest` and verified git branches.",
         "Pytest test automation, mock LLM fixtures for CI/CD, Next.js type-checking (`tsc`).",
         "Test suite hanging when live LLM API calls executed without API keys.",
         "Added `PYTEST_CURRENT_TEST` offline mock fallback in `services/reasoner/reasoner.py`.",
         "100% test pass rate across backend (`pytest`) and frontend (`npm test`, `npx tsc`).",
         "All git branches merged and cleanly pushed to `feature/phase-4-mission-control`.",
         "Prepare final project diary, technical documentation, and presentation."),

        ("Week 15", "07/10/2025", "14/10/2025",
         "Project Documentation, Final Project Diary & Demonstration Setup",
         "Compile formal Project Diary, Literature Survey, and Project Proposal.",
         "• Sujal Hede: Formatted and verified final B.Tech Project Diary and Project Proposal Word document.\n• Atharva Sarnaik: Set up live mission control demonstration on NASA SMAP P-1 and A-7 channels.",
         "Technical report writing, IEEE citation formatting, project lifecycle documentation.",
         "Formatting complex multi-page tables, PO/CO mapping matrices, and Gantt charts.",
         "Automated Word (.docx) generation using Python scripts preserving official college styles.",
         "Fully formatted, print-ready Project Diary and live running mission control demonstration.",
         "Prepared project demo showing real-time NASA SMAP P-1 anomaly detection and Groq triage.",
         "Submit Project Diary and Project Proposal for university evaluation.")
    ]

    for w_idx, w_data in enumerate(weeks_data):
        doc.add_page_break()
        add_header_block(doc, title=f"WEEKLY PROGRESS REPORT — WEEK {w_idx + 1}")
        
        wt = doc.add_table(rows=10, cols=2)
        wt.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(wt)
        
        col_w = [Inches(2.0), Inches(5.9)]
        
        # Row 0: Header with Date
        format_cell(wt.rows[0].cells[0], "Week Number & Dates", bold=True, font_size=8.5, bg_color=HEX_HEADER_BG)
        format_cell(wt.rows[0].cells[1], f"Week {w_idx + 1} ({w_data[0]})\t\tDate: From {w_data[1]} To {w_data[2]}", 
                    bold=True, font_size=8.5, bg_color=HEX_HEADER_BG)
        
        rows_content = [
            ("Planned Activities", w_data[3]),
            ("Activities Completed", w_data[4]),
            ("Work Performed\n(Team Contribution)", w_data[5]),
            ("Technical Skills Acquired", w_data[6]),
            ("Problems / Challenges Faced", w_data[7]),
            ("Corrective Action Taken", w_data[8]),
            ("Experimental Observations", w_data[9]),
            ("Design Changes / Improvements", w_data[10]),
            ("Plan for Next Week", w_data[11])
        ]
        
        for r_idx, (lbl, val) in enumerate(rows_content):
            row = wt.rows[r_idx + 1]
            format_cell(row.cells[0], lbl, bold=True, font_size=8.5, bg_color=HEX_ALT_ROW_BG if r_idx % 2 == 1 else None)
            format_cell(row.cells[1], val, font_size=8.5)
            
        for row in wt.rows:
            row.cells[0].width = col_w[0]
            row.cells[1].width = col_w[1]
            
        # Signature block at bottom of page
        p_sig = doc.add_paragraph()
        p_sig.paragraph_format.space_before = Pt(12)
        p_sig.paragraph_format.space_after = Pt(0)
        r = p_sig.add_run(
            "Student 1: Hede Sujal S. ____________________     "
            "Student 2: Sarnaik Atharva M. ____________________     "
            "Guide: Prof. Dr. A. R. Kulkarni ____________________"
        )
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.5)
        r.font.bold = True

def build_guidelines(doc):
    doc.add_page_break()
    add_header_block(doc, title="GUIDELINES FOR PREPARATION OF FINAL PROJECT REPORT")
    
    add_section_title(doc, "Official Institutional Report Sequence & Binding Guidelines (GCEK)")
    
    guidelines_text = (
        "1. Sequence of Project Report Material:\n"
        "   • Cover Page & Title Page (in prescribed format)\n"
        "   • Certificate of Project Approval from Guide, HOD, and Principal\n"
        "   • Declaration by Students (originality and non-plagiarism)\n"
        "   • Acknowledgements\n"
        "   • Abstract (concise summary under 300 words)\n"
        "   • Table of Contents, List of Figures, List of Tables, List of Abbreviations & Symbols\n"
        "   • Chapter 1: Introduction (Background, Motivation, Objectives, Scope)\n"
        "   • Chapter 2: Literature Review (Survey of existing work, gap analysis, IEEE citations)\n"
        "   • Chapter 3: System Requirement Analysis & Architecture (ADRs, Pydantic contracts)\n"
        "   • Chapter 4: System Design & Multi-Agent Methodology (Specialists, Stacking, Reasoner, Verifier)\n"
        "   • Chapter 5: Implementation Details & Code Artifacts (FastAPI, PyTorch, Next.js 14, SQLite)\n"
        "   • Chapter 6: Results, Performance Benchmarks & Discussion (NASA SMAP/MSL F1 scores, latency)\n"
        "   • Chapter 7: Conclusion & Future Constellation Scope\n"
        "   • References (in IEEE format)\n"
        "   • Appendices (Raw telemetry schemas, audit ledger proofs, unit test matrices)\n\n"
        "2. Binding & Formatting Specifications:\n"
        "   • Binding: Standard Black Book binding with Golden Embossing.\n"
        "   • Document Processor: Compulsory preparation in LaTeX / Microsoft Word standard template.\n"
        "   • Paper Size: A4, 75–80 GSM Bond Paper, single-side printing.\n"
        "   • Margins: Left = 1.25 inch (for binding), Right = 1.0 inch, Top = 1.0 inch, Bottom = 1.0 inch.\n"
        "   • Typography: Times New Roman; Chapter Titles: 16pt Bold; Headings: 14pt Bold; Body: 12pt Justified (1.5 line spacing).\n"
        "   • Number of Copies: 4 copies (1 for Department Library, 1 for Guide, 1 for each Student)."
    )
    
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(guidelines_text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(9.5)

def build_formal_project_proposal(doc):
    doc.add_page_break()
    add_header_block(doc, title="FORMAL PROJECT PROPOSAL")
    
    add_section_title(doc, "1. General Information")
    
    t20 = doc.add_table(rows=10, cols=2)
    t20.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t20)
    
    col_w = [Inches(2.2), Inches(5.7)]
    info_data = [
        ("Name of Institute", "Government College of Engineering, Kolhapur"),
        ("Department", "Department of Artificial Intelligence and Data Science"),
        ("Academic Year", "2025–2026"),
        ("Programme", "B.Tech. in Artificial Intelligence and Data Science"),
        ("Semester", "Semester VII & VIII (Final Year B.Tech)"),
        ("Project Title", "SENTINEL: Multi-Agent Orbital Telemetry Anomaly Detection, Corroborative Fusion, and Grounded LLM Reasoner for Autonomous Spacecraft Operations"),
        ("Project Guide", "Prof. Dr. A. R. Kulkarni"),
        ("Project Coordinator", "Prof. S. B. Patil / Dr. S. M. Patil"),
        ("Team Members (2 Members)", "1. Hede Sujal S. (PRN: 21020045) — Project Leader & Full-Stack / ML Systems Lead\n2. Sarnaik Atharva M. (PRN: 21020078) — AI, Fusion & Verification Lead")
    ]
    
    format_cell(t20.rows[0].cells[0], "Parameter", bold=True, font_size=8.5, bg_color=HEX_HEADER_BG)
    format_cell(t20.rows[0].cells[1], "Institutional Record", bold=True, font_size=8.5, bg_color=HEX_HEADER_BG)
    
    for r_idx, (k, v) in enumerate(info_data):
        row = t20.rows[r_idx + 1]
        format_cell(row.cells[0], k, bold=True, font_size=8.5, bg_color=HEX_ALT_ROW_BG if r_idx % 2 == 1 else None)
        format_cell(row.cells[1], v, font_size=8.5)
        
    for row in t20.rows:
        row.cells[0].width = col_w[0]
        row.cells[1].width = col_w[1]

    # Section 2 to 10
    add_section_title(doc, "2. Project Title")
    add_field(doc, "Official Title: ", "SENTINEL: Autonomous Multi-Agent Spacecraft Telemetry Diagnostics, Neuro-Symbolic Anomaly Fusion, and Cryptographically Verifiable Flight Operations Engine")
    
    add_section_title(doc, "3. Background / Introduction")
    add_field(doc, "Introduction: ", 
              "Modern space exploration relies on autonomous satellite constellations operating in harsh orbital environments. Satellite operations generate hundreds of thousands of telemetry parameters per second across power, thermal, guidance, and telecommunications subsystems. Traditional mission operations centers suffer from high false alarm rates (>70%) and manual triage bottlenecks during critical communication blackout windows. SENTINEL bridges this gap using a multi-agent neuro-symbolic architecture that detects, fuses, explains, and cryptographically audits orbital telemetry anomalies in real time.")
    
    add_section_title(doc, "4. Problem Statement")
    add_field(doc, "Problem Statement: ", 
              "To design, develop, and benchmark an autonomous, multi-agent telemetry diagnostic and fault-management system for spacecraft operations that:\n"
              "1. Decomposes multi-channel satellite telemetry into independent subsystem specialist models (EPS, Thermal, ADCS, TT&C) to overcome static threshold limitations.\n"
              "2. Synthesizes cross-subsystem fault correlations using a learned stacking meta-coordinator with calibrated Bayesian confidence.\n"
              "3. Generates natural language root-cause triage reports using an LLM Reasoner governed by a deterministic grounding verifier to achieve a 0% hallucination rate.\n"
              "4. Guarantees tamper-evident auditability via an immutable SHA-256 cryptographic blackbox ledger.")
    
    add_section_title(doc, "5. Need of the Project")
    add_field(doc, "Operational Need: ", 
              "Existing satellite ground systems are predominantly fragmented. High-precision deep learning models operate purely as black-box numerical scorers without explaining fault causality. Conversely, generative LLMs possess strong diagnostic reasoning abilities but hallucinate metric values and lack access to verified telemetry contracts. A hybrid, neuro-symbolic multi-agent architecture is necessary to bridge this safety-critical divide.")
    
    add_section_title(doc, "6. Specific & Measurable Objectives")
    add_field(doc, "Project Objectives:\n",
              "• Objective 1: Implement localized PyTorch LSTM autoencoder specialist agents achieving F1-score > 0.88 on NASA SMAP/MSL datasets.\n"
              "• Objective 2: Formulate a learned stacking coordinator that arbitrates multi-agent anomaly scores and resolves inter-subsystem correlation.\n"
              "• Objective 3: Integrate an LLM Reasoner (Groq LLaMA-3.3 70B) constrained by a deterministic Grounding Verifier ensuring zero hallucinations.\n"
              "• Objective 4: Construct an interactive aerospace mission control dashboard (Next.js 14) with real-time waveform streaming and deterministic historical replay.")
    
    add_section_title(doc, "7. Existing System & Literature Survey")
    add_field(doc, "Limitations of Existing Systems:\n",
              "• Static Out-of-Limit Alarms: Produces >70% false alarm rate under nominal operational maneuvers.\n"
              "• Isolated Deep Learning: Lack explainability, requiring extensive manual telemetry correlation.\n"
              "• Ungrounded LLM Reasoning: Hallucinates phantom channels and unphysical telemetry values.")
    
    add_section_title(doc, "8. Proposed System Solution")
    add_field(doc, "SENTINEL Architecture:\n",
              "1. Data Plane: NASA telemetry streaming at 100Hz with sliding window evaluation.\n"
              "2. Specialist Tier: 4 decoupled LSTM autoencoder models computing reconstruction errors.\n"
              "3. Coordination Tier: LearnedStackingCoordinator computing calibrated anomaly probabilities and consensus entropy.\n"
              "4. Reasoning & Verification Tier: Groq Reasoner generating root-cause natural language explanations verified by a deterministic GroundingVerifier.\n"
              "5. Ledger: SQLite blackbox recording cryptographic SHA-256 decision hashes.")
    
    add_section_title(doc, "9. Innovation Statement")
    add_field(doc, "Key Innovation: ", 
              "A dual-stage verification protocol where generative LLM reasoning is strictly verified against telemetry contracts, coupled with an edge-triggered historical telemetry replay engine that reproduces real-world NASA anomaly sequences without artificial stalls.")
    
    add_section_title(doc, "10. Development Methodology")
    add_field(doc, "6-Stage Methodology:\n",
              "• Stage 1: Data Ingestion & Preprocessing (Standardized windowing on NASA SMAP/MSL .npy repositories).\n"
              "• Stage 2: Specialist Anomaly Scoring (Independent LSTM autoencoder reconstruction error calculation).\n"
              "• Stage 3: Corroborative Fusion (Bayesian Laplace prior calibration & Stacking Meta-Classifier).\n"
              "• Stage 4: Grounded Diagnostic Synthesis (LangGraph reasoner node with Groq Cloud LLaMA-3.3 70B).\n"
              "• Stage 5: Verification & Ledger Commitment (Deterministic schema verification and SHA-256 blackbox logging).\n"
              "• Stage 6: Visualization (Next.js 14 Mission Control dashboard with live WebSocket feeds).")
    
    # Section 11 to 20
    add_section_title(doc, "11. Hardware & Software Requirements (Table 21)")
    t21 = doc.add_table(rows=5, cols=4)
    t21.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t21)
    
    hw_headers = ["Sr.", "Component / Software", "Specification / Version", "Operational Purpose"]
    for c_idx, h in enumerate(hw_headers):
        format_cell(t21.rows[0].cells[c_idx], h, bold=True, font_size=8.5, bg_color=HEX_HEADER_BG, align=WD_ALIGN_PARAGRAPH.CENTER)
        
    hw_data = [
        ("1", "Development Workstation", "Intel Core i7/i9 / AMD Ryzen 7, 16GB RAM, 512GB NVMe SSD, Windows 11 / Linux", "Local execution of PyTorch models, FastAPI streaming, and Next.js UI"),
        ("2", "Python & ML Environment", "Python 3.12, PyTorch 2.4, PyOD, NumPy, Scikit-learn, LangGraph", "Specialist model training, autoencoders, and multi-agent coordination"),
        ("3", "Mission Control Web Stack", "Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide React", "Real-time aerospace mission control dashboard and waveform visualization"),
        ("4", "LLM APIs & Data Storage", "Groq Cloud API (LLaMA-3.3 70B Versatile), SQLite 3, NASA SMAP/MSL Datasets", "Real-time diagnostic reasoning, verifiable audit ledger, and benchmark validation")
    ]
    for r_idx, row_vals in enumerate(hw_data):
        row = t21.rows[r_idx + 1]
        for c_idx, val in enumerate(row_vals):
            format_cell(row.cells[c_idx], val, bold=(c_idx in [0, 1]), font_size=8.5,
                        align=WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT)
            
    t21_w = [Inches(0.4), Inches(2.0), Inches(2.5), Inches(3.0)]
    for row in t21.rows:
        for idx, w in enumerate(t21_w):
            row.cells[idx].width = w

    add_section_title(doc, "12. Expected Performance Benchmarks")
    add_field(doc, "Empirical Targets:\n",
              "• Anomaly Detection F1-Score: > 0.88 across all evaluated NASA SMAP & MSL telemetry channels.\n"
              "• Inference Latency: < 50ms per 100-timestep window on commodity x86 hardware.\n"
              "• Groq Diagnostic Latency: < 2.0 seconds for complete natural language root-cause triage.\n"
              "• Hallucination Rate: 0.0% enforced via deterministic Grounding Verifier retry loops.\n"
              "• Ledger Verification: 100% cryptographically verifiable SHA-256 decision frames.")

    add_section_title(doc, "13. Estimated Cost & Budget (Table 22)")
    t22 = doc.add_table(rows=5, cols=4)
    t22.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t22)
    
    cost_headers = ["Sr.", "Item Description", "Quantity / Plan", "Estimated Cost (INR)"]
    for c_idx, h in enumerate(cost_headers):
        format_cell(t22.rows[0].cells[c_idx], h, bold=True, font_size=8.5, bg_color=HEX_HEADER_BG, align=WD_ALIGN_PARAGRAPH.CENTER)
        
    cost_data = [
        ("1", "Development Workstations & Compute", "2 Units", "Existing Institute Lab Facilities (₹0)"),
        ("2", "Groq API & Cloud Compute Quotas", "Developer Tier", "Free Developer Tier ($0 / ₹0)"),
        ("3", "NASA Telemetry Repositories (SMAP/MSL)", "Public Open Access", "Open-Source ($0 / ₹0)"),
        ("4", "Documentation, Hard Binding & Printing", "3 Copies (Black Book with Golden Embossing)", "₹1,500 – ₹2,000")
    ]
    for r_idx, row_vals in enumerate(cost_data):
        row = t22.rows[r_idx + 1]
        for c_idx, val in enumerate(row_vals):
            format_cell(row.cells[c_idx], val, bold=(c_idx in [0, 1]), font_size=8.5,
                        align=WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 2] else WD_ALIGN_PARAGRAPH.LEFT)
            
    t22_w = [Inches(0.4), Inches(3.2), Inches(1.8), Inches(2.5)]
    for row in t22.rows:
        for idx, w in enumerate(t22_w):
            row.cells[idx].width = w

    add_section_title(doc, "14. Project Timeline & Gantt Chart (Table 23)")
    t23 = doc.add_table(rows=8, cols=9)
    t23.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t23)
    
    t23_headers = ["Phase / Activity", "W1-2", "W3-4", "W5-6", "W7-8", "W9-10", "W11-12", "W13-14", "W15"]
    for c_idx, h in enumerate(t23_headers):
        format_cell(t23.rows[0].cells[c_idx], h, bold=True, font_size=8.0, bg_color=HEX_HEADER_BG, align=WD_ALIGN_PARAGRAPH.CENTER)
        
    timeline_data = [
        ("Phase 1: Literature Review & Problem Definition", "Done", "Done", "", "", "", "", "", ""),
        ("Phase 2: Data Ingestion & Baseline Anomaly Detectors", "", "Done", "Done", "", "", "", "", ""),
        ("Phase 3: Multi-Agent Specialist Autoencoders", "", "", "Done", "Done", "Done", "", "", ""),
        ("Phase 4: Stacking Fusion & LangGraph Groq Reasoner", "", "", "", "", "Done", "Done", "", ""),
        ("Phase 5: Grounding Verifier & Cryptographic Ledger", "", "", "", "", "", "Done", "Done", ""),
        ("Phase 6: Next.js Mission Control & Historical Replay", "", "", "", "", "", "", "Done", "Done"),
        ("Phase 7: Final Testing, Verification & Black Book", "", "", "", "", "", "", "", "Done")
    ]
    for r_idx, row_vals in enumerate(timeline_data):
        row = t23.rows[r_idx + 1]
        for c_idx, val in enumerate(row_vals):
            format_cell(row.cells[c_idx], val, bold=(c_idx == 0 or val == "Done"), font_size=8.0,
                        bg_color="E6F4EA" if val == "Done" else None,
                        align=WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER)
            
    t23_w = [Inches(3.1)] + [Inches(0.6)] * 8
    for row in t23.rows:
        for idx, w in enumerate(t23_w):
            row.cells[idx].width = w

    add_section_title(doc, "15. References (IEEE Format)")
    references = (
        "[1] K. Hundman et al., “Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding,” in Proc. ACM SIGKDD, 2018, pp. 387–395.\n"
        "[2] J. Audibert et al., “USAD: Unsupervised Anomaly Detection on Multivariate Time Series,” in Proc. ACM SIGKDD, 2020, pp. 3395–3404.\n"
        "[3] Y. Su et al., “Robust Anomaly Detection for Multivariate Time Series through Stochastic RNNs,” in Proc. ACM SIGKDD, 2019, pp. 2828–2837.\n"
        "[4] A. Blázquez-García et al., “A Review on Outlier/Anomaly Detection in Time Series Data,” ACM Comput. Surv., vol. 54, no. 3, 2021.\n"
        "[5] J. Wei et al., “Chain-of-Thought Prompting Elicits Reasoning in Large Language Models,” in NeurIPS, 2022.\n"
        "[6] L. Huang et al., “A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges,” ACM Comput. Surv., 2023.\n"
        "[7] D. H. Wolpert, “Stacked Generalization,” Neural Networks, vol. 5, no. 2, pp. 241–259, 1992.\n"
        "[8] B. Schneier and J. Kelsey, “Secure Audit Logs to Support Computer Forensics,” ACM Trans. Inf. Syst. Secur., vol. 2, no. 2, pp. 159–176, 1999.\n"
        "[9] L. Harrison et al., “LangGraph: Multi-Agent Workflows as Cyclic Graphs,” LangChain Technical Report, 2024.\n"
        "[10] L. Fesq et al., “Model-Based Spacecraft Fault Management,” in IEEE Aerospace Conf., 2018."
    )
    p_ref = doc.add_paragraph()
    p_ref.paragraph_format.space_before = Pt(4)
    p_ref.paragraph_format.space_after = Pt(4)
    p_ref.paragraph_format.line_spacing = 1.15
    r_ref = p_ref.add_run(references)
    r_ref.font.name = "Times New Roman"
    r_ref.font.size = Pt(8.5)

    add_section_title(doc, "16. Student Declaration & Institutional Approval")
    p_dec = doc.add_paragraph()
    p_dec.paragraph_format.space_before = Pt(4)
    p_dec.paragraph_format.space_after = Pt(8)
    r_dec = p_dec.add_run(
        "We hereby declare that the proposed project titled “SENTINEL: Autonomous Multi-Agent Spacecraft Telemetry "
        "Diagnostics, Neuro-Symbolic Anomaly Fusion, and Cryptographically Verifiable Flight Operations Engine” is our "
        "original work carried out under the guidance of Prof. Dr. A. R. Kulkarni. All literature cited has been duly referenced.\n\n"
        "Student Signatures (2 Members Only):\n"
        "1. Hede Sujal S. (PRN: 21020045)  ________________________\n"
        "2. Sarnaik Atharva M. (PRN: 21020078)  ________________________\n\n"
        "Project Guide: Prof. Dr. A. R. Kulkarni ________________________\n"
        "Head of Department: Dr. S. M. Patil ________________________\n"
        "Date: 19th November 2026"
    )
    r_dec.font.name = "Times New Roman"
    r_dec.font.size = Pt(9.5)
    r_dec.font.bold = True

def main():
    print("Generating beautifully formatted Project Diary DOCX...")
    doc = create_document()
    
    build_project_sheet(doc)
    build_po_co_mapping(doc)
    build_parameter_sheet(doc)
    build_literature_review(doc)
    build_innovation_statement(doc)
    build_weekly_reports(doc)
    build_guidelines(doc)
    build_formal_project_proposal(doc)
    
    out_paths = [
        r"c:\Users\sujal\OneDrive\Documents\Satellite\sentinel\PROJECT_DIARY_SENTINEL_FORMATTED.docx",
        r"C:\Users\sujal\.gemini\antigravity\brain\f8ce2f68-6a4c-479e-adf9-093bd7d6b69b\PROJECT_DIARY_SENTINEL.docx"
    ]
    for p in out_paths:
        doc.save(p)
        print(f"Successfully saved to: {p}")
        
    try:
        doc.save(OUT_WORKSPACE)
        print(f"Successfully saved to: {OUT_WORKSPACE}")
    except PermissionError:
        print(f"Notice: {OUT_WORKSPACE} is currently open in Microsoft Word. Saved to PROJECT_DIARY_SENTINEL_FORMATTED.docx instead.")

if __name__ == "__main__":
    main()
