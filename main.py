import os
import json
import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str = "default_user"
    prompt: str

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

tools = [
    {
        "type": "function",
        "function": {
            "name": "remember_info",
            "description": "Simpan maklumat peribadi pengguna.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Topik (cth: nama_kucing)"},
                    "value": {"type": "string", "description": "Kandungan maklumat"}
                },
                "required": ["key", "value"]
            }
        }
    }
]

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
        current_memories = get_all_memories(request.user_id)
        
        system_prompt = f"""Kau ialah JARVIS, pembantu AI yang bijak dan mesra.
Senarai memori sedia ada pengguna ({request.user_id}):
{current_memories}

Jawab soalan pengguna berdasarkan memori di atas jika ada. 
Jika pengguna minta ingat maklumat baru, gunakan tool `remember_info`.
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.prompt}
            ],
            tools=tools,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=300
        )

        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "remember_info":
                    args = json.loads(tool_call.function.arguments)
                    save_memory(request.user_id, args.get("key"), args.get("value"))
                    return {
                        "reply": f"Baik boss, saya dah simpan maklumat: {args.get('key')} = {args.get('value')}",
                        "action": "memory_saved"
                    }

        return {"reply": response_message.content, "action": "chat"}

    except Exception as e:
        return {"reply": f"Groq Error: {str(e)}"}
