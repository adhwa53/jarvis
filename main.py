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
    <title>J.A.R.V.I.S // HUD REACTOR 1:1</title>
    <style>
        :root {
            --bg-deep: #010408;
            --hud-cyan: #00f0ff;
            --hud-cyan-dim: rgba(0, 240, 255, 0.3);
            --hud-orange: #ff9900;
            --hud-orange-glow: rgba(255, 153, 0, 0.8);
            --text-main: #e2e8f0;
        }

        body {
            font-family: 'Courier New', Courier, monospace, sans-serif;
            background-color: var(--bg-deep);
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(0, 240, 255, 0.12) 0%, rgba(1, 4, 8, 0.95) 75%),
                linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.3) 50%);
            background-size: 100% 100%, 100% 4px;
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

        /* 1:1 EXACT STARK HUD REACTOR STYLING */
        .reactor-frame {
            position: relative;
            width: 360px;
            height: 360px;
            display: flex;
            align-items: center;
            justify-content: center;
            filter: drop-shadow(0 0 15px rgba(0, 240, 255, 0.4));
        }

        /* Layer 1: Outer Tech Ring dengan Segmen Tebal */
        .ring-outer-tech {
            position: absolute;
            width: 350px;
            height: 350px;
            border: 3px solid rgba(0, 240, 255, 0.2);
            border-top: 5px solid var(--hud-cyan);
            border-bottom: 5px solid var(--hud-cyan);
            border-radius: 50%;
            animation: spinClockwise 25s linear infinite;
        }

        .ring-outer-tech::before {
            content: '';
            position: absolute;
            top: -6px; left: -6px; right: -6px; bottom: -6px;
            border: 2px dashed rgba(0, 240, 255, 0.4);
            border-radius: 50%;
            animation: spinCounter 18s linear infinite;
        }

        /* Layer 2: Middle Gauge & Orange Arc Segments */
        .ring-gauge-mid {
            position: absolute;
            width: 290px;
            height: 290px;
            border: 12px solid transparent;
            border-left: 12px solid var(--hud-orange);
            border-top: 12px solid var(--hud-cyan);
            border-radius: 50%;
            box-shadow: 0 0 20px var(--hud-orange-glow);
            animation: spinCounter 10s linear infinite;
        }

        /* Layer 3: Inner Ticks & Dashed Target */
        .ring-inner-ticks {
            position: absolute;
            width: 230px;
            height: 230px;
            border: 2px dotted var(--hud-cyan);
            border-radius: 50%;
            animation: spinClockwise 12s linear infinite;
        }

        /* Layer 4: Core Halo Hologram */
        .ring-core-halo {
            position: absolute;
            width: 175px;
            height: 175px;
            background: radial-gradient(circle, rgba(0, 240, 255, 0.25) 0%, rgba(0, 30, 60, 0.8) 75%);
            border: 2px solid var(--hud-cyan);
            border-radius: 50%;
            box-shadow: inset 0 0 25px var(--hud-cyan), 0 0 30px rgba(0, 240, 255, 0.6);
            animation: pulseGlow 3s ease-in-out infinite;
        }

        /* Layer 5: Center Core Text J.A.R.V.I.S. */
        .reactor-core-center {
            position: relative;
            width: 120px;
            height: 120px;
            background: rgba(1, 10, 25, 0.9);
            border: 2px solid var(--hud-cyan);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: inset 0 0 15px var(--hud-cyan);
            z-index: 5;
        }

        .jarvis-title {
            font-size: 0.95rem;
            font-weight: 900;
            color: #ffffff;
            letter-spacing: 3px;
            text-shadow: 0 0 10px var(--hud-cyan), 0 0 20px var(--hud-cyan);
        }

        /* Animations */
        @keyframes spinClockwise {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes spinCounter {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-360deg); }
        }

        @keyframes pulseGlow {
            0%, 100% { transform: scale(1); opacity: 0.85; }
            50% { transform: scale(1.03); opacity: 1; }
        }

        .status-label {
            margin-top: 30px;
            font-size: 0.85rem;
            color: var(--hud-cyan);
            letter-spacing: 4px;
            text-transform: uppercase;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.7);
        }

        .transcript-box {
            margin-top: 12px;
            font-size: 0.75rem;
            color: #94a3b8;
            max-width: 400px;
            min-height: 25px;
            letter-spacing: 1px;
        }
    </style>
</head>
<body onload="initJarvis()">

    <div class="container">
        <div class="reactor-frame">
            <div class="ring-outer-tech"></div>
            <div class="ring-gauge-mid"></div>
            <div class="ring-inner-ticks"></div>
            <div class="ring-core-halo"></div>
            <div class="reactor-core-center">
                <div class="jarvis-title">J.A.R.V.I.S</div>
            </div>
        </div>
        <div class="status-label" id="systemState">ONLINE // MENDENGAR...</div>
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
            recognition.continuous = true;
            recognition.interimResults = false;

            recognition.onstart = function() {
                document.getElementById('systemState').innerText = "ONLINE // MENDENGAR...";
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
                if (!isSpeaking) {
                    try { recognition.start(); } catch(e) {}
                }
            };

            try {
                recognition.start();
            } catch(e) {}
        }

        async function sendToJarvis(prompt) {
            document.getElementById('systemState').innerText = "MEMPROSES ANALISIS...";

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
                document.getElementById('systemState').innerText = "JARVIS BERCAKAP...";
                document.getElementById('transcriptLog').innerText = text;

                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'en-GB'; // English United Kingdom (Gaya British JARVIS)

                const voices = window.speechSynthesis.getVoices();
                const jarvisVoice = voices.find(v => v.lang === 'en-GB' && (v.name.toLowerCase().includes('male') || v.name.toLowerCase().includes('george') || v.name.toLowerCase().includes('oliver') || v.name.toLowerCase().includes('uk english')));
                if (jarvisVoice) {
                    utterance.voice = jarvisVoice;
                }

                utterance.pitch = 0.9;
                utterance.rate = 1.0;
                
                utterance.onend = function() {
                    isSpeaking = false;
                    document.getElementById('systemState').innerText = "ONLINE // MENDENGAR...";
                    document.getElementById('transcriptLog').innerText = "Sila mula bercakap...";
                };

                window.speechSynthesis.speak(utterance);
            }
        }

        if ('speechSynthesis' in window) {
            window.speechSynthesis.onvoiceschanged = () => {
                window.speechSynthesis.getVoices();
            };
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
