from database.mongo import prompts_col

def seed_prompt():
  default = {
    "_id": "Education_Prompt",
    "template": "You are an expert in education domain. Answer the following: {{userInput}}"
  }

  try:
    if prompts_col.find_one({"_id": "Education_Prompt"}) is None:
      prompts_col.insert_one(default)
  except Exception:
    pass