# 🎤 YAPBATTLE

**Say it. Defend it.**

YAPBATTLE is a real-time voice debate application where you battle against AI opponents in different game modes. Built for the UCSB Hackathon using Deepgram voice AI and Claude API.

## 🎮 Game Modes

### 🔥 Hot Takes
- **Fast & chaotic** 90-second debates
- AI has **zero filter** - expect wild, conspiracy-level arguments
- Perfect for quick, entertaining battles

### 🏆 Ranked Mode
- **Competitive gameplay** with ELO ranking system
- Choose difficulty: Easy, Medium, or Hard
- Climb through Bronze, Silver, and Gold ranks
- Earn ELO based on debate performance

### 🎙️ Podcast Mode
- **Chill, thoughtful conversations**
- Explore hypothetical scenarios and deep questions
- No pressure, just curiosity
- Longer 5-minute sessions

## 🚀 Features

- **Real-time voice recognition** using Deepgram Flux
- **AI-powered opponent** with Claude 3 Haiku
- **Live scoring** on clarity, logic, and persuasion
- **ELO ranking system** for competitive play
- **Multiple AI personalities** based on game mode
- **Responsive web UI** with cyberpunk aesthetics

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Voice AI**: Deepgram (STT/TTS)
- **LLM**: Anthropic Claude 3 Haiku
- **Frontend**: Vanilla JS, HTML5, CSS3
- **Real-time Communication**: WebSockets

## 📦 Installation

1. **Clone the repository**
```bash
git clone https://github.com/CadenMinami/sbHacks.git
cd sbHacks
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

**Option A: Using .env file (Recommended)**
```bash
# Copy the example file
cp env.example .env

# Edit .env and add your API keys
# ANTHROPIC_API_KEY=your_actual_key_here
# DEEPGRAM_API_KEY=your_actual_key_here
```

**Option B: Export environment variables**
```bash
export ANTHROPIC_API_KEY='your-anthropic-key'
export DEEPGRAM_API_KEY='your-deepgram-key'
```

**Get API Keys:**
- Anthropic: https://console.anthropic.com/
- Deepgram: https://console.deepgram.com/

4. **Run the application**
```bash
# If you used .env file:
python3 app.py

# If you exported variables, use the startup script:
./run.sh
```

5. **Open in browser**
Navigate to `http://localhost:5001`

## 🎯 How to Play

1. **Select a game mode** from the home screen
2. **Choose difficulty** (Ranked only)
3. **Click the diamond mic button** to start speaking
4. **Make your argument** clearly and confidently
5. **Listen to AI's rebuttal** and counter it
6. **Watch your scores** update in real-time
7. **Win or lose** and earn/lose ELO (Ranked mode)

## 🏗️ Project Structure

```
ranked-debate/
├── app.py                 # Flask server & API routes
├── debate_engine.py       # AI debate logic & scoring
├── prompts_config.py      # AI prompts for each mode
├── user_data.py          # User stats & ELO system
├── voice_handler_simple.py # Deepgram voice integration
├── static/
│   └── debate_voice.js   # Frontend voice handling
├── templates/
│   ├── index.html        # Home screen
│   ├── game.html         # Ranked difficulty selection
│   ├── hot_takes.html    # Hot Takes landing page
│   ├── podcast.html      # Podcast landing page
│   ├── debate.html       # Live debate interface
│   └── stats.html        # User statistics page
└── requirements.txt      # Python dependencies
```

## 🎨 Design Philosophy

- **Cyberpunk aesthetic** with glassmorphism
- **Game-like UI** to make debating feel competitive
- **Real-time feedback** for immediate engagement
- **Accessibility-first** voice interaction

## 📊 Scoring System

Debates are scored on:
- **Clarity** (1-10): How clear and understandable your arguments are
- **Logic** (1-10): Strength of reasoning and evidence
- **Persuasion** (1-10): How convincing you are
- **Overall** (1-10): Weighted average of all metrics

## 🏅 Ranking System

- **Bronze**: 0-99 ELO
- **Silver**: 100-199 ELO
- **Gold**: 200+ ELO

ELO gain/loss depends on:
- Your debate score
- Difficulty level (harder = more ELO)
- Win/loss threshold (6.0+ = win)

## ⚠️ Important Notes

- Microphone access required
- Works best in Chrome/Edge browsers
- Requires stable internet connection
- API keys needed for Deepgram and Anthropic

## 🔒 Security

- Never commit `.env` files
- API keys are stored in environment variables only
- User data stored locally in `user_data.json`

## 📝 License

This project was created for the UCSB Hackathon.

## 🙏 Acknowledgments

- **Deepgram** for voice AI capabilities
- **Anthropic** for Claude API
- **UCSB Hackathon** for the opportunity

---

**Built with 🎤 by [Your Name]**
