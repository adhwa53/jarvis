import os
import json
import sqlite3
import base64
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

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
# ENDPOINTS
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>JARVIS Online</h1><p>Fail index.html belum di-commit ke GitHub root folder.</p>"

@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"reply": "Error: GROQ_API_KEY tak dijumpai di Render!"}
    
    try:
        client = Groq(api_key=api_key.strip())
        current_memories = get_all_memories(request.user_id)
        
        system_prompt = f"""Kau ialah JARVIS, pembantu AI yang bijak, ringkas dan mesra.
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
        return {"reply": f"Groq Error: {str(e)}"}

@app.post("/vision")
async def vision(prompt: str = Form(...), file: UploadFile = File(...)):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"reply": "Error: GROQ_API_KEY tak dijumpai di Render!"}
    
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        client = Groq(api_key=api_key.strip())
        
        # Guna model vision aktif terkini
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
