# BenTester

Uma aplicação que usa a IA para gerenciar os dados de um cliente, com a intenção de verificar a segurança do sistema.

# Funcionalidades

### Gerais

- Envio de arquivos (PDF’s, TXT’s, Códigos em geral, Arquivos executáveis);
- Envio de link (Para a análise de se tal botão de tal site, faz algo relativamente seguro);
- Provas de que tal bug existe e o porquê.
- O código corrigido (Patch).
- A explicação técnica do que foi feito.

### Técnicas

- **Detectar falhas** em códigos de infraestrutura crítica automaticamente;
- **Criar e aplicar "patches" (correções)** em tempo real sem intervenção humana;
- Utilizar uma combinação de técnicas tradicionais de segurança com Grandes Modelos de Linguagem (LLMs);
- Gerar um diagrama de como a IA detecta falhas de segurança.

# IA Pentester (White-Hat)

O foco é automatizar a detecção de vulnerabilidades básicas, educar a equipe sobre cibersegurança e aplicar conceitos de IA no processo, gerando um diagrama do caminho percorrido.

> **⚠️ Regra de Ouro (Ética):** Absolutamente todos os testes, scripts e varreduras serão executados **exclusivamente** em ambientes virtuais locais (`localhost`) ou em máquinas de laboratório (como Metasploitable ou instâncias Docker configuradas para isso). Zero testes em alvos reais.
> 

### 🗺️ Roadmap de Arquitetura (Passo a Passo com termos técnicos)

- **Fase 1: Fundação e Laboratório (Semana Atual)**
    - Configuração do repositório no GitHub para todos os membros.
    - Criação do ambiente de testes seguro (ex: rodar um servidor web local vulnerável de propósito).
    - *Hello World* do projeto em Python.
- **Fase 2: O "Sentido" da IA (Coleta de Dados)**
    - Criar um script simples (ex: usando `socket` ou `nmap` no Python) para ler portas abertas em uma rede local.
    - Salvar o resultado dessa leitura em um arquivo de texto (JSON ou TXT).
- **Fase 3: O "Cérebro" (Integração com IA)**
    - Conectar nosso script a uma API de IA (como a do Gemini ou OpenAI).
    - Fazer o script enviar o relatório de portas abertas para a IA e pedir: "Quais são as vulnerabilidades comuns nessas portas?".

<div align="center">
  <img src="./frontend/src/assets/BenTesterLogo.png" alt="BenTester Logo" width="200">
</div>

# 👥 Equipe
- Miguel Chagas Maciel ( **Scrum Master** )
- João Manoel ( **Developer** - *Security* )
- João Victor ( **Developer** - *Backend* )
- Isabela Arques ( **Developer** - *Frontend* )
- João Pedro ( **Developer** - *General* )
- Pedro Formiga ( **PO** )

# Ferramentas:

### Stack Tecnológica

- **Backend (API & Core):**
    - **Python** + **FastAPI** (alta performance e requisições assíncronas) rodando com **Uvicorn**.
- **Varredura e Coleta:**
    - **python-nmap** (mapeamento de rede e portas) e **httpx** (extração rápida de cabeçalhos e metadados HTTP).
- **Integração de IA:**
    - **LangChain** (framework para orquestrar agentes e estruturar os dados) conectado à **Google Gemini API** ou **OpenAI API**.
- **Interface (Dashboard):**
    - **React** (upload de arquivos e visualização de dados).
- **Geração de Diagramas:**
    - **Mermaid.js** (renderização de fluxogramas dinâmicos gerados pela IA direto no frontend).
- **Relatórios (PDF/HTML):**
    - **Jinja2** (criação dos templates HTML) em conjunto com **WeasyPrint** (exportação profissional para PDF).
- **Laboratório de Testes (Localhost):**
    - **OWASP Juice Shop** (via Docker)
- **Infraestrutura e Deploy:**
    - **Railway** (para hospedar a aplicação final, devido à facilidade de deploy direto do GitHub e suporte nativo aos containers da aplicação).
