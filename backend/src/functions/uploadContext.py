import os
import shutil
import glob
import logging

# Configure logging
logger = logging.getLogger(__name__)

async def copy_to_context_folder():
    """
    Copies .txt files from the 'txt_files' directory to the 'context' directory
    in the local file system.
    
    Returns:
        tuple: (list of copied file data or None, error message or None)
               - (list, None): If files are copied successfully.
               - (None, str): If an error occurs.
    """
    try:
        # Get source and destination directories
        base_dir = os.path.dirname(os.path.dirname(__file__))
        txt_folder = os.path.join(base_dir, "txt_files")
        context_folder = os.path.join(base_dir, "context")
        
        logger.info(f"Source folder: {txt_folder}")
        logger.info(f"Destination context folder: {context_folder}")
        
        # Create the context directory if it doesn't exist
        os.makedirs(context_folder, exist_ok=True)
        
        # Find all .txt files in the source directory
        txt_files = glob.glob(os.path.join(txt_folder, "*.txt"))
        
        if not txt_files:
            logger.error(f"No .txt files found in source directory: {txt_folder}")
            return None, "No .txt files found for copying to context folder"
        
        logger.info(f"Found {len(txt_files)} .txt files to copy to context folder")
        
        # Copy files to context folder
        copied_files = []
        for file_path in txt_files:
            file_name = os.path.basename(file_path)
            destination_path = os.path.join(context_folder, file_name)
            
            try:
                # Copy the file
                shutil.copy2(file_path, destination_path)
                logger.info(f"Copied {file_name} to context folder")
                
                # Get file stats for the copied file
                file_stats = os.stat(destination_path)
                
                copied_files.append({
                    "name": file_name,
                    "path": destination_path,
                    "size": file_stats.st_size,
                    "copied": True
                })
            except Exception as e:
                logger.error(f"Error copying {file_name} to context folder: {str(e)}")
                continue
        
        return copied_files, None
    except Exception as e:
        logger.error(f"An unexpected error occurred while copying to context folder: {str(e)}")
        return None, f"An unexpected error occurred: {str(e)}"