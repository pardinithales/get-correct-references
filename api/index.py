import os
import json
import tempfile
import logging
import datetime
import re
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
from dotenv import load_dotenv

# Configuração de logging robusta
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(log_dir, exist_ok=True)

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"gemini_process_{timestamp}.log")

# Formatter personalizado que lida com request_id opcional
class CustomFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = 'N/A'  # Valor padrão se request_id não estiver presente
        return super().format(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s - [RequestID:%(request_id)s]',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Aplicar o formatter personalizado
for handler in logging.getLogger().handlers:
    handler.setFormatter(CustomFormatter(
        '%(asctime)s - %(levelname)s - %(message)s - [RequestID:%(request_id)s]'
    ))

class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        request_id = kwargs.pop('extra', {}).get('request_id', 'N/A')
        return msg, {'extra': {'request_id': request_id}}

logger = RequestLoggerAdapter(logging.getLogger("EnhancedGeminiApp"), {})

# Carregar variáveis de ambiente com cache
@lru_cache()
def load_environment():
    load_dotenv()
    return os.environ.get("GEMINI_API_KEY")

GEMINI_API_KEY = load_environment()
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("API Gemini initialized", extra={'request_id': 'SYSTEM_INIT'})

app = Flask(__name__)

@lru_cache(maxsize=1000)
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
    return None

class EnhancedGeminiProcessor:
    def __init__(self, max_retries=2, retry_delay=1):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = RequestLoggerAdapter(logging.getLogger("GeminiProcessor"), {})

    @lru_cache(maxsize=500)
    def get_optimized_prompt(self, reference):
        return f"""[Request: Extract reference data]
Input: "{reference}"
Output format: JSON only
Fields: title, authors (list), year, journal, volume, issue, pages, doi, url, status, confidence
Rules:
- DOI format: 10.xxxx/xxxx
- URL: https://doi.org/[DOI] if DOI exists
- Status: "found" or "not_found"
- Confidence: 0-1 float"""

    def process_single_reference(self, reference, request_id):
        if not reference.strip():
            return {"status": "not_found", "error": "Empty reference"}
        
        prompt = self.get_optimized_prompt(reference)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        for attempt in range(1, self.max_retries + 1):
            try:
                start_time = time.perf_counter()
                self.logger.info(f"Processing attempt {attempt}/{self.max_retries}", 
                               extra={'request_id': request_id})
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=2048,
                        response_mime_type="application/json"
                    )
                )
                
                elapsed = time.perf_counter() - start_time
                self.logger.info(f"API response received in {elapsed:.2f}s",
                               extra={'request_id': request_id})
                
                result = extract_json_from_text(response.text)
                if result:
                    result["original_reference"] = reference
                    if result.get("doi") and not result.get("url"):
                        result["url"] = f"https://doi.org/{result['doi']}"
                    self.logger.info(f"Successfully processed: {result.get('title', 'N/A')[:50]}",
                                   extra={'request_id': request_id})
                    return result
                
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
            
            except Exception as e:
                self.logger.error(f"Attempt {attempt} failed: {str(e)}",
                                extra={'request_id': request_id})
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
        
        return {"status": "not_found", "error": "All attempts failed"}

    def process_references(self, references_list, request_id):
        self.logger.info(f"Starting to process {len(references_list)} references",
                        extra={'request_id': request_id})
        
        start_time = time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(
                lambda ref: self.process_single_reference(ref, request_id),
                [ref for ref in references_list if ref.strip()]
            ))
        
        elapsed = time.perf_counter() - start_time
        found_count = sum(1 for r in results if r.get("status") == "found")
        self.logger.info(f"Completed in {elapsed:.2f}s - Found: {found_count}/{len(results)}",
                        extra={'request_id': request_id})
        
        return results

    def save_json(self, data, output_file):
        start_time = time.perf_counter()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"JSON saved in {time.perf_counter() - start_time:.2f}s",
                        extra={'request_id': 'FILE_OP'})
        return output_file

    def generate_ris(self, data, output_file):
        start_time = time.perf_counter()
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                if item.get("status") == "found":
                    f.write("TY  - JOUR\n")
                    if item.get("authors"):
                        authors = item["authors"]
                        if isinstance(authors, list):
                            for author in authors:
                                f.write(f"AU  - {author}\n")
                        elif isinstance(authors, str):
                            f.write(f"AU  - {authors}\n")
                    for key, tag in [("title", "TI"), ("year", "PY"), ("journal", "JO"), 
                                   ("volume", "VL"), ("issue", "IS"), ("pages", "SP"), 
                                   ("doi", "DO"), ("url", "UR"), ("original_reference", "N1")]:
                        if item.get(key):
                            f.write(f"{tag}  - {item[key]}\n")
                    f.write("ER  - \n\n")
                else:
                    f.write("TY  - JOUR\n")
                    f.write(f"N1  - [NOT_FOUND] {item.get('original_reference', '')}\n")
                    if item.get("error"):
                        f.write(f"N1  - Error: {item['error']}\n")
                    f.write("ER  - \n\n")
        elapsed = time.perf_counter() - start_time
        self.logger.info(f"RIS saved in {elapsed:.2f}s", extra={'request_id': 'FILE_OP'})
        return output_file

    def generate_csv(self, data, output_file):
        import csv
        start_time = time.perf_counter()
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['status', 'title', 'authors', 'year', 'journal', 'volume', 'issue', 
                         'pages', 'doi', 'url', 'confidence', 'original_reference']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in data:
                row = {field: item.get(field, '') for field in fieldnames}
                if isinstance(row['authors'], list):
                    row['authors'] = '; '.join(str(author) for author in row['authors'])
                writer.writerow(row)
        elapsed = time.perf_counter() - start_time
        self.logger.info(f"CSV saved in {elapsed:.2f}s", extra={'request_id': 'FILE_OP'})
        return output_file

@app.route('/')
def index():
    logger.info("Serving index page", extra={'request_id': 'PAGE_LOAD'})
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    request_id = f"REQ_{int(time.time()*1000)}"
    logger.info(f"New request received - Input size: {len(request.data)} bytes",
                extra={'request_id': request_id})
    
    # Tentar obter texto da requisição de diferentes formas
    text = None
    
    # Verificar se os dados vieram como form-data
    if request.form:
        text = request.form.get('text', '')
        logger.info("Dados recebidos via form-data", extra={'request_id': request_id})
    
    # Se não encontrou no form, verificar se veio como JSON
    if not text and request.is_json:
        data = request.get_json()
        text = data.get('text', '')
        logger.info("Dados recebidos via JSON", extra={'request_id': request_id})
    
    # Se ainda não encontrou, tentar ler os dados brutos
    if not text and request.data:
        try:
            data = json.loads(request.data.decode('utf-8'))
            text = data.get('text', '')
            logger.info("Dados recebidos via request.data", extra={'request_id': request_id})
        except:
            logger.warning("Falha ao decodificar dados brutos como JSON", extra={'request_id': request_id})
    
    # Registrar detalhes da requisição para diagnóstico
    logger.info(f"Headers: {dict(request.headers)}", extra={'request_id': request_id})
    logger.info(f"Content-Type: {request.content_type}", extra={'request_id': request_id})
    logger.info(f"Dados recebidos: {request.data[:200]}", extra={'request_id': request_id})
    
    if not text:
        logger.warning("Nenhum texto fornecido na requisição", extra={'request_id': request_id})
        return jsonify({'error': 'Nenhum texto fornecido'}), 400
    
    logger.info(f"Texto recebido: {text[:100]}{'...' if len(text) > 100 else ''}", 
               extra={'request_id': request_id})
    
    references = [line.strip() for line in text.split('\n') if line.strip()]
    logger.info(f"Parsed {len(references)} references from input",
                extra={'request_id': request_id})
    
    temp_dir = tempfile.mkdtemp()
    processor = EnhancedGeminiProcessor()
    
    try:
        start_time = time.perf_counter()
        results = processor.process_references(references, request_id)
        
        json_path = processor.save_json(results, os.path.join(temp_dir, 'references.json'))
        processor.generate_ris(results, os.path.join(temp_dir, 'references.ris'))
        processor.generate_csv(results, os.path.join(temp_dir, 'references.csv'))
        
        elapsed = time.perf_counter() - start_time
        found_count = sum(1 for r in results if r.get("status") == "found")
        
        response = {
            'total': len(results),
            'found': found_count,
            'not_found': len(results) - found_count,
            'results': results,
            'temp_dir': temp_dir,
            'processing_time': f"{elapsed:.2f}s"
        }
        
        logger.info(f"Request completed - Total: {len(results)}, Found: {found_count}, Time: {elapsed:.2f}s",
                   extra={'request_id': request_id})
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", extra={'request_id': request_id})
        return jsonify({'error': str(e)}), 500

@app.route('/download/<format_type>')
def download(format_type):
    request_id = f"DL_{int(time.time()*1000)}"
    temp_dir = request.args.get('temp_dir')
    logger.info(f"Download requested - Format: {format_type}", extra={'request_id': request_id})
    
    if not temp_dir or not os.path.exists(temp_dir):
        logger.error("Temp directory not found", extra={'request_id': request_id})
        return jsonify({'error': 'Temporary directory not found'}), 404
    
    file_map = {
        'json': ('references.json', 'application/json'),
        'ris': ('references.ris', 'application/x-research-info-systems'),
        'csv': ('references.csv', 'text/csv')
    }
    
    if format_type in file_map:
        file_path = os.path.join(temp_dir, file_map[format_type][0])
        logger.info(f"Sending file: {file_path}", extra={'request_id': request_id})
        return send_file(file_path, as_attachment=True, 
                        download_name=file_map[format_type][0], 
                        mimetype=file_map[format_type][1])
    else:
        logger.warning(f"Unsupported format: {format_type}", extra={'request_id': request_id})
        return jsonify({'error': 'Unsupported format'}), 400

# Criar diretório de templates se não existir
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
os.makedirs(templates_dir, exist_ok=True)

# Definir a pasta de templates para o Flask
app.template_folder = templates_dir 