from pymongo import MongoClient
from config import MONGO_URL,DB_NAME

# connect mongo with backend 
client = MongoClient(MONGO_URL)

db = client[DB_NAME]

# define collection in mongo
prompts_col = db.prompts
history_col = db.history