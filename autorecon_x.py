import os
import sys
import json
import time
import socket
import requests
import subprocess
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any

# ==================================================
# 🧩 BASE MODULE (All features inherit from this)
# ==================================================
class RedTeamModule(ABC):
    def __init__(self, target: str):
        self.target = target
        self.name = self.__class__.__name__
        self.description = ""
        self.results = {}

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """Execute module logic"""
        pass

    def log(self, msg: str):
        print(f"[{self.name}] {msg}")

# ==================================================
# 🔍 1. RECONNAISSANCE MODULE (OSINT + Network)
# ==================================================
class ReconModule(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "Passive + Active Recon: DNS, Subdomains, Ports, Tech Stack"

    def run(self) -> Dict[str, Any]:
        self.log("Starting Reconnaissance...")
        data = {
            "timestamp": datetime.now().isoformat(),
            "target": self.target,
            "dns": self._get_dns(),
            "subdomains": self._get_subdomains(),
            "open_ports": self._scan_ports(),
            "tech_stack": self._detect_tech()
        }
        self.results = data
        return data

    def _get_dns(self) -> Dict:
        try:
            return {"A": socket.gethostbyname(self.target)}
        except:
            return {"error": "Failed to resolve"}

    def _get_subdomains(self) -> List[str]:
        # Integration with CRT.SH / Certificate Transparency
        try:
            res = requests.get(f"https://crt.sh/?q=%.{self.target}&output=json", timeout=10)
            if res.status_code == 200:
                subs = list({entry['name_value'] for entry in res.json()})
                return [s for s in subs if '*' not in s]
        except:
            pass
        return []

    def _scan_ports(self) -> List[int]:
        open_ports = []
        common = [21,22,80,443,3389,8080,8443]
        for p in common:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            if s.connect_ex((self.target, p)) == 0:
                open_ports.append(p)
            s.close()
        return open_ports

    def _detect_tech(self) -> List[str]:
        try:
            r = requests.get(f"http://{self.target}", timeout=5)
            tech = []
            if 'nginx' in r.headers.get('Server','').lower(): tech.append("Nginx")
            if 'apache' in r.headers.get('Server','').lower(): tech.append("Apache")
            if 'x-powered-by' in r.headers: tech.append(r.headers['x-powered-by'])
            return tech
        except:
            return []

# ==================================================
# 🎯 2. VULNERABILITY ANALYSIS + EXPLOIT SUGGEST
# ==================================================
class VulnAnalyzer(RedTeamModule):
    def __init__(self, target: str, recon_data: Dict):
        super().__init__(target)
        self.description = "Analyze recon data, find CVEs, suggest exploits"
        self.recon = recon_data

    def run(self) -> Dict[str, Any]:
        self.log("Analyzing vulnerabilities...")
        findings = []

        # Rule-based logic (can replace with LLM later)
        ports = self.recon.get("open_ports", [])
        tech = self.recon.get("tech_stack", [])

        if 80 in ports or 443 in ports:
            findings.append({
                "risk": "Medium",
                "issue": "Web service exposed",
                "cve": "CWE-776",
                "exploit": "Directory brute-force, XSS test"
            })
        if 22 in ports:
            findings.append({
                "risk": "Low",
                "issue": "SSH open",
                "note": "Check weak credentials / old versions"
            })
        if "PHP" in str(tech):
            findings.append({
                "risk": "High",
                "issue": "PHP detected",
                "cve": "Multiple PHP CVEs",
                "exploit": "File upload, RFI"
            })

        return {"vulnerabilities": findings, "risk_score": len(findings)*10}

# ==================================================
# 🕵️ 3. STEALTH PAYLOAD GENERATOR (EDR BYPASS)
# ==================================================
class PayloadGenerator(RedTeamModule):
    def __init__(self, target: str, vuln_data: Dict):
        super().__init__(target)
        self.description = "Generate fileless, obfuscated payloads"
        self.vuln = vuln_data

    def run(self) -> Dict[str, Any]:
        self.log("Generating evasive payload...")
        payloads = []

        # Fileless PowerShell (no disk write)
        ps1 = """
        $code = 'Write-Host "Access Granted"; whoami; hostname'
        $bytes = [System.Text.Encoding]::Unicode.GetBytes($code)
        $encoded = [Convert]::ToBase64String($bytes)
        powershell -EncodedCommand $encoded
        """
        payloads.append({
            "type": "Fileless PowerShell",
            "evasion": "Base64 Obfuscation, No File Drop",
            "code": ps1.strip()
        })

        # Linux Memory Payload
        bash = """
        echo "$(base64 -d <<'EOF'
        IyEvYmluL2Jhc2gKZWNobyAiQWNjZXNzIGdyYW50ZWQiOwp3aG9hbWk7Cg==
        EOF
        )" | bash
        """
        payloads.append({
            "type": "Linux Obfuscated Bash",
            "evasion": "Base64 Wrapped",
            "code": bash.strip()
        })

        return {"payloads": payloads}

# ==================================================
# 📊 4. REPORTING ENGINE (Google Style Output)
# ==================================================
class ReportGenerator:
    @staticmethod
    def generate(recon, vuln, payloads, output_file="autorecon_report.json"):
        report = {
            "project": "AutoRecon-X Red Team Assessment",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "target": recon["target"],
                "open_ports": len(recon["open_ports"]{}),
                "vulns_found": len(vuln["vulnerabilities"]{}),
                "risk_level": "High" if vuln.get("risk_score",0) > 20 else "Medium"
            },
            "details": {
                "recon": recon,
                "vulnerabilities": vuln,
                "payloads": payloads
            },
            "recommendations": [
                "Close unused ports",
                "Update web frameworks",
                "Enable WAF/EDR"
            ]
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Report saved: {output_file}")
        return report

# ==================================================
# 🚀 MAIN FRAMEWORK ORCHESTRATOR
# ==================================================
class AutoReconX:
    def __init__(self, target: str):
        self.target = target
        self.modules = []
        self.data = {}

    def register_module(self, module: RedTeamModule):
        self.modules.append(module)

    def execute(self):
        print("="*60)
        print(f"🚀 AUTORECON-X RED TEAM FRAMEWORK | TARGET: {self.target}")
        print("="*60 + "\n")

        # Step 1: Recon
        recon = ReconModule(self.target)
        self.data["recon"] = recon.run()

        # Step 2: Vuln Analysis
        vuln = VulnAnalyzer(self.target, self.data["recon"])
        self.data["vuln"] = vuln.run()

        # Step 3: Payload
        pay = PayloadGenerator(self.target, self.data["vuln"])
        self.data["payloads"] = pay.run()

        # Step 4: Report
        ReportGenerator.generate(**self.data)

        print("\n✅ ALL MODULES COMPLETED SUCCESSFULLY")

# ==================================================
# 📌 RUN
# ==================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python autorecon_x.py <target-domain-or-ip>")
        sys.exit(1)

    framework = AutoReconX(sys.argv[1])
    framework.execute()
          
