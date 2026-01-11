// Continuous voice debate - real conversation style
const urlParams = new URLSearchParams(window.location.search);
const mode = urlParams.get('mode');
const difficulty = urlParams.get('difficulty');

let isActive = false;
let debateStartTime = null;
let timerInterval = null;
let timeLimit = 120;
let silenceDelay = 2000;
let sessionId = null;
let voiceInitialized = false;

// Deepgram WebSocket for continuous listening
let deepgramSocket = null;
let mediaRecorder = null;
let audioContext = null;
let isAISpeaking = false;
let currentAudio = null;
let silenceTimeout = null;
let currentTranscript = '';
let isProcessing = false;

// Deepgram API key is injected by backend in debate.html
// const DEEPGRAM_API_KEY is defined in the HTML template


document.getElementById('display-difficulty').textContent = difficulty;

async function initDebate() {
    try {
        const response = await fetch('/api/start-debate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, difficulty })
        });
        
        const data = await response.json();
        if (data.success) {
            sessionId = data.session_id;
            document.getElementById('topic').textContent = data.topic;
            
            // Get configuration from backend
            if (data.config) {
                timeLimit = data.config.time_limit || 120;
                silenceDelay = data.config.response_delay || 2000;
                console.log(`📏 Debate Config: Time=${timeLimit}s, Delay=${silenceDelay}ms`);
            }
            
            // Initialize voice system
            await initVoice();
        }
    } catch (error) {
        console.error('❌ Error:', error);
        document.getElementById('topic').textContent = 'CONNECTION ERROR';
    }
}

async function initVoice() {
    try {
        // IMPORTANT: Request microphone permission FIRST before any API calls
        console.log('🎤 Requesting microphone permission...');
        
        try {
            // Request mic access early to trigger browser permission prompt
            const testStream = await navigator.mediaDevices.getUserMedia({ 
                audio: true 
            });
            console.log('✅ Microphone permission granted');
            
            // Stop the test stream immediately
            testStream.getTracks().forEach(track => track.stop());
        } catch (micError) {
            console.error('❌ Microphone permission denied:', micError);
            
            let errorMessage = '🎤 MICROPHONE ACCESS REQUIRED\n\n';
            
            if (micError.name === 'NotAllowedError' || micError.name === 'PermissionDeniedError') {
                errorMessage += 'Please allow microphone access:\n\n';
                errorMessage += '1. Click the 🎤 or 🔒 icon in your browser\'s address bar\n';
                errorMessage += '2. Select "Allow" for Microphone\n';
                errorMessage += '3. Refresh this page\n\n';
                errorMessage += 'Chrome/Edge: Click the camera icon in the address bar\n';
                errorMessage += 'Safari: Safari > Settings for This Website > Microphone > Allow\n';
                errorMessage += 'Firefox: Click the crossed-out microphone icon';
            } else if (micError.name === 'NotFoundError') {
                errorMessage += 'No microphone detected. Please connect a microphone.';
            } else {
                errorMessage += 'Error: ' + micError.message;
            }
            
            alert(errorMessage);
            window.location.href = '/';
            return;
        }
        
        // Now initialize the voice system
        const response = await fetch('/api/voice/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        if (data.success) {
            voiceInitialized = true;
            
            // Show difficulty-specific message
            let message = '';
            if (difficulty === 'easy') {
                message = 'READY - I\'LL GIVE YOU TIME TO THINK';
            } else if (difficulty === 'medium') {
                message = 'READY - BALANCED RESPONSE TIME';
            } else if (difficulty === 'hard') {
                message = 'READY - I\'LL INTERRUPT FAST ⚡';
            }
            
            updateStatus(message, 'active');
            console.log(`✅ Voice ready - ${silenceDelay}ms response delay`);
        }
    } catch (error) {
        console.error('❌ Voice init error:', error);
        alert('Voice system failed. Returning to home.');
        window.location.href = '/';
    }
}

function updateStatus(text, type) {
    const status = document.getElementById('status');
    const dot = document.getElementById('status-dot');
    status.textContent = text;
    if (type === 'active') dot.classList.add('active');
    else dot.classList.remove('active');
}

function toggleMic() {
    if (!voiceInitialized) {
        alert('Voice system not ready. Please wait...');
        return;
    }
    
    if (!isActive) {
        startConversation();
    } else {
        stopConversation();
    }
}

async function startConversation() {
    try {
        isActive = true;
        debateStartTime = Date.now();
        timerInterval = setInterval(updateTimer, 1000);
        document.getElementById('mic-btn').classList.add('recording');
        
        updateStatus('🎤 CONVERSATION ACTIVE - SPEAK ANYTIME', 'active');
        
        // List available audio devices
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioInputs = devices.filter(device => device.kind === 'audioinput');
            console.log('🎤 Available microphones:');
            audioInputs.forEach((device, i) => {
                console.log(`  ${i + 1}. ${device.label || 'Unknown Device'}`);
            });
            
            // Find macOS built-in microphone
            const macMic = audioInputs.find(d => 
                d.label.toLowerCase().includes('built-in') || 
                d.label.toLowerCase().includes('macbook') ||
                d.label.toLowerCase().includes('default')
            );
            
            if (macMic) {
                console.log(`✅ Found macOS microphone: ${macMic.label}`);
            }
        } catch (e) {
            console.log('⚠️ Could not enumerate devices (permission needed)');
        }
        
        // Start continuous listening with Deepgram
        await startContinuousListening();
        
    } catch (error) {
        console.error('❌ Error starting:', error);
        alert('Could not start conversation. Check microphone permissions.');
        stopConversation();
    }
}

async function startContinuousListening() {
    try {
        console.log('🎤 Requesting macOS microphone access...');
        
        // Get microphone stream - explicitly request default device (macOS built-in)
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: 16000,
                channelCount: 1
            }
        }).catch(error => {
            console.error('❌ getUserMedia failed:', error);
            
            // Provide specific error messages
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                throw new Error('MICROPHONE_PERMISSION_DENIED');
            } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                throw new Error('NO_MICROPHONE_FOUND');
            } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                throw new Error('MICROPHONE_IN_USE');
            } else {
                throw error;
            }
        });
        
        // Log which device we're using
        const audioTrack = stream.getAudioTracks()[0];
        console.log('✅ Using microphone:', audioTrack.label);
        console.log('📊 Audio settings:', audioTrack.getSettings());
        
        // Connect to Deepgram WebSocket with optimal settings for voice pickup
        const deepgramUrl = `wss://api.deepgram.com/v1/listen?model=nova-2-general&language=en&smart_format=true&interim_results=true&vad_events=true&endpointing=1000&utterance_end_ms=1000`;
        
        deepgramSocket = new WebSocket(deepgramUrl, ['token', DEEPGRAM_API_KEY]);
        
        deepgramSocket.onopen = () => {
            console.log('⚡ Connected to Deepgram - Listening for voice...');
            updateStatus('🎤 LISTENING - SPEAK NOW', 'active');
        };
        
        deepgramSocket.onmessage = (message) => {
            const data = JSON.parse(message.data);
            console.log('📡 Deepgram response:', data.type);
            handleTranscript(data);
        };
        
        deepgramSocket.onerror = (error) => {
            console.error('❌ Deepgram WebSocket error:', error);
            alert('Deepgram connection error. Check console for details.');
        };
        
        deepgramSocket.onclose = (event) => {
            console.log('🔌 Deepgram disconnected:', event.code, event.reason);
        };
        
        // Set up MediaRecorder to send audio to Deepgram
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                console.log('🎤 Audio chunk:', event.data.size, 'bytes');
                if (deepgramSocket && deepgramSocket.readyState === WebSocket.OPEN) {
                    deepgramSocket.send(event.data);
                    console.log('📤 Sent audio to Deepgram');
                } else {
                    console.warn('⚠️ WebSocket not ready, state:', deepgramSocket?.readyState);
                }
            }
        };
        
        mediaRecorder.onerror = (error) => {
            console.error('❌ MediaRecorder error:', error);
        };
        
        mediaRecorder.start(250); // Send audio every 250ms
        console.log('🎤 MediaRecorder started, state:', mediaRecorder.state);
        
    } catch (error) {
        console.error('❌ Microphone error:', error);
        
        let errorMessage = 'Microphone access error. ';
        
        if (error.message === 'MICROPHONE_PERMISSION_DENIED') {
            errorMessage = `🎤 MICROPHONE ACCESS DENIED

To fix this:
1. Click the 🔒 lock icon in your browser's address bar
2. Find "Microphone" permissions
3. Change to "Allow"
4. Refresh this page

On Safari: Go to Safari > Settings > Websites > Microphone
On Chrome: Click site settings and allow microphone`;
        } else if (error.message === 'NO_MICROPHONE_FOUND') {
            errorMessage = 'No microphone detected. Please connect a microphone and refresh.';
        } else if (error.message === 'MICROPHONE_IN_USE') {
            errorMessage = 'Microphone is already in use by another application. Close other apps using the mic.';
        } else {
            errorMessage += error.message;
        }
        
        alert(errorMessage);
        stopConversation();
    }
}

function handleTranscript(data) {
    try {
        console.log('📥 Received data type:', data.type);
        
        if (data.type === 'Results') {
            const transcript = data.channel.alternatives[0].transcript;
            console.log('📝 Transcript:', transcript, '| Final:', data.is_final);
            
            if (transcript && transcript.trim().length > 0) {
                const isFinal = data.is_final;
                const speechFinal = data.speech_final;
                
                if (isFinal || speechFinal) {
                    currentTranscript += transcript + ' ';
                    
                    // Show what we captured
                    console.log('✅ Captured:', currentTranscript.trim());
                    updateCurrentMessage('you', currentTranscript.trim());
                    
                    // Clear any existing timeout
                    if (silenceTimeout) {
                        clearTimeout(silenceTimeout);
                    }
                    
                    // Process after difficulty-based delay
                    silenceTimeout = setTimeout(() => {
                        const finalText = currentTranscript.trim();
                        if (finalText.length > 5 && !isAISpeaking && !isProcessing) {
                            console.log('🤖 Processing:', finalText);
                            processArgument(finalText);
                            currentTranscript = '';
                        } else if (isProcessing) {
                            console.log('⚠️ Already processing, skipping...');
                        }
                    }, silenceDelay);
                    
                } else {
                    // Show live transcript
                    const display = currentTranscript + transcript;
                    updateCurrentMessage('you', display + '...');
                }
            }
        } else if (data.type === 'UtteranceEnd') {
            console.log('🛑 Utterance ended');
            const finalText = currentTranscript.trim();
            if (finalText.length > 5 && !isAISpeaking && !isProcessing) {
                if (silenceTimeout) clearTimeout(silenceTimeout);
                console.log('🤖 Processing on utterance end:', finalText);
                processArgument(finalText);
                currentTranscript = '';
            } else if (isProcessing) {
                console.log('⚠️ Already processing, ignoring utterance end');
            }
        } else if (data.type === 'Metadata') {
            console.log('ℹ️ Metadata:', data);
        }
    } catch (error) {
        console.error('❌ Transcript handling error:', error);
    }
}

let lastUserMessage = null;

function updateCurrentMessage(side, text) {
    const boxId = side === 'you' ? 'your-transcript' : 'ai-transcript';
    const msgClass = side === 'you' ? 'user-msg' : 'ai-msg';
    const box = document.getElementById(boxId);
    
    if (side === 'you') {
        if (lastUserMessage) {
            lastUserMessage.textContent = text;
        } else {
            const msg = document.createElement('div');
            msg.className = `msg ${msgClass}`;
            msg.textContent = text;
            box.appendChild(msg);
            lastUserMessage = msg;
            box.scrollTop = box.scrollHeight;
        }
    } else {
        addMessage(side, text);
    }
}

async function processArgument(transcript) {
    try {
        // CRITICAL: Prevent multiple simultaneous processing
        if (isProcessing) {
            console.log('⚠️ Already processing an argument, skipping this one');
            return;
        }
        
        isProcessing = true;
        console.log('🔒 Processing locked');
        
        // Stop current audio if AI is speaking
        if (isAISpeaking && currentAudio) {
            console.log('🛑 Stopping current AI audio');
            currentAudio.pause();
            currentAudio.currentTime = 0;
            currentAudio = null;
            isAISpeaking = false;
        }
        
        console.log('🤖 Processing argument:', transcript);
        updateStatus('AI ANALYZING YOUR POINT...', 'active');
        
        // Finalize user message
        lastUserMessage = null;
        
        // Process with AI
        const response = await fetch('/api/voice/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                session_id: sessionId, 
                text: transcript 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update scores
            if (data.scores) {
                updateScores(data.scores);
                const scoreText = `📊 Clarity ${data.scores.clarity} | Logic ${data.scores.argument} | Persuasion ${data.scores.rhetoric}`;
                addMessage('feedback', scoreText);
            }
            
            // Show AI response
            if (data.ai_response) {
                addMessage('ai', data.ai_response);
            }
            
            // Show feedback
            if (data.feedback) {
                addMessage('feedback', `💭 ${data.feedback}`);
            }
            
            // Play AI voice
            if (data.audio) {
                updateStatus('🔊 AI RESPONDING...', 'active');
                await playAIVoice(data.audio);
            }
            
            // IMPORTANT: Reset for next turn
            console.log('✅ Turn complete - ready for next argument');
            updateStatus('🎤 LISTENING - YOUR TURN', 'active');
            
        } else {
            console.error('❌ Processing error:', data.error);
            updateStatus('ERROR - CLICK MIC TO RESTART', '');
        }
        
    } catch (error) {
        console.error('❌ Error processing argument:', error);
        updateStatus('ERROR - CLICK MIC TO RESTART', '');
    } finally {
        // CRITICAL: Always unlock processing AND reset transcript
        isProcessing = false;
        currentTranscript = ''; // Reset for next input
        lastUserMessage = null; // Reset message tracking
        console.log('🔓 Processing unlocked - ready for next argument');
    }
}

async function playAIVoice(base64Audio) {
    return new Promise((resolve) => {
        try {
            // CRITICAL: Stop any existing audio first
            if (currentAudio) {
                console.log('🛑 Stopping previous audio before playing new one');
                currentAudio.pause();
                currentAudio.currentTime = 0;
                currentAudio = null;
            }
            
            isAISpeaking = true;
            console.log('🔊 Starting to play AI voice');
            
            // Decode base64
            const audioData = atob(base64Audio);
            const arrayBuffer = new Uint8Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
                arrayBuffer[i] = audioData.charCodeAt(i);
            }
            
            // Create audio
            const blob = new Blob([arrayBuffer], { type: 'audio/mp3' });
            const url = URL.createObjectURL(blob);
            currentAudio = new Audio(url);
            
            currentAudio.onended = () => {
                console.log('✅ AI voice finished');
                URL.revokeObjectURL(url);
                isAISpeaking = false;
                currentAudio = null;
                updateStatus('🎤 LISTENING - YOUR TURN', 'active');
                resolve();
            };
            
            currentAudio.onerror = (error) => {
                console.error('❌ Audio playback error:', error);
                URL.revokeObjectURL(url);
                isAISpeaking = false;
                currentAudio = null;
                resolve();
            };
            
            // Play audio
            currentAudio.play()
                .then(() => {
                    console.log('🔊 AI voice playing...');
                })
                .catch(err => {
                    console.error('❌ Audio play error:', err);
                    isAISpeaking = false;
                    currentAudio = null;
                    resolve();
                });
            
        } catch (error) {
            console.error('❌ Audio creation error:', error);
            isAISpeaking = false;
            currentAudio = null;
            resolve();
        }
    });
}

function addMessage(side, text) {
    let boxId, msgClass;
    
    if (side === 'you') {
        boxId = 'your-transcript';
        msgClass = 'user-msg';
    } else if (side === 'ai') {
        boxId = 'ai-transcript';
        msgClass = 'ai-msg';
    } else if (side === 'feedback') {
        boxId = 'your-transcript';
        msgClass = 'feedback-msg';
    }
    
    const box = document.getElementById(boxId);
    const msg = document.createElement('div');
    msg.className = `msg ${msgClass}`;
    msg.textContent = text;
    
    box.appendChild(msg);
    box.scrollTop = box.scrollHeight;
}

function updateScores(scores) {
    document.getElementById('overall-score').textContent = Math.round(scores.overall);
    document.getElementById('clarity-score').textContent = scores.clarity;
    document.getElementById('argument-score').textContent = scores.argument;
    document.getElementById('rhetoric-score').textContent = scores.rhetoric;
}

function updateTimer() {
    const elapsed = Math.floor((Date.now() - debateStartTime) / 1000);
    const remaining = Math.max(0, timeLimit - elapsed);
    const mins = Math.floor(remaining / 60);
    const secs = remaining % 60;
    document.getElementById('timer').textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    
    if (remaining === 0) {
        console.log('⏰ Time expired - ending debate');
        endDebate();
    }
}

async function endDebate() {
    stopConversation();
    
    try {
        updateStatus('CALCULATING RESULTS...', 'active');
        
        const response = await fetch('/api/end-debate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showResults(data);
        } else {
            console.error('Error ending debate:', data.error);
            setTimeout(() => exitDebate(), 2000);
        }
    } catch (error) {
        console.error('Error:', error);
        setTimeout(() => exitDebate(), 2000);
    }
}

function showResults(data) {
    // Create results overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(5, 7, 10, 0.95);
        backdrop-filter: blur(20px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    `;
    
    const won = data.won;
    const eloChange = data.elo_change;
    const eloSign = eloChange >= 0 ? '+' : '';
    const resultColor = won ? '#10b981' : '#fb7185';
    
    overlay.innerHTML = `
        <style>
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            @keyframes slideUp { from { transform: translateY(30px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        </style>
        <div style="background: #0d1117; padding: 50px; border-radius: 24px; max-width: 550px; width: 90%; text-align: center; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 80px rgba(0,0,0,0.8); animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);">
            <div style="font-family: 'Bebas Neue', sans-serif; font-size: 1.2rem; color: ${resultColor}; letter-spacing: 4px; margin-bottom: 10px;">DEBATE CONCLUDED</div>
            <h1 style="font-family: 'Bebas Neue', sans-serif; font-size: 5rem; color: ${resultColor}; margin: 0; line-height: 1; text-shadow: 0 0 30px ${resultColor}44;">
                ${won ? 'VICTORY' : 'DEFEAT'}
            </h1>
            
            <div style="margin: 40px 0; display: flex; align-items: center; justify-content: center; gap: 30px;">
                <div style="text-align: left;">
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 900; text-transform: uppercase; letter-spacing: 2px;">BATTLE RATING</div>
                    <div style="font-size: 3.5rem; font-weight: 900; color: #f8fafc; font-family: 'Bebas Neue', sans-serif;">${data.final_scores.overall.toFixed(1)}<span style="font-size: 1.5rem; color: #4b5563;">/10</span></div>
                </div>
                <div style="width: 2px; height: 60px; background: rgba(255,255,255,0.1);"></div>
                <div style="text-align: left;">
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 900; text-transform: uppercase; letter-spacing: 2px;">ELO CHANGE</div>
                    <div style="font-size: 3.5rem; font-weight: 900; color: ${eloChange >= 0 ? '#10b981' : '#fb7185'}; font-family: 'Bebas Neue', sans-serif;">${eloSign}${eloChange}</div>
                </div>
            </div>
            
            <div style="background: rgba(255,255,255,0.03); padding: 25px; border-radius: 16px; margin-bottom: 30px; border: 1px solid rgba(255,255,255,0.05);">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span style="color: #94a3b8; font-weight: 700; font-size: 0.9rem;">RANK: ${data.new_rank.toUpperCase()}</span>
                    <span style="color: #f8fafc; font-weight: 900; font-size: 0.9rem;">${data.new_elo} ELO</span>
                </div>
                ${data.rank_progress.next_rank !== 'MAX RANK!' ? `
                    <div style="background: rgba(255,255,255,0.1); height: 10px; border-radius: 5px; overflow: hidden; margin-top: 10px;">
                        <div style="background: linear-gradient(90deg, #38bdf8, #818cf8); height: 100%; width: ${data.rank_progress.percentage}%; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1);"></div>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.75rem; color: #64748b; font-weight: 700; letter-spacing: 1px;">
                        NEXT RANK: ${data.rank_progress.next_rank.toUpperCase()} (${data.rank_progress.needed - data.rank_progress.current} MORE ELO)
                    </div>
                ` : `<div style="color: #fbbf24; font-weight: 900; margin-top: 15px; font-size: 0.9rem; letter-spacing: 2px;">🏆 SUPREME CHAMPION RANK ACHIEVED</div>`}
            </div>
            
            <button onclick="window.location.href='/'" style="
                background: var(--text-main);
                color: #05070a;
                border: none;
                padding: 18px 50px;
                font-size: 1rem;
                font-weight: 900;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
                text-transform: uppercase;
                letter-spacing: 2px;
                width: 100%;
            " onmouseover="this.style.background='#38bdf8'; this.style.transform='scale(1.02)'" onmouseout="this.style.background='#f8fafc'; this.style.transform='scale(1)'">
                RETURN TO BASE
            </button>
        </div>
    `;
    
    document.body.appendChild(overlay);
}

function stopConversation() {
    isActive = false;
    document.getElementById('mic-btn').classList.remove('recording');
    updateStatus('CONVERSATION ENDED', '');
    clearInterval(timerInterval);
    
    // Stop audio
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    
    // Stop recording
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    
    // Close Deepgram connection
    if (deepgramSocket && deepgramSocket.readyState === WebSocket.OPEN) {
        deepgramSocket.close();
    }
    
    console.log('🛑 Conversation stopped');
}

function exitDebate() {
    stopConversation();
    window.location.href = '/';
}

// Initialize
initDebate();
