from pathlib import Path
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import cv2
from PIL import Image

def detect_pages_in_image(image_path: Path):
    img = cv2.imread(str(image_path))
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 1000]
    if not boxes:
        return []
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    if len(boxes) == 1:
        x, y, bw, bh = boxes[0]
        if bw > w * 0.8 and bh > h * 0.8:
            return [(0, 0, w, h)]
    return boxes

def split_image_into_pages(image_path: Path, output_dir: Path) -> list:
    pages = detect_pages_in_image(image_path)
    if not pages:
        return []
    img = cv2.imread(str(image_path))
    created = []
    for i, (x, y, bw, bh) in enumerate(pages):
        page_img = img[y:y+bh, x:x+bw]
        out_path = output_dir / f"{image_path.stem}_page_{i+1}.png"
        cv2.imwrite(str(out_path), page_img)
        created.append(out_path)
    return created

def ocr_image(image_path: Path, output_txt: Path):
    text = pytesseract.image_to_string(Image.open(image_path), lang='por')
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(text)

def process_pdf(input_pdf: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(input_pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        if total_pages == 0:
            print("PDF vazio.")
            return
        if total_pages > 1:
            print(f"PDF com {total_pages} páginas – processando cada página.")
            for i in range(total_pages):
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[i])
                temp_pdf = output_dir / f"{input_pdf.stem}_page_{i+1}.pdf"
                with open(temp_pdf, 'wb') as out:
                    writer.write(out)
                ocr_pdf(temp_pdf, output_dir / f"{input_pdf.stem}_page_{i+1}.txt")
            return
    images = convert_from_path(str(input_pdf), dpi=300)
    if not images:
        print("Falha na conversão para imagem.")
        return
    temp_img = output_dir / f"{input_pdf.stem}_temp.png"
    images[0].save(str(temp_img), "PNG")
    page_images = split_image_into_pages(temp_img, output_dir)
    if page_images:
        print(f"Detectadas {len(page_images)} sub‑páginas.")
        for p in page_images:
            ocr_image(p, output_dir / f"{p.stem}.txt")
        temp_img.unlink()
    else:
        print("Não foi possível detectar sub‑páginas – OCR na imagem inteira.")
        ocr_image(temp_img, output_dir / f"{input_pdf.stem}.txt")
        temp_img.unlink()

def ocr_pdf(pdf_path: Path, output_txt: Path):
    images = convert_from_path(str(pdf_path), dpi=300)
    text = ""
    for i, img in enumerate(images):
        text += f"\n\n--- PAGE {i+1} ---\n\n"
        text += pytesseract.image_to_string(img, lang='por')
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(text)