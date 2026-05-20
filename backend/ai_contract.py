import html
import re
from typing import Any


DEFAULT_MERMAID = "graph TD\nA[Entrada] --> B[Analise]\nB --> C[Conclusao]"


def markdown_to_html(markdown: str) -> str:
    lines = str(markdown or "").replace("\r\n", "\n").split("\n")
    output = []
    paragraph = []
    list_items = []
    code_lines = []
    in_code = False

    def render_inline(value: str) -> str:
        escaped = html.escape(value)
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        return escaped

    def flush_paragraph():
        if paragraph:
            output.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list():
        if list_items:
            output.append("<ul>" + "".join(f"<li>{render_inline(item)}</li>" for item in list_items) + "</ul>")
            list_items.clear()

    for line in lines:
        if line.startswith("```"):
            if in_code:
                output.append(f"<pre><code>{html.escape(chr(10).join(code_lines).strip())}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = min(len(heading.group(1)) + 3, 6)
            output.append(f"<h{level}>{render_inline(heading.group(2).strip())}</h{level}>")
            continue

        list_item = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.+)$", line)
        if list_item:
            flush_paragraph()
            list_items.append(list_item.group(1).strip())
            continue

        flush_list()
        paragraph.append(line.strip())

    if in_code:
        output.append(f"<pre><code>{html.escape(chr(10).join(code_lines).strip())}</code></pre>")
    flush_paragraph()
    flush_list()

    return "".join(output)


def normalize_ai_analysis(data: dict[str, Any]) -> dict[str, Any]:
    vulnerabilities = data.get("vulnerabilidades")
    if not isinstance(vulnerabilities, list):
        vulnerabilities = data.get("web_vulnerabilidades")
    if not isinstance(vulnerabilities, list):
        vulnerabilities = []

    normalized = []
    for index, item in enumerate(vulnerabilities, start=1):
        if not isinstance(item, dict):
            item = {"explicacao": str(item)}

        patch = _clean_text(item.get("patch"))
        if not patch:
            patch = (
                "## Solucao causal\n\n"
                "- Revise a evidencia tecnica apresentada.\n"
                "- Aplique uma mitigacao proporcional ao risco identificado.\n"
                "- Reexecute a analise para validar a correcao."
            )

        normalized.append({
            "titulo": _clean_text(item.get("titulo")) or f"Achado de seguranca {index}",
            "explicacao": _clean_text(item.get("explicacao")) or "A IA nao retornou explicacao tecnica para este achado.",
            "patch": patch,
            "patch_html": markdown_to_html(patch),
            "mermaid": _sanitize_mermaid(item.get("mermaid")),
        })

    result = dict(data)
    result["vulnerabilidades"] = normalized
    return result


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _sanitize_mermaid(value: Any) -> str:
    mermaid = _clean_text(value)
    if not mermaid or not mermaid.startswith("graph"):
        return DEFAULT_MERMAID
    return mermaid
