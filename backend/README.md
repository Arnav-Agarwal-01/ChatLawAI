# LawMate AI Backend - Fixed Version

## 🔧 The Problem That Was Fixed

Your backend was stuck in a loop, asking the same question over and over:
- **Root cause**: No tracking of which questions had been asked
- **Symptom**: Always returned "When did the incident occur?" regardless of how many times you answered

## ✅ The Solution

Created `app_fixed.py` with:
1. **Session-level tracking** of asked questions
2. **Smart question generator** that skips already-asked questions
3. **Proper state management** between turns

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
cd backend
./run.sh
```

This will:
- Create a Python virtual environment
- Install all required packages (takes 5-10 minutes)
- Download models and datasets automatically
- Start the server on http://localhost:8000

### Step 2: Test the Backend
In another terminal:
```bash
cd backend
source venv/bin/activate
python3 test_backend.py
```

This will verify the question progression is working correctly.

### Step 3: Start the Frontend
In the main project directory:
```bash
npm run dev
```

Then open http://localhost:5173 in your browser.

## 📁 Files

- **`app_fixed.py`** - Fixed backend with proper question tracking (USE THIS)
- **`app.py`** - Old version with the bug (for reference)
- **`run.sh`** - One-command startup script
- **`test_backend.py`** - Test script to verify the fix works
- **`requirements.txt`** - Python dependencies
- **`FIX_EXPLANATION.md`** - Detailed explanation of what was fixed

## 🔍 How It Works Now

1. **User asks**: "robbery happened"
2. **System asks**: "When did the incident occur?"
3. **User answers**: "3rd Nov"
4. **System asks**: "Where exactly did it happen?" ← Different question!
5. **User answers**: "Delhi"
6. **System asks**: "Was a weapon or threat used?" ← Another different question!
7. ... continues until max_turns or all questions asked

## 🧪 Testing

### Manual Test via cURL:
```bash
# Start consultation
curl -X POST http://localhost:8000/consult/start \
  -H "Content-Type: application/json" \
  -d '{"query": "robbery happened", "max_turns": 7}'

# Answer (use the session_id from above)
curl -X POST http://localhost:8000/consult/answer \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "answer": "3rd November"}'
```

### Automated Test:
```bash
python3 test_backend.py
```

## 💡 Key Code Changes

### Before (Bug):
```python
def _make_followup_question(self, kg, case_type, turns_done):
    ents = kg.entities
    if not ents.get('dates'):
        return "When did the incident occur?"  # ← Always returned this!
    # ... rest of the code never reached
```

### After (Fixed):
```python
def generate_next(self, case_type, kg, asked: List[str]):
    templates = self.QUESTION_TEMPLATES.get(subtype)
    for category, questions in templates.items():
        missing_questions = [q for q in questions if q not in asked]  # ← Check asked!
        if missing_questions:
            return missing_questions[0]
    return None
```

## ⚙️ Configuration

Edit `app_fixed.py` to customize:

```python
# Line 30-35: Choose different models
LLM_PREFERRED = [
    "soketlabs/pragna-1b",      # Lightweight legal model
    "google/flan-t5-large",     # Fallback
]

# Line 38: Enable/disable LLM
USE_LLM = True  # Set to False for faster startup (fallback mode)
```

## 📊 Models Used

1. **Embeddings**: `bhavyagiri/InLegal-Sbert` - Indian legal text embeddings
2. **NER**: `law-ai/InLegalBERT` - Named entity recognition for legal text
3. **LLM**: `soketlabs/pragna-1b` - Legal reasoning model
4. **Dataset**: Indian legal texts from HuggingFace

## 🐛 Troubleshooting

### "Module not found" errors
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Models fail to download
- Check your internet connection
- Models are downloaded to `~/.cache/huggingface/`
- Total download size: ~2-3 GB

### Backend crashes on startup
- Try setting `USE_LLM = False` in `app_fixed.py` for faster startup
- Check logs for specific errors
- Ensure you have at least 8GB RAM

### Questions still looping
- Make sure you're running `app_fixed.py`, not `app.py`
- Check the terminal logs to see if `asked_questions` is being tracked
- Run `python3 test_backend.py` to verify

## 🔄 Development

To restart the backend:
```bash
# Stop the current server (Ctrl+C)
# Then restart
./run.sh
```

To run in background:
```bash
nohup python3 app_fixed.py > backend.log 2>&1 &
```

## 📝 API Endpoints

### `POST /consult/start`
Start a new consultation session.

**Request:**
```json
{
  "query": "robbery happened",
  "max_turns": 7
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "next_action": "ask",
  "question": "When did the incident occur?",
  "partial_report": "Legal Report — Case type: CRIMINAL..."
}
```

### `POST /consult/answer`
Submit an answer to continue the consultation.

**Request:**
```json
{
  "session_id": "uuid-here",
  "answer": "3rd November"
}
```

**Response:**
```json
{
  "next_action": "ask",
  "question": "Where did this happen?",
  "partial_report": "Updated legal report..."
}
```

When all questions are answered:
```json
{
  "next_action": "final",
  "report": "Final detailed legal analysis...",
  "structured": {},
  "timestamp": "2025-11-14T12:00:00"
}
```

## 📞 Support

If you encounter issues:
1. Check `backend.log` for errors
2. Run `python3 test_backend.py` to verify the fix
3. Make sure both frontend and backend are running
4. Check that `http://localhost:8000` is accessible

## ✨ Credits

Based on the ChatLaw notebook with improvements for:
- Session management
- Question progression tracking
- FastAPI integration
- Production-ready error handling

