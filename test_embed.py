import os
from services.embeddings import embed_text

try:
    print("Testing embed_text()...")
    res = embed_text("Hello world")
    print(f"Success! Vector length: {len(res)}")
except Exception as e:
    print(f"FAILED: {e}")
    print("STATUS CODE:", response.status_code)
    print("RESPONSE JSON:", response.json())
except Exception as e:
    print("ERROR:", str(e))
