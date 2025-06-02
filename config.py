from dotenv import load_dotenv
import os
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_IDS = [7393504121, 534952794]
print("Config module loaded successfully.")
