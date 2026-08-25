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
        
        # Cari model chat/instruct sahaja daripada senarai akaun kau
        models_list = client.models.list()
        chat_models = [
            m.id for m in models_list.data 
            if any(k in m.id for k in ["llama-3", "mixtral", "gemma"]) 
            and "guard" not in m.id 
            and "safetensors" not in m.id
        ]
        
        selected_model = chat_models[0] if chat_models else "llama-3.1-8b-instant"
        
        completion = client.chat.completions.create(
            model=selected_model,
            messages=[
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
