import os
import json
import sqlite3
import base64
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

# Benarkan sambungan dari Frontend (HTML/JS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: str = "default_user"
    prompt: str

# ---------------------------------------------------------
# DATABASE & MEMORY MANAGEMENT (SQLite)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("jarvis_memory.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            key TEXT,
            value TEXT,
            UNIQUE(user_id, key)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_memory(user_id: str, key: str, value: str):
    conn = sqlite3.connect("jarvis_memory.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO memory (user_id, key, value) 
        VALUES (?, ?, ?) 
        ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value
    """, (user_id, key.lower(), value))
    conn.commit()
    conn.close()

def get_all_memories(user_id: str):
    conn = sqlite3.connect("jarvis_memory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM memory WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return "Tiada memori disimpan lagi."
    return "\n".join([f"- {k}: {v}" for k, v in rows])

# ---------------------------------------------------------
# FASTAPI ENDPOINTS
# ---------------------------------------------------------
@app.get("/")
def home():
    return {"status": "JARVIS Fasa 2 (Complete) Online"}

# Endpoint 1: Standard Chat + Memory
@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"reply": "Error: GROQ_API_KEY tak dijumpai!"}
    
    try:
        client = Groq(api_key=api_key.strip())
        current_memories = get_all_memories(request.user_id)
        
        system_prompt = f"""Kau ialah JARVIS, pembantu AI yang bijak, ringkas dan pantas.
Memori sedia ada pengguna ({request.user_id}):
{current_memories}
"""
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}

# Endpoint 2: Vision (Upload & Analisis Gambar)
@app.post("/vision")
async def vision(prompt: str = Form(...), file: UploadFile = File(...)):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"reply": "Error: GROQ_API_KEY tak dijumpai!"}
    
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        client = Groq(api_key=api_key.strip())
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=400
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Vision Error: {str(e)}"}
