import os
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

class ChatInput(BaseModel):
    prompt: str

@app.get("/")
def home():
    return {"status": "JARVIS Online"}

@app.post("/chat")
def chat(data: ChatInput):

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Anda ialah JARVIS."
            },
            {
                "role": "user",
                "content": data.prompt
            }
        ],
        model="llama3-8b-8192",
    )
    jawapan = chat_completion.choices[0].message.content
    return {"reply": jawapan}
