"""
YAPBATTLE Web Server
Flask application to serve the game UI and handle voice interactions
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from user_data import UserData
from debate_engine import DebateEngine
from voice_handler_simple import VoiceDebateHandler
import threading
import os
import random
import base64
import sys
import logging

from prompts_config import get_prompt, get_random_topic

# Configure logging to stderr
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global user data
user_data = UserData()

# Active debate sessions (in-memory for now)
debate_sessions = {}

# Active voice handlers  
voice_handlers = {}


@app.route('/')
def home():
    """Serve the home page"""
    return render_template('index.html')


@app.route('/api/user-stats')
def get_user_stats():
    """API endpoint to get user statistics"""
    return jsonify({
        'rank': user_data['rank'],
        'rank_icon': user_data.get_rank_icon(),
        'rank_color': user_data.get_rank_color(),
        'elo': user_data['elo'],
        'streak_days': user_data['streak_days'],
        'total_debates': user_data['total_debates'],
        'wins': user_data['wins'],
        'losses': user_data['losses'],
        'win_rate': user_data.get_win_rate(),
        'hot_takes_played': user_data['hot_takes_played'],
        'ranked_played': user_data['ranked_played'],
        'podcast_played': user_data['podcast_played']
    })


@app.route('/game/<mode>')
def game(mode):
    """Serve the game mode selection page"""
    if mode == 'ranked':
        return render_template('game.html', mode=mode)
    elif mode == 'hot_takes':
        return render_template('hot_takes.html')
    elif mode == 'podcast':
        return render_template('podcast.html')
    else:
        return render_template('game.html', mode=mode)


@app.route('/debate')
def debate():
    """Serve the debate page"""
    deepgram_key = os.environ.get('DEEPGRAM_API_KEY', '')
    return render_template('debate.html', deepgram_key=deepgram_key)


@app.route('/api/start-debate', methods=['POST'])
def start_debate():
    """Start a new debate session"""
    try:
        data = request.json
        mode = data.get('mode', 'ranked')
        difficulty = data.get('difficulty', 'medium')
        
        logger.info(f"🎯 Starting debate: mode={mode}, difficulty={difficulty}")
        
        # Get random topic based on mode
        topic = get_random_topic(mode)
        logger.info(f"📝 Topic selected: {topic}")
        
        # Create debate engine
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        if not anthropic_key:
            logger.error("❌ Missing Anthropic API key!")
            return jsonify({
                'success': False,
                'error': 'Anthropic API key not configured'
            }), 500
        
        session_id = f"{mode}_{difficulty}_{random.randint(1000, 9999)}"
        logger.info(f"🔑 Creating debate engine for session: {session_id}")
        
        engine = DebateEngine(anthropic_key, difficulty, topic, mode)
        logger.info(f"✅ Engine created, config: {engine.config.keys()}")
        
        debate_sessions[session_id] = {
            'engine': engine,
            'topic': topic,
            'mode': mode,
            'difficulty': difficulty
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'topic': topic,
            'difficulty': difficulty,
            'mode': mode,
            'config': engine.config
        })
    except Exception as e:
        error_msg = f"❌ Error starting debate: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full traceback:")
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/process-argument', methods=['POST'])
def process_argument():
    """Process user's argument and get AI response"""
    data = request.json
    session_id = data.get('session_id')
    user_text = data.get('text')
    
    print(f"🎤 Received argument from session {session_id}: {user_text[:50]}...")
    
    if session_id not in debate_sessions:
        print(f"❌ Invalid session: {session_id}")
        return jsonify({
            'success': False,
            'error': 'Invalid session'
        }), 400
    
    session = debate_sessions[session_id]
    engine = session['engine']
    
    try:
        print(f"🤖 Processing with Claude...")
        result = engine.process_user_argument(user_text)
        
        print(f"✅ Got result:")
        print(f"   AI Response: {result['ai_response'][:100]}...")
        print(f"   Scores: {result.get('scores')}")
        print(f"   Feedback: {result.get('feedback')}")
        
        return jsonify({
            'success': True,
            'ai_response': result['ai_response'],
            'scores': result.get('scores'),
            'feedback': result.get('feedback')
        })
    except Exception as e:
        print(f"❌ Error processing argument: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/get-scores/<session_id>')
def get_scores(session_id):
    """Get current debate scores"""
    if session_id not in debate_sessions:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400
    
    engine = debate_sessions[session_id]['engine']
    scores = engine.get_current_scores()
    
    return jsonify({
        'success': True,
        'scores': scores
    })


@app.route('/stats')
def stats():
    """Serve the stats page"""
    stats_data = {
        'username': user_data['username'],
        'rank': user_data['rank'],
        'rank_icon': user_data.get_rank_icon(),
        'rank_color': user_data.get_rank_color(),
        'elo': user_data['elo'],
        'streak_days': user_data['streak_days'],
        'best_streak': user_data['best_streak'],
        'total_debates': user_data['total_debates'],
        'wins': user_data['wins'],
        'losses': user_data['losses'],
        'win_rate': user_data.get_win_rate(),
        'average_score': user_data['average_score'],
        'ranked_played': user_data['ranked_played'],
        'hot_takes_played': user_data['hot_takes_played'],
        'podcast_played': user_data['podcast_played'],
        'rank_progress': user_data.get_rank_progress()
    }
    return render_template('stats.html', stats=stats_data)


# ============================================
# Voice Debate API Endpoints
# ============================================

@app.route('/api/voice/init', methods=['POST'])
def init_voice():
    """Initialize voice handler for a debate session"""
    data = request.json
    session_id = data.get('session_id')
    
    if session_id not in debate_sessions:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400
    
    session = debate_sessions[session_id]
    
    # Get API keys
    deepgram_key = os.environ.get('DEEPGRAM_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not deepgram_key or not anthropic_key:
        return jsonify({'success': False, 'error': 'API keys not configured'}), 500
    
    # Create voice handler
    voice_handler = VoiceDebateHandler(
        deepgram_key,
        anthropic_key,
        session['difficulty'],
        session['topic'],
        session.get('mode', 'ranked')
    )
    
    voice_handlers[session_id] = voice_handler
    
    print(f"🎤 Voice initialized for session {session_id}")
    
    return jsonify({'success': True, 'message': 'Voice system ready'})


@app.route('/api/voice/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio data using Deepgram"""
    data = request.json
    session_id = data.get('session_id')
    audio_base64 = data.get('audio')
    
    if session_id not in voice_handlers:
        return jsonify({'success': False, 'error': 'Voice handler not initialized'}), 400
    
    try:
        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64)
        
        # Transcribe
        handler = voice_handlers[session_id]
        transcript = handler.transcribe_audio(audio_data)
        
        return jsonify({
            'success': True,
            'transcript': transcript
        })
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/voice/process', methods=['POST'])
def process_voice_argument():
    """Process transcribed argument and generate AI response with voice"""
    data = request.json
    session_id = data.get('session_id')
    user_text = data.get('text')
    
    print(f"🎤 Voice argument from session {session_id}: {user_text[:50]}...")
    
    if session_id not in voice_handlers:
        return jsonify({'success': False, 'error': 'Voice handler not initialized'}), 400
    
    try:
        handler = voice_handlers[session_id]
        result = handler.process_argument(user_text)
        
        if result:
            print(f"✅ Processed voice argument successfully")
            return jsonify({
                'success': True,
                'ai_response': result['ai_response'],
                'scores': result.get('scores'),
                'feedback': result.get('feedback'),
                'audio': result.get('audio')  # base64 encoded MP3
            })
        else:
            return jsonify({'success': False, 'error': 'Processing failed'}), 500
            
    except Exception as e:
        print(f"❌ Error processing voice argument: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/end-debate', methods=['POST'])
def end_debate():
    """End debate and calculate final results"""
    data = request.json
    session_id = data.get('session_id')
    
    if session_id not in debate_sessions:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400
    
    session = debate_sessions[session_id]
    engine = session['engine']
    difficulty = session['difficulty']
    mode = session['mode']
    
    # Get final scores
    scores = engine.get_current_scores()
    overall_score = scores['overall']
    
    # Record debate and calculate ELO
    result = user_data.record_debate(mode, overall_score, difficulty)
    
    # Clean up session
    del debate_sessions[session_id]
    if session_id in voice_handlers:
        voice_handlers[session_id].cleanup()
        del voice_handlers[session_id]
    
    return jsonify({
        'success': True,
        'final_scores': scores,
        'elo_change': result['elo_change'],
        'new_elo': result['new_elo'],
        'new_rank': result['new_rank'],
        'won': result['won'],
        'rank_progress': user_data.get_rank_progress()
    })


def run_server(host='0.0.0.0', port=5001, debug=False):
    """Run the Flask server"""
    print(f"\n🌐 YAPBATTLE Web Server Starting...")
    print(f"📍 Open your browser to: http://localhost:{port}")
    print(f"🎮 Ready to battle!\n")
    app.run(host=host, port=port, debug=debug, load_dotenv=False)


if __name__ == '__main__':
    run_server()
