import time
import os
import argparse
from datetime import datetime
from config import test_config
from document_pipeline import DocumentPipeline

def main():
    # Parse command-line arguments for a minimal, flexible script
    parser = argparse.ArgumentParser(description='Run document pipeline with sequential processing and retry capability')
    parser.add_argument('--start-section', type=int, default=0, help='Section index to start from (0-based)')
    parser.add_argument('--resume-file', type=str, help='Path to existing summary file to resume from')
    parser.add_argument('--output', type=str, help='Custom output filename')
    args = parser.parse_args()

    # Track total execution time
    start_time = time.time()
    print(f"Pipeline started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load config
    pdfs = test_config.PDF_FILE_NAMES
    questions = test_config.QUESTIONS

    # Handle resuming from a specific section
    if args.start_section > 0:
        print(f"Starting from section {args.start_section+1} (skipping sections 1-{args.start_section})")
        questions = questions[args.start_section:]

    # Generate output filename
    if args.output:
        output_filename = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"summary_{timestamp}.txt"

    # Initialize pipeline
    pipeline = DocumentPipeline()

    try:
        # Step 1: Ensure we have markdown files
        step_start = time.time()
        print("\n=== Checking/Converting PDFs to Markdown ===")

        # Check if we already have markdown files
        markdown_dir = pipeline.markdown_output_dir
        existing_files = [f for f in os.listdir(markdown_dir) if f.endswith('.md')]

        if existing_files:
            print(f"Found {len(existing_files)} existing markdown files")
        else:
            # Convert PDFs to markdown if needed
            markdown_paths = pipeline.convert_to_markdown(pdfs)
            if not markdown_paths:
                raise ValueError("No PDFs were successfully converted to markdown")

        step_time = time.time() - step_start
        print(f"Markdown preparation completed in {step_time:.2f} seconds")

        # Step 2: Process questions sequentially
        step_start = time.time()
        print("\n=== Processing questions sequentially ===")

        # If resuming from an existing file
        if args.resume_file and os.path.exists(args.resume_file):
            # Copy existing file to output location
            output_path = os.path.join(pipeline.results_dir, output_filename)
            with open(args.resume_file, 'r', encoding='utf-8') as src:
                existing_content = src.read()

            with open(output_path, 'w', encoding='utf-8') as dest:
                dest.write(existing_content)

            print(f"Resuming from existing file: {args.resume_file}")

        # Process questions with retry capability
        result = pipeline.query_documents_sequential(
            questions,
            output_filename
        )

        step_time = time.time() - step_start
        print(f"Question processing completed in {step_time:.2f} seconds")

        # Print results
        total_time = time.time() - start_time
        print("\n=== Results ===")
        print(f"Summary saved to: results/{output_filename}")
        print(f"Summary length: {len(result)} characters")
        print(f"Total execution time: {total_time:.2f} seconds")

    except Exception as e:
        total_time = time.time() - start_time
        print(f"Pipeline failed after {total_time:.2f} seconds: {e}")
        print("\nTo resume from the last successful section, run:")
        print(f"python {__file__} --start-section {args.start_section + 1}")

if __name__ == "__main__":
    main()
