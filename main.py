import os
import json
import sqlite3
import subprocess
import platform
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

# Fungsi Kawalan Komputer (System Control)
def execute_system_command(command: str):
    system_name = platform.system()
    cmd_lower = command.lower()
    try:
        if "notepad" in cmd_lower:
            if system_name == "Windows":
                subprocess.Popen(["notepad.exe"])
            return "Opening Notepad."
        elif "calculator" in cmd_lower or "kalkulator" in cmd_lower:
            if system_name == "Windows":
                subprocess.Popen(["calc.exe"])
            elif system_name == "Darwin":
                subprocess.Popen(["open", "-a", "Calculator"])
            return "Opening Calculator."
        elif "browser" in cmd_lower or "google" in cmd_lower:
            if system_name == "Windows":
                subprocess.Popen(["start", "chrome"], shell=True)
            elif system_name == "Darwin":
                subprocess.Popen(["open", "-a", "Google Chrome"])
            return "Opening browser."
        return None
    except Exception as e:
        return f"Failed to execute command: {str(e)}"

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

        .reactor-frame {
            position: relative;
            width: 380px;
            height: 380px;
            display: flex;
            align-items: center;
            justify-content: center;
            filter: drop-shadow(0 0 15px rgba(0, 240, 255, 0.4));
        }

        .ring-outer-tech {
            position: absolute;
            width: 370px;
            height: 370px;
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

        .ring-gauge-mid {
            position: absolute;
            width: 305px;
            height: 305px;
            border: 12px solid transparent;
            border-left: 12px solid var(--hud-orange);
            border-top: 12px solid var(--hud-cyan);
            border-radius: 50%;
            box-shadow: 0 0 20px var(--hud-orange-glow);
            animation: spinCounter 10s linear infinite;
        }

        .ring-inner-ticks {
            position: absolute;
            width: 240px;
            height: 240px;
            border: 2px dotted var(--hud-cyan);
            border-radius: 50%;
            animation: spinClockwise 12s linear infinite;
        }

        .ring-core-halo {
            position: absolute;
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, rgba(0, 240, 255, 0.25) 0%, rgba(0, 30, 60, 0.8) 75%);
            border: 2px solid var(--hud-cyan);
            border-radius: 50%;
            box-shadow: inset 0 0 25px var(--hud-cyan), 0 0 30px rgba(0, 240, 255, 0.6);
            animation: pulseGlow 3s ease-in-out infinite;
        }

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
    </div>

    <script>
        const BACKEND_URL = window.location.origin;
        let recognition;
        let isSpeaking = false;

        function initJarvis() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                return;
            }

            recognition = new SpeechRecognition();
            recognition.lang = 'ms-MY';
            recognition.continuous = true;
            recognition.interimResults = false;

            recognition.onresult = function(event) {
                if (isSpeaking) return;
                const transcript = event.results[event.results.length - 1][0].transcript.trim();
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
            try {
                const res = await fetch(`${BACKEND_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt, persona: "standard" })
                });
                const data = await res.json();
                speakResponse(data.reply);
            } catch (err) {
                console.log("Network error");
            }
        }

        function speakResponse(text) {
            if ('speechSynthesis' in window) {
                isSpeaking = true;

                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'en-GB';

                const voices = window.speechSynthesis.getVoices();
                const jarvisVoice = voices.find(v => v.lang === 'en-GB' && (v.name.toLowerCase().includes('male') || v.name.toLowerCase().includes('george') || v.name.toLowerCase().includes('oliver') || v.name.toLowerCase().includes('uk english')));
                if (jarvisVoice) {
                    utterance.voice = jarvisVoice;
                }

                utterance.pitch = 0.9;
                utterance.rate = 1.0;
                
                utterance.onend = function() {
                    isSpeaking = false;
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
    
    # Semak jika arahan berkaitan kawalan komputer (System Control)
    system_action_result = execute_system_command(request.prompt)
    if system_action_result:
        return {"reply": system_action_result}

    try:
        client = Groq(api_key=api_key.strip())
        current_memories = get_all_memories(request.user_id)
        
        system_prompt = f"""Kau ialah JARVIS, pembantu AI peribadi pintar bersgaya sains fiksyen. 
Kamu mempunyai kebolehan penuh untuk **menganalisis data** (seperti data teknikal, kod pengaturcaraan, pasaran kewangan, atau log matematik) dan memberikan rumusan yang mendalam dan tepat.
Memori pengguna:
{current_memories}

ARAHAN: Berikan jawapan yang ringkas, berwibawa, dan terus kepada isi kerana jawapan akan dibaca menggunakan suara gaya British. Jika pengguna bagi maklumat peribadi, simpan secara senyap dengan kod [SAVE:key=value] di hujung jawapan.
"""
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.7,
            max_tokens=200
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
