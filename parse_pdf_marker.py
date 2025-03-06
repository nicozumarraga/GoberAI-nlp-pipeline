import requests
import os
import time
import json
import base64
from config import test_config

def parse_pdf_with_marker(pdf_path, output_dir="data/markdown"):
    """
    Parse PDF to markdown using the Marker API

    Args:
        pdf_path: Path to the PDF file
        api_key: Marker API key
        output_dir: Directory to save output markdown

    Returns:
        Path to the markdown file if successful, None otherwise
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found - {pdf_path}")
        return None
    print("Parsing started")

    # Check if markdown file already exists
    output_filename = os.path.basename(pdf_path).replace('.pdf', '.md')
    output_path = os.path.join(output_dir, output_filename)

    if os.path.exists(output_path):
        return output_path

    # API endpoints
    submit_url = "https://www.datalab.to/api/v1/marker"
    api_key = test_config.MARKER_API

    try:
        # Prepare the file for upload
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}

            # Set up the request
            headers = {
                'accept': 'application/json',
                'X-API-Key': api_key
            }

            data = {
                'output_format': 'markdown',
                'disable_image_extraction': 'true',
                'paginate': 'false',
                'skip_cache': 'false'
            }

            # Submit the PDF for processing
            print(f"Submitting {pdf_path} to Marker API...")
            response = requests.post(submit_url, headers=headers, files=files, data=data)
            response.raise_for_status()

            # Get request ID
            result = response.json()
            if not result.get('success'):
                print(f"Error: {result.get('error', 'Unknown error')}")
                return None

            request_id = result['request_id']
            check_url = f"https://www.datalab.to/api/v1/marker/{request_id}"

            # Poll for results
            print(f"Processing request {request_id}...")
            max_attempts = 100
            for attempt in range(max_attempts):
                status_response = requests.get(check_url, headers=headers)
                status_response.raise_for_status()
                status = status_response.json()

                if status.get('status') == 'complete':
                    # Get the markdown content
                    markdown_content = status.get('markdown', '')

                    # Create output directory if it doesn't exist
                    os.makedirs(output_dir, exist_ok=True)

                    # Save the markdown content
                    output_filename = os.path.basename(pdf_path).replace('.pdf', '.md')
                    output_path = os.path.join(output_dir, output_filename)

                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)

                    print(f"Successfully parsed {pdf_path} to {output_path}")
                    return output_path

                elif status.get('status') == 'error':
                    print(f"Error processing PDF: {status.get('error')}")
                    return None

                # Wait before polling again
                time.sleep(0.1)
                print(f"Waiting for processing to complete... (attempt {attempt+1}/{max_attempts})")

            print("Maximum polling attempts reached. Request may still be processing.")
            return None

    except Exception as e:
        print(f"Error parsing PDF with Marker: {e}")
        return None
