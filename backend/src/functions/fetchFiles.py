import supabase
import asyncio
import datetime
import os
import logging
# from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables once at module level
# load_dotenv()
# env = Env()
# env.read_env(".env")  

async def fetch_files(file_names, bucket_name="pdf", output_dir=None):
    """
    Fetches specified files from Supabase storage, downloads them, and saves them locally.
    
    Args:
        file_names (list): A list of file names (strings) to fetch from the Supabase storage.
        bucket_name (str): The Supabase storage bucket name. Defaults to 'pdf'.
        output_dir (str, optional): Custom output directory. If None, uses '../pdf_files'.
    
    Returns:
        tuple: (list of successfully downloaded file data, list of failed files)
    """
    # Validate input
    if not file_names or not isinstance(file_names, list):
        logger.error("Invalid or empty file_names list provided.")
        return None, "Invalid or empty file_names list provided."
    
    try:
        # Load environment variables
        supabase_url = "http://127.0.0.1:54321"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
        # supabase_url = os.getenv("SUPABASE_URL")
        # supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase URL or key not provided in environment variables.")
            return None, "Supabase URL or key not provided."
        
        # Initialize Supabase client once
        logger.info(f"Connecting to Supabase at {supabase_url}")
        supabase_client = supabase.create_client(supabase_url, supabase_key)
        
        # Create the output directory
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "pdf_files"
        else:
            output_dir = Path(output_dir)
            
        output_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Files will be saved to: {output_dir.absolute()}")
        
        # Track results
        successful_downloads = []
        failed_downloads = []
        
        # Process each file
        for file_name in file_names:
            try:
                file_path = output_dir / file_name
                
                # Check if file already exists
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    logger.info(f"Skipping download: {file_name} already exists ({file_size} bytes)")
                    
                    successful_downloads.append({
                        "id": file_name,
                        "name": file_name,
                        "size": file_size,
                        "lastModified": datetime.datetime.fromtimestamp(file_path.stat().st_mtime),
                        "type": "application/pdf",
                        "status": "skipped"
                    })
                    continue
                
                # Download the file
                logger.info(f"Downloading {file_name} from {bucket_name} bucket...")
                file_content = supabase_client.storage.from_(bucket_name).download(file_name)
                
                # Save the file
                with open(file_path, "wb") as f:
                    f.write(file_content)
                
                file_size = len(file_content)
                logger.info(f"Successfully downloaded {file_name} ({file_size} bytes)")
                
                successful_downloads.append({
                    "id": file_name,
                    "name": file_name,
                    "size": file_size,
                    "lastModified": datetime.datetime.now(),
                    "type": "application/pdf",
                    "status": "downloaded"
                })
                
            except Exception as e:
                logger.error(f"Failed to download {file_name}: {str(e)}")
                failed_downloads.append({
                    "name": file_name,
                    "error": str(e)
                })
        
        # Report results
        if successful_downloads:
            logger.info(f"Successfully processed {len(successful_downloads)} out of {len(file_names)} files")
        if failed_downloads:
            logger.warning(f"Failed to download {len(failed_downloads)} files")
            
        return successful_downloads, failed_downloads
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return None, f"An unexpected error occurred: {str(e)}"


async def main():
    """
    Main function to demonstrate the fetch_files function.
    """
    # Example list of file names
    sample_files = ["document1.pdf", "document2.pdf", "nonexistent.pdf"]
    
    # Call the fetch_files function
    successful, failed = await fetch_files(sample_files)
    
    # Display results
    if successful:
        logger.info("\nSuccessfully processed files:")
        for file in successful:
            logger.info(f"- {file['name']} ({file['size']} bytes, {file['status']})")
    
    if failed:
        logger.error("\nFailed files:")
        for file in failed:
            logger.error(f"- {file['name']}: {file['error']}")


if __name__ == "__main__":
    asyncio.run(main())