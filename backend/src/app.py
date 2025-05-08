from flask import Flask, request, jsonify
from flask_cors import CORS
from functions.fetchAllFiles import fetch_all_files
from functions.fetchFiles import fetch_files
from functions.answer import answer_question
from functions.uploadfiles import upload_txt_files
from functions.ocr import better_ocr
import os
from functions.uploadContext import copy_to_context_folder
import shutil
import logging
import traceback

app = Flask(__name__, static_folder='frontend')

# Allow requests from localhost:3000 to ALL routes the app
CORS(app, origins=["http://localhost:3000", "http://10.10.129.80:3000"])

# logging for detailed error tracking
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/convertFiles', methods=['POST'])
async def convert_files():
    try:
        # Define directory paths    
        base_dir = os.path.dirname(os.path.abspath(__file__)) 
        pdf_files_dir = os.path.join(base_dir, "pdf_files")
        txt_files_dir = os.path.join(base_dir, "txt_files")
        
        # Ensure directories exist
        os.makedirs(pdf_files_dir, exist_ok=True)
        os.makedirs(txt_files_dir, exist_ok=True)
        
        data = request.get_json()
        if not data or 'input' not in data:
            error_msg = "No input provided or invalid JSON payload"
            logger.error(f"400 Bad Request: {error_msg}, Request Data: {request.data}")
            return jsonify({
                "error": error_msg,
                "details": "The request must include a JSON payload with an 'input' field"
            }), 400
        
        user_input = data.get('input', '')
        if not user_input:
            error_msg = "Input field is empty"
            logger.error(f"400 Bad Request: {error_msg}, Request Data: {data}")
            return jsonify({
                "error": error_msg,
                "details": "The 'input' field cannot be empty or whitespace"
            }), 400
        
        if isinstance(user_input, str):
            user_input = [user_input]
        
        logger.info(f"Starting file fetch for: {user_input}")
        fetched_files, fetch_error = await fetch_files(user_input)
        
        if fetch_error:
            logger.error(f"Error fetching files: {fetch_error}")
            return jsonify({
                "error": fetch_error,
                "details": "Failed to fetch PDF files from Supabase"
            }), 500
            
        logger.info(f"Files fetched successfully: {len(fetched_files) if fetched_files else 0} files")
        
        # Run OCR on fetched PDFs
        convert_summary = await better_ocr()
        logger.info(f"OCR conversion result: {convert_summary}")
        
        # Copy files to local context folder
        context_copies, context_error = await copy_to_context_folder()
        
        if context_error:
            logger.error(f"Error copying files to context folder: {context_error}")
            logger.info("Continuing with upload to Supabase...")
        else:
            logger.info(f"Successfully copied {len(context_copies) if context_copies else 0} files to context folder")
        
        # Upload text files to Supabase
        uploaded_files, upload_error = await upload_txt_files()
        
        if upload_error:
            logger.error(f"Error uploading files to Supabase: {upload_error}")
            return jsonify({
                "error": upload_error,
                "details": "Failed to upload text files to Supabase"
            }), 500
            
        logger.info(f"Files uploaded successfully to Supabase: {len(uploaded_files) if uploaded_files else 0} files")
        
        # Safely clean up directories
        # try:
        #     if os.path.exists(pdf_files_dir):
        #         shutil.rmtree(pdf_files_dir)
        #         logger.info(f"Successfully deleted directory and its contents: {pdf_files_dir}")
        # except Exception as cleanup_error:
        #     logger.warning(f"Error cleaning up PDF directory: {str(cleanup_error)}")
        
        # try:
        #     if os.path.exists(txt_files_dir):
        #         shutil.rmtree(txt_files_dir)
        #         logger.info(f"Successfully deleted directory and its contents: {txt_files_dir}")
        # except Exception as cleanup_error:
        #     logger.warning(f"Error cleaning up TXT directory: {str(cleanup_error)}")
        
        logger.info("Successfully processed request")
        return jsonify({
            "message": "Files processed and uploaded successfully.",
            "conversion_summary": convert_summary,
            "context_copies": context_copies,
            "uploaded_files": uploaded_files,
            "original_input": user_input 
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in /convertFiles: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500
         
# converts all files
@app.route('/convertAll', methods=['GET'])
async def convertAllFile():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__)) 
        pdf_files_dir = os.path.join(base_dir, "pdf_files")
        txt_files_dir = os.path.join(base_dir, "txt_files")
        
        # Ensure directories exist
        os.makedirs(pdf_files_dir, exist_ok=True)
        os.makedirs(txt_files_dir, exist_ok=True)
        
        # Run async fetch_all_files
        pdf_files, pdf_error = await fetch_all_files() 
        if pdf_error:
            logger.error(f"Error fetchings files: {pdf_error}")
            return jsonify({
                "error": pdf_error,
                "details": "Failed to fetch pdf files from supabase"
            }), 500

        convert_summary = better_ocr()  
        
        context_copies, context_error = await copy_to_context_folder()
        if context_error:
            logger.error(f"Error copying files: {context_error}")
            return jsonify({
                "error": context_error,
                "details": "Failed to upload text files to context folder"
            }), 500

        # Upload processed .txt files 
        uploaded_files, upload_error = await upload_txt_files()  #
        if upload_error:
            logger.error(f"Error uploading files: {upload_error}")
            return jsonify({
                "error": upload_error,
                "details": "Failed to upload text files to Supabase"
            }), 500
            
        # Attempt to delete the folder
        # if os.path.exists(pdf_files_dir):
        #     try:
        #         shutil.rmtree(pdf_files_dir)
        #         print(f"Successfully deleted directory and its contents: {pdf_files_dir}")
        #     except Exception as e_delete:
        #         print(f"Error deleting directory {pdf_files_dir}: {e_delete}")
        # if os.path.exists(txt_files_dir):
        #     try:
        #         shutil.rmtree(txt_files_dir)
        #         print(f"Successfully deleted directory and its contents: {txt_files_dir}")
        #     except Exception as e_delete:
        #         print(f"Error deleting directory {txt_files_dir}: {e_delete}")
                

        return jsonify({
            "message": "Files processed and uploaded successfully",
            "details": {
                "convert_summary": convert_summary,
                "uploaded_files": uploaded_files,
                "context_copies": context_copies,
                "pdf_files": pdf_files,
            }
        }), 200

    except Exception as e:
        logger.error(f"Unexpected error in convertFile: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500
        

@app.route('/content', methods=['POST'])
async def answerQues():
    try:
        data = request.get_json()
        if not data or 'input' not in data:
            error_msg = "No input provided or invalid JSON payload"
            logger.error(f"400 Bad Request: {error_msg}, Request Data: {request.data}")
            return jsonify({
                "error": error_msg,
                "details": "The request must include a JSON payload with an 'input' field"
            }), 400

        user_input = data.get('input', '')
        if not user_input.strip():
            error_msg = "Input field is empty"
            logger.error(f"400 Bad Request: {error_msg}, Request Data: {data}")
            return jsonify({
                "error": error_msg,
                "details": "The 'input' field cannot be empty or whitespace"
            }), 400
        
        print(f"DEBUG: Calling answer_question with input: {user_input}")
        result = answer_question(user_input) 
        print(f"DEBUG: answer_question returned: {result}")

        if not isinstance(result, dict):
            error_msg = f"Unexpected return type from answer_question: {type(result)}"
            logger.error(error_msg)
            return jsonify({
                "error": "Internal server error",
                "details": error_msg
            }), 500

        answer_text = result.get('answer', '') 
        if answer_text.startswith(("Something went wrong", "No .txt files found", "Directory")):
            logger.error(f"Error in RAG: {answer_text}")
            return jsonify({
                "error": answer_text,
                "details": "Failed to generate an answer from the RAG process"
            }), 500
            
        return jsonify({
            "answer": result.get('answer'), 
            "sources": result.get('sources') 
        }), 200 

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)