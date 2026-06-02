import requests
from typing import Dict
from autorecon_x import RedTeamModule

class AIAdvisor(RedTeamModule):
    def __init__(self, target: str, recon_data: Dict, vuln_data: Dict):
        super().__init__(target)
        self.description = "AI-Powered Attack Planner using Gemini API"
        self.recon = recon_data
        self.vuln = vuln_data
        # 👉 Replace with your own Gemini API Key
        self.api_key = "YOUR_GEMINI_API_KEY" 
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"

    def run(self) -> Dict:
        print("[🧠] AI Advisor analyzing attack path...")
        
        prompt = f"""
        Act as a Senior Red Team Expert. Based on this data:
        Target: {self.target}
        Recon: {self.recon}
        Vulnerabilities: {self.vuln}

        Give me:
        1. Top 3 recommended attack steps
        2. Evasion techniques needed
        3. Probability of success (%)
        Output in structured JSON format only.
        """

        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(self.api_url, json=payload, timeout=15)
            if res.status_code == 200:
                return {"ai_strategy": res.json(), "status": "success"}
        except Exception as e:
            return {"error": f"AI failed: {e}", "fallback": "Focus on port 80/443 and brute force"}
        
        return {}
      
