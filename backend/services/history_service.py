from datetime import datetime,timezone
from database.mongo import history_col

def save_history(user_input, ai_response):
  try:
    history_col.insert_one({
      "userInput": user_input,
      "aiResponse": ai_response,
      "timestamp": datetime.now(timezone.utc)
    })
  except Exception:
    pass
  
  
def get_recent_history():
  try:
    docs = history_col.find(
      {},
      {"_id": 0}
    ).sort("timestamp", -1).limit(20)
  except Exception:
    return []

  out = []

  for d in docs:
    ts = d.get("timestamp")

    if ts:
      d["timestamp"] = ts.isoformat() + "Z"

    out.append(d)

  return out