import asyncio
import aiohttp

from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_URL

def call_openrouter(prompt: str):
  if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not configured")

  async def _call():
    timeout = aiohttp.ClientTimeout(total=25)
    headers = {
      "Authorization": f"Bearer {OPENROUTER_API_KEY}",
      "Content-Type": "application/json",
      "HTTP-Referer": "http://localhost",
      "X-Title": "ChatBot",
    }
    payload = {
      "model": OPENROUTER_MODEL,
      "messages": [
        {"role": "user", "content": prompt}
      ],
      "temperature": 0.4,
      "max_tokens": 500,
    }

    async with aiohttp.ClientSession(timeout=timeout) as session:
      async with session.post(OPENROUTER_URL, json=payload, headers=headers) as response:
        body = await response.json(content_type=None)
        if response.status >= 400:
          raise RuntimeError(f"OpenRouter request failed ({response.status}): {body}")

        try:
          return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
          raise RuntimeError(f"Unexpected OpenRouter response: {body}") from exc

  return asyncio.run(_call())


async def call_openrouter_async(session,prompt:str):
  if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not configured")

  headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "ChatBot",
  }
  payload = {
    "model": OPENROUTER_MODEL,
    "messages": [
      {"role": "user", "content": prompt}
    ],
    "temperature": 0.4,
    "max_tokens": 500,
  }

  async with session.post(OPENROUTER_URL, json=payload, headers=headers) as response:
    body = await response.json(content_type=None)
    if response.status >= 400:
      raise RuntimeError(f"OpenRouter request failed ({response.status}): {body}")

    try:
      return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
      raise RuntimeError(f"Unexpected OpenRouter response: {body}") from exc

async def call_openrouter_parallel(prompts_list:list):
  async with aiohttp.ClientSession() as session:
    
    tasks=[
      call_openrouter_async(session,p)
      for p in prompts_list
    ]
    
    return await asyncio.gather(*tasks)