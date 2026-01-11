# Virtual AI Interview Room

A production-ready web application that simulates a real virtual interview room similar to Google Meet/Google Classroom with an AI interviewer powered by Google Gemini.

## Features

- **AI-Powered Interviewer**: Conducts realistic interviews using Google Gemini API
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
- Google Gemini API integration
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
Gemini Processes Answer
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
│   │   ├── gemini_service.py    # Gemini API integration
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
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

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

5. Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

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

1. **Start the backend server** (see Backend Setup above)

2. **Start the frontend server** (see Frontend Setup above)

3. **Open your browser** and navigate to `http://localhost:5173`

4. **Click "Start Interview"** to begin

5. **Allow microphone and camera permissions** when prompted

6. **The AI interviewer will:**
   - Greet you with a welcome message
   - Ask interview questions one at a time
   - Wait for your response
   - Automatically detect when you stop speaking
   - Ask follow-up questions based on your answers

7. **At the end**, you'll receive:
   - A comprehensive feedback summary
   - An interview score (out of 100)
   - Areas of strength and improvement

## Privacy & Security

- **Webcam Video**: Displayed locally only, never transmitted or stored
- **Audio**: Only text transcripts are sent to the backend, no audio files are saved
- **Data**: Interview transcripts are processed by Gemini API but not permanently stored by the application
- **WebSocket**: All communication is real-time, no persistent storage

## Interview State Machine

The system uses a finite state machine to manage interview flow:

- `AI_ASKING` → Initial state
- `AI_SPEAKING` → AI is speaking the question
- `WAITING_FOR_USER` → Waiting for user to start speaking
- `USER_SPEAKING` → User is speaking
- `SILENCE_DETECTED` → User stopped speaking
- `PROCESSING_WITH_GEMINI` → Backend processing the answer
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

### Gemini API errors
- Verify your API key is correct in backend `.env`
- Check API quota/limits
- Review backend logs for detailed error messages

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
- `GEMINI_API_KEY`: Your Google Gemini API key (required)
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

Built with ❤️ using React, FastAPI, and Google Gemini
# new-mockinterview
