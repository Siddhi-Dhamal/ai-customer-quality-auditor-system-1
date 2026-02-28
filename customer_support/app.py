import os
import shutil
import gc
import csv
import pandas as pd
from datetime import datetime
from groq import Groq
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel

# ---------------- CONFIG ----------------
TRANSCRIPT_FILE = "transcriptions_with_speakers.csv"
SUMMARY_FILE = "final_summaries.csv"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # <-- Add your key

# ----------------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=GROQ_API_KEY)

# Whisper Model (No diarization)
whisper_model = WhisperModel(
    "small", 
    device="cpu", 
    compute_type="int8"
)

# ---------------- AI ROLE + SUMMARY ----------------

def final_ai_processor(raw_lines):

    # Add line numbers so LLM understands conversation flow
    formatted_text = "\n".join(
        [f"Line {i}: {line}" for i, line in enumerate(raw_lines)]
    )

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are analyzing a customer support call transcript.\n"
                    "1. Identify who is the Agent and who is the Customer.\n"
                    "2. Label each line properly.\n"
                    "3. Do NOT alternate automatically.\n"
                    "4. Agent is the person answering the phone and helping.\n\n"
                    "Return strictly in this format:\n"
                    "Speaker 00 (Agent): text\n"
                    "Speaker 01 (Customer): text\n"
                    "...\n"
                    "SUMMARY: One sentence summary."
                ),
            },
            {"role": "user", "content": formatted_text},
        ],
        temperature=0.1,
    )

    response = completion.choices[0].message.content.strip()

    lines = response.split("\n")
    transcript_data = []
    summary = "No summary generated."

    for line in lines:
        if line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
        elif ":" in line:
            label, text = line.split(":", 1)
            transcript_data.append(
                {"speaker": label.strip(), "text": text.strip()}
            )

    return summary, transcript_data


# ---------------- API ----------------

@app.post("/upload")
async def process_upload(file: UploadFile = File(...)):

    temp_file = f"temp_{file.filename}"

    try:
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1️⃣ Transcription (No diarization)
        segments, _ = whisper_model.transcribe(
            temp_file,
            beam_size=5,
            word_timestamps=True
        )

        raw_lines = [seg.text.strip() for seg in segments if seg.text.strip()]

        # 2️⃣ AI Role Detection + Summary
        final_summary, refined_data = final_ai_processor(raw_lines)

        # 3️⃣ Save Transcript CSV
        pd.DataFrame(refined_data).to_csv(TRANSCRIPT_FILE, index=False)

        # 4️⃣ Save Summary History
        file_exists = os.path.isfile(SUMMARY_FILE)

        with open(SUMMARY_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["file_name", "timestamp", "summary"],
                quoting=csv.QUOTE_ALL,
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "file_name": file.filename,
                    "timestamp": datetime.now().strftime("%I:%M %p"),
                    "summary": final_summary,
                }
            )

        return {"status": "success", "summary": final_summary}

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        gc.collect()


@app.get("/get-transcript")
async def get_transcript():
    if not os.path.exists(TRANSCRIPT_FILE):
        return []
    return pd.read_csv(TRANSCRIPT_FILE).to_dict(orient="records")


@app.get("/get-summary")
async def get_summary():
    if not os.path.exists(SUMMARY_FILE):
        raise HTTPException(status_code=404, detail="Summary not found")

    df = pd.read_csv(SUMMARY_FILE, quoting=csv.QUOTE_ALL)

    if df.empty:
        return {"summary": "No data."}

    return {"summary": df["summary"].iloc[-1]}


@app.get("/history")
async def get_history():
    if not os.path.exists(SUMMARY_FILE):
        return []

    df = pd.read_csv(SUMMARY_FILE, quoting=csv.QUOTE_ALL)
    return df.tail(10).iloc[::-1].to_dict(orient="records")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)