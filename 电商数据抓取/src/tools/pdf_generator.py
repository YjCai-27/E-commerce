from fpdf import FPDF
import re
from datetime import datetime
import os

def clean_text_for_pdf(text):
    """过滤掉PDF不能显示的特殊字符"""
    # 替换特殊字符
    text = text.replace("'", " ")
    text = text.replace('"', " ")
    text = text.replace('"', " ")
    text = text.replace('–', "-")
    text = text.replace('—', "-")
    text = text.replace('’', " ")
    text = text.replace('‘', " ")
    text = text.replace('“', " ")
    text = text.replace('”', " ")
    text = text.replace('…', "...")
    text = text.replace('\u200b', "")
    text = text.replace('\ufeff', "")
    # 截断过长的产品名称，避免表格宽度问题
    if len(text) > 50:
        text = text[:47] + "..."
    # 移除surrogate和其他不可打印字符
    return text.encode('utf-8', 'ignore').decode('utf-8')

def generate_pdf_report(report_content: str, output_path: str) -> str:
    """
    生成PDF格式的选品报告，支持中文

    Args:
        report_content: Markdown格式的报告内容
        output_path: 输出文件路径

    Returns:
        PDF文件路径
    """
    # 创建PDF
    pdf = FPDF()
    pdf.add_page()

    # 尝试加载中文字体
    loaded_font = None
    # Windows系统字体路径
    windows_fonts = [
        ("msyh", "C:/Windows/Fonts/msyh.ttc"),
        ("simsun", "C:/Windows/Fonts/simsun.ttc"),
        ("simhei", "C:/Windows/Fonts/simhei.ttf"),
    ]

    for font_name, font_path in windows_fonts:
        if os.path.exists(font_path):
            try:
                pdf.add_font(font_name, "", font_path, uni=True)
                pdf.set_font(font_name, "", 12)
                loaded_font = font_name
                break
            except Exception:
                continue

    if not loaded_font:
        pdf.set_font('Arial', '', 12)

    # 添加标题
    if loaded_font:
        pdf.set_font(loaded_font, "", 15)
    pdf.cell(0, 10, clean_text_for_pdf('Amazon选品分析报告'), 0, 1, 'C')
    date_str = datetime.now().strftime("%Y-%m-%d")
    if loaded_font:
        pdf.set_font(loaded_font, "", 10)
    pdf.cell(0, 10, clean_text_for_pdf(f'生成日期: {date_str}'), 0, 1, 'R')
    pdf.ln(5)

    if loaded_font:
        pdf.set_font(loaded_font, "", 12)

    # 解析Markdown
    lines = report_content.split('\n')

    for line in lines:
        line = clean_text_for_pdf(line.strip())
        if not line:
            pdf.ln(5)
            continue

        # 跳过表格分隔线 (|------|----------|...)
        if '---' in line or all(c == '-' for c in line.replace('|', '')):
            continue

        # 处理标题
        if line.startswith('# '):
            if loaded_font:
                pdf.set_font(loaded_font, "", 18)
            content = line[2:]
            pdf.cell(0, 10, content, 0, 1)
            pdf.ln(3)
            if loaded_font:
                pdf.set_font(loaded_font, "", 12)
        elif line.startswith('## '):
            if loaded_font:
                pdf.set_font(loaded_font, "", 16)
            content = line[3:]
            pdf.cell(0, 10, content, 0, 1)
            pdf.ln(3)
            if loaded_font:
                pdf.set_font(loaded_font, "", 12)
        elif line.startswith('### '):
            if loaded_font:
                pdf.set_font(loaded_font, "", 14)
            content = line[4:]
            pdf.cell(0, 10, content, 0, 1)
            pdf.ln(3)
            if loaded_font:
                pdf.set_font(loaded_font, "", 12)
        # 处理表格
        elif '|' in line:
            # 表格行
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) > 0:
                # 对推荐产品表格，给产品名称列分配更多宽度
                if len(cells) == 9 and '排名' in cells[0]:
                    # 表头: | 排名 | 产品名称 | 价格$ | 评论数 | 竞争度 | 预估月销 | 单台利润$ | 总分 | 推荐等级 |
                    # 自定义列宽分配，产品名称列更宽
                    col_widths = [12, 60, 16, 16, 16, 20, 22, 14, 14]
                elif len(cells) == 9:
                    col_widths = [12, 60, 16, 16, 16, 20, 22, 14, 14]
                else:
                    # 平均分配，确保最小宽度不小于8
                    avg_width = max(8, 190 // len(cells))
                    col_widths = [avg_width] * len(cells)
                for cell, width in zip(cells, col_widths):
                    cleaned_cell = clean_text_for_pdf(cell)
                    try:
                        pdf.cell(width, 8, cleaned_cell, 1, 0, 'C')
                    except Exception:
                        # 如果出错，尝试截断
                        while len(cleaned_cell) > 0 and cleaned_cell:
                            cleaned_cell = cleaned_cell[:-1]
                            try:
                                pdf.cell(width, 8, cleaned_cell + '...', 1, 0, 'C')
                                break
                            except Exception:
                                pass
                pdf.ln(8)
        # 处理列表
        elif line.startswith('- ') or line.startswith('* '):
            content = f"* {line[2:]}"
            # 移除markdown加粗符号
            content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
            content = re.sub(r'\*(.*?)\*', r'\1', content)
            # 逐行打印避免超长
            try:
                pdf.multi_cell(0, 6, content)
            except Exception:
                pdf.ln(6)
        # 普通文本
        else:
            # 移除markdown加粗符号
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            line = re.sub(r'\*(.*?)\*', r'\1', line)
            if line.strip():
                try:
                    pdf.multi_cell(0, 6, line)
                except Exception:
                    pdf.ln(6)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 保存PDF
    pdf.output(output_path)
    return output_path
