import os
import json
import sqlite3
from fastapi import FastAPI
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
# DATABASE SETUP (SQLite)
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

try:
    init_db()
except Exception:
    pass

def save_memory(user_id: str, key: str, value: str):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memory (user_id, key, value) VALUES (?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET value = ?
        """, (user_id, key, value, value))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

def get_all_memories(user_id: str):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM memory WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "Tiada memori disimpan lagi."
        return "\n".join([f"- {k}: {v}" for k, v in rows])
    except Exception:
        return "Tiada memori."

# ---------------------------------------------------------
# CYBERPUNK SCI-FI UI (HTML EMBEDDED)
# ---------------------------------------------------------
HTML_CODE = """
<!DOCTYPE html>
<html lang="ms">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS // CYBER-INTERFACE</title>
    <style>
        :root {
            --bg-deep: #07090f;
            --panel-bg: rgba(18, 24, 38, 0.7);
            --border-neon: rgba(249, 115, 22, 0.4);
            --orange-glow: #f97316;
            --cyan-glow: #38bdf8;
            --text-main: #f1f5f9;
        }

        body {
            font-family: 'Courier New', Courier, monospace, 'Segoe UI', sans-serif;
            background-color: var(--bg-deep);
            background-image: 
                radial-gradient(circle at 20% 30%, rgba(249, 115, 22, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 80% 70%, rgba(56, 189, 248, 0.08) 0%, transparent 40%);
            color: var(--text-main);
            padding: 20px;
            max-width: 900px;
            margin: auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border-neon);
            padding-bottom: 15px;
            margin-bottom: 25px;
        }

        h1 {
            font-size: 1.5rem;
            letter-spacing: 2px;
            color: var(--orange-glow);
            text-shadow: 0 0 10px rgba(249, 115, 22, 0.5);
            margin: 0;
        }

        .status-badge {
            font-size: 0.8rem;
            color: #4ade80;
            background: rgba(74, 222, 128, 0.1);
            border: 1px solid #4ade80;
            padding: 4px 10px;
            border-radius: 4px;
            box-shadow: 0 0 8px rgba(74, 222, 128, 0.2);
        }

        .grid-container {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }

        @media (max-width: 768px) {
            .grid-container { grid-template-columns: 1fr; }
        }

        .card {
            background: var(--panel-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-neon);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            position: relative;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 6px; height: 100%;
            background: var(--orange-glow);
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
        }

        h3 {
            color: var(--cyan-glow);
            margin-top: 0;
            font-size: 1rem;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        #chatbox {
            height: 320px;
            overflow-y: auto;
            background: rgba(3, 7, 18, 0.8);
            padding: 15px;
            border-radius: 6px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            margin-bottom: 15px;
            font-size: 0.95rem;
        }

        .user-msg { color: var(--cyan-glow); margin: 8px 0; }
        .jarvis-msg { color: #4ade80; margin: 8px 0; }

        .input-group {
            display: flex;
            gap: 10px;
        }

        input[type="text"] {
            flex: 1;
            padding: 12px;
            background: rgba(3, 7, 18, 0.9);
            color: var(--text-main);
            border: 1px solid var(--border-neon);
            border-radius: 6px;
            outline: none;
            font-family: inherit;
        }

        input[type="text"]:focus {
            border-color: var(--cyan-glow);
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.4);
        }

        button {
            background: linear-gradient(135deg, #f97316, #c2410c);
            color: white;
            border: none;
            padding: 10px 18px;
            cursor: pointer;
            border-radius: 6px;
            font-weight: bold;
            letter-spacing: 1px;
            transition: all 0.2s ease;
            box-shadow: 0 0 10px rgba(249, 115, 22, 0.4);
        }

        button:hover {
            background: linear-gradient(135deg, #fb923c, #ea580c);
            box-shadow: 0 0 15px rgba(249, 115, 22, 0.8);
        }

        .btn-voice {
            background: linear-gradient(135deg, #0284c7, #0369a1);
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
            margin-top: 10px;
            width: 100%;
        }

        .sys-info p {
            margin: 8px 0;
            font-size: 0.85rem;
            color: #94a3b8;
            border-bottom: 1px dashed rgba(255,255,255,0.1);
            padding-bottom: 5px;
        }

        .sys-info span {
            color: var(--orange-glow);
            float: right;
        }
    </style>
</head>
<body>

    <header>
        <h1>⚡ J.A.R.V.I.S // OS</h1>
        <div class="status-badge">● SYSTEM ONLINE</div>
    </header>

    <div class="grid-container">
        <div class="card">
            <h3>Neural Communication Link</h3>
            <div id="chatbox">
                <p class="jarvis-msg"><b>JARVIS:</b> Sistem protokol diaktifkan. Sedia menerima arahan, Tuan Adhwa.</p>
            </div>
            <div class="input-group">
                <input type="text" id="userInput" placeholder="Masukkan arahan atau tanya sesuatu..." onkeypress="if(event.key === 'Enter') sendChat()">
                <button onclick="sendChat()">HANTAR</button>
            </div>
            <button class="btn-voice" onclick="startVoice()">🎙️ AKTIFKAN INPUT SUARA</button>
        </div>

        <div class="card sys-info">
            <h3>System Metrics</h3>
            <p>Core Model: <span>Groq Cloud</span></p>
            <p>Memory Engine: <span>SQLite Active</span></p>
            <p>Security Level: <span>Alpha-1</span></p>
            <p>Network Latency: <span>14ms</span></p>
            <hr style="border:0; border-top:1px solid rgba(255,255,255,0.1); margin: 15px 0;">
            <p style="color: var(--cyan-glow); text-align: center; font-size: 0.8rem;">[ HOLOGRAPHIC HUD v2.5 ]</p>
        </div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;

        function startVoice() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) return alert("Pelayar anda tidak menyokong rekod suara.");
            
            const recognition = new SpeechRecognition();
            recognition.lang = 'ms-MY';
            recognition.start();

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('userInput').value = transcript;
                sendChat();
            };
        }

        function speak(text) {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'ms-MY';
                window.speechSynthesis.speak(utterance);
            }
        }

        async function sendChat() {
            const prompt = document.getElementById('userInput').value;
            if (!prompt) return;

            const chatbox = document.getElementById('chatbox');
            chatbox.innerHTML += `<p class="user-msg"><b>Anda:</b> ${prompt}</p>`;

            try {
                const res = await fetch(`${BACKEND_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt })
                });
                const data = await res.json();
                chatbox.innerHTML += `<p class="jarvis-msg"><b>JARVIS:</b> ${data.reply}</p>`;
                chatbox.scrollTop = chatbox.scrollHeight;
                document.getElementById('userInput').value = '';
                speak(data.reply);
            } catch (err) {
                chatbox.innerHTML += `<p style="color:red">Ralat sambungan rangkaian.</p>`;
            }
        }
    </script>
</body>
</html>
"""

# ---------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_CODE

@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"reply": "Error: GROQ_API_KEY tidak dijumpai di Render!"}
    
    try:
        client = Groq(api_key=api_key.strip())
        current_memories = get_all_memories(request.user_id)
        
        system_prompt = f"""Kau ialah JARVIS, pembantu AI peribadi gaya sains fiksyen yang cerdik, ringkas, dan setia.
Memori sedia ada pengguna ({request.user_id}):
{current_memories}

ARAHAN KHAS:
Jika pengguna memberitahu maklumat peribadi (contoh: nama, hobi, minat), balas seperti biasa dan masukkan kod ini di hujung mesej tersembunyi:
[SAVE:key=value]
Contoh: Baik Tuan, saya catat. [SAVE:nama=adhwa]
Jika tiada maklumat baru, jangan tulis [SAVE:...].
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
        
        reply_text = response.choices[0].message.content
        
        if "[SAVE:" in reply_text:
            try:
                parts = reply_text.split("[SAVE:")
                clean_reply = parts[0].strip()
                save_part = parts[1].split("]")[0]
                if "=" in save_part:
                    k, v = save_part.split("=", 1)
                    save_memory(request.user_id, k.strip(), v.strip())
                reply_text = clean_reply
            except Exception:
                pass

        return {"reply": reply_text}
    except Exception as e:
        return {"reply": f"Groq Error: {str(e)}"}
