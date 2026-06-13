"""
check_setup.py - Verify your Gemini API key works and list the models you can use.

Run it with:   uv run check_setup.py
"""
import os

from dotenv import load_dotenv
from google import genai

# Load the variables from the .env file into the environment.
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("No GEMINI_API_KEY found. Make sure it is set in your .env file.")

print(f"API key loaded: starts with '{api_key[:6]}', {len(api_key)} characters long.\n")

# The Client is your single entry point to every Gemini feature.
client = genai.Client(api_key=api_key)

print("Asking Google which models this key can access...\n")
chat_models, embed_models = [], []
try:
    for m in client.models.list():
        actions = getattr(m, "supported_actions", None) or []
        if "generateContent" in actions:
            chat_models.append(m.name)
        if "embedContent" in actions:
            embed_models.append(m.name)
except Exception as e:
    raise SystemExit(
        "\nCould NOT reach the API with this key. It may be invalid or the wrong type.\n"
        f"Error:\n  {e}\n\n"
        "Fix: create a Gemini API key at https://aistudio.google.com/apikey\n"
        "(a valid key usually starts with 'AIza'), then paste it into the .env file."
    )

print(f"Models that can CHAT ({len(chat_models)} found):")
for name in chat_models:
    print(f"   - {name}")

print(f"\nModels that can EMBED ({len(embed_models)} found):")
for name in embed_models:
    print(f"   - {name}")

print("\nYour key works. Setup is good!")
