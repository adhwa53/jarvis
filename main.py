import os
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str

@app.get("/")
def home():
    return {"status": "JARVIS Online"}

@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"reply": "Error: GROQ_API_KEY tak dijumpai kat Render!"}
    
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Kau ialah JARVIS, pembantu AI yang bijak, ringkas dan mesra."},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return {"reply": completion.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Groq Error: {str(e)}"}
