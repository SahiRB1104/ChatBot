from database.mongo import prompts_col

def build_prompt(user_input: str) -> str:
  try:
    doc = prompts_col.find_one({"_id": "Education_Prompt"})
  except Exception:
    doc = None

  template = doc.get("template") if doc else "{{userInput}}"
  style_instructions = (
    "You are an education Q&A bot. Answer in a clear markdown format with a short direct answer, "
    "2-4 key points when useful, and a brief next step or takeaway if it adds value. "
    "Keep the answer concise but complete, usually around 80-140 words, and avoid rambling. "
    "Use simple headings or bullets when they help readability."
  )

  rendered_template = template.replace("{{userInput}}", user_input)

  return f"{style_instructions}\n\n{rendered_template}"
  