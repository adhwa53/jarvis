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

class MemoryDeleteRequest(BaseModel):
    user_id: str = "default_user"
    key: str

class NoteRequest(BaseModel):
    user_id: str = "default_user"
    title: str
    content: str

class ReminderRequest(BaseModel):
    user_id: str = "default_user"
    task: str
    time_str: str

# ---------------------------------------------------------
# DATABASE SETUP (SQLite - Diinspirasikan dari Jarvis Architecture)
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            title TEXT,
            content TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            task TEXT,
            time_str TEXT,
            status TEXT DEFAULT 'PENDING'
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
# ULTIMATE SCI-FI OMNI-HUD UI v5.0
# ---------------------------------------------------------
HTML_CODE = """
<!DOCTYPE html>
<html lang="ms">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S // OMNI-HUD v5.0</title>
    <style>
        :root {
            --bg-deep: #020408;
            --panel-bg: rgba(8, 13, 24, 0.94);
            --border-neon: rgba(249, 115, 22, 0.45);
            --orange-glow: #f97316;
            --cyan-glow: #38bdf8;
            --text-main: #f1f5f9;
        }

        body {
            font-family: 'Courier New', Courier, monospace, 'Segoe UI', sans-serif;
            background-color: var(--bg-deep);
            background-image: 
                linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%),
                radial-gradient(circle at 10% 15%, rgba(249, 115, 22, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 85%, rgba(56, 189, 248, 0.08) 0%, transparent 40%);
            background-size: 100% 4px, 100% 100%;
            color: var(--text-main);
            padding: 10px;
            max-width: 1300px;
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
            font-size: 1.25rem;
            letter-spacing: 3px;
            color: var(--orange-glow);
            text-shadow: 0 0 12px rgba(249, 115, 22, 0.7);
            margin: 0;
        }

        .hud-clock {
            font-size: 0.8rem;
            color: var(--cyan-glow);
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.4);
            padding: 4px 10px;
            border-radius: 4px;
        }

        .grid-container {
            display: grid;
            grid-template-columns: 1.5fr 1fr 1fr;
            gap: 12px;
        }

        @media (max-width: 1024px) {
            .grid-container { grid-template-columns: 1fr 1fr; }
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
            font-size: 0.8rem;
            letter-spacing: 1px;
            text-transform: uppercase;
            border-bottom: 1px dashed rgba(56, 189, 248, 0.2);
            padding-bottom: 5px;
        }

        #chatbox {
            height: 190px;
            overflow-y: auto;
            background: rgba(1, 3, 8, 0.95);
            padding: 8px;
            border-radius: 4px;
            border: 1px solid rgba(56, 189, 248, 0.2);
            margin-bottom: 8px;
            font-size: 0.8rem;
        }

        .user-msg { color: var(--cyan-glow); margin: 4px 0; }
        .jarvis-msg { color: #4ade80; margin: 4px 0; }

        .input-group {
            display: flex;
            gap: 6px;
            margin-bottom: 6px;
        }

        input[type="text"], select, textarea, input[type="datetime-local"] {
            width: 100%;
            padding: 7px;
            background: rgba(1, 3, 8, 0.95);
            color: var(--text-main);
            border: 1px solid var(--border-neon);
            border-radius: 4px;
            outline: none;
            font-family: inherit;
            font-size: 0.75rem;
            margin-bottom: 6px;
        }

        input:focus, select:focus, textarea:focus {
            border-color: var(--cyan-glow);
            box-shadow: 0 0 6px rgba(56, 189, 248, 0.4);
        }

        button {
            background: linear-gradient(135deg, #f97316, #c2410c);
            color: white;
            border: none;
            padding: 7px 10px;
            cursor: pointer;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.75rem;
            letter-spacing: 1px;
            box-shadow: 0 0 6px rgba(249, 115, 22, 0.4);
        }

        button:hover { box-shadow: 0 0 10px rgba(249, 115, 22, 0.8); }

        .btn-full { width: 100%; margin-top: 4px; background: linear-gradient(135deg, #0284c7, #0369a1); }

        .quick-actions {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 4px;
            margin-bottom: 6px;
        }
        .btn-quick {
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: var(--cyan-glow);
            font-size: 0.65rem;
            padding: 5px;
            text-align: left;
            border-radius: 3px;
        }
        .btn-quick:hover { background: rgba(56, 189, 248, 0.2); }

        .visualizer {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 3px;
            height: 18px;
            margin: 5px 0;
            background: rgba(0,0,0,0.5);
            border-radius: 3px;
        }
        .bar { width: 3px; height: 4px; background: var(--cyan-glow); border-radius: 2px; }
        .active-bar .bar { animation: pulseWave 0.4s infinite alternate; }
        @keyframes pulseWave { 0% { height: 4px; } 100% { height: 14px; background: var(--orange-glow); } }

        #memoryList, #notesList, #remindersList {
            max-height: 100px;
            overflow-y: auto;
            background: rgba(1, 3, 8, 0.95);
            padding: 5px;
            border-radius: 4px;
            border: 1px solid rgba(249, 115, 22, 0.2);
            font-size: 0.7rem;
            margin-bottom: 5px;
        }
        .mem-item, .note-item, .rem-item { display: flex; justify-content: space-between; align-items: center; padding: 2px 0; border-bottom: 1px dotted rgba(255,255,255,0.1); }
        .mem-item span { color: #facc15; }
        .note-item span { color: #38bdf8; }
        .rem-item span { color: #f43f5e; }
        .btn-del { background: #dc2626; padding: 1px 4px; font-size: 0.6rem; box-shadow: none; }

        #terminalLog {
            background: #010308;
            color: #4ade80;
            border: 1px solid rgba(74, 222, 128, 0.3);
            border-radius: 4px;
            padding: 6px;
            height: 60px;
            overflow-y: auto;
            font-size: 0.65rem;
            line-height: 1.1;
        }

        .sys-metrics p {
            margin: 3px 0;
            font-size: 0.7rem;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
        }
        .sys-metrics span { color: var(--orange-glow); }

        .settings-box label { font-size: 0.7rem; color: #94a3b8; display: block; margin-top: 3px; }
        .settings-box input { width: 100%; accent-color: var(--orange-glow); }
    </style>
</head>
<body onload="initSystem()">

    <header>
        <h1>⚡ J.A.R.V.I.S // OMNI-HUD v5</h1>
        <div class="hud-clock" id="clockDisplay">00:00:00</div>
    </header>

    <div class="grid-container">
        <!-- Kolum 1: Komunikasi & Sembang -->
        <div>
            <div class="card">
                <h3>Neural Communication Link</h3>
                <label style="font-size:0.65rem; color:#94a3b8">Mod Protokol AI:</label>
                <select id="personaSelect" onchange="logTerm('Persona ditukar ke: ' + this.value)">
                    <option value="standard">Standard (Bijak & Setia)</option>
                    <option value="stark">Tony Stark (Sarcastic & Santai)</option>
                    <option value="it_expert">Pakar IT (Teknikal & Mendalam)</option>
                </select>

                <div id="chatbox">
                    <p class="jarvis-msg"><b>JARVIS:</b> Sistem v5 aktif dengan modul automasi misi.</p>
                </div>
                
                <div class="visualizer" id="vizBar">
                    <div class="bar" style="animation-delay: 0.1s"></div>
                    <div class="bar" style="animation-delay: 0.2s"></div>
                    <div class="bar" style="animation-delay: 0.3s"></div>
                    <div class="bar" style="animation-delay: 0.4s"></div>
                    <div class="bar" style="animation-delay: 0.5s"></div>
                </div>

                <div class="quick-actions">
                    <button class="btn-quick" onclick="sendQuick('Siapa nama aku?')">📌 Siapa nama aku?</button>
                    <button class="btn-quick" onclick="sendQuick('Senaraikan memori')">🧠 Imbas Memori</button>
                    <button class="btn-quick" onclick="sendQuick('Status sistem')">⚙️ Status Sistem</button>
                    <button class="btn-quick" onclick="sendQuick('Beri kata semangat')">⚡ Protokol Semangat</button>
                </div>

                <div class="input-group">
                    <input type="text" id="userInput" placeholder="Taip arahan..." onkeypress="if(event.key === 'Enter') sendChat()">
                    <button onclick="sendChat()">HANTAR</button>
                </div>
                <button class="btn-full" onclick="startVoice()">🎙️ AKTIFKAN SUARA</button>
            </div>
        </div>

        <!-- Kolum 2: Memori & Log Terminal -->
        <div>
            <div class="card">
                <h3>Active Memory Bank</h3>
                <div id="memoryList">
                    <p style="color:#64748b; text-align:center; font-size:0.7rem;">Memuatkan data...</p>
                </div>
                <button class="btn-full" style="background:#059669; font-size:0.7rem; padding:4px;" onclick="loadMemories()">🔄 Segarkan Memori</button>
            </div>

            <div class="card">
                <h3>System Terminal Log</h3>
                <div id="terminalLog">
                    [00:00:01] System boot initialized...<br>
                    [00:00:02] Automation modules loaded.
                </div>
            </div>

            <div class="card sys-metrics">
                <h3>Hardware Metrics</h3>
                <p>Cloud AI: <span>Groq gpt-oss-20b</span></p>
                <p>Status: <span style="color:#4ade80">ONLINE</span></p>
            </div>
        </div>

        <!-- Kolum 3: Nota Misi & Reminders (Modul Tambahan Baru) -->
        <div>
            <div class="card">
                <h3>Mission Logs & Notes</h3>
                <input type="text" id="noteTitle" placeholder="Tajuk nota...">
                <textarea id="noteContent" placeholder="Kandungan nota..." rows="2"></textarea>
                <button class="btn-full" style="background:#d97706; font-size:0.7rem; padding:4px;" onclick="saveNote()">➕ Simpan Nota</button>
                <div id="notesList" style="margin-top:5px;">
                    <p style="color:#64748b; text-align:center; font-size:0.7rem;">Tiada nota.</p>
                </div>
            </div>

            <div class="card">
                <h3>Protocol Reminders</h3>
                <input type="text" id="remTask" placeholder="Perkara/Tugasan...">
                <input type="text" id="remTime" placeholder="Masa (cth: Esok 3 petang)">
                <button class="btn-full" style="background:#e11d48; font-size:0.7rem; padding:4px;" onclick="saveReminder()">⏰ Tambah Peringatan</button>
                <div id="remindersList" style="margin-top:5px;">
                    <p style="color:#64748b; text-align:center; font-size:0.7rem;">Tiada peringatan.</p>
                </div>
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
            loadNotes();
            loadReminders();
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
            logTerm("Voice recognition active...");
            recognition.start();

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('userInput').value = transcript;
                setVisualizer(false);
                sendChat();
            };
            recognition.onerror = () => { setVisualizer(false); logTerm("Voice error."); };
            recognition.onspeechend = () => setVisualizer(false);
        }

        function speak(text) {
            if ('speechSynthesis' in window) {
                setVisualizer(true);
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'ms-MY';
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
                    listDiv.innerHTML = '<p style="color:#64748b; text-align:center; font-size:0.7rem;">Tiada memori.</p>';
                    return;
                }
                listDiv.innerHTML = data.memories.map(m => `
                    <div class="mem-item">
                        <span><b>${m.key}</b>: ${m.value}</span>
                        <button class="btn-del" onclick="deleteMemory('${m.key}')">X</button>
                    </div>
                `).join('');
            } catch (err) { console.error("Gagal muat memori"); }
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

        async function loadNotes() {
            try {
                const res = await fetch(`${BACKEND_URL}/notes`);
                const data = await res.json();
                const listDiv = document.getElementById('notesList');
                if (data.notes.length === 0) {
                    listDiv.innerHTML = '<p style="color:#64748b; text-align:center; font-size:0.7rem;">Tiada nota.</p>';
                    return;
                }
                listDiv.innerHTML = data.notes.map(n => `
                    <div class="note-item">
                        <span><b>${n.title}</b>: ${n.content}</span>
                        <button class="btn-del" onclick="deleteNote(${n.id})">X</button>
                    </div>
                `).join('');
            } catch (err) { console.error("Gagal muat nota"); }
        }

        async function saveNote() {
            const title = document.getElementById('noteTitle').value;
            const content = document.getElementById('noteContent').value;
            if (!title || !content) return alert("Sila isi tajuk dan kandungan nota.");

            await fetch(`${BACKEND_URL}/add_note`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content })
            });
            document.getElementById('noteTitle').value = '';
            document.getElementById('noteContent').value = '';
            logTerm(`Mission note saved: ${title}`);
            loadNotes();
        }

        async function deleteNote(id) {
            await fetch(`${BACKEND_URL}/delete_note`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            logTerm("Mission note deleted.");
            loadNotes();
        }

        async function loadReminders() {
            try {
                const res = await fetch(`${BACKEND_URL}/reminders`);
                const data = await res.json();
                const listDiv = document.getElementById('remindersList');
                if (data.reminders.length === 0) {
                    listDiv.innerHTML = '<p style="color:#64748b; text-align:center; font-size:0.7rem;">Tiada peringatan.</p>';
                    return;
                }
                listDiv.innerHTML = data.reminders.map(r => `
                    <div class="rem-item">
                        <span><b>${r.task}</b> (${r.time_str})</span>
                        <button class="btn-del" onclick="deleteReminder(${r.id})">X</button>
                    </div>
                `).join('');
            } catch (err) { console.error("Gagal muat reminders"); }
        }

        async function saveReminder() {
            const task = document.getElementById('remTask').value;
            const time_str = document.getElementById('remTime').value;
            if (!task || !time_str) return alert("Sila isi tugasan dan masa.");

            await fetch(`${BACKEND_URL}/add_reminder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task, time_str })
            });
            document.getElementById('remTask').value = '';
            document.getElementById('remTime').value = '';
            logTerm(`Reminder set: ${task}`);
            loadReminders();
        }

        async function deleteReminder(id) {
            await fetch(`${BACKEND_URL}/delete_reminder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            logTerm("Reminder deleted.");
            loadReminders();
        }

        async function sendChat() {
            const prompt = document.getElementById('userInput').value;
            const persona = document.getElementById('personaSelect').value;
            if (!prompt) return;

            const chatbox = document.getElementById('chatbox');
            chatbox.innerHTML += `<p class="user-msg"><b>Anda:</b> ${prompt}</p>`;
            document.getElementById('userInput').value = '';
            chatbox.scrollTop = chatbox.scrollHeight;

            setVisualizer(true);
            logTerm(`Transmitting prompt (Persona: ${persona})...`);

            try {
                const res = await fetch(`${BACKEND_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt, persona: persona })
                });
                const data = await res.json();
                chatbox.innerHTML += `<p class="jarvis-msg"><b>JARVIS:</b> ${data.reply}</p>`;
                chatbox.scrollTop = chatbox.scrollHeight;
                setVisualizer(false);
                logTerm("Response received.");
                loadMemories(); 
                speak(data.reply);
            } catch (err) {
                setVisualizer(false);
                chatbox.innerHTML += `<p style="color:red">Ralat rangkaian.</p>`;
                logTerm("Error: Transmission failed.");
            }
        }
    </script>
</body>
</html>
"""

# ---------------------------------------------------------
# ENDPOINTS BACKEND (TAMBAHAN REMINDERS)
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
        return {"memories": [{"key": r[0], "value": r[1]} for r in rows]}
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

@app.get("/notes")
def get_notes_api(user_id: str = "default_user"):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content FROM notes WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return {"notes": [{"id": r[0], "title": r[1], "content": r[2]} for r in rows]}
    except Exception:
        return {"notes": []}

@app.post("/add_note")
def add_note_api(req: NoteRequest):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)", (req.user_id, req.title, req.content))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class NoteDeleteRequest(BaseModel):
    id: int

@app.post("/delete_note")
def delete_note_api(req: NoteDeleteRequest):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (req.id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/reminders")
def get_reminders_api(user_id: str = "default_user"):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, task, time_str FROM reminders WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return {"reminders": [{"id": r[0], "task": r[1], "time_str": r[2]} for r in rows]}
    except Exception:
        return {"reminders": []}

@app.post("/add_reminder")
def add_reminder_api(req: ReminderRequest):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (user_id, task, time_str) VALUES (?, ?, ?)", (req.user_id, req.task, req.time_str))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/delete_reminder")
def delete_reminder_api(req: NoteDeleteRequest):
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (req.id,))
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
        
        persona_instructions = {
            "standard": "Kau ialah JARVIS, pembantu AI peribadi gaya sains fiksyen yang bijak, ringkas, dan setia.",
            "stark": "Kau ialah JARVIS dalam mod Tony Stark. Gaya bahasa kau sedikit 'sarcastic', bersahaja, santai, bijak, tetapi tetap membantu.",
            "it_expert": "Kau ialah JARVIS dalam mod Pakar IT & Kejuruteraan. Fokus pada istilah teknikal, struktur data, pengaturcaraan, dan analisis mendalam."
        }
        
        base_persona = persona_instructions.get(request.persona, persona_instructions["standard"])
        
        system_prompt = f"""{base_persona}
Memori sedia ada pengguna ({request.user_id}):
{current_memories}

ARAHAN KHAS:
Jika pengguna memaklumkan maklumat peribadi (cth: nama, hobi, minat), balas seperti biasa dan sertakan kod ini di hujung mesej secara senyap:
[SAVE:key=value]
Contoh: Baik Tuan.[SAVE:nama=adhwa]
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
