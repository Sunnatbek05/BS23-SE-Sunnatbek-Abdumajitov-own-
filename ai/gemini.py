import aiohttp
from config import GEMINI_API_KEY

# Request productivity advice from Google Gemini API
async def get_ai_tips(completed_tasks: str, unfinished_tasks: str) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key is not configured."

    prompt = f"""
    You are a productivity and time-management expert.
    Analyze the user's task list for the past few days.

    Completed: {completed_tasks}
    Unfinished: {unfinished_tasks}

    Give a short, friendly, and motivating piece of advice (max 3 sentences) on how to improve productivity and close unfinished tasks.
    Answer strictly in English. Write simply, without complex formatting.
    """

    headers = {"Content-Type": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            # Fetch active models dynamically to prevent 404 errors
            models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
            async with session.get(models_url) as resp:
                if resp.status != 200:
                    return "🤖 Unfortunately, the AI is resting right now."

                models_data = await resp.json()

                available_models =[]
                for m in models_data.get("models",[]):
                    name = m.get("name", "")
                    methods = m.get("supportedGenerationMethods",[])
                    if "generateContent" in methods and "gemini" in name:
                        available_models.append(name)

            if not available_models:
                return "🤖 No available models found."

            data = {"contents": [{"parts":[{"text": prompt}]}]}

            # Iterate through available models to handle high demand (503 errors)
            for model_name in available_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"

                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        print(f"Model {model_name} busy (error {response.status}). Trying next...")
                        continue

            return "🤖 Google servers are currently overloaded (high demand). Please try again in 10 minutes!"

    except Exception as e:
        print(f"Gemini connection error: {e}")
        return "🤖 Unfortunately, the AI is resting right now."