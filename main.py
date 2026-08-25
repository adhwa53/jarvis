import os
import json
import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str = "default_user"  # ID pengguna untuk simpan memori
    prompt: str

# ---------------------------------------------------------
# 1. SETUP DATABASE UNTUK MEMORY (SQLite)
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
# 2. DEFINE TOOLS / FUNCTION CALLING
# ---------------------------------------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "remember_info",
            "description": "Gunakan fungsi ini untuk menyimpan maklumat peribadi pengguna atau nota yang perlu diingati untuk masa hadapan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Kategori/Topik maklumat (cth: nama_kucing, hobi, makanan_kegemaran)"},
                    "value": {"type": "string", "description": "Maklumat lengkap yang nak diingat"}
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Gunakan fungsi ini untuk menyelesaikan pengiraan matematik kompleks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Matematik ekspresi seperti '25 * 4 + 10'"}
                },
                "required": ["expression"]
            }
        }
    }
]

# ---------------------------------------------------------
# 3. FASTAPI ROUTE
# ---------------------------------------------------------
@app.get("/")
def home():
    return {"status": "JARVIS Fasa 1 Online"}

@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"reply": "Error: GROQ_API_KEY tak dijumpai kat Render!"}
    
    try:
        client = Groq(api_key=api_key.strip())
        
        # Tarik memori sedia ada untuk dimasukkan dalam kontek System
        current_memories = get_all_memories(request.user_id)
        
        system_prompt = f"""Kau ialah JARVIS, pembantu AI yang bijak, ringkas dan mesra.
        
Memori sedia ada pengguna ini ({request.user_id}):
{current_memories}

Jika pengguna meminta untuk mengingati sesuatu, panggil fungsi `remember_info`.
Jika pengguna bertanya soalan yang memerlukan pengiraan, panggil fungsi `calculate`.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.prompt}
        ]

        # Panggil LLM Groq bersama senarai Tools
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=400
        )

        response_message = response.choices[0].message
        
        # Semak jika LLM mahu memanggil mana-mana Function / Tool
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                if func_name == "remember_info":
                    save_memory(request.user_id, func_args.get("key"), func_args.get("value"))
                    return {
                        "reply": f"Baik, saya sudah simpan maklumat ini: [{func_args.get('key')}: {func_args.get('value')}]",
                        "action": "memory_saved"
                    }
                
                elif func_name == "calculate":
                    try:
                        # Pengiraan selamat
                        result = eval(func_args.get("expression"), {"__builtins__": None}, {})
                        return {
                            "reply": f"Hasil pengiraan `{func_args.get('expression')}` ialah: {result}",
                            "action": "calculated"
                        }
                    except Exception:
                        return {"reply": "Maaf, pengiraan tersebut gagal dilaksanakan."}

        # Jika tiada tool dipanggil, pulangkan jawapan biasa
        return {
            "reply": response_message.content,
            "action": "chat"
        }

    except Exception as e:
        return {"reply": f"Groq Error: {str(e)}"}
