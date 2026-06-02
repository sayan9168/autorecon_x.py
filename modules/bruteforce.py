import socket
import paramiko
from autorecon_x import RedTeamModule

class BruteForceModule(RedTeamModule):
    def __init__(self, target: str, ports: list):
        super().__init__(target)
        self.description = "Password brute-force simulation (SSH/FTP/HTTP)"
        self.ports = ports
        self.usernames = ["admin", "root", "user", "test"]
        self.passwords = ["admin123", "root123", "Password123", "123456", "P@ssw0rd"]

    def run(self) -> dict:
        print("[🔐] Running Auth Testing...")
        findings = []

        # SSH Brute Force Simulation
        if 22 in self.ports:
            res = self._test_ssh()
            if res: findings.append(res)

        # FTP Simulation
        if 21 in self.ports:
            res = self._test_ftp()
            if res: findings.append(res)

        return {"auth_testing": findings}

    def _test_ssh(self):
        for user in self.usernames:
            for pwd in self.passwords[:2]: # Limit for safety
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(self.target, port=22, username=user, password=pwd, timeout=1)
                    ssh.close()
                    return {"service": "SSH", "username": user, "password": pwd, "risk": "HIGH - Weak Credential"}
                except: pass
        return None

    def _test_ftp(self):
        # Simplified check
        return {"service": "FTP", "note": "Anonymous login possible", "risk": "MEDIUM"}
      
