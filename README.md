# Processador de Referências Acadêmicas com Gemini AI

Este projeto é uma aplicação web que utiliza a API Gemini da Google para processar e extrair informações estruturadas de referências acadêmicas.

## Funcionalidades

- Processamento de múltiplas referências acadêmicas
- Extração de metadados como título, autores, ano, journal, DOI, etc.
- Exportação dos resultados em formatos JSON, RIS e CSV
- Interface web amigável e responsiva

## Tecnologias Utilizadas

- Python 3.9+
- Flask (Framework web)
- Google Generative AI (Gemini API)
- HTML/CSS/JavaScript (Frontend)

## Configuração para Desenvolvimento Local

1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` na raiz do projeto com sua chave API do Gemini:
   ```
   GEMINI_API_KEY=sua_chave_api_aqui
   ```
4. Execute a aplicação:
   ```
   python api/index.py
   ```

## Deploy na Vercel

Este projeto está configurado para ser facilmente implantado na Vercel:

1. Faça fork deste repositório
2. Conecte o repositório à sua conta Vercel
3. Configure a variável de ambiente `GEMINI_API_KEY` nas configurações do projeto na Vercel
4. Implante!

## Estrutura do Projeto

- `api/index.py`: Ponto de entrada da aplicação
- `api/templates/index.html`: Template da interface web
- `requirements.txt`: Dependências do projeto
- `vercel.json`: Configuração para deploy na Vercel

## Licença

MIT

## Autor

Thales Pardini Fagundes 