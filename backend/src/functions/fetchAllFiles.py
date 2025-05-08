import supabase
import asyncio
import datetime
import os
import errno

async def fetch_all_files():
    """
    Fetches files from the 'pdf' storage in Supabase, downloads them, and saves them to the 'pdf_files' directory.

    Returns:
        tuple: A tuple containing either a list of mapped file data or None, and an error message or None.
               - (list, None): If files are fetched successfully.
               - (None, str): If an error occurs during fetching.
    """
    try:
        # Initialize Supabase client
        supabase_url = "http://127.0.0.1:54321"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
        supabase_client = supabase.create_client(supabase_url, supabase_key)
        
        # List files in the 'pdf' bucket
        response = supabase_client.storage.from_("pdf").list()
        data = response
        print(data)
        if data == []:
            print("No files found")
            return None, "no files found"
        if not data:
            print("error occurred")
            return None, "error occurred"

        # Create the 'pdf_files' directory if it doesn't exist
        pdf_files_dir = os.path.join(os.path.dirname(__file__), "..", "pdf_files")
        try:
            os.makedirs(pdf_files_dir, exist_ok=True)
        except OSError as e:
            if e.errno != errno.EEXIST:
                print(f"Error creating directory {pdf_files_dir}: {e}")
                return None, f"Error creating directory: {str(e)}"

        mapped = []
        for f in data:
            file_data = {
                "id": f["name"],
                "name": f["name"],
                "size": f.get("metadata", {}).get("size", 0),
                "lastModified": datetime.datetime.fromisoformat(f.get("updated_at")) if f.get("updated_at") else datetime.datetime.now(),
                "type": f.get("metadata", {}).get("mimetype", "application/pdf"),
            }
            mapped.append(file_data)

            # Download and save the file
            try:
                file_content = supabase_client.storage.from_("pdf").download(f["name"])
                file_path = os.path.join(pdf_files_dir, f["name"])
                
                # Save the file to the 'pdf_files' directory
                with open(file_path, "wb") as file:
                    file.write(file_content)
                print(f"Saved file: {file_path}")
            except Exception as e:
                print(f"Error downloading or saving {f['name']}: {str(e)}")
                continue  # Continue with the next file

        return mapped, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        message = f"An unexpected error occurred: {str(e)}"
        return None, message

async def main():
    """
    Main function to call fetch_files and process the results.
    """
    files, error_message = await fetch_all_files()
    if error_message:
        print(error_message)
    elif files:
        print("\nFetched and saved files:")
        for file in files:
            print(f"- {file['name']} ({file['type']}, {file['size']} bytes)")
    else:
        print("No files fetched or an unknown error occurred.")

if __name__ == "__main__":
    asyncio.run(main())