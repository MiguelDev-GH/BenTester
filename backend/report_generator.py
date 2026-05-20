import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from ai_contract import normalize_ai_analysis


def should_show_open_ports(scan_data: dict) -> bool:
    open_ports = scan_data.get("open_ports") if scan_data else None
    if not isinstance(open_ports, list):
        return False

    return bool(open_ports) or bool(scan_data.get("status") or scan_data.get("resolved_target"))


class ReportGenerator:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.output_dir = os.path.join(os.path.dirname(__file__), "reports")
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def generate_pdf(self, scan_data: dict, analysis_data: dict) -> str:
        print("[*] Renderizando o template do relatório SEC-OPS...")
        template = self.env.get_template("report.html.j2")
        normalized_analysis = normalize_ai_analysis(analysis_data)
        
        html_content = template.render(
            scan=scan_data,
            show_open_ports=should_show_open_ports(scan_data),
            anomalias=normalized_analysis.get("vulnerabilidades", [])
        )
        
        output_file = os.path.join(self.output_dir, "secops_report.pdf")
        
        print("[*] Convertendo para PDF profissional via WeasyPrint...")
        HTML(string=html_content).write_pdf(output_file)
        
        print(f"[*] Relatório finalizado e salvo em: {output_file}")
        return output_file
