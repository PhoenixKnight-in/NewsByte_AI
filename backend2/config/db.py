# config/db.py
from pymongo import MongoClient

#Cloud connection to MongoDB Atlas
MONGO_URI = "mongodb+srv://phoenixknight-in:Phoenix18.in@cluster.xopt5jz.mongodb.net/"
client = MongoClient(MONGO_URI)

# Database name
db = client["NewsByte_AI"]
