import os
import json
import time
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # <-- Add your key
TRANSCRIPT_FILE = "transcriptions_with_speakers.csv"
SCORES_FILE = "quality_scores.json"

app = FastAPI()

# Enable CORS for your React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=GROQ_API_KEY)

@app.post("/analyze-quality")
async def analyze_quality(file: UploadFile = File(...)):
    try:
        file_name = file.filename.lower()
        file_ext = file_name.split(".")[-1]
        conversation_text = ""

        # --- STEP 1: ROUTING LOGIC ---
        
        # IF TEXT/CHAT FILE: Read directly from the upload
        if file_ext in ["txt", "csv"]:
            print(f"DEBUG: Processing Chat/Text file: {file_name}")
            content = await file.read()
            try:
                conversation_text = content.decode("utf-8")
            except:
                conversation_text = content.decode("latin-1")
            
            if not conversation_text.strip():
                raise Exception("The uploaded text file is empty.")

        # IF AUDIO FILE: Wait for app.py to finish transcription
        else:
            print(f"DEBUG: Processing Audio. Waiting for transcript sync...")
            # We wait 6 seconds to ensure app.py (Port 8000) has overwritten the CSV
            time.sleep(6) 
            
            if os.path.exists(TRANSCRIPT_FILE):
                df = pd.read_csv(TRANSCRIPT_FILE)
                # Join all transcribed rows into one block of text
                conversation_text = " ".join(df['text'].astype(str).tolist())
            else:
                raise Exception("Transcript file not found. Ensure app.py is running.")

        # --- STEP 2: GROQ LLAMA 3 ANALYSIS ---
        
        prompt = f"""
        Act as a Professional Call Quality Auditor. 
        Analyze the following conversation strictly based on the text provided.
        
        CONVERSATION TEXT:
        {conversation_text}

        Evaluate and provide integer scores (1-10) for:
        1. Empathy: Did the agent show concern and politeness?
        2. Compliance: Did the agent follow security/business protocols?
        3. Resolution: Was the customer's issue addressed?

        Return ONLY a JSON object with this structure:
        {{
            "empathy": number,
            "compliance": number,
            "resolution": number,
            "reasoning": "A concise explanation of why these scores were given based ONLY on the provided text."
        }}
        """

        # Using the versatile Llama 3.3 70B model for high accuracy
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"} # Forces JSON output
        )

        result_json = json.loads(chat_completion.choices[0].message.content)
        
        # --- STEP 3: SAVE RESULTS ---
        with open(SCORES_FILE, "w") as f:
            json.dump(result_json, f, indent=4)

        print(f"SUCCESS: Scores generated for {file_name}")
        return result_json

    except Exception as e:
        print(f"ERROR: {str(e)}")
        error_data = {
            "empathy": 0,
            "compliance": 0,
            "resolution": 0,
            "reasoning": f"Analysis failed: {str(e)}"
        }
        with open(SCORES_FILE, "w") as f:
            json.dump(error_data, f, indent=4)
        return error_data

@app.get("/get-quality-scores")
async def get_scores():
    """Endpoint for RightSidebar to fetch the latest scores"""
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    return {
        "empathy": 0, 
        "compliance": 0, 
        "resolution": 0, 
        "reasoning": "No analysis data found. Please upload a file."
    }

if __name__ == "__main__":
    import uvicorn
    # Running on Port 8002 to avoid conflict with Audio (8000) and Text (8001)
    uvicorn.run(app, host="0.0.0.0", port=8002)