import requests
from autorecon_x import RedTeamModule

class CloudScanner(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "Check exposed AWS S3, Azure Blob, GCP Buckets"

    def run(self) -> Dict:
        print("[☁️] Scanning Cloud Storage...")
        issues = []

        # Check common bucket patterns
        buckets = [
            f"http://{target}.s3.amazonaws.com",
            f"https://storage.googleapis.com/{target}",
            f"https://{target}.blob.core.windows.net/"
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
      
