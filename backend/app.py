# pip install flask pymongo flask-cors requests aiohttp
# pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import requests
import aiohttp
import asyncio
from datetime import datetime
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct:free")
OPENROUTER_URL = os.environ.get("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "education_ai")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY environment variable not set. Please set it before running the app.")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable not set. Please set it before running the app.")

app = Flask(__name__)
CORS(app)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
prompts_col = db.prompts
history_col = db.history


# Insert default Education_Prompt into MongoDB if missing
def seed_prompt():
    default = {
        "_id": "Education_Prompt",
        "template": "You are an expert in education domain. Answer the following: {{userInput}}"
    }
    if prompts_col.find_one({"_id": "Education_Prompt"}) is None:
        prompts_col.insert_one(default)


# Fetch template and build final prompt by replacing placeholder
def build_prompt(user_input: str) -> str:
    doc = prompts_col.find_one({"_id": "Education_Prompt"})
    template = doc.get("template") if doc else "{{userInput}}"
    return template.replace("{{userInput}}", user_input)


# Synchronous POST to OpenRouter API and return AI response text
def call_openrouter(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512
    }
    try:
        r = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if isinstance(choice, dict) and "message" in choice:
                return choice["message"].get("content", "").strip()
            return choice.get("text", "").strip()
        return str(data)
    except Exception as e:
        return f"[error] {str(e)}"


# Single async OpenRouter call using provided aiohttp session
async def call_openrouter_async(session, prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512
    }
    try:
        async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30) as resp:
            text = await resp.text()
            try:
                data = await resp.json()
            except Exception:
                return text
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if isinstance(choice, dict) and "message" in choice:
                    return choice["message"].get("content", "").strip()
                return choice.get("text", "").strip()
            return str(data)
    except Exception as e:
        return f"[error] {str(e)}"


# Run many OpenRouter calls concurrently and return list of responses
async def call_openrouter_parallel(prompts_list: list) -> list:
    async with aiohttp.ClientSession() as session:
        tasks = [call_openrouter_async(session, p) for p in prompts_list]
        return await asyncio.gather(*tasks)


# Save question/answer pair with UTC timestamp into history collection
def save_history(user_input: str, ai_response: str):
    history_col.insert_one({
        "userInput": user_input,
        "aiResponse": ai_response,
        "timestamp": datetime.utcnow()
    })


@app.route("/ask", methods=["POST"])
def ask():
    """Accept a single question, query OpenRouter, save and return the answer."""
    data = request.get_json() or {}
    user_input = data.get("userInput", "").strip()
    if not user_input:
        return jsonify({"error": "userInput required"}), 400
    prompt = build_prompt(user_input)
    ai_resp = call_openrouter(prompt)
    save_history(user_input, ai_resp)
    return jsonify({"response": ai_resp})


@app.route("/ask-batch", methods=["POST"])
def ask_batch():
    """Accept multiple questions, call OpenRouter in parallel, save and return answers."""
    data = request.get_json() or {}
    inputs = data.get("userInputs", [])
    if not isinstance(inputs, list) or len(inputs) == 0:
        return jsonify({"error": "userInputs must be a non-empty list"}), 400
    prompts = [build_prompt(q.strip()) for q in inputs]
    try:
        responses = asyncio.run(call_openrouter_parallel(prompts))
    except Exception as e:
        return jsonify({"error": f"async error: {str(e)}"}), 500
    for q, a in zip(inputs, responses):
        save_history(q, a)
    return jsonify({"responses": responses})


@app.route("/history", methods=["GET"])
def get_history():
    """Return last 20 question/answer records from history, newest first."""
    docs = history_col.find({}, {"_id": 0}).sort("timestamp", -1).limit(20)
    out = []
    for d in docs:
        ts = d.get("timestamp")
        if isinstance(ts, datetime):
            d["timestamp"] = ts.isoformat() + "Z"
        out.append(d)
    return jsonify(out)


if __name__ == "__main__":
    seed_prompt()
    app.run(debug=True, port=5000)
