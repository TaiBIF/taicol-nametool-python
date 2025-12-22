# main.py
from flask import Flask, request, jsonify
import requests
import os
import time
import json
import logging
from google import genai
from utils.usage import UsageResult

app = Flask(__name__)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 Google GenAI 客戶端
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'your-api-key')
client = genai.Client(api_key=GEMINI_API_KEY)


# 定義結構化輸出的 schema
REFERENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": ["journal-article", "book-chapter", "book", "checklist"]
        },
        "author": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "given": {"type": "string"},
                    "family": {"type": "string"},
                    "sequence": {"type": "string", "enum": ["first", "additional"]},
                    "affiliation": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["given", "family", "sequence"]
            }
        },
        "published": {
            "type": "object",
            "properties": {
                "date-parts": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "integer"}
                    }
                }
            }
        },
        "title": {
            "type": "array",
            "items": {"type": "string"}
        },
        "container-title": {
            "type": "array",
            "items": {"type": "string"}
        },
        "volume": {"type": "string"},
        "issue": {"type": "string"},
        "page": {"type": "string"},
        "doi": {"type": "string"},
        "url": {"type": "string"},
        "language": {
            "type": "string",
            "enum": ["en-us", "zh-tw", "jp-jp", "zh-cn", "de-de", "fr-fr", "lat", "others"]
        }
    },
    "required": ["type", "title"]
}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.route('/process-reference', methods=['POST'])
def process_reference():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        logger.info(f"Processing PDF: {file_path}")
            
        # 使用 google-genai 上傳檔案
        logger.info("Uploading to Gemini...")
        # file_path = '/pdfs/references/tai.2024.69.302_20251210.pdf'
        uploaded_file = client.files.upload(file='/pdfs/' + file_path)

        logger.info(f"File uploaded with URI: {uploaded_file}")
                
        # Check the file status and wait until it is ACTIVE
        while uploaded_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            time.sleep(2) # Wait for 5 seconds before re-checking
            # Re-fetch the file metadata to get the current state
            uploaded_file = client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise ValueError(f"File processing failed: {uploaded_file.error.message}")

        print(f"\nFile {uploaded_file.name} is now in state: {uploaded_file.state.name}")
        
        logger.info("Generating content...")

        # 生成內容
        with open("/prompts/reference.md", "r", encoding="utf-8") as f:
            prompt = f.read()
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, uploaded_file],
            config={
                "response_mime_type": "application/json",
                "response_json_schema": REFERENCE_SCHEMA,
            },  
        )

        result = json.loads(response.text)

        # 取得 usage metadata
        tokens_used = None
        input_tokens = None
        output_tokens = None
        
        if hasattr(response, 'usage_metadata'):
            tokens_used = getattr(response.usage_metadata, 'total_token_count', None)
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', None)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', None)

        # 清理 Gemini 檔案
        try:
            client.files.delete(name=uploaded_file.name)
        except:
            pass
        
        logger.info("Processing completed successfully")
        
        return jsonify({
            'success': True, 
            'result': result,
            'metadata': {
                'tokens_used': tokens_used,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            },
            'file_uri': uploaded_file.name
        }), 200
                        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500
    

@app.route('/process-usage', methods=['POST'])
def process_usage():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        logger.info(f"Processing PDF: {file_path}")
            
        # 使用 google-genai 上傳檔案
        logger.info("Uploading to Gemini...")
        uploaded_file = client.files.upload(file='/pdfs/' + file_path)

        logger.info(f"File uploaded with URI: {uploaded_file}")
                
        # Check the file status and wait until it is ACTIVE
        while uploaded_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            time.sleep(2) # Wait for 5 seconds before re-checking
            # Re-fetch the file metadata to get the current state
            uploaded_file = client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise ValueError(f"File processing failed: {uploaded_file.error.message}")

        print(f"\nFile {uploaded_file.name} is now in state: {uploaded_file.state.name}")
        
        logger.info("Generating content...")

        # 生成內容
        with open("/prompts/usage.md", "r", encoding="utf-8") as f:
            prompt = f.read()
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, uploaded_file],
            config={
                "response_mime_type": "application/json",
                "response_json_schema": UsageResult.model_json_schema()
            },  
        )

        result = json.loads(response.text)
        with open(f'/usage_results/{uploaded_file.name}.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 取得 usage metadata
        tokens_used = None
        input_tokens = None
        output_tokens = None
        
        if hasattr(response, 'usage_metadata'):
            tokens_used = getattr(response.usage_metadata, 'total_token_count', None)
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', None)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', None)

        # 清理 Gemini 檔案
        try:
            client.files.delete(name=uploaded_file.name)
        except:
            pass
        
        logger.info("Processing completed successfully")

        return jsonify({
            'success': True, 
            'metadata': {
                'tokens_used': tokens_used,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            },
            'file_uri': uploaded_file.name
        }), 200
                        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8009, debug=True)