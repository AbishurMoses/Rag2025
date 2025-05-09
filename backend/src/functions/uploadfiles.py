import supabase
import asyncio
import datetime
import os
import errno
import glob
import logging
# from dotenv import load_dotenv

# load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

async def upload_txt_files():
    """
    Uploads .txt files from the 'txt_files' directory to the 'ragfiles' bucket in Supabase.
    
    Returns:
        tuple: (list of mapped file data or None, error message or None)
               - (list, None): If files are uploaded successfully.
               - (None, str): If an error occurs.
    """
    try:
        # Initialize Supabase client
        supabase_url = "http://127.0.0.1:54321"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
        # supabase_url = os.getenv("SUPABASE_URL")
        # supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL or SUPABASE_KEY environment variables are not set")
            return None, "Supabase credentials not found in environment variables"
        
        supabase_client = supabase.create_client(supabase_url, supabase_key)
        
        # Create the 'txt_files' directory if it doesn't exist
        txt_upload_dir = os.path.join(os.path.dirname(__file__), "..", "txt_files")
        
        # Wait briefly to ensure file system operations are complete
        await asyncio.sleep(1)
        
        logger.info(f"Looking for .txt files in: {txt_upload_dir}")
        
        # Find all .txt files
        txt_files = glob.glob(os.path.join(txt_upload_dir, "*.txt"))
        
        if not txt_files:
            logger.error(f"No .txt files found in directory: {txt_upload_dir}")
            # List directory contents for debugging
            if os.path.exists(txt_upload_dir):
                dir_contents = os.listdir(txt_upload_dir)
                logger.info(f"Directory contents: {dir_contents}")
            else:
                logger.error(f"Directory does not exist: {txt_upload_dir}")
            return None, "No .txt files found"
        
        logger.info(f"Found {len(txt_files)} .txt files: {[os.path.basename(f) for f in txt_files]}")
        
        # List existing files in bucket once
        try:
            response = supabase_client.storage.from_("ragfiles").list()
            if isinstance(response, dict) and "error" in response:
                logger.error(f"Error listing files: {response['error']}")
                return None, f"Error listing files: {response['error']}"
            existing_files = response or []
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return None, f"Error listing files: {str(e)}"
        
        mapped = []
        for file_path in txt_files:
            file_name = os.path.basename(file_path)
            
            # Skip if file already exists
            if any(f["name"] == file_name for f in existing_files):
                logger.warning(f"⚠️ {file_name} already exists in ragfiles. Upload cancelled.")
                continue
            
            # Read and upload file
            try:
                with open(file_path, "rb") as file:
                    file_content = file.read()
                
                logger.info(f"Uploading {file_name} to 'ragfiles' bucket...")
                
                supabase_client.storage.from_("ragfiles").upload(
                    file_name,
                    file_content,
                    file_options={
                        "content-type": "text/plain",
                        "cache-control": "3600"
                    }
                )
                logger.info(f"Text file uploaded to ragfiles: {file_name} ✅")
                
                # Update mapped list
                mapped.append({
                    "id": file_name,
                    "name": file_name,
                    "size": len(file_content),
                    "lastModified": datetime.datetime.now(),
                    "type": "text/plain"
                })
            except Exception as e:
                logger.error(f"Upload failed for {file_name}: {str(e)}")
                continue
        
        return mapped, None
    except Exception as e:
        logger.error(f"An unexpected error occurred in upload_txt_files: {e}")
        return None, f"An unexpected error occurred: {str(e)}"