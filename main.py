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
                radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.08) 0%, transparent 70%);
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

        /* ARC REACTOR STYLING */
        .arc-reactor-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            width: 280px;
            height: 280px;
            cursor: pointer;
        }

        .ring-outer {
            position: absolute;
            width: 260px;
            height: 260px;
            border: 2px dashed rgba(56, 189, 248, 0.4);
            border-radius: 50%;
            animation: spinClockwise 15s linear infinite;
        }

        .ring-middle {
            position: absolute;
            width: 215px;
            height: 215px;
            border: 4px solid transparent;
            border-top: 4px solid var(--cyan-glow);
            border-bottom: 4px solid var(--orange-glow);
            border-radius: 50%;
            animation: spinCounter 8s linear infinite;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
        }

        .ring-inner {
            position: absolute;
            width: 170px;
            height: 170px;
            border: 1px dotted rgba(249, 115, 22, 0.8);
            border-radius: 50%;
            animation: spinClockwise 10s linear infinite;
        }

        .reactor-core {
            width: 120px;
            height: 120px;
            background: radial-gradient(circle, rgba(56, 189, 248, 0.5) 0%, rgba(2, 6, 23, 0.95) 80%);
            border: 2px solid var(--cyan-glow);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: inset 0 0 15px var(--cyan-glow), 0 0 25px rgba(56, 189, 248, 0.7);
            z-index: 2;
            transition: all 0.3s ease;
        }

        .reactor-text {
            font-size: 0.75rem;
            font-weight: bold;
            color: var(--text-main);
            letter-spacing: 2px;
            text-align: center;
            text-shadow: 0 0 8px var(--cyan-glow);
        }

        @keyframes spinClockwise {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes spinCounter {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-360deg); }
        }

        .active-reactor .ring-middle {
            border-top-color: var(--orange-glow);
            border-bottom-color: var(--cyan-glow);
            animation-duration: 1.5s;
            box-shadow: 0 0 35px var(--orange-glow);
        }

        .status-label {
            margin-top: 20px;
            font-size: 0.8rem;
            color: var(--cyan-glow);
            letter-spacing: 2px;
            text-transform: uppercase;
            text-shadow: 0 0 8px rgba(56, 189, 248, 0.5);
        }

        .transcript-box {
            margin-top: 10px;
            font-size: 0.7rem;
            color: #94a3b8;
            max-width: 300px;
            min-height: 20px;
        }
    </style>
</head>
<body onload="initJarvis()">

    <div class="container">
        <div class="arc-reactor-container" id="arcReactor" onclick="toggleListening()">
            <div class="ring-outer"></div>
            <div class="ring-middle"></div>
            <div class="ring-inner"></div>
            <div class="reactor-core">
                <div class="reactor-text" id="reactorStatus">STANDBY</div>
            </div>
        </div>
        <div class="status-label" id="systemState">Klik atau mula bercakap...</div>
        <div class="transcript-box" id="transcriptLog"></div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;
        let recognition;
        let isListening = false;
        let isSpeaking = false;

        function initJarvis() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Pelayar web ini tidak menyokong pengecaman suara.");
                return;
            }

            recognition = new SpeechRecognition();
            recognition.lang = 'ms-MY';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = function() {
                isListening = true;
                setVisualizer(true);
                document.getElementById('systemState').innerText = "LISTENING...";
            };

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('transcriptLog').innerText = `"${transcript}"`;
                sendToJarvis(transcript);
            };

            recognition.onerror = function(event) {
                console.log("Speech error: ", event.error);
                stopListening();
            };

            recognition.onend = function() {
                isListening = false;
                if (!isSpeaking) {
                    setVisualizer(false);
                    document.getElementById('systemState').innerText = "STANDBY (Klik untuk mula)";
                }
            };

            // Auto-start listening on load or click
            startListening();
        }

        function toggleListening() {
            if (isListening) {
                stopListening();
            } else {
                startListening();
            }
        }

        function startListening() {
            if (recognition && !isListening && !isSpeaking) {
                try {
                    recognition.start();
                } catch(e) {
                    console.log(e);
                }
            }
        }

        function stopListening() {
            if (recognition && isListening) {
                recognition.stop();
            }
        }

        function setVisualizer(active) {
            const reactor = document.getElementById('arcReactor');
            const statusText = document.getElementById('reactorStatus');
            
            if (active) {
                reactor.classList.add('active-reactor');
                statusText.innerText = "ACTIVE";
            } else {
                reactor.classList.remove('active-reactor');
                statusText.innerText = "STANDBY";
            }
        }

        async function sendToJarvis(prompt) {
            document.getElementById('systemState').innerText = "PROCESSING...";
            setVisualizer(true);

            try {
                const res = await fetch(`${BACKEND_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt, persona: "standard" })
                });
                const data = await res.json();
                speakResponse(data.reply);
            } catch (err) {
                document.getElementById('systemState').innerText = "ERROR";
                setVisualizer(false);
            }
        }

        function speakResponse(text) {
            if ('speechSynthesis' in window) {
                isSpeaking = true;
                stopListening();
                setVisualizer(true);
                document.getElementById('systemState').innerText = "SPEAKING...";
                document.getElementById('transcriptLog').innerText = text;

                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'ms-MY';
                
                utterance.onend = function() {
                    isSpeaking = false;
                    setVisualizer(false);
                    document.getElementById('systemState').innerText = "STANDBY";
                    // Sambung semula mendengar selepas AI habis bercakap
                    setTimeout(startListening, 500);
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
