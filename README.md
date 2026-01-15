

## Features

- **AI-Powered Interviewer**: Conducts realistic interviews using LM Studio (local LLM) with automatic fallback to Google Gemini
- **Voice Interaction**: Natural conversation with automatic speech recognition (STT) and text-to-speech (TTS)
- **Google Meet-Style UI**: Professional interface with main stage, floating webcam preview, and transcript panel
- **Privacy First**: Webcam video stays local-only, only text transcripts are sent to the backend
- **Real-Time Communication**: WebSocket-based real-time interaction
- **Auto Silence Detection**: Automatically detects when user stops speaking
- **Interview Feedback**: Get comprehensive feedback and score at the end

## Architecture

### Tech Stack

**Frontend:**
- React 18 with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- Zustand for state management
- Web Speech API for STT/TTS
- WebRTC getUserMedia for local webcam preview

**Backend:**
- Python FastAPI
- WebSocket server
- LM Studio integration (local LLM via OpenAI-compatible API)
- Google Gemini API integration (fallback)
- Unified AI service with automatic fallback
- Interview state machine

### System Flow

```
User Starts Interview
    ↓
WebSocket Connection
    ↓
AI Greeting (TTS)
    ↓
User Speaks → Silence Detected
    ↓
Speech to Text
    ↓
Send Transcript to Backend
    ↓
AI Service Processes Answer (LM Studio or Gemini)
    ↓
Next Question (TTS)
    ↓
[Loop continues...]
    ↓
Final Feedback & Score
```

## Project Structure

```
new mockinterview/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app & WebSocket server
│   │   ├── websocket_manager.py # WebSocket connection management
│   │   ├── interview_state.py   # State machine logic
│   │   ├── ai_service.py         # Unified AI service with fallback
│   │   ├── lm_studio_service.py  # LM Studio API integration
│   │   ├── gemini_service.py    # Gemini API integration (fallback)
│   │   └── models.py            # Pydantic models
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── store/               # Zustand store
│   │   ├── types/               # TypeScript types
│   │   └── utils/               # Utility functions
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn
- **LM Studio** (recommended): Download from [lmstudio.ai](https://lmstudio.ai/) and start a local server
- **Google Gemini API key** (for fallback): [Get one here](https://makersuite.google.com/app/apikey)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```

5. Edit `.env` and configure your AI services:
```
# LM Studio Configuration (Primary - Local LLM)
LM_STUDIO_BASE_URL=http://localhost:1234
USE_LM_STUDIO=true

# Gemini Configuration (Fallback)
GEMINI_API_KEY=your_gemini_api_key_here

# Server Configuration
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Note:** The system will try LM Studio first (if running), then automatically fall back to Gemini if LM Studio is unavailable. You can disable LM Studio by setting `USE_LM_STUDIO=false`.

6. Run the backend server:
```bash
python -m app.main
# Or using uvicorn directly:
uvicorn app.main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file:
```bash
cp .env.example .env
```

4. Edit `.env` (usually defaults are fine):
```
VITE_WS_URL=ws://localhost:8000/ws
VITE_API_URL=http://localhost:8000
```

5. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

### Quick Start (Recommended)

Use the unified startup script to run both servers:

```bash
# Production mode: Build frontend and serve from backend (same port)
python start.py --unified
# Access at: http://localhost:8000

# Development mode: Start both backend and frontend separately
python start.py

# Or with build first
python start.py --build

# Start only backend
python start.py --backend-only

# Start only frontend
python start.py --frontend-only

# Build frontend only
python start.py --build-only
```

**Unified Mode (Recommended for Production):**
- Builds the frontend automatically
- Serves frontend from backend on port 8000
- Everything runs on the same port
- No need to run separate frontend server

### Manual Start

1. **Start LM Studio** (if using local LLM):
   - Open LM Studio
   - Load a model
   - Start the local server (usually runs on port 1234)
   - The backend will automatically detect and use it

2. **Start the backend server** (see Backend Setup above)

3. **Start the frontend server** (see Frontend Setup above)

4. **Open your browser** and navigate to `http://localhost:5173`

5. **Click "Start Interview"** to begin

5. **Allow microphone and camera permissions** when prompted

6. **The AI interviewer will:**
   - Greet you with a welcome message
   - Ask interview questions one at a time
   - Wait for your response
   - Automatically detect when you stop speaking
   - Ask follow-up questions based on your answers

6. **At the end**, you'll receive:
   - A comprehensive feedback summary
   - An interview score (out of 100)
   - Areas of strength and improvement

## Privacy & Security

- **Webcam Video**: Displayed locally only, never transmitted or stored
- **Audio**: Only text transcripts are sent to the backend, no audio files are saved
- **Data**: Interview transcripts are processed by LM Studio (local) or Gemini API but not permanently stored by the application
- **WebSocket**: All communication is real-time, no persistent storage

## Interview State Machine

The system uses a finite state machine to manage interview flow:

- `AI_ASKING` → Initial state
- `AI_SPEAKING` → AI is speaking the question
- `WAITING_FOR_USER` → Waiting for user to start speaking
- `USER_SPEAKING` → User is speaking
- `SILENCE_DETECTED` → User stopped speaking
- `PROCESSING_WITH_GEMINI` → Backend processing the answer (using LM Studio or Gemini)
- `NEXT_QUESTION` → Ready for next question
- `INTERVIEW_ENDED` → Interview complete

## Voice Interaction

### Text-to-Speech (TTS)
- Uses browser's `SpeechSynthesis` API
- Automatically speaks AI questions
- Waits for completion before starting microphone

### Speech-to-Text (STT)
- Uses browser's `SpeechRecognition` API (webkitSpeechRecognition)
- Automatically starts after AI finishes speaking
- Detects silence (2.5 second timeout)
- Extracts final transcript and sends to backend

## Browser Compatibility

- **Chrome/Edge**: Full support (recommended)
- **Firefox**: Limited Speech Recognition support
- **Safari**: Limited Speech Recognition support

For best experience, use Chrome or Edge.

## Troubleshooting

### Microphone not working
- Check browser permissions
- Ensure microphone is not muted
- Try refreshing the page

### WebSocket connection issues
- Verify backend is running on port 8000
- Check CORS settings in backend `.env`
- Check browser console for errors

### Speech recognition not starting
- Ensure you're using Chrome or Edge
- Check microphone permissions
- Try refreshing the page

### AI Service errors

**LM Studio issues:**
- Ensure LM Studio is running and server is started
- Check that LM Studio is listening on port 1234 (or your configured port)
- Verify a model is loaded in LM Studio
- Check backend logs for connection errors

**Gemini API errors (fallback):**
- Verify your API key is correct in backend `.env`
- Check API quota/limits
- Review backend logs for detailed error messages

**Service fallback:**
- If LM Studio is unavailable, the system automatically falls back to Gemini
- Check backend logs to see which service is being used
- You can disable LM Studio by setting `USE_LM_STUDIO=false` in `.env`

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
```

**Backend:**
The backend can be deployed using any ASGI server (uvicorn, gunicorn, etc.)

## Environment Variables

### Backend (.env)
- `LM_STUDIO_BASE_URL`: LM Studio API base URL (default: http://localhost:1234)
- `LM_STUDIO_MODEL`: Explicit model name (optional, auto-detected if not set)
- `USE_LM_STUDIO`: Prefer LM Studio over Gemini (default: true)
- `GEMINI_API_KEY`: Your Google Gemini API key (required for fallback)
- `PORT`: Backend server port (default: 8000)
- `CORS_ORIGINS`: Comma-separated list of allowed origins

### Frontend (.env)
- `VITE_WS_URL`: WebSocket URL (default: ws://localhost:8000/ws)
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

## License

This project is provided as-is for educational and development purposes.

## Contributing

This is a production-ready implementation. Feel free to extend and customize for your needs.

## Support

For issues or questions, please check:
1. Browser console for frontend errors
2. Backend logs for server errors
3. Network tab for WebSocket connection issues

---

Built with ❤️ using React, FastAPI, LM Studio, and Google Gemini
# new-mockinterview
