import os
import json
import base64
import logging
import datetime
import re
import time
import requests
from functools import lru_cache
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
from io import StringIO

# Configuração de logging simples para ambiente serverless
logging.basicConfig(
    level=logging.DEBUG,  # Alterado para DEBUG para mais detalhes
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ReferenceProcessor")

# Carregar variáveis de ambiente com cache
@lru_cache()
def load_environment():
    load_dotenv()
    return {
        "SITE_URL": os.environ.get("SITE_URL", "https://reference-processor.vercel.app"),
        "SITE_NAME": os.environ.get("SITE_NAME", "Processador de Referências Acadêmicas")
    }

# Função para fazer requisições ao OpenRouter
def openrouter_request(prompt, api_key, request_id):
    """
    Faz uma requisição para o OpenRouter usando o modelo Gemini Flash Lite 2.0
    """
    logger.info(f"[{request_id}] Enviando requisição para OpenRouter")

    try:
        env = load_environment()
        site_url = env["SITE_URL"]
        site_name = env["SITE_NAME"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": site_url,
            "X-Title": site_name
        }

        data = {
            "model": "google/gemini-2.0-flash-lite-preview-02-05:free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )

        if response.status_code != 200:
            logger.error(f"[{request_id}] Erro na API do OpenRouter: {response.status_code} - {response.text}")
            return None

        result = response.json()
        return result

    except Exception as e:
        logger.error(f"[{request_id}] Erro ao fazer requisição para OpenRouter: {str(e)}")
        return None

app = Flask(__name__)

def extract_json_from_text(text):
    """Extrai JSON de texto que pode conter delimitadores de código"""
    if not text:
        return None
    patterns = [
        r'(?:json)?\s*([\s\S]*?)\s*',
        r'{[\s\S]*}',
        r'\s*{\s[\s\S]*\s}\s*'
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
    return None

class ReferenceProcessor:
    def __init__(self, max_retries=2, retry_delay=1):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def get_optimized_prompt(self, reference):
        return f"""[Request: Extract reference data]
Input: "{reference}"
Output format: JSON only
Fields: title, authors (list), year, journal, volume, issue, pages, doi, url, status, confidence
Rules:
- DOI format: 10.xxxx/xxxx
- URL: https://doi.org/[DOI] if DOI exists
- Status: "found" or "not_found"
- Confidence: 0-1 float
- Return only valid JSON, no additional text or code blocks"""

    def process_single_reference(self, reference, request_id, api_key):
        if not reference.strip():
            return {"status": "not_found", "error": "Empty reference", "original_reference": reference}

        prompt = self.get_optimized_prompt(reference)

        for attempt in range(1, self.max_retries + 1):
            try:
                start_time = time.perf_counter()
                logger.info(f"[{request_id}] Processing attempt {attempt}/{self.max_retries}")

                response = openrouter_request(prompt, api_key, request_id)

                elapsed = time.perf_counter() - start_time
                logger.info(f"[{request_id}] API response received in {elapsed:.2f}s")

                if response and 'choices' in response and len(response['choices']) > 0:
                    content = response['choices'][0]['message']['content']
                    logger.debug(f"[{request_id}] API response content: {content}")  # Log do conteúdo bruto
                    result = extract_json_from_text(content)

                    if result is None:
                        logger.warning(f"[{request_id}] Failed to extract JSON from response: {content}")
                        raise ValueError("No valid JSON extracted from API response")

                    if not isinstance(result, dict):
                        logger.error(f"[{request_id}] Result is not a dictionary: {result}")
                        raise TypeError(f"Expected dict, got {type(result).__name__}")

                    result["original_reference"] = reference
                    if result.get("doi") and not result.get("url"):
                        result["url"] = f"https://doi.org/{result['doi']}"
                    logger.info(f"[{request_id}] Successfully processed reference")
                    return result

                else:
                    logger.warning(f"[{request_id}] Invalid API response structure: {response}")

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

            except Exception as e:
                logger.error(f"[{request_id}] Attempt {attempt} failed: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        return {
            "status": "not_found",
            "error": "All attempts failed",
            "original_reference": reference
        }

    def process_references(self, references_list, request_id, api_key):
        logger.info(f"[{request_id}] Processing {len(references_list)} references")

        start_time = time.perf_counter()

        # Processar sequencialmente para evitar problemas com concorrência na Vercel
        results = []
        for i, ref in enumerate(references_list):
            if ref.strip():
                logger.info(f"[{request_id}] Processing reference {i+1}/{len(references_list)}")
                result = self.process_single_reference(ref, request_id, api_key)
                results.append(result)

        elapsed = time.perf_counter() - start_time
        found_count = sum(1 for r in results if r.get("status") == "found")
        logger.info(f"[{request_id}] Completed in {elapsed:.2f}s - Found: {found_count}/{len(results)}")

        return results, elapsed

    def generate_json_data(self, data):
        return json.dumps(data, ensure_ascii=False, indent=2)

    def generate_ris_data(self, data):
        output = []
        for item in data:
            if item.get("status") == "found":
                lines = ["TY  - JOUR"]
                if item.get("authors"):
                    authors = item["authors"]
                    if isinstance(authors, list):
                        for author in authors:
                            lines.append(f"AU  - {author}")
                    elif isinstance(authors, str):
                        lines.append(f"AU  - {authors}")

                for key, tag in [("title", "TI"), ("year", "PY"), ("journal", "JO"),
                              ("volume", "VL"), ("issue", "IS"), ("pages", "SP"),
                              ("doi", "DO"), ("url", "UR"), ("original_reference", "N1")]:
                    if item.get(key):
                        lines.append(f"{tag}  - {item[key]}")

                lines.append("ER  - \n")
            else:
                lines = ["TY  - JOUR"]
                lines.append(f"N1  - [NOT_FOUND] {item.get('original_reference', '')}")
                if item.get("error"):
                    lines.append(f"N1  - Error: {item['error']}")
                lines.append("ER  - \n")

            output.append("\n".join(lines))

        return "\n".join(output)

    def generate_csv_data(self, data):
        import csv
        output = StringIO()
        fieldnames = ['status', 'title', 'authors', 'year', 'journal', 'volume', 'issue',
                     'pages', 'doi', 'url', 'confidence', 'original_reference']

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for item in data:
            row = {field: item.get(field, '') for field in fieldnames}
            if isinstance(row['authors'], list):
                row['authors'] = '; '.join(str(author) for author in row['authors'])
            writer.writerow(row)

        return output.getvalue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    request_id = f"REQ_{int(time.time()*1000)}"
    logger.info(f"[{request_id}] New request received")

    # Tentar obter texto da requisição de diferentes formas
    text = None
    api_key = None

    # Verificar se os dados vieram como form-data
    if request.form:
        text = request.form.get('text', '')
        api_key = request.form.get('api_key', '')
        logger.info(f"[{request_id}] Dados recebidos via form-data")

    # Se não encontrou no form, verificar se veio como JSON
    if not text and request.is_json:
        data = request.get_json()
        text = data.get('text', '')
        api_key = data.get('api_key', '')
        logger.info(f"[{request_id}] Dados recebidos via JSON")

    # Se ainda não encontrou, tentar ler os dados brutos
    if not text and request.data:
        try:
            data = json.loads(request.data.decode('utf-8'))
            text = data.get('text', '')
            api_key = data.get('api_key', '')
            logger.info(f"[{request_id}] Dados recebidos via request.data")
        except:
            logger.warning(f"[{request_id}] Falha ao decodificar dados brutos como JSON")

    if not text:
        logger.warning(f"[{request_id}] Nenhum texto fornecido na requisição")
        return jsonify({'error': 'Nenhum texto fornecido'}), 400

    # Verificar se a chave API foi fornecida
    if not api_key:
        logger.warning(f"[{request_id}] Chave API do OpenRouter não fornecida")
        return jsonify({'error': 'Chave API do OpenRouter não fornecida. Por favor, forneça sua chave API.'}), 400

    logger.info(f"[{request_id}] Texto recebido com {len(text)} caracteres")

    references = [line.strip() for line in text.split('\n') if line.strip()]
    logger.info(f"[{request_id}] Parsed {len(references)} references from input")

    processor = ReferenceProcessor()

    try:
        # Processar referências
        results, processing_time = processor.process_references(references, request_id, api_key)

        # Gerar dados em memória em vez de arquivos
        json_data = processor.generate_json_data(results)
        ris_data = processor.generate_ris_data(results)
        csv_data = processor.generate_csv_data(results)

        # Codificar dados para download
        encoded_data = {
            'json': base64.b64encode(json_data.encode('utf-8')).decode('utf-8'),
            'ris': base64.b64encode(ris_data.encode('utf-8')).decode('utf-8'),
            'csv': base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')
        }

        found_count = sum(1 for r in results if r.get("status") == "found")

        response = {
            'total': len(results),
            'found': found_count,
            'not_found': len(results) - found_count,
            'results': results,
            'encoded_data': encoded_data,
            'processing_time': f"{processing_time:.2f}s"
        }

        logger.info(f"[{request_id}] Request completed - Total: {len(results)}, Found: {found_count}, Time: {processing_time:.2f}s")
        return jsonify(response)

    except Exception as e:
        logger.error(f"[{request_id}] Processing failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<format_type>')
def download(format_type):
    request_id = f"DL_{int(time.time()*1000)}"
    logger.info(f"[{request_id}] Download requested - Format: {format_type}")

    encoded_data = request.args.get('data')
    if not encoded_data:
        logger.error(f"[{request_id}] No encoded data provided")
        return jsonify({'error': 'No data provided'}), 400

    try:
        # Decodificar dados
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')

        # Configurar tipo de conteúdo e nome do arquivo
        content_types = {
            'json': ('application/json', 'references.json'),
            'ris': ('application/x-research-info-systems', 'references.ris'),
            'csv': ('text/csv', 'references.csv')
        }

        if format_type not in content_types:
            logger.warning(f"[{request_id}] Unsupported format: {format_type}")
            return jsonify({'error': 'Unsupported format'}), 400

        # Criar resposta com os dados
        content_type, filename = content_types[format_type]

        response = Response(decoded_data)
        response.headers['Content-Type'] = content_type
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        logger.info(f"[{request_id}] Sending {format_type} file")
        return response

    except Exception as e:
        logger.error(f"[{request_id}] Download failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Definir a pasta de templates para o Flask
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# Iniciar o servidor apenas quando executado diretamente (não quando importado pela Vercel)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
