# config/db.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()
#Cloud connection to MongoDB Atlas
MONGO_URI =  os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

# Database name
db = client["NewsByte_AI"]
