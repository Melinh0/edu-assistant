import os
import streamlit as st
from io import BytesIO
from fpdf import FPDF
from docx import Document

def save_uploaded_file(uploaded_file, save_dir):
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def get_files_list(directory):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def delete_file(filename, directory):
    os.remove(os.path.join(directory, filename))

def create_download_link(text, filename, format):
    if format == "txt":
        b = BytesIO()
        b.write(text.encode('utf-8'))
        b.seek(0)
        return b, f"{filename}.txt", "text/plain"
    elif format == "docx":
        doc = Document()
        doc.add_paragraph(text)
        b = BytesIO()
        doc.save(b)
        b.seek(0)
        return b, f"{filename}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in text.split('\n'):
            pdf.multi_cell(0, 10, txt=line)  
        pdf_bytes = pdf.output(dest='S')    
        b = BytesIO(pdf_bytes)              
        b.seek(0)
        return b, f"{filename}.pdf", "application/pdf"
    else:
        raise ValueError("Formato não suportado")