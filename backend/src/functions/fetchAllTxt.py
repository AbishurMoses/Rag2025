import supabase
import asyncio
import datetime
import os
import errno

async def fetch_txt_files():
    """
    Fetches ALL files from the 'ragfiles' storage in Supabase using pagination,
    filters for .txt files, downloads them, and saves them to the 'txt_files' directory.

    Returns:
        tuple: A tuple containing either a list of mapped file data for .txt files or None, 
               and an error message or None.
               - (list, None): If .txt files are fetched successfully.
               - (None, str): If an error occurs or no .txt files are found.
    """
    try:
        print("Attempting to fetch all files from 'ragfiles' bucket and filter for .txt files...")
        # Initialize Supabase client
        supabase_url = "http://127.0.0.1:54321"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
        supabase_client = supabase.create_client(supabase_url, supabase_key)
        
        all_listed_files = []
        limit = 100  # Number of files to fetch per request
        offset = 0
        
        print("Starting pagination to fetch all file entries...")
        while True:
            # List files in the 'ragfiles' bucket with pagination
            # Assuming .txt files are at the root of the 'ragfiles' bucket. 
            # If they are in a specific subfolder (e.g., "my_texts/"), change path="my_texts/"
            response = supabase_client.storage.from_("ragfiles").list(
                path="",  # Use "" for the root of the bucket, or specify a folder e.g., "my_folder/"
                options={"limit": limit, "offset": offset}
            )
            
            # The supabase-py library might raise an exception on error, 
            # or return an object with an 'error' attribute, or just the data.
            # For this example, we'll assume it returns the list of files directly,
            # and an empty list if no files or an error that doesn't raise an exception.
            # Robust error handling would check for specific error responses if the library provides them.

            if response is None: # More explicit check if API could return None on error
                print(f"Error or no response received during file listing at offset {offset}.")
                if not all_listed_files: # If this was the first attempt
                    return None, "Error occurred during initial file listing."
                else: # If some files were fetched before error
                    print("Partial data might have been fetched before an error. Proceeding with what was found.")
                    break 

            current_batch = response
            
            if not current_batch: # No more files left in this batch
                print(f"No more files found at offset {offset}. Pagination complete.")
                break
            
            all_listed_files.extend(current_batch)
            print(f"Fetched {len(current_batch)} file entries. Total fetched so far: {len(all_listed_files)}.")
            
            if len(current_batch) < limit:
                # Fetched the last batch of files
                print("Fetched the last batch of files.")
                break
            
            offset += limit
        
        if not all_listed_files:
            print("No files found in the 'ragfiles' bucket after pagination.")
            return None, "no files found in the bucket"

        print(f"\nTotal file entries listed from 'ragfiles' bucket: {len(all_listed_files)}")
        
        # Strategy 1: Filter for .txt files client-side
        txt_file_objects = []
        for file_entry in all_listed_files:
            if isinstance(file_entry, dict) and "name" in file_entry and \
               file_entry["name"] is not None and \
               file_entry["name"].lower().endswith(".txt"):
                txt_file_objects.append(file_entry)
            else:
                if isinstance(file_entry, dict) and "name" in file_entry:
                    print(f"Skipping non-TXT file or entry without .txt extension: {file_entry.get('name', 'Unknown name')}")
                else:
                    print(f"Skipping invalid file entry: {file_entry}")


        if not txt_file_objects:
            print("No .txt files found after filtering all listed entries.")
            return None, "no .txt files found after filtering"

        print(f"Found {len(txt_file_objects)} .txt files to download and process.")

        # Create the 'txt_files' directory if it doesn't exist
        content_dir = os.path.join(os.path.dirname(__file__), "..", "context")
        try:
            os.makedirs(content_dir, exist_ok=True)
            print(f"Ensured directory exists: {content_dir}")
        except OSError as e:
            if e.errno != errno.EEXIST:
                print(f"Error creating directory {content_dir}: {e}")
                return None, f"Error creating directory: {str(e)}"

        mapped_txt_files = []
        for f_object in txt_file_objects: # Iterate only over filtered .txt file objects
            file_data = {
                "id": f_object["name"],
                "name": f_object["name"],
                "size": f_object.get("metadata", {}).get("size", 0) if isinstance(f_object.get("metadata"), dict) else 0,
                "lastModified": datetime.datetime.fromisoformat(f_object.get("updated_at")) if f_object.get("updated_at") else datetime.datetime.now(),
                "type": f_object.get("metadata", {}).get("mimetype", "text/plain") if isinstance(f_object.get("metadata"), dict) else "text/plain", # Default to text/plain for .txt
            }
            mapped_txt_files.append(file_data)

            # Download and save the .txt file
            try:
                print(f"Downloading .txt file: {f_object['name']}...")
                # Ensure you are downloading from the correct bucket ('ragfiles')
                file_content = supabase_client.storage.from_("ragfiles").download(f_object["name"])
                
                if file_content is None:
                    print(f"Failed to download {f_object['name']}: received None content.")
                    continue

                file_path = os.path.join(content_dir, f_object["name"])
                
                with open(file_path, "wb") as file_to_save:
                    file_to_save.write(file_content)
                print(f"Saved .txt file: {file_path}")
            except Exception as e:
                print(f"Error downloading or saving {f_object['name']}: {str(e)}")
                # Optionally, add more detailed error logging here
                # traceback.print_exc() 
                continue  # Continue with the next file

        if not mapped_txt_files:
             print("No .txt files were successfully processed and mapped.")
             return None, "no .txt files processed"

        return mapped_txt_files, None
        
    except Exception as e:
        print(f"An unexpected error occurred in fetch_txt_files: {e}")
        import traceback
        traceback.print_exc() # For detailed debugging
        message = f"An unexpected error occurred: {str(e)}"
        return None, message

async def main():
    """
    Main function to call fetch_txt_files and process the results.
    """
    print("Starting main function...")
    # This was originally fetch_all_files() in your provided code for the .txt script.
    # Correcting it to call the relevant function name.
    files, error_message = await fetch_txt_files() 
    
    if error_message:
        print(f"\nProcess finished with an error: {error_message}")
    elif files:
        print("\nFetched, filtered, and saved .txt files successfully:")
        for file_info in files: # Renamed 'file' to 'file_info' to avoid potential conflict
            print(f"- Name: {file_info['name']}, Type: {file_info['type']}, Size: {file_info['size']} bytes, Last Modified: {file_info['lastModified']}")
    else:
        print("\nNo .txt files were fetched or an unknown issue occurred during the process.")

if __name__ == "__main__":
    asyncio.run(main())