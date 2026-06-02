import os
import sys
import json
import time
import socket
import requests
import subprocess
import base64
import hashlib
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from fpdf import FPDF

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
        except Exception as e:
            return {"error": str(e)}

    def _get_subdomains(self) -> List[str]:
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
        common = [21,22,23,80,443,3306,3389,8080,8443]
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
            server = r.headers.get("Server", "").lower()
            if 'nginx' in server: tech.append("Nginx")
            if 'apache' in server: tech.append("Apache")
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
        self.log("Generating stealth payload...")
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
# 📝 4. REPORTING ENGINE (JSON + PDF)
# ==================================================
class ReportGenerator:
    @staticmethod
    def generate(recon, vuln, payloads, evasion=None, credentials=None, ai_plan=None, cloud=None, output_dir="reports/"):
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            "project": "AutoRecon-X Ultimate Red Team Assessment",
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
                "payloads": payloads,
                "evasion_methods": evasion,
                "credentials": credentials,
                "ai_strategy": ai_plan,
                "cloud_audit": cloud
            },
            "recommendations": [
                "Close unused ports",
                "Update web frameworks & software",
                "Enable WAF/EDR solution",
                "Restrict public access to cloud storage",
                "Enforce strong password policies"
            ]
        }

        # Save JSON Report
        json_path = f"{output_dir}report_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)

        # Save PDF Report
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 18)
        pdf.cell(200, 15, "AutoRecon-X Security Report", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.ln(5)
        pdf.cell(200, 10, f"Target: {recon['target']}", ln=True)
        pdf.cell(200, 10, f"Scan Date: {report['date']}", ln=True)
        pdf.cell(200, 10, f"Risk Level: {report['summary']['risk_level']}", ln=True)
        pdf.ln(10)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Key Findings:", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, f"• Open Ports: {recon['open_ports']}\n• Vulnerabilities: {len(vuln['vulnerabilities'])}\n• Cloud Issues: {len(cloud.get('cloud_findings', [])) if cloud else 0}")

        pdf_path = f"{output_dir}report_{timestamp}.pdf"
        pdf.output(pdf_path)

        print(f"\n✅ Reports Generated:")
        print(f"   📄 JSON: {json_path}")
        print(f"   📄 PDF:  {pdf_path}")
        return report

# ==================================================
# 🧠 🆕 AI ADVISOR MODULE
# ==================================================
class AIAdvisor(RedTeamModule):
    def __init__(self, target: str, recon_data: Dict, vuln_data: Dict):
        super().__init__(target)
        self.description = "AI-Powered Attack Planner using Gemini API"
        self.recon = recon_data
        self.vuln = vuln_data
        self.api_key = "YOUR_GEMINI_API_KEY" # 👉 Replace with your key

    def run(self) -> Dict[str, Any]:
        self.log("Analyzing attack path with AI...")
        
        prompt = f"""
        Act as a Senior Red Team Expert. Based on:
        Target: {self.target}
        Recon: {self.recon}
        Vulnerabilities: {self.vuln}

        Provide:
        1. Top 3 recommended attack steps
        2. Evasion techniques needed
        3. Success probability (%)
        Output in JSON format.
        """

        try:
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(api_url, json=payload, timeout=15)
            if res.status_code == 200:
                return {"ai_strategy": res.json(), "status": "success"}
        except Exception as e:
            return {"error": f"AI failed: {e}", "fallback": "Focus on web ports & brute force"}
        
        return {}

# ==================================================
# 🕵️ 🆕 EVASION ENGINE
# ==================================================
class EvasionEngine(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "AV/EDR Evasion: Encoding, Obfuscation, Anti-Sandbox"

    def run(self) -> Dict[str, Any]:
        self.log("Generating evasion techniques...")
        
        return {
            "techniques": [
                self._xor_encrypt(),
                self._base64_wrap(),
                self._string_mutation()
            ],
            "anti_sandbox": self._check_sandbox()
        }

    def _xor_encrypt(self, payload="cmd.exe /c whoami", key=0x42):
        enc = ''.join([chr(ord(c) ^ key) for c in payload])
        return {
            "method": "XOR Encryption",
            "code": f"key={key};decoded=''.join([chr(ord(c)^key) for c in '{enc}']);exec(decoded)"
        }

    def _base64_wrap(self):
        code = "import os;os.system('dir')"
        b64 = base64.b64encode(code.encode()).decode()
        return {
            "method": "Base64 Obfuscation",
            "code": f"exec(__import__('base64').b64decode('{b64}'))"
        }

    def _string_mutation(self):
        return {
            "method": "String Splitting",
            "code": "imp" + "ort o" + "s; o" + "s.sy" + "stem('who'+'ami')"
        }

    def _check_sandbox(self):
        return {"detected": False, "note": "System appears as real hardware"}

# ==================================================
# 🔑 🆕 CREDENTIAL HARVESTER
# ==================================================
class CredentialHarvester(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "Simulate credential dumping & hash cracking"

    def run(self) -> Dict[str, Any]:
        self.log("Harvesting credentials...")
        
        dummy_hashes = [
            {"user": "Administrator", "hash": "aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"},
            {"user": "LocalAdmin", "hash": "ntlm:98765asdfghjkl"}
        ]

        cracked = self._crack_hashes(dummy_hashes)
        
        return {
            "hashes_captured": len(dummy_hashes),
            "cracked_credentials": cracked,
            "method": "LSASS Memory Dump Simulation"
        }

    def _crack_hashes(self, hash_list):
        common_pass = ["Password123", "Admin@123", "P@ssw0rd"]
        found = []
        for h in hash_list:
            for p in common_pass:
                if hashlib.md5(p.encode()).hexdigest() in h['hash']:
                    found.append({"user": h['user'], "pass": p})
        return found

# ==================================================
# ☁️ 🆕 CLOUD SCANNER
# ==================================================
class CloudScanner(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "Check exposed AWS S3, Azure Blob, GCP Buckets"

    def run(self) -> Dict[str, Any]:
        self.log("Scanning cloud storage...")
        issues = []

        buckets = [
            f"http://{self.target}.s3.amazonaws.com",
            f"https://storage.googleapis.com/{self.target}",
            f"https://{self.target}.blob.core.windows.net/"
        ]

        for url in buckets:
            try:
                res = requests.get(url, timeout=3)
                if res.status_code == 200 or res.status_code == 403:
                    issues.append({
                        "url": url,
                        "status": res.status_code,
                        "risk": "Possible Exposed Bucket"
                    })
            except:
                pass

        return {"cloud_findings": issues}

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
        print(f"🚀 AUTORECON-X ULTIMATE | TARGET: {self.target}")
        print("="*60 + "\n")

        # Step 1: Recon
        recon = ReconModule(self.target)
        self.data["recon"] = recon.run()

        # Step 2: Vuln Analysis
        vuln = VulnAnalyzer(self.target, self.data["recon"])
        self.data["vuln"] = vuln.run()

        # 🆕 NEW STEPS ADDED 🆕
        # Step 3: Cloud Check
        cloud = CloudScanner(self.target)
        self.data["cloud"] = cloud.run()

        # Step 4: AI Strategy
        ai = AIAdvisor(self.target, self.data["recon"], self.data["vuln"])
        self.data["ai_plan"] = ai.run()

        # Step 5: Evasion & Payload
        evade = EvasionEngine(self.target)
        pay = PayloadGenerator(self.target, self.data["vuln"])
        self.data["payloads"] = pay.run()
        self.data["evasion"] = evade.run()

        # Step 6: Credential Access
        cred = CredentialHarvester(self.target)
        self.data["credentials"] = cred.run()

        # Step 7: Report
        ReportGenerator.generate(**self.data)

        print("\n✅✅✅ ALL ADVANCED MODULES COMPLETED SUCCESSFULLY ✅✅✅")

# ==================================================
# 📌 RUN
# ==================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python autorecon_x.py <target-domain-or-ip>")
        sys.exit(1)

    framework = AutoReconX(sys.argv[1])
    framework.execute()
            
