# Processador de Referências Acadêmicas

![Versão](https://img.shields.io/badge/versão-1.0-blue)


Este aplicativo incrível processa referências acadêmicas de graça! Cole sua lista de referências — mesmo as mais caóticas — e ele gera arquivos RIS, CSV e JSON com metadados perfeitos. Totalmente gratuito, usa um modelo da Open Router Free para analisar cada citação, extraindo autores, título, ano, DOI e mais, com retries automáticos para confiabilidade total. Consulta a CrossRef para enriquecer os dados, corrigindo falhas e adicionando URLs e DOIs verificados. Ideal para pesquisadores, elimina erros em manuscritos e entrega referências prontas para Zotero, Mendeley ou submissões. Salva tudo em uma pasta personalizável com logs detalhados!

This fantastic app processes academic references for free! Paste your reference list — even the wildest ones — and it generates RIS, CSV, and JSON files with spot-on metadata. Completely free thanks to an Open Router Free model, it parses each citation, pulling out authors, title, year, DOI, and more, with automatic retries for total reliability. It queries CrossRef to boost the data, fixing gaps and adding verified URLs and DOIs. Perfect for researchers, it wipes out manuscript errors, producing references ready for Zotero, Mendeley, or submissions. Everything’s saved in a customizable folder with detailed logs!
## 🌐 Acesse Agora

**[referencias.brainin.dev.br](https://brainin.dev.br)**

## ✨ Funcionalidades

- **Processamento em Lote**: Cole várias referências de uma vez
- **Extração Inteligente**: Identifica automaticamente título, autores, ano, revista, DOI e mais
- **Exportação Flexível**: Baixe seus resultados em JSON, RIS (para gerenciadores de referências) ou CSV (para planilhas)
- **Interface Amigável**: Design responsivo que funciona em qualquer dispositivo

## 🚀 Como Usar

1. Acesse [referencias.brainin.dev.br](https://brainin.dev.br)
2. Insira sua chave API do OpenRouter (obtenha gratuitamente em [openrouter.ai/keys](https://openrouter.ai/keys))
3. Cole suas referências bibliográficas (uma por linha)
4. Clique em "Processar"
5. Visualize os resultados e baixe no formato desejado

## 🧠 Tecnologia

Este aplicativo utiliza o modelo **Gemini Flash Lite 2.0** da Google através do OpenRouter, oferecendo:

- Processamento de alta qualidade com IA avançada
- Capacidade de entender diversos formatos de referências
- Tempo de resposta rápido
- Uso gratuito (sujeito a limites de taxa do OpenRouter)

## 🔑 Sobre a Chave API

- Você precisa de uma chave API do OpenRouter para usar o aplicativo
- A chave é gratuita e pode ser obtida em [openrouter.ai/keys](https://openrouter.ai/keys)
- Sua chave API é armazenada apenas no seu navegador e nunca em nossos servidores
- Cada usuário usa sua própria chave, garantindo privacidade e controle sobre o uso

## 💡 Dicas de Uso

- Para melhores resultados, inclua o máximo de informações possível em cada referência
- Referências com DOI têm maior taxa de sucesso na extração
- Você pode processar até 100 referências de uma vez
- Sua chave API é salva no navegador para uso futuro

## 🛠️ Para Desenvolvedores

### Tecnologias Utilizadas

- Python 3.9+ com Flask
- OpenRouter API (acesso ao Gemini Flash Lite 2.0)
- HTML/CSS/JavaScript
- Hospedagem serverless na Vercel

### Configuração Local

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute: `python api/index.py`
4. Acesse: `http://localhost:5000`

### Deploy na Vercel

Consulte [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) para instruções detalhadas.


## 👤 Autor

Desenvolvido por Thales Pardini Fagundes

---

### Gostou da ferramenta?

⭐ Dê uma estrela no [repositório GitHub](https://github.com/thales-pardini/get-correct-references)  
🐛 Encontrou um bug? [Abra uma issue](https://github.com/thales-pardini/get-correct-references/issues) 
Instagram: @thalespardinifagundes
X: thales_pardini
