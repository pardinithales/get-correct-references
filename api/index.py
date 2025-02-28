import os
import json
import base64
import logging
import re
import time
import requests
from functools import lru_cache
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
from io import StringIO

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ReferenceProcessor")

@lru_cache()
def load_environment():
    load_dotenv()
    return {
        "SITE_URL": os.environ.get("SITE_URL", "https://reference-processor.vercel.app"),
        "SITE_NAME": os.environ.get("SITE_NAME", "Processador de Referências Acadêmicas")
    }

def openrouter_request(prompt, api_key, request_id):
    try:
        env = load_environment()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": env["SITE_URL"],
            "X-Title": env["SITE_NAME"]
        }
        data = {
            "model": "google/gemini-2.0-flash-lite-preview-02-05:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2048
        }
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        if response.status_code != 200:
            logger.error(f"[{request_id}] Erro na API: {response.status_code} - {response.text}")
            return None
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Exception: {str(e)}")
        return None

app = Flask(__name__)

def extract_json_from_text(text):
    if not text:
        return None
    patterns = [
        r'```(?:json)?\s*([\s\S]*?)\s*```',
        r'\{[\s\S]*\}',
        r'\[\s*\{[\s\S]*\}\s*\]'
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
    return {"status": "not_found", "error": "Invalid JSON", "api_response": text.strip()}

class ReferenceProcessor:
    def __init__(self, max_retries=2, retry_delay=1):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def get_optimized_prompt(self, reference):
        return f"""Extract as JSON (empty fields allowed): title, authors, year, journal, volume, issue, pages, doi, url, status, confidence from '{reference}'."""

    def process_single_reference(self, reference, request_id, api_key):
        if not reference.strip():
            return {"status": "not_found", "error": "Empty reference", "original_reference": reference}
        prompt = self.get_optimized_prompt(reference)
        for attempt in range(self.max_retries):
            response = openrouter_request(prompt, api_key, request_id)
            if response and 'choices' in response:
                content = response['choices'][0]['message']['content']
                result = extract_json_from_text(content)
                result["original_reference"] = reference
                return result
            time.sleep(self.retry_delay)
        return {"status": "not_found", "error": "All attempts failed", "original_reference": reference}

    def process_references(self, references, request_id, api_key):
        return [self.process_single_reference(r, request_id, api_key) for r in references], time.perf_counter()

    def generate_json_data(self, data):
        return json.dumps(data, ensure_ascii=False, indent=2)

    def generate_ris_data(self, data):
        output = []
        for item in data:
            lines = ["TY  - JOUR"]
            if item.get("status") == "found":
                for author in item.get("authors", []):
                    lines.append(f"AU  - {author}")
                for key, tag in [("title", "TI"), ("year", "PY"), ("journal", "JO"), ("volume", "VL"), ("issue", "IS"), ("pages", "SP"), ("doi", "DO"), ("url", "UR")]:
                    if item.get(key):
                        lines.append(f"{tag}  - {item[key]}")
            else:
                lines.append(f"N1  - [NOT_FOUND] {item['original_reference']}")
                lines.append(f"N1  - Error: {item.get('error', 'No details')}")
                if "api_response" in item:
                    lines.append(f"N1  - API Response: {item['api_response']}")
            lines.append("ER  - ")
            output.append("\n".join(lines))
        return "\n".join(output)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    request_id = f"REQ_{int(time.time()*1000)}"
    text = request.form.get('text') or request.json.get('text')
    api_key = request.form.get('api_key') or request.json.get('api_key')
    if not text or not api_key:
        return jsonify({'error': 'Missing text or API key'}), 400
    references = [line.strip() for line in text.split('\n') if line.strip()]
    processor = ReferenceProcessor()
    results, processing_time = processor.process_references(references, request_id, api_key)
    response = {
        'results': results,
        'processing_time': f"{processing_time:.2f}s"
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
