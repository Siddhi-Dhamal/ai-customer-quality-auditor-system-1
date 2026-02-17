import os
import time
from huggingface_hub import InferenceClient
from dotenv import load_dotenv  # <--- Add this

# Load variables from the .env file
load_dotenv()

# ===== CONFIGURATION =====
# 1. Fetch your API token from the environment variable
HF_TOKEN = os.getenv("HF_TOKEN") 

# Check if token exists to avoid errors later
if not HF_TOKEN:
    raise ValueError("❌ Error: HF_TOKEN not found. Check your .env file.")

# 2. Settings for your files
INPUT_FILE = "human_chat.txt"
OUTPUT_FILE = "chat_summary.txt"

# Initialize the official Hugging Face Client
client = InferenceClient(api_key=HF_TOKEN)

# ... (the rest of your code remains the same)

def process_chat_summary():
    # Check if the input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Could not find '{INPUT_FILE}'. Please check the filename.")
        return

    print(f"📖 Reading '{INPUT_FILE}'...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        chat_content = f.read().strip()

    if not chat_content:
        print("⚠️ The chat file is empty.")
        return

    print("🤖 Sending to AI for summarization...")
    try:
        # Using the Router with a highly capable model
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional assistant. Summarize the following chat log in exactly one meaningful sentence. Focus on the main topic and the final conclusion or decision."
                },
                {"role": "user", "content": chat_content}
            ],
            max_tokens=150,
            temperature=0.1
        )
        
        summary_result = response.choices[0].message.content.strip()

        # 3. SAVE THE OUTPUT
        with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
            out_f.write("--- CHAT SUMMARY REPORT ---\n")
            out_f.write(f"Source File: {INPUT_FILE}\n")
            out_f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            out_f.write("---------------------------\n\n")
            out_f.write(summary_result)
            out_f.write("\n\n--- END OF REPORT ---")

        print(f"✅ Success! Summary saved to: {OUTPUT_FILE}")
        print(f"Summary Preview: {summary_result}")

    except Exception as e:
        # Handle "Model Loading" or "Busy" states automatically
        if "503" in str(e) or "429" in str(e):
            print("⏳ Model is busy or loading. Retrying in 15 seconds...")
            time.sleep(15)
            process_chat_summary()
        else:
            print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    process_chat_summary()