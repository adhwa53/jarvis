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
# UI HTML EMBEDDED DIRECT
# ---------------------------------------------------------
HTML_CODE = """
<!DOCTYPE html>
<html lang="ms">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS AI Control</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; max-width: 650px; margin: auto; }
        .card { background: #1e293b; padding: 20px; margin-bottom: 20px; border-radius: 12px; border: 1px solid #334155; }
        h2, h3 { color: #38bdf8; margin-top: 0; }
        button { background: #0284c7; color: white; border: none; padding: 10px 16px; cursor: pointer; border-radius: 6px; font-weight: bold; margin-right: 5px; }
        button:hover { background: #0369a1; }
        input[type="text"], input[type="file"] { width: 100%; padding: 10px; margin: 8px 0; background: #0f172a; color: #f8fafc; border: 1px solid #475569; border-radius: 6px; box-sizing: border-box; }
        #chatbox { height: 220px; overflow-y: auto; background: #090d16; padding: 12px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 12px; }
        .user-msg { color: #38bdf8; margin: 4px 0; }
        .jarvis-msg { color: #4ade80; margin: 4px 0; }
    </style>
</head>
<body>
    <h2>🤖 JARVIS Dashboard</h2>

    <div class="card">
        <h3>1. Sembang & Suara</h3>
        <div id="chatbox"></div>
        <input type="text" id="userInput" placeholder="Tulis mesej atau cakap...">
        <button onclick="sendChat()">Hantar</button>
        <button onclick="startVoice()">🎙️ Suara</button>
    </div>

    <div class="card">
        <h3>2. Vision (Analisis Gambar)</h3>
        <input type="file" id="imageInput" accept="image/*">
        <input type="text" id="imagePrompt" placeholder="Tanya sesuatu tentang gambar ni...">
        <button onclick="sendVision()">Hantar Gambar</button>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;

        function startVoice() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) return alert("Pelayar anda tak menyokong rekod suara.");
            
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
                chatbox.innerHTML += `<p style="color:red">Ralat sambungan ke server.</p>`;
            }
        }

        async function sendVision() {
            const fileInput = document.getElementById('imageInput');
            const prompt = document.getElementById('imagePrompt').value || "Apa yang ada dalam gambar ni?";
            
            if (fileInput.files.length === 0) return alert("Sila pilih gambar dahulu.");

            const formData = new FormData();
            formData.append("file", fileInput.files[0]);
            formData.append("prompt", prompt);

            const chatbox = document.getElementById('chatbox');
            chatbox.innerHTML += `<p class="user-msg"><i>[Memproses gambar...]</i></p>`;

            try {
                const res = await fetch(`${BACKEND_URL}/vision`, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                chatbox.innerHTML += `<p class="jarvis-msg"><b>JARVIS (Vision):</b> ${data.reply}</p>`;
                chatbox.scrollTop = chatbox.scrollHeight;
                speak(data.reply);
            } catch (err) {
                chatbox.innerHTML += `<p style="color:red">Ralat memproses gambar.</p>`;
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
