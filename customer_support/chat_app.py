import os
import shutil
import gc
import csv
import pandas as pd
from datetime import datetime
from groq import Groq
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ---------------- CONFIG ----------------

TRANSCRIPT_FILE = "text_transcript.csv"
SUMMARY_FILE = "text_summaries.csv"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # <-- Add your key

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=GROQ_API_KEY)

analysis_history = []


# ---------------- AI SUMMARY ----------------

def generate_ai_summary(text):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional call analyst. "
                        "Provide ONLY a short final conclusion in 1-2 sentences. "
                        "No bullet points. No formatting."
                    )
                },
                {
                    "role": "user",
                    "content": f"Transcript:\n{text[:4000]}"
                }
            ],
            temperature=0.2,
            max_tokens=120
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        print("Groq Error:", e)
        return "Summary unavailable due to API limits."


# ---------------- UPLOAD TEXT ----------------

@app.post("/upload-text")
async def upload_text(file: UploadFile = File(...)):

    temp_file = f"temp_{file.filename}"

    try:
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        formatted_data = []
        full_text = ""
        speaker_map = {}

        with open(temp_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            if ":" in line:
                raw_speaker, text_content = line.split(":", 1)
                raw_speaker = raw_speaker.strip()
                text_content = text_content.strip()

                if raw_speaker not in speaker_map:
                    speaker_map[raw_speaker] = f"SPEAKER_{len(speaker_map):02d}"

                speaker_id = speaker_map[raw_speaker]

                formatted_data.append({
                    "speaker": speaker_id,
                    "text": text_content,
                    "start": i,
                    "end": i + 1
                })

                full_text += " " + text_content
            else:
                formatted_data.append({
                    "speaker": "UNKNOWN",
                    "text": line,
                    "start": i,
                    "end": i + 1
                })
                full_text += " " + line

        # Save transcript
        pd.DataFrame(formatted_data).to_csv(TRANSCRIPT_FILE, index=False)

        # Generate summary
        summary_text = generate_ai_summary(full_text)

        # Save summary properly (WITH TIMESTAMP)
        file_exists = os.path.isfile(SUMMARY_FILE)

        with open(SUMMARY_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["file_name", "timestamp", "summary"]
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                "file_name": file.filename,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "summary": summary_text
            })

        # Update history
        analysis_history.insert(0, {
            "id": len(analysis_history) + 1,
            "file_name": file.filename,
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "status": "Ready"
        })

        return {"status": "success", "summary": summary_text}

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        gc.collect()


# ---------------- GET TRANSCRIPT ----------------

@app.get("/get-text-transcript")
async def get_text_transcript():
    if not os.path.exists(TRANSCRIPT_FILE):
        return []
    return pd.read_csv(TRANSCRIPT_FILE).to_dict(orient="records")


# ---------------- GET SUMMARY ----------------

@app.get("/get-text-summary")
async def get_text_summary():

    if not os.path.exists(SUMMARY_FILE):
        return {"summary": "No summary available."}

    try:
        df = pd.read_csv(SUMMARY_FILE)

        if df.empty:
            return {"summary": "No summary available."}

        latest_summary = df.iloc[-1]["summary"]

        # Prevent NaN crash
        if pd.isna(latest_summary):
            latest_summary = "Summary unavailable."

        return JSONResponse(content={"summary": str(latest_summary)})

    except Exception as e:
        print("Summary Fetch Error:", e)
        return JSONResponse(
            status_code=500,
            content={"summary": "Error fetching summary."}
        )


# ---------------- HISTORY ----------------

@app.get("/history")
async def get_history():
    return analysis_history


# ---------------- RUN ----------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)