import requests
from autorecon_x import RedTeamModule

class SubdomainTakeoverScanner(RedTeamModule):
    def __init__(self, target: str, subdomains: list):
        super().__init__(target)
        self.description = "Check for Subdomain Takeover vulnerability"
        self.subdomains = subdomains
        # Common fingerprint patterns
        self.fingerprints = {
            "GitHub": "There isn't a GitHub Pages site here.",
            "AWS S3": "NoSuchBucket",
            "Heroku": "No such app",
            "Azure": "The resource you are looking for has been removed",
            "Cloudflare": "Error 1001"
        }

    def run(self) -> dict:
        print("[⚠️] Checking Subdomain Takeover...")
        vulnerable = []

        for sub in self.subdomains:
            if "*" in sub or not sub: continue
            try:
                url = f"http://{sub}"
                res = requests.get(url, timeout=4, allow_redirects=True)
                
                for provider, pattern in self.fingerprints.items():
                    if pattern in res.text or pattern in res.reason:
                        vulnerable.append({
                            "subdomain": sub,
                            "provider": provider,
                            "risk": "CRITICAL",
                            "issue": "Potential Takeover"
                        })
            except: pass

        return {"takeover_vulnerable": vulnerable}
      
