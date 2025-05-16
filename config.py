from dotenv import load_dotenv
import os
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_IDS = [739350421, 534952794]
print("Config module loaded successfully.")
