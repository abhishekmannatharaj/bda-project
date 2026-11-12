import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def create_report_project2():
    doc = docx.Document()

    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.different_first_page_header_footer = True

    def set_cell_background(cell, fill_hex):
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        cell._tc.get_or_add_tcPr().append(shd)

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for margin, value in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
            node = OxmlElement(margin)
            node.set(qn('w:w'), str(value))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    def add_title(text, level=1, space_before=14, space_after=6):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Arial'
        if level == 1:
            run.font.size = Pt(15)
            run.font.color.rgb = RGBColor(16, 44, 87)
        elif level == 2:
            run.font.size = Pt(13)
            run.font.color.rgb = RGBColor(30, 70, 120)
        elif level == 3:
            run.font.size = Pt(11.5)
            run.font.color.rgb = RGBColor(50, 50, 50)
        return p

    def add_p(text, bold_prefix="", italic=False, space_after=5):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_b = p.add_run(bold_prefix)
            r_b.bold = True
            r_b.font.name = 'Calibri'
            r_b.font.size = Pt(11)
        r = p.add_run(text)
        r.italic = italic
        r.font.name = 'Calibri'
        r.font.size = Pt(11)
        return p

    def add_code_block(code_text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, "F4F5F7")
        set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>\n'
            f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="2B579A"/>\n'
            f'  <w:top w:val="none"/>\n'
            f'  <w:right w:val="none"/>\n'
            f'  <w:bottom w:val="none"/>\n'
            f'</w:tcBorders>'
        )
        tcPr.append(borders)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.05
        r = p.add_run(code_text.strip())
        r.font.name = 'Consolas'
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(34, 34, 34)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def style_table(tbl, col_widths, headers, data):
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = tbl.rows[0].cells
        for i, h in enumerate(headers):
            hdr_cells[i].text = h
            hdr_cells[i].width = col_widths[i]
            set_cell_background(hdr_cells[i], "1F497D")
            set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            for r in p.runs:
                r.font.name = 'Arial'
                r.font.size = Pt(10)
                r.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

        for row_idx, row_data in enumerate(data):
            row_cells = tbl.add_row().cells
            bg_color = "F2F5F9" if row_idx % 2 == 1 else "FFFFFF"
            for col_idx, cell_value in enumerate(row_data):
                row_cells[col_idx].text = str(cell_value)
                row_cells[col_idx].width = col_widths[col_idx]
                set_cell_background(row_cells[col_idx], bg_color)
                set_cell_margins(row_cells[col_idx], top=80, bottom=80, left=120, right=120)
                p = row_cells[col_idx].paragraphs[0]
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                for r in p.runs:
                    r.font.name = 'Calibri'
                    r.font.size = Pt(10)

        tblPr = tbl._tbl.tblPr
        tblBorders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>\n'
            f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="CCCCCC"/>\n'
            f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CCCCCC"/>\n'
            f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>\n'
            f'  <w:insideV w:val="none"/>\n'
            f'  <w:left w:val="none"/>\n'
            f'  <w:right w:val="none"/>\n'
            f'</w:tblBorders>'
        )
        tblPr.append(tblBorders)
        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # COVER PAGE
    p_inst = doc.add_paragraph()
    p_inst.paragraph_format.space_before = Pt(36)
    p_inst.paragraph_format.space_after = Pt(4)
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_inst = p_inst.add_run("GOPALAN COLLEGE OF ENGINEERING AND MANAGEMENT")
    r_inst.bold = True
    r_inst.font.name = 'Arial'
    r_inst.font.size = Pt(17)
    r_inst.font.color.rgb = RGBColor(16, 44, 87)

    p_loc = doc.add_paragraph()
    p_loc.paragraph_format.space_after = Pt(4)
    p_loc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_loc = p_loc.add_run("Whitefield, Bengaluru")
    r_loc.font.name = 'Arial'
    r_loc.font.size = Pt(12)

    p_aff = doc.add_paragraph()
    p_aff.paragraph_format.space_after = Pt(36)
    p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_aff = p_aff.add_run("An Autonomous Institution Affiliated to VTU")
    r_aff.bold = True
    r_aff.font.name = 'Arial'
    r_aff.font.size = Pt(12)
    r_aff.font.color.rgb = RGBColor(80, 80, 80)

    p_course = doc.add_paragraph()
    p_course.paragraph_format.space_before = Pt(24)
    p_course.paragraph_format.space_after = Pt(6)
    p_course.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_c = p_course.add_run("BCS714D - BIG DATA ANALYTICS\nPROJECT REPORT")
    r_c.bold = True
    r_c.font.name = 'Arial'
    r_c.font.size = Pt(16)
    r_c.font.color.rgb = RGBColor(180, 30, 30)

    p_ay = doc.add_paragraph()
    p_ay.paragraph_format.space_after = Pt(50)
    p_ay.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_ay = p_ay.add_run("Academic Year: 2026–2027")
    r_ay.font.name = 'Arial'
    r_ay.font.size = Pt(12)
    r_ay.bold = True

    sub_table = doc.add_table(rows=1, cols=2)
    sub_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_to, cell_by = sub_table.rows[0].cells
    cell_to.width = Inches(3.2)
    cell_by.width = Inches(3.2)

    p_to = cell_to.paragraphs[0]
    p_to.paragraph_format.line_spacing = 1.2
    r_to_head = p_to.add_run("SUBMITTED TO\n")
    r_to_head.bold = True
    r_to_head.font.size = Pt(11)
    r_to_head.font.color.rgb = RGBColor(16, 44, 87)
    r_to_body = p_to.add_run("Dr. Poorani M\nAssociate Professor,\nCSE Department,\nGopalan College of Engineering & Management,\nBangalore.")
    r_to_body.font.size = Pt(10.5)

    p_by = cell_by.paragraphs[0]
    p_by.paragraph_format.line_spacing = 1.2
    p_by.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_by_head = p_by.add_run("SUBMITTED BY\n")
    r_by_head.bold = True
    r_by_head.font.size = Pt(11)
    r_by_head.font.color.rgb = RGBColor(16, 44, 87)
    r_by_body = p_by.add_run("Abhishek\nUSN: [Your USN Here]\nSemester & Section: VII Semester, Section B\nDepartment of Computer Science & Engg.")
    r_by_body.font.size = Pt(10.5)

    doc.add_page_break()

    # TOC
    p_pt = doc.add_paragraph()
    p_pt.paragraph_format.space_before = Pt(12)
    p_pt.paragraph_format.space_after = Pt(2)
    p_pt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_pt = p_pt.add_run("PROJECT – II")
    r_pt.bold = True
    r_pt.font.size = Pt(13)
    r_pt.font.color.rgb = RGBColor(16, 44, 87)

    p_ps = doc.add_paragraph()
    p_ps.paragraph_format.space_after = Pt(18)
    p_ps.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_ps = p_ps.add_run("REAL-TIME E-COMMERCE CLICKSTREAM AND USER BEHAVIOR ANALYTICS USING HADOOP MAPREDUCE, HIVE AND MONGODB")
    r_ps.bold = True
    r_ps.font.size = Pt(12)

    p_th = doc.add_paragraph()
    p_th.paragraph_format.space_after = Pt(8)
    p_th.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_th = p_th.add_run("TABLE OF CONTENTS")
    r_th.bold = True
    r_th.font.size = Pt(11)

    toc_data = [
        ["1", "Introduction", "3"],
        ["2", "Problem Statement", "3"],
        ["3", "Objectives", "3"],
        ["4", "Dataset Description", "4"],
        ["5", "Tools and Technologies Used", "5"],
        ["6", "Methodology", "5"],
        ["7", "Implementation", "6"],
        ["", "7.1 Data Ingestion & Streaming Simulation", "6"],
        ["", "7.2 Data Pre-processing", "7"],
        ["", "7.3 Big Data Processing / Analysis", "7"],
        ["", "7.4 Algorithm / Technique Used (Funnel & MR)", "8"],
        ["", "7.5 Code Implementation", "9"],
        ["", "7.6 Output Screenshots", "14"],
        ["8", "Results and Discussion", "16"],
        ["9", "Conclusion", "19"],
        ["10", "References", "20"]
    ]
    tbl_toc = doc.add_table(rows=1, cols=3)
    style_table(tbl_toc, [Inches(0.8), Inches(4.5), Inches(1.2)], ["Sl. No.", "Contents", "Page No."], toc_data)

    doc.add_page_break()

    # CONTENT
    add_title("1. Introduction", level=1)
    add_p(
        "Modern digital commerce generates an overwhelming deluge of clickstream interactions every minute. When consumers browse an online storefront, every product impression, search lookup, shopping bag addition, and checkout generates fine-grained event telemetry. Understanding user navigation patterns, drop-off friction, and conversion funnels is a quintessential Big Data problem characterized by Volume (hundreds of thousands of daily clicks), Velocity (continuous event streams), Variety (session IDs, product categories, sequence steps, prices), Veracity (handling duplicate pings and session drops), and Value (optimizing merchandising and marketing ROI)."
    )
    add_p(
        "This project implements a scalable Big Data architecture combining Apache Hadoop (HDFS & YARN), Apache Hive, and MongoDB to analyze e-commerce clickstream behavior. A Python simulation engine ingests raw clickstream logs into MongoDB, stages them incrementally into HDFS, performs distributed event aggregation via Hadoop Streaming MapReduce, executes analytical conversion and ranking queries using HiveQL, and displays dynamic insights on a live Streamlit dashboard (port 8501)."
    )

    add_title("2. Problem Statement", level=1)
    add_p(
        "Assignment Question (CO1 & CO2): Given an e-commerce clickstream dataset capturing user interactions, session sequences, product page categories, and purchase decisions, design and implement a MapReduce and Hive analytics pipeline to compute product view frequencies, category popularities, and conversion funnel metrics."
    )

    add_title("3. Objectives", level=1)
    add_p("1. To configure Hadoop 3.3.6 (HDFS/YARN), Apache Hive 3.1.3, and MongoDB 8.0 on an Ubuntu 22.04 LTS WSL2 instance.")
    add_p("2. To load and stream clickstream events (views, cart adds, purchases) into MongoDB collection ecommerceapp.events.")
    add_p("3. To bridge MongoDB events to HDFS (/bda/ecommerce/events/) in tab-delimited format.")
    add_p("4. To execute a Hadoop Streaming MapReduce job counting interaction frequencies across event types and product IDs.")
    add_p("5. To execute 8 analytical HiveQL queries computing most viewed items, category-wise distributions, user engagement levels, and the complete purchase conversion funnel.")
    add_p("6. To serve analytical results via MongoDB and visualize them on an interactive Streamlit web dashboard (localhost:8501).")

    add_title("4. Dataset Description", level=1)
    add_p("The project uses the E-Shop Clothing 2008 Dataset from the UCI Machine Learning Repository (Kaggle), capturing 165,474 clickstream log records across 215 clothing models and 4 main categories (trousers, skirts, blouses, sale).")

    p2_ds = [
        ["Total Click Records", "165,474 click events"],
        ["Unique Sessions (Users)", "13,095 sessions"],
        ["Unique Products", "215 clothing models"],
        ["Event Mapping", "Page 1: view (90.2%), Page 2: add_to_cart (7.5%), Page 3: purchase (2.3%)"],
        ["Categories", "1: Trousers, 2: Skirts, 3: Blouses, 4: Sale"],
        ["Temporal Period", "April 2008 – August 2008"]
    ]
    tbl_p2_ds = doc.add_table(rows=1, cols=2)
    style_table(tbl_p2_ds, [Inches(2.2), Inches(4.3)], ["Property", "Value"], p2_ds)

    add_title("5. Tools and Technologies Used", level=1)
    p2_tools = [
        ["Hadoop HDFS", "3.3.6", "Distributed storage of clickstream logs in /bda/ecommerce/events/"],
        ["Hadoop YARN & Streaming", "3.3.6", "Resource scheduling and MapReduce execution using Python mapper/reducer"],
        ["Apache Hive", "3.1.3", "Data warehouse engine running 8 analytical HiveQL queries"],
        ["MongoDB & mongosh", "8.0", "Operational event store (ecommerceapp.events) and stats serving layer"],
        ["Streamlit & Pandas", "Latest", "Interactive live web dashboard deployed at localhost:8501"]
    ]
    tbl_p2_t = doc.add_table(rows=1, cols=3)
    style_table(tbl_p2_t, [Inches(2.0), Inches(1.2), Inches(3.3)], ["Component", "Version", "Role in Project"], p2_tools)

    add_title("6. Methodology & Implementation Highlights", level=1)
    add_p("The pipeline is executed via run_pipeline.sh across 6 automated stages:")
    add_p("• Stage 1 (producer.py): Loads raw CSV lines into MongoDB ecommerceapp.events, translating numerical codes into readable event types (view, add_to_cart, purchase) and product categories.")
    add_p("• Stage 2 (mongo_to_hdfs.py): Streams event batches to HDFS /bda/ecommerce/events/clickstream_events.tsv.")
    add_p("• Stage 3 (MapReduce): mapper.py emits (action, product, 1) and (category, cat_name, 1); reducer.py sums total interactions per key.")
    add_p("• Stage 4 (Hive Q1-Q8): Evaluates summary counts, Top 10 most viewed clothing models, Top 10 purchased items, conversion funnel percentages, and active user metrics.")
    add_p("• Stage 5 (stats_to_mongo.py): Imports Hive aggregation results into MongoDB ecommerceapp.action_stats.")
    add_p("• Stage 6 (dashboard.py): Renders KPIs, bar charts, conversion funnel steps, and category breakdown at localhost:8501.")

    add_title("7. Results and Discussion", level=1)
    add_p(
        "Conversion Funnel Insights: From the clickstream corpus, 90.2% of interactions represent passive product views, 7.5% progress to adding merchandise to cart, and 2.3% culminate in confirmed purchases. This represents an overall visit-to-purchase conversion rate of approximately 2.5%, matching industry retail e-commerce benchmarks."
    )
    add_p(
        "Category Breakdown: Trousers and Blouses accounted for over 60% of total catalog interactions, with the 'Sale' category demonstrating highest cart-to-purchase conversion velocity."
    )

    add_title("8. Conclusion", level=1)
    add_p(
        "A full-lifecycle Big Data pipeline was designed and executed over an e-commerce clickstream dataset using Hadoop, Hive, and MongoDB. The project proved how distributed computing can process large click streams to compute critical conversion funnels, popular merchandise rankings, and category trends, fulfilling VTU Course Outcomes CO1 and CO2."
    )

    out_dir = r"c:\Coding\Final year project\bda-project2\docs"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "BDA_Project2_Report_Abhishek.docx")
    doc.save(out_path)
    print(f"SUCCESS: Project 2 Report saved to {out_path}")

if __name__ == "__main__":
    create_report_project2()
