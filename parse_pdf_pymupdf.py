import pymupdf
import os


def pymupdf_parse_pdf_to_text(pdf_path, output_dir="data/markdown"):
    """Extract text from PDF and return output file path."""
    if not os.path.exists(pdf_path):
        print(f"Error: File not found - {pdf_path}")
        return None

    try:
        doc = pymupdf.open(pdf_path)
        text = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text.append(page.get_text())

        doc.close()
        full_text = "\n\n".join(text)

        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.basename(pdf_path).replace('.pdf', '.txt')
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)

        return output_path

    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return None
