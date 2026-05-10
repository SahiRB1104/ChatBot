from flask import Blueprint,request,jsonify
import asyncio

from services.prompt_service import build_prompt
from services.openrouter_service import (
  call_openrouter,
  call_openrouter_parallel
)

from services.format_service import format_response_as_html

from services.history_service import save_history

ask_bp=Blueprint("ask_bp",__name__)

@ask_bp.route("/ask",methods=["POST"])
def ask():
  data = request.get_json() or {}
  
  user_input = data.get("userInput","").strip()
  
  if not user_input:
    return jsonify({"error":"userInput required"}),400
  
  prompt = build_prompt(user_input)
  
  ai_resp=call_openrouter(prompt)
  
  save_history(user_input,ai_resp)
  
  response_html = format_response_as_html(ai_resp)

  return jsonify({
    "question": user_input,
    "answer": ai_resp,
    "response": ai_resp,
    "answer_html": response_html,
    "response_html": response_html,
  })

@ask_bp.route("/ask-batch",methods=["POST"])
def ask_batch():
  data = request.get_json() or {}
   
  inputs = data.get("userInputs",[])
   
  if not isinstance(inputs,list):
     return jsonify({"error":"Invalid input"}),400
   
  prompts = [build_prompt(q) for q in inputs]
   
  response = asyncio.run(call_openrouter_parallel(prompts)
                          )
   
  for q ,a in zip(inputs, response):
     save_history(q,a)

  responses_html = [format_response_as_html(r) for r in response]

  return jsonify({
    "items": [
      {
        "question": q,
        "answer": a,
        "answer_html": html,
      }
      for q, a, html in zip(inputs, response, responses_html)
    ],
    "responses": response,
    "responses_html": responses_html,
  })