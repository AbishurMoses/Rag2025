import os
import logging
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import asyncio # Potentially needed if this function is called in an async context

# Configure logging
# It's good practice to configure logging at the application entry point
# rather than in every module. For now, we'll get a logger instance.
logger = logging.getLogger(__name__)

async def better_ocr():
    """
    Process PDF files using DocTR OCR and save extracted text to txt files.

    This function is declared as async, but the core OCR processing and 
    file I/O operations within it are synchronous. If this is part of a larger
    asyncio application and needs to be non-blocking, consider running 
    synchronous parts in a thread pool (e.g., with asyncio.to_thread).

    Returns:
        str: Status message summarizing the conversion process
    """
    # === Settings ===
    # Assumes this script is in a subdirectory (e.g., 'functions')
    # and 'pdf_files', 'txt_files' are in the parent directory of that subdirectory.
    # Example: if script is /app/src/functions/betterOCR.py
    # pdf_folder will be /app/src/pdf_files
    # txt_folder will be /app/src/txt_files
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_file_directory) # Parent of the current script's directory

    pdf_folder = os.path.join(base_dir, "pdf_files")
    txt_folder = os.path.join(base_dir, "txt_files")
    
    logger.info(f"PDF folder path: {pdf_folder}")
    logger.info(f"TXT folder path: {txt_folder}")

    # Ensure the output directory for text files exists
    os.makedirs(txt_folder, exist_ok=True)

    # Check if PDF folder exists
    if not os.path.exists(pdf_folder):
        logger.error(f"PDF folder does not exist: {pdf_folder}")
        return "PDF folder not found"

    # List PDF files in the folder
    try:
        pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    except FileNotFoundError:
        logger.error(f"Error accessing PDF folder (it might have been deleted): {pdf_folder}")
        return "PDF folder not found or inaccessible"
        
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_folder}")
        return "No PDF files found"

    logger.info(f"Found {len(pdf_files)} PDF files to process: {pdf_files}")

    # Load the OCR model once
    # Consider adding device selection here if GPU is available, e.g., device='cuda'
    # ocr_model = ocr_predictor(pretrained=True, device=torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    # You would need to import torch for the above line.
    logger.info("Loading OCR model...")
    try:
        ocr_model = ocr_predictor(pretrained=True)
        logger.info("OCR model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load OCR model: {str(e)}")
        return "Failed to load OCR model"

    processed_count = 0
    error_count = 0

    # Loop over PDFs
    for pdf_file_name in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file_name)
        logger.info(f"📄 Processing: {pdf_file_name}")

        try:
            doc = DocumentFile.from_pdf(pdf_path)
        
            result = ocr_model(doc)
            
            # Extract text from the result
            ocr_text = ""
            for page_num, page in enumerate(result.pages):
                # Adding a header for each page in the output text
                ocr_text += f"\n--- Page {page_num + 1} of {pdf_file_name} ---\n"
                for block in page.blocks:
                    for line in block.lines:
                        # Concatenate word values to form a line
                        line_text = " ".join([word.value for word in line.words])
                        ocr_text += line_text + "\n"
            
            # Define output text file path
            output_filename = os.path.splitext(pdf_file_name)[0] + ".txt" # More robust way to change extension
            output_path = os.path.join(txt_folder, output_filename)
            
            # Write extracted text to the output file
            # Note: File writing is I/O bound.
            # If running in a highly concurrent async environment,
            # this could be wrapped with asyncio.to_thread.
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(ocr_text.strip()) # Use strip() to remove leading/trailing whitespace
            
            logger.info(f"✅ Saved OCR text to: {output_path}")
            processed_count += 1
        
        except Exception as e:
            logger.error(f"❌ Failed to process {pdf_file_name}: {str(e)}", exc_info=True) # Log traceback
            error_count += 1
            # Continue to the next file if an error occurs
            continue 

    summary_message = f"Conversion process complete: {processed_count} files processed, {error_count} errors."
    logger.info(summary_message)
    
    return summary_message