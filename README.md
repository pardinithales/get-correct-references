# Processador de Referências Acadêmicas com OpenRouter

Este projeto é uma aplicação web que utiliza o modelo Gemini Flash Lite 2.0 através do OpenRouter para processar e extrair informações estruturadas de referências acadêmicas.

## Funcionalidades

- Processamento de múltiplas referências acadêmicas
- Extração de metadados como título, autores, ano, journal, DOI, etc.
- Exportação dos resultados em formatos JSON, RIS e CSV
- Interface web amigável e responsiva

## Tecnologias Utilizadas

- Python 3.9+
- Flask (Framework web)
- OpenRouter API (Acesso ao modelo Gemini Flash Lite 2.0)
- HTML/CSS/JavaScript (Frontend)

## Configuração para Desenvolvimento Local

1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Execute a aplicação:
   ```
   python api/index.py
   ```
4. Acesse a aplicação em seu navegador em `http://localhost:5000`
5. Insira sua chave API do OpenRouter (obtenha em [openrouter.ai/keys](https://openrouter.ai/keys))

## Deploy na Vercel

Este projeto está configurado para ser facilmente implantado na Vercel:

1. Faça fork deste repositório
2. Conecte o repositório à sua conta Vercel
3. Implante!

## Sobre o OpenRouter e Gemini Flash Lite 2.0

Este aplicativo utiliza o modelo `google/gemini-2.0-flash-lite-preview-02-05:free` através do OpenRouter. Este modelo oferece:

- Contexto de 1 milhão de tokens
- Tempo de resposta rápido
- Alta qualidade de processamento de texto
- Uso gratuito (sujeito a limites de taxa)

Os usuários precisam fornecer sua própria chave API do OpenRouter para usar o aplicativo.

## Estrutura do Projeto

- `api/index.py`: Ponto de entrada da aplicação
- `api/templates/index.html`: Template da interface web
- `requirements.txt`: Dependências do projeto
- `vercel.json`: Configuração para deploy na Vercel

## Licença

MIT

## Autor

Thales Pardini Fagundes 