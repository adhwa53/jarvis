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
    persona: str = "standard"

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

HTML_CODE = """
<!DOCTYPE html>
<html lang="ms">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S // ARC REACTOR CORE</title>
    <style>
        :root {
            --bg-deep: #020408;
            --orange-glow: #f97316;
            --cyan-glow: #38bdf8;
            --text-main: #f1f5f9;
        }

        body {
            font-family: 'Courier New', Courier, monospace, sans-serif;
            background-color: var(--bg-deep);
            background-image: 
                linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%),
                radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.1) 0%, transparent 70%);
            background-size: 100% 4px, 100% 100%;
            color: var(--text-main);
            height: 100vh;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        /* ARC REACTOR STYLING - SENTIASA AKTIF */
        .arc-reactor-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            width: 280px;
            height: 280px;
        }

        .ring-outer {
            position: absolute;
            width: 260px;
            height: 260px;
            border: 2px dashed rgba(56, 189, 248, 0.6);
            border-radius: 50%;
            animation: spinClockwise 12s linear infinite;
        }

        .ring-middle {
            position: absolute;
            width: 215px;
            height: 215px;
            border: 4px solid transparent;
            border-top: 4px solid var(--orange-glow);
            border-bottom: 4px solid var(--cyan-glow);
            border-radius: 50%;
            animation: spinCounter 6s linear infinite;
            box-shadow: 0 0 25px rgba(249, 115, 22, 0.5);
        }

        .ring-inner {
            position: absolute;
            width: 170px;
            height: 170px;
            border: 1px dotted rgba(56, 189, 248, 0.9);
            border-radius: 50%;
            animation: spinClockwise 8s linear infinite;
        }

        .reactor-core {
            width: 120px;
            height: 120px;
            background: radial-gradient(circle, rgba(56, 189, 248, 0.6) 0%, rgba(2, 6, 23, 0.95) 80%);
            border: 2px solid var(--cyan-glow);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: inset 0 0 20px var(--cyan-glow), 0 0 30px rgba(56, 189, 248, 0.8);
            z-index: 2;
        }

        .reactor-text {
            font-size: 0.75rem;
            font-weight: bold;
            color: var(--text-main);
            letter-spacing: 2px;
            text-align: center;
            text-shadow: 0 0 10px var(--cyan-glow);
        }

        @keyframes spinClockwise {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes spinCounter {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-360deg); }
        }

        .status-label {
            margin-top: 25px;
            font-size: 0.85rem;
            color: var(--cyan-glow);
            letter-spacing: 3px;
            text-transform: uppercase;
            text-shadow: 0 0 10px rgba(56, 189, 248, 0.6);
        }

        .transcript-box {
            margin-top: 10px;
            font-size: 0.75rem;
            color: #94a3b8;
            max-width: 350px;
            min-height: 25px;
            letter-spacing: 1px;
        }
    </style>
</head>
<body onload="initJarvis()">

    <div class="container">
        <div class="arc-reactor-container" id="arcReactor">
            <div class="ring-outer"></div>
            <div class="ring-middle"></div>
            <div class="ring-inner"></div>
            <div class="reactor-core">
                <div class="reactor-text" id="reactorStatus">ONLINE</div>
            </div>
        </div>
        <div class="status-label" id="systemState">SISTEM AKTIF // MENUNGGU ARAHAN...</div>
        <div class="transcript-box" id="transcriptLog">Sila mula bercakap...</div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;
        let recognition;
        let isSpeaking = false;

        function initJarvis() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Pelayar web ini tidak menyokong pengecaman suara.");
                return;
            }

            recognition = new SpeechRecognition();
            recognition.lang = 'ms-MY';
            recognition.continuous = true; // Sentiasa hidup
            recognition.interimResults = false;

            recognition.onstart = function() {
                document.getElementById('systemState').innerText = "MENDENGAR...";
            };

            recognition.onresult = function(event) {
                if (isSpeaking) return;
                const transcript = event.results[event.results.length - 1][0].transcript.trim();
                document.getElementById('transcriptLog').innerText = `"${transcript}"`;
                sendToJarvis(transcript);
            };

            recognition.onerror = function(event) {
                console.log("Speech error: ", event.error);
            };

            recognition.onend = function() {
                // Auto restart kalau terpadam supaya sentiasa mendengar
                if (!isSpeaking) {
                    try { recognition.start(); } catch(e) {}
                }
            };

            // Mula mendengar secara automatik
            try {
                recognition.start();
            } catch(e) {}
        }

        async function sendToJarvis(prompt) {
            document.getElementById('systemState').innerText = "MEMPROSES...";

            try {
                const res = await fetch(`${BACKEND_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt, persona: "standard" })
                });
                const data = await res.json();
                speakResponse(data.reply);
            } catch (err) {
                document.getElementById('systemState').innerText = "RALAT RANGKAIAN";
            }
        }

        function speakResponse(text) {
            if ('speechSynthesis' in window) {
                isSpeaking = true;
                document.getElementById('systemState').innerText = "BERCAKAP...";
                document.getElementById('transcriptLog').innerText = text;

                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'ms-MY';
                
                utterance.onend = function() {
                    isSpeaking = false;
                    document.getElementById('systemState').innerText = "MENDENGAR...";
                    document.getElementById('transcriptLog').innerText = "Sila mula bercakap...";
                };

                window.speechSynthesis.speak(utterance);
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_CODE

@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"reply": "Error: GROQ_API_KEY tidak dijumpai."}
    
    try:
        client = Groq(api_key=api_key.strip())
        current_memories = get_all_memories(request.user_id)
        
        system_prompt = f"""Kau ialah JARVIS, pembantu AI peribadi gaya sains fiksyen yang bijak dan ringkas.
Memori pengguna:
{current_memories}

ARAHAN: Berikan jawapan yang pendek, padat, dan terus kepada isi kerana jawapan ini akan dibaca menggunakan suara. Jika pengguna bagi maklumat peribadi, simpan secara senyap dengan kod [SAVE:key=value] di hujung jawapan.
"""
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.7,
            max_tokens=150
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
        return {"reply": f"Ralat sistem: {str(e)}"}
