from typing import List, Optional, Dict
import os
from pdf_downloader import download_pdf
from parse_pdf_marker import parse_pdf_with_marker
from gemini_rag import GeminiRAG
from config import test_config

class DocumentPipeline:
    def __init__(
        self,
        pdf_output_dir: str = "data/raw_pdfs",
        markdown_output_dir: str = "data/markdown",
        gemini_model: str = "models/gemini-1.5-flash-001",
        cache_name: str = "tender_documents"
    ):
        self.pdf_output_dir = pdf_output_dir
        self.markdown_output_dir = markdown_output_dir
        self.cache_name = cache_name

        # Initialize Gemini RAG
        self.gemini = GeminiRAG(model_name=gemini_model)

        # Create output directories
        os.makedirs(pdf_output_dir, exist_ok=True)
        os.makedirs(markdown_output_dir, exist_ok=True)

    def process_urls(self, urls: List[str]) -> Dict[str, str]:
        """
        Download PDFs from URLs and track their local paths
        Returns: Dictionary mapping URLs to local PDF paths
        """
        pdf_paths = {}
        for url in urls:
            print(f"Downloading PDF from {url}...")
            pdf_path = download_pdf(url, self.pdf_output_dir)
            if pdf_path:
                pdf_paths[url] = pdf_path
            else:
                print(f"Failed to download PDF from {url}")

        return pdf_paths

    def convert_to_markdown(self, pdf_paths: Dict[str, str]) -> List[str]:
        """
        Convert downloaded PDFs to markdown format
        Returns: List of markdown file paths
        """
        markdown_paths = []
        for pdf_path in pdf_paths:
            print(f"Converting {pdf_path} to markdown...")
            markdown_path = parse_pdf_with_marker(pdf_path, self.markdown_output_dir)
            if markdown_path:
                markdown_paths.append(markdown_path)
            else:
                print(f"Failed to convert PDF to markdown: {pdf_path}")

        return markdown_paths

    def query_documents(self, questions: List[str]) -> Dict[str, str]:
        """
        Query the processed documents using Gemini
        Returns: Dictionary mapping questions to answers
        """
        results = {}

        # Get all markdown files in the output directory
        markdown_files = [
            os.path.join(self.markdown_output_dir, f)
            for f in os.listdir(self.markdown_output_dir)
            if f.endswith('.md')
        ]

        if not markdown_files:
            raise ValueError("No markdown files found to process")

        # Create cache with all documents
        cache = self.gemini.process_mkd_documents(markdown_files, self.cache_name)

        # Process each question
        for question in questions:
            print(f"\nProcessing question: {question}")
            answer = self.gemini.query(cache, question)
            results[question] = answer

        return results

    def run_pipeline(self, urls: List[str], questions: List[str]) -> Dict[str, str]:
        """
        Run the complete pipeline from URLs to answers
        Returns: Dictionary mapping questions to answers
        """
        # Step 1: Download PDFs
        print("\n=== Downloading PDFs ===")
        pdf_paths = self.process_urls(urls)
        if not pdf_paths:
            raise ValueError("No PDFs were successfully downloaded")

        # Step 2: Convert to Markdown
        print("\n=== Converting to Markdown ===")
        markdown_paths = self.convert_to_markdown(pdf_paths)
        if not markdown_paths:
            raise ValueError("No PDFs were successfully converted to markdown")

        # Step 3: Query documents
        print("\n=== Querying Documents ===")
        results = self.query_documents(questions)

        return results

    def run_partial_pipeline(self, pdf_paths: List[str], questions: List[str]) -> Dict[str, str]:
        """
        Run the complete pipeline from URLs to answers
        Returns: Dictionary mapping questions to answers
        """
        # Step 1: Convert to Markdown
        print("\n=== Converting to Markdown ===")
        markdown_paths = self.convert_to_markdown(pdf_paths)
        if not markdown_paths:
            raise ValueError("No PDFs were successfully converted to markdown")

        # Step 2: Query documents
        print("\n=== Querying Documents ===")
        results = self.query_documents(questions)

        return results

if __name__ == "__main__":
    # Example usage
    urls = test_config.PDF_URLS
    pdfs = test_config.PDF_FILE_NAMES

    questions = test_config.QUESTIONS

    pipeline = DocumentPipeline()
    try:
        results = pipeline.run_partial_pipeline(pdfs, questions)

        # Print results
        print("\n=== Results ===")
        for question, answer in results.items():
            print(f"\nQuestion: {question[:50]}...")
            print("-" * 50)
            print(f"Answer: {answer}")
            print("=" * 50)

    except Exception as e:
        print(f"Pipeline failed: {e}")
