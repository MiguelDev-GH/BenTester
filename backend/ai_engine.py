import os
import json
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import asyncio
from ai_contract import normalize_ai_analysis

# Load .env at module level to ensure variables are available
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# OpenAI models available for Plus plan
OPENAI_MODELS = {
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "o1",
    "o1-mini",
    "o3-mini",
    "o4-mini",
}

class PentestAIEngine:
    def __init__(self, model_name: str = None):
        # ── Determine provider based on model name ────────────────────────────
        # If the model is a known OpenAI model, use OpenAI; otherwise use Gemini.
        self.provider = "openai" if (model_name and model_name in OPENAI_MODELS) else "gemini"

        if self.provider == "openai":
            self._init_openai(model_name)
        else:
            self._init_gemini(model_name)

        # ── Prompt modo INFRA (Nmap) ──────────────────────────────────────────
        self.prompt_template = PromptTemplate(
            input_variables=["scan_data"],
            template="""
Você é um Arquiteto de Software Especialista e Engenheiro de Segurança Principal (SecOps) Autônomo.
Analise o seguinte resultado de varredura (scan) de um ambiente isolado:

[DADOS DO SCAN EM JSON]
{scan_data}

Quais são as falhas essenciais ou vulnerabilidades que você detecta nos serviços e portas abertas? Crie uma resposta de raciocínio profundo formatada da seguinte forma:
(a) Uma prova documental de como isso é explorável junto com uma explicação técnica profunda de por que o código gera o bug.
(b) Gere a solução ou patch causal em Markdown legível, usando títulos curtos, listas e blocos de código quando houver código pronto para aplicação.
(c) Crie uma estrutura visual para Mermaid.js que descreva explicitamente o caminho lógico da detecção.

Retorne SOMENTE um JSON estruturado com os seguintes campos (sem crases Markdown, apenas o JSON cru):
CONTRATO OBRIGATORIO:
- Nunca omita os campos titulo, explicacao, patch e mermaid.
- O campo patch deve ser Markdown puro, com titulos, listas e blocos ``` quando houver codigo.
- O campo patch NAO deve usar HTML.
- Se nao houver codigo aplicavel, escreva passos de mitigacao em Markdown.
{{
    "vulnerabilidades": [
        {{
            "titulo": "Nome da Falha",
            "explicacao": "Sua prova técnica (use tags HTML como <br> e <b> para formatar o texto e quebrar linhas)",
            "patch": "Resposta em Markdown com a solução causal, passos de correção e blocos de código quando aplicável",
            "mermaid": "graph TD\\nA[Identificacao] --> B[Analise]\\nB --> C[Conclusao]\\n(REGRA CRITICA para o campo mermaid: Use SOMENTE letras ASCII sem acento, numeros e espacos nos rotulos dos nos. PROIBIDO usar acentos, cedilha, parenteses, colchetes extras, aspas ou qualquer caractere especial. Ex CORRETO: A[Deteccao de Portas] --> B[Vulnerabilidade Encontrada]. Ex ERRADO: A[Detecção de Risco (Alto)] --> B[Não Seguro].)"
        }}
    ]
}}
"""
        )
        self.chain = self.prompt_template | self.llm

    # ─────────────────────────────────────────────────────────────────────────
    # Provider initialisation helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _init_gemini(self, model_name: str = None):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "sua_chave_aqui":
            raise ValueError("[CRITICAL ERROR] GOOGLE_API_KEY not found or invalid in .env file. Please add your real Gemini API key.")
        os.environ["GOOGLE_API_KEY"] = api_key

        chosen_model = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        print(f"[*] Conectando ao Gemini com o modelo {chosen_model}...")
        self.llm = ChatGoogleGenerativeAI(
            model=chosen_model,
            temperature=0.2,
            api_key=api_key,
            max_retries=2
        )

    def _init_openai(self, model_name: str = None):
        from langchain_openai import ChatOpenAI

        # Read key from .env
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key == "sua_chave_openai_aqui":
            raise ValueError("[CRITICAL ERROR] OPENAI_API_KEY não encontrada ou inválida no .env. Adicione sua chave real da OpenAI.")

        chosen_model = model_name or "gpt-4o-mini"
        print(f"[*] Conectando à OpenAI com o modelo {chosen_model}...")
        self.llm = ChatOpenAI(
            model=chosen_model,
            temperature=0.2,
            api_key=api_key,
            max_retries=2
        )

    # ─────────────────────────────────────────────────────────────────────────
    # MODO INFRA: análise de scan Nmap
    # ─────────────────────────────────────────────────────────────────────────
    async def analyze_scan(self) -> dict:
        try:
            with open("scan_results.json", "r", encoding="utf-8") as f:
                scan_data_str = f.read()
        except FileNotFoundError:
            return {"error": "Arquivo scan_results.json não encontrado. Execute o scanner primeiro."}
            
        print(f"[*] Iniciando análise de dados (Tamanho: {len(scan_data_str)} bytes)...")
        print("[*] Enviando solicitação para a IA Generativa (isso pode levar de 5 a 20 segundos)...")
        
        try:
            response = await self.chain.ainvoke({"scan_data": scan_data_str})
            print("[✓] Resposta da IA recebida com sucesso!")
        except Exception as e:
            msg = self._friendly_error(e)
            print(f"[ERRO] A IA falhou ao processar a solicitação: {str(e)}")
            return {"error": msg, "status": "ai_failure"}
        
        return normalize_ai_analysis(self._parse_json_response(response.content))

    # ─────────────────────────────────────────────────────────────────────────
    # MODO WEB: análise DAST multimodal (HTML + Screenshot + Console Logs)
    # ─────────────────────────────────────────────────────────────────────────
    async def analyze_web_target(self, web_data: dict) -> dict:
        """
        Análise multimodal: envia ao modelo o HTML renderizado, o screenshot
        (imagem JPEG em Base64) e os logs do console da página alvo.
        Retorna JSON com fingerprint de IA, riscos de injeção e riscos de console.
        """
        url = web_data.get("url", "N/A")
        html_snippet = web_data.get("html", "")[:12000]   # Limite para não estourar o contexto
        screenshot_b64 = web_data.get("screenshot_b64", "")
        console_logs = web_data.get("console_logs", [])
        network_errors = web_data.get("network_errors", [])

        # Formata logs do console em texto legível
        console_text = "\n".join(
            f"[{log['type'].upper()}] {log['text']}  @ {log.get('location', '')}"
            for log in console_logs
        ) or "Nenhum log de console capturado."

        network_text = "\n".join(
            f"[FALHA REDE] {e['method']} {e['url']} → {e['failure']}"
            for e in network_errors
        ) or "Nenhum erro de rede."

        prompt_text = f"""Você é um Engenheiro de Segurança Ofensiva (Red Team) e especialista em análise de aplicações web.
Analise a aplicação web em: {url}

Você recebeu três fontes de dados:
1. **HTML RENDERIZADO** (DOM pós-execução de JavaScript, primeiros 12000 chars):
```html
{html_snippet}
```

2. **LOGS DO CONSOLE DO NAVEGADOR** (capturados durante o carregamento):
```
{console_text}
```

3. **ERROS DE REDE** (requisições que falharam):
```
{network_text}
```

4. **SCREENSHOT** da página (imagem anexada à esta mensagem).

Realize uma análise DAST (Dynamic Application Security Testing) completa e retorne SOMENTE um JSON cru (sem crases Markdown) com esta estrutura exata:
CONTRATO OBRIGATORIO:
- Nunca omita os campos titulo, explicacao, patch e mermaid em web_vulnerabilidades.
- O campo patch deve ser Markdown puro, com titulos, listas e blocos ``` quando houver codigo.
- O campo patch NAO deve usar HTML.
- Se nao houver codigo aplicavel, escreva passos de mitigacao em Markdown.
{{
    "fingerprint_ia": {{
        "detectado": true ou false,
        "confianca": "alta/media/baixa",
        "evidencias": ["evidência 1", "evidência 2"],
        "explicacao": "Explicação de por que esta página parece (ou não) gerada por ferramentas automáticas/IA. Use tags HTML <br> e <b>."
    }},
    "web_vulnerabilidades": [
        {{
            "titulo": "Nome da Vulnerabilidade",
            "categoria": "SQLi | XSS | CSRF | IDOR | InfoDisclosure | MiscConfig | Outro",
            "severidade": "Crítica | Alta | Média | Baixa | Informação",
            "explicacao": "Prova técnica detalhada com referência ao DOM/HTML. Use tags HTML <br> e <b>.",
            "evidencia_dom": "Trecho de código HTML ou padrão que prova a vulnerabilidade",
            "patch": "Resposta em Markdown com a solução causal, recomendação técnica e blocos de código quando aplicável",
            "mermaid": "graph TD\\nA[Atacante] --> B[Explora Input]\\nB --> C[Injecao SQL]"
        }}
    ],
    "riscos_console": [
        {{
            "titulo": "Nome do Risco",
            "tipo": "vazamento_dados | erro_arquitetura | dependencia_vulneravel | Outro",
            "severidade": "Alta | Média | Baixa",
            "log_original": "Log exato capturado",
            "explicacao": "Por que este log representa um risco de segurança."
        }}
    ],
    "resumo_executivo": "Parágrafo resumindo os principais riscos encontrados na análise. Use tags HTML <br> e <b>."
}}"""

        print(f"[*] Iniciando análise multimodal DAST para {url}...")
        print(f"[*] Contexto: {len(html_snippet)} chars HTML, {len(console_logs)} console logs, screenshot={bool(screenshot_b64)}")

        # ── Monta mensagem multimodal (texto + imagem) ────────────────────────
        content_parts = [{"type": "text", "text": prompt_text}]

        # Note: vision (image) is only supported by Gemini and GPT-4 Vision models.
        # For OpenAI, only attach image if the model supports it (gpt-4o, gpt-4-turbo, gpt-4.1*).
        supports_vision = self.provider == "gemini" or (self.provider == "openai" and any(
            m in (self.llm.model_name if hasattr(self.llm, "model_name") else "")
            for m in ["gpt-4o", "gpt-4-turbo", "gpt-4.1"]
        ))

        if screenshot_b64 and supports_vision:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}"},
            })

        message = HumanMessage(content=content_parts)

        try:
            response = await self.llm.ainvoke([message])
            print("[✓] Resposta multimodal da IA recebida com sucesso!")
        except Exception as e:
            msg = self._friendly_error(e)
            print(f"[ERRO] Análise multimodal falhou: {str(e)}")
            return {"error": msg, "status": "ai_failure"}

        parsed = normalize_ai_analysis(self._parse_json_response(response.content))
        self._save_analysis(parsed)
        return parsed

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _parse_json_response(self, raw_content: str) -> dict:
        raw_text = raw_content.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        try:
            parsed_data = json.loads(raw_text)
            self._save_analysis(parsed_data)
            return parsed_data
        except json.JSONDecodeError as e:
            print(f"[ERRO] Falha ao analisar JSON da IA: {e}")
            return {"error": "A IA não retornou um JSON válido.", "raw": raw_text}

    def _save_analysis(self, data: dict):
        with open("analysis_results.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("[*] Análise salva em analysis_results.json")

    def _friendly_error(self, exc: Exception) -> str:
        """
        Converte exceções brutas das APIs (OpenAI / Google) em mensagens
        de uma frase, prontas para exibir no frontend.
        """
        raw = str(exc)

        # ── Códigos HTTP conhecidos ───────────────────────────────────────────
        if "429" in raw or "insufficient_quota" in raw or "rate_limit" in raw.lower():
            provider = "OpenAI" if self.provider == "openai" else "Google Gemini"
            return f"Cota da API {provider} esgotada — verifique seu plano e faturamento."

        if "401" in raw or "invalid_api_key" in raw or "API_KEY_INVALID" in raw:
            provider = "OpenAI" if self.provider == "openai" else "Google Gemini"
            return f"Chave de API {provider} inválida — confira o valor no arquivo .env."

        if "403" in raw or "permission" in raw.lower():
            return "Sem permissão para usar este modelo — verifique as configurações da sua conta."

        if "404" in raw or "NOT_FOUND" in raw or "not found" in raw.lower():
            return "Modelo não encontrado na API — pode estar indisponível ou com nome incorreto."

        if "503" in raw or "overloaded" in raw.lower() or "unavailable" in raw.lower():
            return "Serviço de IA temporariamente indisponível — tente novamente em alguns instantes."

        if "timeout" in raw.lower() or "timed out" in raw.lower():
            return "A requisição para a IA excedeu o tempo limite — tente novamente."

        if "connect" in raw.lower() or "network" in raw.lower() or "connection" in raw.lower():
            return "Falha de conexão com a API de IA — verifique sua internet."

        # ── Tenta extrair o campo 'message' do JSON de erro da OpenAI ────────
        try:
            import re
            match = re.search(r"'message':\s*'([^']+)'", raw)
            if match:
                return match.group(1)
            match = re.search(r'"message":\s*"([^"]+)"', raw)
            if match:
                return match.group(1)
        except Exception:
            pass

        # ── Fallback: primeira linha do erro ─────────────────────────────────
        first_line = raw.split("\n")[0][:160]
        return first_line if first_line else "Erro desconhecido ao chamar a IA."

    # ─────────────────────────────────────────────────────────────────────────
    # MODO SAST: análise estática de código fonte
    # ─────────────────────────────────────────────────────────────────────────
    async def analyze_file_target(self, vt_data: dict, filename: str) -> dict:
        """
        Análise de arquivo via VirusTotal + IA: recebe o JSON de detecção do
        VirusTotal e gera um relatório inteligente no formato padrão.
        """
        import json as _json
        vt_json_str = _json.dumps(vt_data, indent=2, ensure_ascii=False)
        print(f"[*] Iniciando análise IA dos dados VirusTotal para {filename}...")

        prompt_text = f"""Você é um Arquiteto de Software Especialista e Engenheiro de Segurança Principal (SecOps) Autônomo.
Analise o seguinte relatório de detecção do VirusTotal para o arquivo "{filename}":

[DADOS DO VIRUSTOTAL EM JSON]
{vt_json_str}

O seu foco principal deve ser em:
1. Interpretar as detecções dos motores antivírus (engines) e suas categorias.
2. Avaliar a gravidade com base nas estatísticas (malicious, suspicious, undetected, harmless).
3. Explicar os riscos reais que este arquivo representa.
4. Recomendar ações de mitigação/remediação.

Retorne SOMENTE um JSON cru (sem crases Markdown) com esta estrutura:
CONTRATO OBRIGATORIO:
- Nunca omita os campos titulo, explicacao, patch e mermaid.
- O campo patch deve ser Markdown puro, com titulos, listas e blocos ``` quando houver comandos ou codigo.
- O campo patch NAO deve usar HTML.
- Se nao houver codigo aplicavel, escreva passos de mitigacao em Markdown.
{{
    "vulnerabilidades": [
        {{
            "titulo": "Nome da Ameaça ou Risco",
            "explicacao": "Prova técnica detalhada baseada nos dados do VirusTotal. Cite engines específicos, categorias e estatísticas. Use tags HTML <br> e <b> para formatar.",
            "patch": "Resposta em Markdown com ações recomendadas de mitigação, quarentena ou remoção",
            "mermaid": "graph TD\\nA[Arquivo Recebido] --> B[Hash SHA256]\\nB --> C[Consulta VirusTotal]\\nC --> D[Analise de Deteccoes]\\nD --> E[Conclusao]\\n(REGRA CRITICA para o campo mermaid: Use SOMENTE letras ASCII sem acento, numeros e espacos nos rotulos dos nos. PROIBIDO usar acentos, cedilha, parenteses, colchetes extras, aspas ou qualquer caractere especial. Ex CORRETO: A[Deteccao de Ameaca] --> B[Arquivo Malicioso]. Ex ERRADO: A[Detecção de Risco (Alto)] --> B[Não Seguro].)"
        }}
    ]
}}"""

        message = HumanMessage(content=[{"type": "text", "text": prompt_text}])

        try:
            response = await self.llm.ainvoke([message])
            print("[✓] Resposta IA (VirusTotal) recebida!")
        except Exception as e:
            msg = self._friendly_error(e)
            print(f"[ERRO] Análise IA (VirusTotal) falhou: {str(e)}")
            return {"error": msg, "status": "ai_failure"}

        return normalize_ai_analysis(self._parse_json_response(response.content))


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    engine = PentestAIEngine()
    result = asyncio.run(engine.analyze_scan())
    print(json.dumps(result, indent=2))
