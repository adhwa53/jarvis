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
        return {"reply": "Error: GROQ_API_KEY tak dijumpai kat Render Environment!"}
    
    try:
        client = Groq(api_key=api_key.strip())
        
        # 1. Tarik senarai rasmi model yang dibenarkan untuk API key kau
        models_list = client.models.list()
        available_models = [m.id for m in models_list.data if "llama" in m.id or "mixtral" in m.id]
        
        if not available_models:
            # Fallback jika tiada keyword spesifik
            available_models = [m.id for m in models_list.data]
            
        selected_model = available_models[0]
        
        # 2. Hantar prompt guna model pertama yang sah
        completion = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": "Kau ialah JARVIS, pembantu AI yang bijak, ringkas dan mesra."},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return {
            "reply": completion.choices[0].message.content,
            "model_used": selected_model
        }
        
    except Exception as e:
        return {"reply": f"Groq Error: {str(e)}"}
