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

class MemoryDeleteRequest(BaseModel):
    user_id: str = "default_user"
    key: str

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
# ULTIMATE SCI-FI HUD UI
# ---------------------------------------------------------
HTML_CODE = """
<!DOCTYPE html>
<html lang="ms">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S // ULTIMATE HUD</title>
    <style>
        :root {
            --bg-deep: #030508;
            --panel-bg: rgba(10, 15, 28, 0.9);
            --border-neon: rgba(249, 115, 22, 0.5);
            --orange-glow: #f97316;
            --cyan-glow: #38bdf8;
            --text-main: #f1f5f9;
        }

        body {
            font-family: 'Courier New', Courier, monospace, 'Segoe UI', sans-serif;
            background-color: var(--bg-deep);
            background-image: 
                radial-gradient(circle at 5% 10%, rgba(249, 115, 22, 0.08) 0%, transparent 45%),
                radial-gradient(circle at 95% 90%, rgba(56, 189, 248, 0.08) 0%, transparent 45%);
            color: var(--text-main);
            padding: 10px;
            max-width: 1100px;
            margin: auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border-neon);
            padding-bottom: 10px;
            margin-bottom: 15px;
        }

        h1 {
            font-size: 1.3rem;
            letter-spacing: 3px;
            color: var(--orange-glow);
            text-shadow: 0 0 12px rgba(249, 115, 22, 0.7);
            margin: 0;
        }

        .hud-clock {
            font-size: 0.85rem;
            color: var(--cyan-glow);
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.4);
            padding: 4px 10px;
            border-radius: 4px;
        }

        .grid-container {
            display: grid;
            grid-template-columns: 1.8fr 1.2fr;
            gap: 12px;
        }

        @media (max-width: 768px) {
            .grid-container { grid-template-columns: 1fr; }
        }

        .card {
            background: var(--panel-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-neon);
            border-radius: 6px;
            padding: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.8);
            position: relative;
            margin-bottom: 12px;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 4px; height: 100%;
            background: var(--orange-glow);
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
        }

        h3 {
            color: var(--cyan-glow);
            margin-top: 0;
            font-size: 0.85rem;
            letter-spacing: 1px;
            text-transform: uppercase;
            border-bottom: 1px dashed rgba(56, 189, 248, 0.2);
            padding-bottom: 5px;
        }

        #chatbox {
            height: 220px;
            overflow-y: auto;
            background: rgba(1, 3, 8, 0.95);
            padding: 10px;
            border-radius: 4px;
            border: 1px solid rgba(56, 189, 248, 0.2);
            margin-bottom: 10px;
            font-size: 0.85rem;
        }

        .user-msg { color: var(--cyan-glow); margin: 5px 0; }
        .jarvis-msg { color: #4ade80; margin: 5px 0; }

        .input-group {
            display: flex;
            gap: 6px;
            margin-bottom: 6px;
        }

        input[type="text"] {
            flex: 1;
            padding: 8px;
            background: rgba(1, 3, 8, 0.95);
            color: var(--text-main);
            border: 1px solid var(--border-neon);
            border-radius: 4px;
            outline: none;
            font-family: inherit;
            font-size: 0.85rem;
        }

        input[type="text"]:focus {
            border-color: var(--cyan-glow);
            box-shadow: 0 0 6px rgba(56, 189, 248, 0.4);
        }

        button {
            background: linear-gradient(135deg, #f97316, #c2410c);
            color: white;
            border: none;
            padding: 8px 12px;
            cursor: pointer;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.8rem;
            letter-spacing: 1px;
            box-shadow: 0 0 6px rgba(249, 115, 22, 0.4);
        }

        button:hover { box-shadow: 0 0 10px rgba(249, 115, 22, 0.8); }

        .btn-full { width: 100%; margin-top: 4px; background: linear-gradient(135deg, #0284c7, #0369a1); }

        /* Quick Shortcut Buttons */
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 5px;
            margin-bottom: 8px;
        }
        .btn-quick {
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: var(--cyan-glow);
            font-size: 0.7rem;
            padding: 6px;
            text-align: left;
            border-radius: 4px;
        }
        .btn-quick:hover { background: rgba(56, 189, 248, 0.2); }

        /* Audio Visualizer */
        .visualizer {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 3px;
            height: 20px;
            margin: 6px 0;
            background: rgba(0,0,0,0.5);
            border-radius: 3px;
        }
        .bar { width: 3px; height: 4px; background: var(--cyan-glow); border-radius: 2px; }
        .active-bar .bar { animation: pulseWave 0.5s infinite alternate; }
        @keyframes pulseWave { 0% { height: 4px; } 100% { height: 16px; background: var(--orange-glow); } }

        /* Memory List */
        #memoryList {
            max-height: 120px;
            overflow-y: auto;
            background: rgba(1, 3, 8, 0.95);
            padding: 6px;
            border-radius: 4px;
            border: 1px solid rgba(249, 115, 22, 0.2);
            font-size: 0.75rem;
            margin-bottom: 6px;
        }
        .mem-item { display: flex; justify-content: space-between; align-items: center; padding: 3px 0; border-bottom: 1px dotted rgba(255,255,255,0.1); }
        .mem-item span { color: #facc15; }
        .btn-del { background: #dc2626; padding: 1px 4px; font-size: 0.65rem; box-shadow: none; }

        /* Terminal Log */
        #terminalLog {
            background: #010308;
            color: #4ade80;
            border: 1px solid rgba(74, 222, 128, 0.3);
            border-radius: 4px;
            padding: 8px;
            height: 90px;
            overflow-y: auto;
            font-size: 0.7rem;
            line-height: 1.2;
        }

        .sys-metrics p {
            margin: 4px 0;
            font-size: 0.75rem;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
        }
        .sys-metrics span { color: var(--orange-glow); }

        .settings-box label { font-size: 0.75rem; color: #94a3b8; display: block; margin-top: 4px; }
        .settings-box input { width: 100%; accent-color: var(--orange-glow); }
    </style>
</head>
<body onload="initSystem()">

    <header>
        <h1>⚡ J.A.R.V.I.S // OMNI-HUD</h1>
        <div class="hud-clock" id="clockDisplay">00:00:00</div>
    </header>

    <div class="grid-container">
        <!-- Left Panel: Chat, Voice & Quick Actions -->
        <div>
            <div class="card">
                <h3>Neural Communication Link</h3>
                <div id="chatbox">
                    <p class="jarvis-msg"><b>JARVIS:</b> Sistem protokol muat turun selesai. Sedia menerima arahan.</p>
                </div>
                
                <div class="visualizer" id="vizBar">
                    <div class="bar" style="animation-delay: 0.1s"></div>
                    <div class="bar" style="animation-delay: 0.2s"></div>
                    <div class="bar" style="animation-delay: 0.3s"></div>
                    <div class="bar" style="animation-delay: 0.4s"></div>
                    <div class="bar" style="animation-delay: 0.5s"></div>
                    <div class="bar" style="animation-delay: 0.2s"></div>
                </div>

                <div class="quick-actions">
                    <button class="btn-quick" onclick="sendQuick('Siapa nama aku?')">📌 Siapa nama aku?</button>
                    <button class="btn-quick" onclick="sendQuick('Senaraikan memori')">🧠 Imbas Memori</button>
                    <button class="btn-quick" onclick="sendQuick('Status sistem')">⚙️ Status Sistem</button>
                    <button class="btn-quick" onclick="sendQuick('Beri kata semangat')">⚡ Protokol Semangat</button>
                </div>

                <div class="input-group">
                    <input type="text" id="userInput" placeholder="Masukkan arahan teks..." onkeypress="if(event.key === 'Enter') sendChat()">
                    <button onclick="sendChat()">HANTAR</button>
                </div>
                <button class="btn-full" onclick="startVoice()">🎙️ AKTIFKAN SUARA</button>
            </div>

            <!-- Terminal Log -->
            <div class="card">
                <h3>Live System Terminal Log</h3>
                <div id="terminalLog">
                    [00:00:01] System boot sequence initialized...<br>
                    [00:00:02] Connected to Groq neural cloud server.<br>
                    [00:00:03] SQLite database loaded successfully.
                </div>
            </div>
        </div>

        <!-- Right Panel: Memory, Metrics & Voice Settings -->
        <div>
            <div class="card">
                <h3>Active Memory Bank</h3>
                <div id="memoryList">
                    <p style="color:#64748b; text-align:center; font-size:0.75rem;">Memuatkan data...</p>
                </div>
                <button class="btn-full" style="background:#059669; font-size:0.75rem; padding:5px;" onclick="loadMemories()">🔄 Segarkan Memori</button>
            </div>

            <div class="card settings-box">
                <h3>Voice Config (TTS)</h3>
                <label>Kelajuan Suara: <span id="rateVal">1.0</span>x</label>
                <input type="range" id="speechRate" min="0.7" max="1.5" step="0.1" value="1.0" oninput="document.getElementById('rateVal').innerText=this.value">
                
                <label>Nada Suara: <span id="pitchVal">1.0</span></label>
                <input type="range" id="speechPitch" min="0.5" max="1.5" step="0.1" value="1.0" oninput="document.getElementById('pitchVal').innerText=this.value">
            </div>

            <div class="card sys-metrics">
                <h3>Hardware Metrics</h3>
                <p>Cloud AI: <span>Groq gpt-oss-20b</span></p>
                <p>Database: <span>SQLite (Local)</span></p>
                <p>Latency: <span>12ms (Optimal)</span></p>
                <p>Security Protocol: <span style="color:#4ade80">SECURE</span></p>
            </div>
        </div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;

        function logTerm(msg) {
            const term = document.getElementById('terminalLog');
            const time = new Date().toLocaleTimeString();
            term.innerHTML += `<br>[${time}] ${msg}`;
            term.scrollTop = term.scrollHeight;
        }

        function initSystem() {
            loadMemories();
            updateClock();
        }

        function updateClock() {
            const now = new Date();
            document.getElementById('clockDisplay').innerText = now.toLocaleTimeString();
            setTimeout(updateClock, 1000);
        }

        function setVisualizer(active) {
            const viz = document.getElementById('vizBar');
            if (active) viz.classList.add('active-bar');
            else viz.classList.remove('active-bar');
        }

        function sendQuick(text) {
            document.getElementById('userInput').value = text;
            sendChat();
        }

        function startVoice() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) return alert("Pelayar tidak menyokong rakaman suara.");
            
            const recognition = new SpeechRecognition();
            recognition.lang = 'ms-MY';
            setVisualizer(true);
            logTerm("Voice recognition activated...");
            recognition.start();

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('userInput').value = transcript;
                setVisualizer(false);
                sendChat();
            };
            recognition.onerror = () => { setVisualizer(false); logTerm("Voice recognition error."); };
            recognition.onspeechend = () => setVisualizer(false);
        }

        function speak(text) {
            if ('speechSynthesis' in window) {
                setVisualizer(true);
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'ms-MY';
                utterance.rate = parseFloat(document.getElementById('speechRate').value);
                utterance.pitch = parseFloat(document.getElementById('speechPitch').value);
                utterance.onend = () => setVisualizer(false);
                window.speechSynthesis.speak(utterance);
            }
        }

        async function loadMemories() {
            try {
                const res = await fetch(`${BACKEND_URL}/memories`);
                const data = await res.json();
                const listDiv = document.getElementById('memoryList');
                if (data.memories.length === 0) {
                    listDiv.innerHTML = '<p style="color:#64748b; text-align:center; font-size:0.75rem;">Tiada memori tersimpan.</p>';
                    return;
                }
                listDiv.innerHTML = data.memories.map(m => `
                    <div class="mem-item">
                        <span><b>${m.key}</b>: ${m.value}</span>
                        <button class="btn-del" onclick="deleteMemory('${m.key}')">X</button>
                    </div>
                `).join('');
                logTerm("Memory banks refreshed.");
            } catch (err) {
                logTerm("Failed to fetch memories.");
            }
        }

        async function deleteMemory(key) {
            await fetch(`${BACKEND_URL}/delete_memory`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: key })
            });
            logTerm(`Memory deleted: ${key}`);
            loadMemories();
        }

        async function sendChat() {
            const prompt = document.getElementById('userInput').value;
            if (!prompt) return;

            const chatbox = document.getElementById('chatbox');
            chatbox.innerHTML += `<p class="user-msg"><b>Anda:</b> ${prompt}</p>`;
            document.getElementById('userInput').value = '';
            chatbox.scrollTop = chatbox.scrollHeight;

            setVisualizer(true);
            logTerm(`Transmitting prompt to Groq API...`);

            try {
                const res = await fetch(`${BACKEND_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt })
                });
                const data = await res.json();
                chatbox.innerHTML += `<p class="jarvis-msg"><b>JARVIS:</b> ${data.reply}</p>`;
                chatbox.scrollTop = chatbox.scrollHeight;
                setVisualizer(false);
                logTerm("Response received successfully.");
                loadMemories(); 
                speak(data.reply);
            } catch (err) {
                setVisualizer(false);
                chatbox.innerHTML += `<p style="color:red">Ralat rangkaian.</p>`;
                logTerm("Error: Network transmission failed.");
            }
        }
    </script>
</body>
</html>
"""

# ---------------------------------------------------------
# ENDPOINTS BACKEND
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_CODE

@app.get("/memories")
def get_memories_api(user_id: str = "default_user"):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM memory WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        memories = [{"key": r[0], "value": r[1]} for r in rows]
        return {"memories": memories}
    except Exception:
        return {"memories": []}

@app.post("/delete_memory")
def delete_memory_api(req: MemoryDeleteRequest):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memory WHERE user_id = ? AND key = ?", (req.user_id, req.key))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"reply": "Error: GROQ_API_KEY tidak dijumpai di Render!"}
    
    try:
        client = Groq(api_key=api_key.strip())
        current_memories = get_all_memories(request.user_id)
        
        system_prompt = f"""Kau ialah JARVIS, pembantu AI peribadi gaya sains fiksyen yang bijak dan setia.
Memori sedia ada pengguna ({request.user_id}):
{current_memories}

ARAHAN KHAS:
Jika pengguna memaklumkan maklumat peribadi (cth: nama, hobi, minat), balas seperti biasa dan sertakan kod ini di hujung mesej secara senyap:
[SAVE:key=value]
Contoh: Baik Tuan, saya simpan.[SAVE:nama=adhwa]
Jika tiada maklumat baru, jangan sertakan [SAVE:...].
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
