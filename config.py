from pymongo import MongoClient

# 本機 MongoDB 範例（如果你用 Atlas，請改成你的連線字串）
client = MongoClient("mongodb://localhost:27017/")

db = client['nosql_assignment_db']
collection = db['forms']   # 後面會放 form documents
users = db['users']       # 儲存使用者
