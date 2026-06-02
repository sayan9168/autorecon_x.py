import socket
import requests
from datetime import datetime
from typing import Dict, List
from autorecon_x import RedTeamModule

class ReconModule(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "Passive + Active Recon: DNS, Subdomains, Ports, Tech Stack"

    def run(self) -> Dict:
        print(f"[+] Starting Recon on {self.target}...")
        return {
            "timestamp": datetime.now().isoformat(),
            "target": self.target,
            "dns": self._get_dns(),
            "subdomains": self._get_subdomains(),
            "open_ports": self._scan_ports(),
            "tech_stack": self._detect_tech()
        }

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
        common_ports = [21,22,23,80,443,3306,3389,8080,8443]
        for port in common_ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            if s.connect_ex((self.target, port)) == 0:
                open_ports.append(port)
            s.close()
        return open_ports

    def _detect_tech(self) -> List[str]:
        try:
            r = requests.get(f"http://{self.target}", timeout=5)
            tech = []
            server = r.headers.get("Server", "").lower()
            if "nginx" in server: tech.append("Nginx")
            if "apache" in server: tech.append("Apache")
            if "x-powered-by" in r.headers: tech.append(r.headers['x-powered-by'])
            return tech
        except:
            return []
          
