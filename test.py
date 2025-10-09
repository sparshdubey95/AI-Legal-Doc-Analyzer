import os
from dotenv import load_dotenv

load_dotenv()
print("Loaded Gemini Token: ",os.getenv("GEMINI_TOKEN"))