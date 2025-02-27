# Processador de Referências Acadêmicas

![Versão](https://img.shields.io/badge/versão-1.0-blue)
![Licença](https://img.shields.io/badge/licença-MIT-green)

## 📚 O que é?

Uma ferramenta online que transforma suas referências bibliográficas bagunçadas em dados estruturados e organizados. Ideal para estudantes, pesquisadores e acadêmicos que precisam organizar suas bibliografias.

## 🌐 Acesse Agora

**[referencias.brainin.dev.br](https://referencias.brainin.dev.br)**

## ✨ Funcionalidades

- **Processamento em Lote**: Cole várias referências de uma vez
- **Extração Inteligente**: Identifica automaticamente título, autores, ano, revista, DOI e mais
- **Exportação Flexível**: Baixe seus resultados em JSON, RIS (para gerenciadores de referências) ou CSV (para planilhas)
- **Interface Amigável**: Design responsivo que funciona em qualquer dispositivo

## 🚀 Como Usar

1. Acesse [referencias.brainin.dev.br](brainin.dev.br)
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

## 📝 Licença

MIT

## 👤 Autor

Desenvolvido por Thales Pardini Fagundes

---

### Gostou da ferramenta?

⭐ Dê uma estrela no [repositório GitHub](https://github.com/thales-pardini/get-correct-references)  
🐛 Encontrou um bug? [Abra uma issue](https://github.com/thales-pardini/get-correct-references/issues) 
