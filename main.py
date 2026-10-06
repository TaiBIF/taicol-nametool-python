# main.py
from flask import Flask, request, jsonify
import requests
import os
import time
import hashlib
import re
import json
import logging
from google import genai
from google.genai import errors as genai_errors
from utils.usage import UsageResult

app = Flask(__name__)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 Google GenAI 客戶端
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'your-api-key')
client = genai.Client(api_key=GEMINI_API_KEY)

# 使用的模型（改模型只需改 .env 並重建容器）
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.8-flash')

# 測試用快取：off（預設，正常呼叫 AI）/ record（呼叫 AI 並存下結果）/ replay（有存過就直接回傳，不呼叫 AI）
AI_CACHE_MODE = os.environ.get('AI_CACHE_MODE', 'off').lower()
AI_CACHE_DIR = os.environ.get('AI_CACHE_DIR', '/ai_cache')


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
    # author、published 設為必填：新版模型對非必填欄位較容易直接省略
    "required": ["type", "title", "author", "published"]
}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

class AiModelError(Exception):
    """非 APIError 但屬於模型端的失敗（檔案處理失敗、回應被截斷/阻擋/無法解析）"""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def error_response(e):
    if isinstance(e, genai_errors.APIError):
        return jsonify({
            'success': False,
            'error_type': 'ai_model',
            'error_code': e.code,       # 429 / 503 / 504 / 400...
            'error_status': e.status,   # RESOURCE_EXHAUSTED 等
            'error': e.message or str(e),
        }), 502
    if isinstance(e, AiModelError):
        return jsonify({
            'success': False,
            'error_type': 'ai_model',
            'error_code': e.code,
            'error': str(e),
        }), 502
    return jsonify({'success': False, 'error_type': 'internal', 'error': str(e)}), 500


def upload_and_wait(file_path):
    logger.info(f"Uploading to Gemini: {file_path}")
    uploaded_file = client.files.upload(file='/pdfs/' + file_path)

    while uploaded_file.state.name == "PROCESSING":
        time.sleep(2)
        uploaded_file = client.files.get(name=uploaded_file.name)

    if uploaded_file.state.name == "FAILED":
        raise AiModelError(f"File processing failed: {uploaded_file.error.message}", 'FILE_FAILED')

    logger.info(f"File {uploaded_file.name} is now in state: {uploaded_file.state.name}")
    return uploaded_file


RETRYABLE_CODES = (429, 503, 504)


def quota_retry_delay(e):
    """
    解析 429 的額度資訊
    回傳 (是否為每日額度用完, Gemini 建議的等待秒數或 None)
    """
    text = f"{getattr(e, 'details', '')} {getattr(e, 'message', '')} {e}"
    is_daily = 'PerDay' in text
    match = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", text)
    delay = float(match.group(1)) if match else None
    return is_daily, delay


def generate_with_retry(contents, schema, max_total_timeout):
    """
    針對 429 / 503 / 504 做指數退避重試
    429 額度問題：每日額度用完、或建議等待時間超過剩餘重試時間 → 不重試，直接回報
    """
    retry_delay = 2
    max_delay_cap = 30
    start_time = time.time()

    while True:
        try:
            return client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": schema,
                },
            )
        except genai_errors.APIError as e:
            elapsed_time = time.time() - start_time
            if e.code not in RETRYABLE_CODES:
                logger.error(f"Non-retryable Gemini error: {e}")
                raise

            wait = retry_delay
            if e.code == 429:
                is_daily, suggested = quota_retry_delay(e)
                if is_daily:
                    logger.error(f"Gemini daily quota exhausted, not retrying: {e}")
                    raise
                if suggested is not None:
                    # 依 Gemini 建議的時間等待（例如每分鐘上限）
                    wait = suggested
                    if elapsed_time + wait > max_total_timeout:
                        logger.error(f"Gemini suggested retry in {int(wait)}s exceeds timeout, not retrying: {e}")
                        raise

            if elapsed_time + wait > max_total_timeout:
                logger.error(f"Retry timeout ({max_total_timeout}s) exceeded. Last error: {e}")
                raise
            logger.warning(f"Gemini {e.code}, retry in {int(wait)}s (elapsed {int(elapsed_time)}s)")
            time.sleep(wait)
            retry_delay = min(retry_delay * 2, max_delay_cap)


def parse_response(response):
    """檢查回應是否完整，並轉成 dict"""
    feedback = getattr(response, 'prompt_feedback', None)
    if feedback and getattr(feedback, 'block_reason', None):
        raise AiModelError(f"Prompt blocked: {feedback.block_reason}", 'BLOCKED')

    candidates = getattr(response, 'candidates', None) or []
    finish_reason = getattr(candidates[0], 'finish_reason', None) if candidates else None
    reason = getattr(finish_reason, 'name', str(finish_reason)) if finish_reason else None

    if reason == 'MAX_TOKENS':
        raise AiModelError("Response truncated (MAX_TOKENS)", 'MAX_TOKENS')
    if reason in ('SAFETY', 'RECITATION', 'PROHIBITED_CONTENT', 'BLOCKLIST', 'SPII'):
        raise AiModelError(f"Response blocked: {reason}", 'SAFETY')

    if not response.text:
        raise AiModelError(f"Empty response (finish_reason={reason})", 'INVALID_JSON')
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise AiModelError(f"Invalid JSON from model: {e}", 'INVALID_JSON')


def get_usage_metadata(response):
    um = getattr(response, 'usage_metadata', None)
    return {
        'tokens_used': getattr(um, 'total_token_count', None),
        'input_tokens': getattr(um, 'prompt_token_count', None),
        'output_tokens': getattr(um, 'candidates_token_count', None),
    }


def delete_file_quietly(uploaded_file):
    if uploaded_file is None:
        return
    try:
        client.files.delete(name=uploaded_file.name)
    except Exception:
        pass


# ---------- 測試用快取 ----------
def cache_key(file_path, kind):
    """以 PDF 內容的雜湊值當作快取 key（同一份 PDF 重新上傳、檔名不同也能命中）"""
    with open('/pdfs/' + file_path, 'rb') as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    return f"{kind}_{digest}"


def cache_load(key):
    if AI_CACHE_MODE != 'replay':
        return None
    path = os.path.join(AI_CACHE_DIR, key + '.json')
    if not os.path.exists(path):
        logger.info(f"[AI cache] miss: {key}")
        return None
    logger.info(f"[AI cache] hit: {key}（未呼叫 AI）")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def cache_save(key, payload):
    if AI_CACHE_MODE not in ('record', 'replay'):
        return
    os.makedirs(AI_CACHE_DIR, exist_ok=True)
    with open(os.path.join(AI_CACHE_DIR, key + '.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info(f"[AI cache] saved: {key}")


@app.route('/process-reference', methods=['POST'])
def process_reference():
    uploaded_file = None
    try:
        file_path = request.get_json().get('file_path')
        logger.info(f"Processing reference PDF: {file_path}")

        key = cache_key(file_path, 'reference')
        cached = cache_load(key)
        if cached:
            return jsonify({'success': True, **cached}), 200

        uploaded_file = upload_and_wait(file_path)

        with open("/prompts/reference.md", "r", encoding="utf-8") as f:
            prompt = f.read()

        # 同步請求，重試時間不宜過長（Laravel 端 timeout 600s）
        response = generate_with_retry([prompt, uploaded_file], REFERENCE_SCHEMA, max_total_timeout=60)
        result = parse_response(response)

        # 記錄解析結果，方便排查欄位缺漏（不需重新呼叫 AI）
        logger.info("Reference result: %s", json.dumps(result, ensure_ascii=False)[:3000])

        payload = {
            'result': result,
            'metadata': get_usage_metadata(response),
            'file_uri': uploaded_file.name,
        }
        cache_save(key, payload)

        logger.info("Processing completed successfully")
        return jsonify({'success': True, **payload}), 200

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return error_response(e)
    finally:
        delete_file_quietly(uploaded_file)


@app.route('/process-usage', methods=['POST'])
def process_usage():
    uploaded_file = None
    try:
        file_path = request.get_json().get('file_path')
        logger.info(f"Processing usage PDF: {file_path}")

        key = cache_key(file_path, 'usage')
        cached = cache_load(key)
        if cached:
            # 重新寫出結果檔，Laravel 端照常讀取
            file_uri = f"cache/{key}"
            os.makedirs('/usage_results/cache', exist_ok=True)
            with open(f'/usage_results/{file_uri}.json', 'w', encoding='utf-8') as f:
                json.dump(cached['result'], f, ensure_ascii=False, indent=2)
            return jsonify({'success': True, 'metadata': cached.get('metadata', {}), 'file_uri': file_uri}), 200

        uploaded_file = upload_and_wait(file_path)

        with open("/prompts/usage.md", "r", encoding="utf-8") as f:
            prompt = f.read()

        response = generate_with_retry([prompt, uploaded_file], UsageResult.model_json_schema(), max_total_timeout=600)
        result = parse_response(response)

        with open(f'/usage_results/{uploaded_file.name}.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        cache_save(key, {'result': result, 'metadata': get_usage_metadata(response)})

        logger.info("Processing completed successfully")
        return jsonify({
            'success': True,
            'metadata': get_usage_metadata(response),
            'file_uri': uploaded_file.name
        }), 200

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return error_response(e)
    finally:
        delete_file_quietly(uploaded_file)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8009, debug=True)