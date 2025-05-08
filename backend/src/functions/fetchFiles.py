import supabase
import asyncio
import datetime
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def fetch_files(file_names):
    """
    Fetches specified files from the 'pdf' storage in Supabase, downloads them, and saves them to the 'pdf_files' directory.

    Args:
        file_names (list): A list of file names (strings) to fetch from the Supabase storage.

    Returns:
        tuple: A tuple containing either a list of mapped file data or None, and an error message or None.
               - (list, None): If files are fetched successfully.
               - (None, str): If an error occurs during fetching.
    """
    if not file_names or not isinstance(file_names, list):
        logger.error("Invalid or empty file_names list provided.")
        return None, "Invalid or empty file_names list provided."

    try:
        # Load environment variables
        supabase_url = "http://127.0.0.1:54321"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
        supabase_client = supabase.create_client(supabase_url, supabase_key)
                
        if not supabase_url or not supabase_key:
            logger.error("Supabase URL or key not provided.")
            return None, "Supabase URL or key not provided."

        # Initialize Supabase client
        supabase_client = supabase.create_client(supabase_url, supabase_key)
        
        # Create the 'pdf_files' directory
        pdf_files_dir = os.path.join(os.path.dirname(__file__), "..", "pdf_files")
        os.makedirs(pdf_files_dir, exist_ok=True)

        mapped = []
        failed_downloads = []
        for file_name in file_names:
            try:
                # Get file metadata (Supabase Python client doesn't have a direct 'get file metadata' method,
                # so we attempt to download and infer metadata from the response or use a fallback)
                file_data = {
                    "id": file_name,
                    "name": file_name,
                    "size": 0,  # Size will be updated after download if available
                    "lastModified": datetime.datetime.now(),  # Fallback if metadata is unavailable
                    "type": "application/pdf",  # Default MIME type
                }

                # Check if file already exists
                file_path = os.path.join(pdf_files_dir, file_name)
                if os.path.exists(file_path):
                    local_size = os.path.getsize(file_path)
                    file_data["size"] = local_size
                    logger.info(f"Skipping download: {file_name} already exists with size {local_size} bytes.")
                    mapped.append(file_data)
                    continue

                # Download the file
                file_content = supabase_client.storage.from_("pdf").download(file_name)
                
                # Update file size from downloaded content
                file_data["size"] = len(file_content)
                
                # Save the file to the 'pdf_files' directory
                with open(file_path, "wb") as file:
                    file.write(file_content)
                logger.info(f"Saved file: {file_path}")
                
                mapped.append(file_data)
            except Exception as e:
                logger.error(f"Error downloading or saving {file_name}: {str(e)}")
                failed_downloads.append(file_name)
                continue

        if failed_downloads:
            logger.warning(f"Failed to download {len(failed_downloads)} files: {failed_downloads}")

        if not mapped:
            logger.warning("No files were successfully fetched.")
            return None, "No files were successfully fetched."

        return mapped, None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return None, f"An unexpected error occurred: {str(e)}"

async def main():
    """
    Main function to call fetch_files with a sample list of file names and process the results.
    """
    # Example list of file names
    sample_files = ["document1.pdf", "document2.pdf", "nonexistent.pdf"]
    files, error_message = await fetch_files(sample_files)
    
    if error_message:
        logger.error(error_message)
    elif files:
        logger.info("\nFetched and saved files:")
        for file in files:
            logger.info(f"- {file['name']} ({file['type']}, {file['size']} bytes)")
    else:
        logger.warning("No files fetched or an unknown error occurred.")

if __name__ == "__main__":
    asyncio.run(main())