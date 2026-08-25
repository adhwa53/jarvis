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
        return {"reply": "Error: GROQ_API_KEY tak jumpa kat Render!"}
    
    client = Groq(api_key=api_key.strip())
    
    # Senarai model ikut keutamaan
    models = ["llama-3.1-8b-instant", "llama3-70b-8192", "mixtral-8x7b-32768"]
    
    for m in models:
        try:
            completion = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": "Kau ialah JARVIS, pembantu AI yang bijak dan ringkas."},
                    {"role": "user", "content": request.prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return {"reply": completion.choices[0].message.content, "model_used": m}
        except Exception as e:
            continue
            
    return {"reply": "Semua model Groq gagal dipanggil. Sila semak API Key."}
