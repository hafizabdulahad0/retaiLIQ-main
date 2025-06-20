# debug_openai.py
import os
from dotenv import load_dotenv
import openai

# 1) Load .env from current working directory
load_dotenv()  

# 2) Print out exactly what Python got
key = os.getenv("OPENAI_API_KEY")
print("Raw value of OPENAI_API_KEY:", repr(key))
print("Starts with 'sk-'?", bool(key and key.startswith("sk-")))

# 3) If key exists, try a minimal OpenAI call (list models)
if key:
    openai.api_key = key
    try:
        result = openai.Model.list(limit=3)
        print("→ OpenAI accepted the key! You can see some model IDs:")
        for m in result["data"]:
            print("   •", m["id"])
    except Exception as e:
        print("→ OpenAI rejected the key. Error:", e)
else:
    print("→ No key found. Did you run this from the correct directory?")
