import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ai_contract import normalize_ai_analysis


class AIContractTest(unittest.TestCase):
    def test_normalizes_missing_vulnerability_fields(self):
        normalized = normalize_ai_analysis({"vulnerabilidades": [{"titulo": "SSH exposto"}]})

        vuln = normalized["vulnerabilidades"][0]
        self.assertEqual(vuln["titulo"], "SSH exposto")
        self.assertIn("explicacao", vuln)
        self.assertIn("patch", vuln)
        self.assertIn("mermaid", vuln)
        self.assertTrue(vuln["patch"].startswith("## Solucao causal"))

    def test_converts_web_vulnerabilities_to_frontend_contract(self):
        normalized = normalize_ai_analysis({
            "web_vulnerabilidades": [{
                "titulo": "XSS",
                "explicacao": "Input sem escape",
                "patch": "- Escape HTML",
                "mermaid": "graph TD\nA[Input] --> B[XSS]",
            }]
        })

        self.assertEqual(normalized["vulnerabilidades"][0]["titulo"], "XSS")

    def test_report_template_does_not_depend_on_custom_jinja_filter(self):
        template = pathlib.Path(__file__).resolve().parents[1] / "templates" / "report.html.j2"
        self.assertNotIn("markdown_to_html", template.read_text(encoding="utf-8"))

    def test_report_template_does_not_depend_on_custom_jinja_global(self):
        template = pathlib.Path(__file__).resolve().parents[1] / "templates" / "report.html.j2"
        self.assertNotIn("should_show_open_ports", template.read_text(encoding="utf-8"))

    def test_pdf_code_blocks_override_inline_code_styles(self):
        template = pathlib.Path(__file__).resolve().parents[1] / "templates" / "report.html.j2"
        css = template.read_text(encoding="utf-8")

        self.assertIn(".patch-block pre code", css)
        self.assertIn("background: transparent", css)
        self.assertIn("color: #f8fafc", css)


if __name__ == "__main__":
    unittest.main()
