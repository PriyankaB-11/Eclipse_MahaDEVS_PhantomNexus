import os

from groq import Groq


api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise SystemExit("Set GROQ_API_KEY before running this script.")


client = Groq(api_key=api_key)
try:
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Reply with only this JSON: {\"ok\":true}"}],
        max_tokens=20,
    )
    print("SUCCESS:", r.choices[0].message.content)
except Exception as e:
    print("ERROR:", type(e).__name__, str(e))
