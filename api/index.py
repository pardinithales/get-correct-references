import json
import logging
import time
import requests
from xml.etree import ElementTree as ET
from flask import Flask, render_template, request, jsonify, Response
from io import StringIO
import base64
import csv

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ReferenceProcessor")

app = Flask(__name__)

# Função para fazer requisições ao OpenRouter
def openrouter_request(prompt, api_key, request_id):
    logger.info(f"[{request_id}] Enviando requisição para OpenRouter")
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://example.com",
            "X-Title": "ReferenceProcessor"
        }
        data = {
            "model": "google/gemini-2.0-flash-lite-preview-02-05:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2048
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=10
        )
        if response.status_code != 200:
            logger.error(f"[{request_id}] Erro na API do OpenRouter: {response.status_code} - {response.text}")
            return None
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Erro ao fazer requisição para OpenRouter: {str(e)}")
        return None

# Função para busca na PubMed API com validação mais flexível
def pubmed_request(parsed_data, request_id):
    logger.info(f"[{request_id}] Consultando PubMed para enriquecer dados")
    try:
        query_parts = [parsed_data.get("title", "")]
        if parsed_data.get("year"):
            query_parts.append(str(parsed_data["year"]))
        query = " ".join(filter(None, query_parts))
        if not query:
            logger.warning(f"[{request_id}] Nenhum dado válido para busca na PubMed")
            return parsed_data

        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": 1,
            "retmode": "json"
        }
        response = requests.get(esearch_url, params=params, timeout=10)
        if response.status_code != 200:
            logger.error(f"[{request_id}] Erro no esearch da PubMed: {response.status_code} - {response.text}")
            return parsed_data
        
        search_data = response.json()
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            logger.info(f"[{request_id}] Nenhum resultado encontrado no esearch da PubMed para query: {query}")
            return parsed_data
        
        pmid = id_list[0]
        logger.info(f"[{request_id}] PMID encontrado: {pmid}")

        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
            "rettype": "medline"
        }
        response = requests.get(efetch_url, params=params, timeout=10)
        if response.status_code != 200:
            logger.error(f"[{request_id}] Erro no efetch da PubMed: {response.status_code} - {response.text}")
            return parsed_data
        
        root = ET.fromstring(response.content)
        article = root.find(".//Article")
        if article is None:
            logger.info(f"[{request_id}] Nenhum artigo encontrado no XML da PubMed")
            return parsed_data

        title = article.findtext("ArticleTitle") or parsed_data.get("title", "")
        original_title_words = set(parsed_data.get("title", "").lower().split())
        pubmed_title_words = set(title.lower().split())
        common_words = original_title_words.intersection(pubmed_title_words)
        common_words_list = list(common_words)

        if len(common_words) > 0:
            some_value = common_words_list[0]  # This works

        # Or simply don't try to index it at all if you don't need to   
        authors = [author.findtext("LastName") + " " + author.findtext("Initials", "")
                  for author in article.findall(".//Author")] or parsed_data.get("authors", ["Unknown"])
        journal = article.find(".//Journal/Title")
        journal_title = journal.text if journal is not None else parsed_data.get("journal", "")
        year = article.findtext(".//JournalIssue/PubDate/Year") or parsed_data.get("year", "")
        volume = article.findtext(".//JournalIssue/Volume") or parsed_data.get("volume", "")
        issue = article.findtext(".//JournalIssue/Issue") or parsed_data.get("issue", "")
        pages = article.findtext(".//Pagination/MedlinePgn") or parsed_data.get("pages", "")
        
        doi = None
        for article_id in root.findall(".//ArticleId"):
            if article_id.get("IdType") == "doi":
                doi = article_id.text
                break
        doi = doi or parsed_data.get("doi", "")
        url = f"https://doi.org/{doi}" if doi else parsed_data.get("url", "")

        result = {
            "title": title,
            "authors": [a.strip() for a in authors if a.strip()],
            "year": year,
            "journal": journal_title,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "doi": doi,
            "url": url,
            "status": "found",
            "confidence": max(parsed_data.get("confidence", 0), 0.95),
            "original_reference": parsed_data.get("original_reference", query)
        }
        logger.info(f"[{request_id}] Dados enriquecidos pela PubMed")
        return result
    except Exception as e:
        logger.error(f"[{request_id}] Erro ao consultar PubMed: {str(e)}")
        return parsed_data

# Função para extrair JSON da resposta do OpenRouter, lidando com caracteres inválidos
def extract_json_from_text(text):
    if not text:
        return None
    try:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        
        # Replace all control characters (ASCII codes 0-31) with spaces
        # except for allowed whitespace characters like \n, \r, \t
        cleaned_text = ''
        for c in text:
            if ord(c) < 32 and c not in '\n\r\t':
                cleaned_text += ' '
            else:
                cleaned_text += c
                
        return json.loads(cleaned_text.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"Erro ao decodificar JSON: {str(e)} - Texto: {text}")
        return None

# Função principal para processar uma referência
def process_reference(reference, api_key, request_id):
    if not reference.strip():
        return {"status": "not_found", "error": "Empty reference", "original_reference": reference}

    prompt = f"""[Request: Extract reference data]
Input: "{reference}"
Output format: JSON only
Fields: title (string), authors (list of strings), year (int or null), journal (string), volume (string), issue (string or null), pages (string), doi (string), url (string), status ("found" or "not_found"), confidence (float 0-1), original_reference (string)
Rules:
- Parse flexibly: extract as much metadata as possible from the input
- DOI format: 10.xxxx/xxxx if present
- URL: https://doi.org/[DOI] if DOI exists, otherwise empty string
- Status: "found" if metadata is extracted, "not_found" if unable to parse
- Confidence: 0-1 float based on parsing certainty
- original_reference: the exact input text
- Return only valid JSON, no additional text or code blocks"""

    max_retries = 2
    retry_delay = 1

    for attempt in range(1, max_retries + 1):
        try:
            start_time = time.perf_counter()
            logger.info(f"[{request_id}] Processing attempt {attempt}/{max_retries}")
            response = openrouter_request(prompt, api_key, request_id)
            elapsed = time.perf_counter() - start_time
            logger.info(f"[{request_id}] API response received in {elapsed:.2f}s")

            if not response or 'choices' not in response or not response['choices']:
                logger.warning(f"[{request_id}] Resposta inválida do OpenRouter: {response}")
                raise ValueError("Invalid API response structure")

            content = response['choices'][0]['message']['content']
            logger.debug(f"[{request_id}] API response content: {content}")
            result = extract_json_from_text(content)

            if result is None:
                logger.warning(f"[{request_id}] Falha ao extrair JSON da resposta: {content}")
                raise ValueError("No valid JSON extracted from API response")

            if not isinstance(result, dict):
                logger.error(f"[{request_id}] Resultado não é um dicionário: {result}")
                raise TypeError(f"Expected dict, got {type(result).__name__}")

            result["original_reference"] = reference
            if result.get("doi") and not result.get("url"):
                result["url"] = f"https://doi.org/{result['doi']}"

            if result.get("status") == "found":
                enriched_result = pubmed_request(result, request_id)
                logger.info(f"[{request_id}] Referência processada com sucesso")
                return enriched_result

            raise ValueError("Status not 'found' after parsing")

        except Exception as e:
            logger.error(f"[{request_id}] Attempt {attempt} failed: {str(e)}")
            if attempt < max_retries:
                time.sleep(retry_delay)

    return {
        "status": "not_found",
        "error": "All attempts failed",
        "original_reference": reference
    }

# Função para processar múltiplas referências
def process_references(references, api_key):
    if not api_key:
        return {"error": "Chave API do OpenRouter não fornecida"}, 400

    request_id = f"REQ_{int(time.time()*1000)}"
    logger.info(f"[{request_id}] Iniciando processamento de {len(references)} referências")
    start_time = time.perf_counter()
    results = []
    for i, ref in enumerate(references):
        logger.info(f"[{request_id}] Processando referência {i+1}/{len(references)}")
        result = process_reference(ref, api_key, request_id)
        results.append(result)
    elapsed = time.perf_counter() - start_time
    logger.info(f"[{request_id}] Processamento concluído em {elapsed:.2f}s")
    return results, elapsed

# Funções para gerar arquivos de download
def generate_json_data(data):
    return json.dumps(data, ensure_ascii=False, indent=2)

def generate_ris_data(data):
    output = []
    for item in data:
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
        lines.append("ER  - ")
        output.append("\n".join(lines))
    return "\n".join(output)

def generate_csv_data(data):
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

# Rotas Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    request_id = f"REQ_{int(time.time()*1000)}"
    logger.info(f"[{request_id}] New request received")

    text = request.form.get('text', '')
    api_key = request.form.get('api_key', '')

    if not text:
        logger.warning(f"[{request_id}] Nenhum texto fornecido na requisição")
        return jsonify({'error': 'Nenhum texto fornecido'}), 400
    if not api_key:
        logger.warning(f"[{request_id}] Chave API do OpenRouter não fornecida")
        return jsonify({'error': 'Chave API do OpenRouter não fornecida'}), 400

    logger.info(f"[{request_id}] Texto recebido com {len(text)} caracteres")
    references = [line.strip() for line in text.split('\n') if line.strip()]
    logger.info(f"[{request_id}] Parsed {len(references)} references from input")

    try:
        results, processing_time = process_references(references, api_key)
        json_data = generate_json_data(results)
        ris_data = generate_ris_data(results)
        csv_data = generate_csv_data(results)

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
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')
        content_types = {
            'json': ('application/json', 'references.json'),
            'ris': ('application/x-research-info-systems', 'references.ris'),
            'csv': ('text/csv', 'references.csv')
        }
        if format_type not in content_types:
            logger.warning(f"[{request_id}] Unsupported format: {format_type}")
            return jsonify({'error': 'Unsupported format'}), 400
        content_type, filename = content_types[format_type]
        response = Response(decoded_data)
        response.headers['Content-Type'] = content_type
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        logger.info(f"[{request_id}] Sending {format_type} file")
        return response
    except Exception as e:
        logger.error(f"[{request_id}] Download failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
