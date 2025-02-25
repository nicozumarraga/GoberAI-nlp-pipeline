import requests
import os
from urllib.parse import unquote
from config import test_config

def download_pdf(url, output_dir="data/raw_pdfs"):
    """Download PDF from URL and return local filepath."""
    os.makedirs(output_dir, exist_ok=True)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Simple filename extraction
        filename = 'document.pdf'
        if 'Content-Disposition' in response.headers:
            content_disposition = response.headers['Content-Disposition']
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"\'')

        filepath = os.path.join(output_dir, os.path.basename(filename))

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath

    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return None
