import json
from datetime import datetime
from fpdf import FPDF

class ReportGenerator:
    @staticmethod
    def generate(recon, vuln, payloads, output_dir="reports/"):
        report_data = {
            "project": "AutoRecon-X Assessment",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "target": recon["target"],
                "open_ports": len(recon["open_ports"]),
                "vulns_found": len(vuln["vulnerabilities"]),
                "risk_level": "High" if vuln.get("risk_score",0) > 20 else "Medium"
            },
            "details": {
                "recon": recon,
                "vulnerabilities": vuln,
                "payloads": payloads
            },
            "recommendations": [
                "Close unused ports",
                "Update software versions",
                "Deploy WAF/EDR solution"
            ]
        }

        # Save JSON
        json_path = f"{output_dir}report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=2)

        # Save PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "AutoRecon-X Security Report", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, f"Target: {recon['target']}", ln=True)
        pdf.cell(200, 10, f"Risk Level: {report_data['summary']['risk_level']}", ln=True)
        pdf_path = json_path.replace(".json", ".pdf")
        pdf.output(pdf_path)

        print(f"[✓] Report saved: {json_path} | {pdf_path}")
        return report_data
              
