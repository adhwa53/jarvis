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
        client = Groq(api_key=api_key.strip())
        
        # Dapatkan senarai model dari akaun Groq
        models_data = client.models.list().data
        all_model_ids = [m.id for m in models_data]
        
        # Cuba setiap model satu per satu sehingga berjaya
        for model_id in all_model_ids:
            # Elak model keselamatan/guard
            if "guard" in model_id or "safetensors" in model_id:
                continue
                
            try:
                completion = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": request.prompt}],
                    temperature=0.7,
                    max_tokens=300
                )
                return {
                    "reply": completion.choices[0].message.content,
                    "model_used": model_id
                }
            except Exception:
                continue
                
        return {"reply": f"Tiada model yang boleh digunakan. Senarai model akaun anda: {all_model_ids}"}
        
    except Exception as e:
        return {"reply": f"Groq Error: {str(e)}"}
