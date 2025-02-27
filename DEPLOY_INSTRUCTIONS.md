# Instruções para Deploy na Vercel

Siga estes passos para fazer o deploy do Processador de Referências Acadêmicas na Vercel:

## 1. Preparação do Repositório

1. Crie um novo repositório no GitHub
2. Faça upload dos seguintes arquivos para o repositório:
   - Pasta `api/` com os arquivos `index.py` e `templates/index.html`
   - Arquivo `requirements.txt`
   - Arquivo `vercel.json`
   - Arquivo `.gitignore`
   - Arquivo `README.md`

## 2. Configuração na Vercel

1. Acesse [vercel.com](https://vercel.com) e faça login com sua conta
2. Clique em "Add New" > "Project"
3. Importe o repositório GitHub que você criou
4. Na seção de configuração do projeto:
   - Framework Preset: Deixe como "Other"
   - Root Directory: Deixe como "/"
   - Build Command: Deixe em branco
   - Output Directory: Deixe em branco
   - Install Command: `pip install -r requirements.txt`

5. Expanda a seção "Environment Variables" e adicione:
   - Nome: `GEMINI_API_KEY`
   - Valor: Sua chave API do Gemini (obtenha em [ai.google.dev](https://ai.google.dev))

6. Clique em "Deploy"

## 3. Verificação do Deploy

1. Após o deploy ser concluído, a Vercel fornecerá uma URL para acessar sua aplicação
2. Acesse a URL e verifique se a aplicação está funcionando corretamente
3. Teste o processamento de algumas referências acadêmicas

## 4. Configurações Adicionais (Opcional)

1. Configure um domínio personalizado nas configurações do projeto na Vercel
2. Ajuste as configurações de cache se necessário
3. Configure integrações com serviços de monitoramento

## Solução de Problemas

Se encontrar problemas durante o deploy:

1. Verifique os logs de build e função na interface da Vercel
2. Certifique-se de que a chave API do Gemini está correta
3. Verifique se todos os arquivos necessários estão no repositório
4. Verifique se a estrutura de diretórios está correta

## Limitações na Vercel

- Os arquivos temporários criados durante o processamento serão perdidos após a execução da função
- O download de arquivos pode não funcionar como esperado devido à natureza serverless
- Considere adaptar o código para usar armazenamento em nuvem (como AWS S3) para uma solução mais robusta 