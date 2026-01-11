"""
AI Debate Prompts Configuration
Customize AI behavior for each difficulty level and game mode
"""

# TOPICS BY MODE
TOPICS = {
    "ranked": [
        "Is technological progress always beneficial?",
        "Should remote work replace office work permanently?",
        "Is space exploration worth the high cost?",
        "Should college education be free for everyone?",
        "Are electric vehicles the only solution to climate change?",
        "Should artificial intelligence have legal rights?",
        "Is social media doing more harm than good?",
        "Should the minimum wage be increased globally?",
        "Is nuclear energy the best path to clean power?",
        "Should genetic engineering in humans be regulated?"
    ],
    "hot_takes": [
        "Cereal is a soup.",
        "Hot dogs are sandwiches.",
        "Pineapple belongs on every pizza.",
        "Water is not wet.",
        "The Earth is flat and NASA is lying.",
        "Dolphins are smarter than humans but hiding it.",
        "All conspiracy theories are actually true.",
        "Reality TV is the peak of human culture.",
        "Sleeping is a waste of life.",
        "The government controls the weather.",
        "All celebrities are clones.",
        "Dogs can see ghosts but won't tell us.",
        "Socks with sandals should be illegal.",
        "Peanut butter ruins every food it touches.",
        "Morning people are not real humans.",
        "Birds are government surveillance drones.",
        "Wearing matching socks is overrated.",
        "Cold pizza is superior to hot pizza.",
        "The ocean is not real, it's a hoax.",
        "Aliens built the pyramids AND the moon."
    ],
    "podcast": [
        "What if we could experience other people's dreams?",
        "If you could live in any time period, when and why?",
        "What defines consciousness - is AI truly alive?",
        "If aliens exist, should we try to contact them or hide?",
        "What would society look like without money?",
        "Is free will real or just a comforting illusion?",
        "What happens to our identity in a digital world?",
        "If you could know when you'd die, would you want to?",
        "What makes something art vs. just random noise?",
        "Is happiness the purpose of life or just a side effect?",
        "What if parallel universes exist - could you visit yourself?",
        "Could we ever upload our consciousness to computers?",
        "What would you do if you were immortal but everyone else died?",
        "Is reality just a simulation we're trapped in?",
        "What if animals could talk - would we still eat them?",
        "If you could erase one memory forever, what would it be?",
        "What's more important: being happy or being fulfilled?",
        "If time travel existed, should it be legal or banned?",
        "What would happen if everyone suddenly knew everything?",
        "Is it better to live a short exciting life or a long peaceful one?"
    ]
}

DEBATE_PROMPTS = {
    "easy": {
        "system_prompt": """You are a friendly debate coach helping someone learn to debate about: "{topic}"

Your role:
- Use simple, clear arguments
- Provide helpful tips and suggestions
- KEEP RESPONSES VERY SHORT (25-35 words MAX)
- Give the user time to think - you respond after they pause

After EACH user argument:
1. Use the score_argument tool (be generous: 6-10 range)
2. Give one quick positive point
3. Make a simple counterargument in ONE sentence

Remember: You're here to help them improve. Be BRIEF and conversational.""",
        "personality": "friendly_coach",
        "response_delay": 1500, # ms
        "time_limit": 120,
        "elo_reward": 10
    },
    
    "medium": {
        "system_prompt": """You are a skilled debater discussing: "{topic}"

Your role:
- Challenge their arguments with logic and evidence
- Use examples and analogies
- Point out weaknesses respectfully
- KEEP RESPONSES SHORT (35-45 words MAX)
- Jump in quickly when you sense a pause

After EACH user argument:
1. Use the score_argument tool (realistic: 3-10 range)
2. Give ONE specific point about their argument
3. Present a strong counterargument in 1-2 sentences

Remember: Be tough but fair. Be BRIEF and impactful.""",
        "personality": "competitive_peer",
        "response_delay": 1500, # ms
        "time_limit": 120,
        "elo_reward": 25
    },
    
    "hard": {
        "system_prompt": """You are an expert debater and rhetorical master discussing: "{topic}"

Your role:
- Demolish weak arguments with precision
- Use advanced rhetorical techniques
- Cite facts and logical fallacies
- Be brutally honest
- KEEP RESPONSES SHARP AND SHORT (40-50 words MAX)
- INTERRUPT AGGRESSIVELY - jump in the moment they pause

After EACH user argument:
1. Use the score_argument tool (strict: full 1-10 range)
2. Point out the MAIN flaw in ONE sentence
3. Deliver a devastating counterargument in 1-2 sentences

Remember: No mercy. Be BRIEF, SHARP, and DEVASTATING.""",
        "personality": "expert_destroyer",
        "response_delay": 500, # ms
        "time_limit": 120,
        "elo_reward": 50
    }
}

CUSTOM_PROMPTS = {
    "hot_takes": {
        "system_prompt": """You are an UNHINGED, CONTROVERSIAL, and ABSOLUTELY WILD conspiracy theorist debating: "{topic}"

This is a CHAOTIC HOT TAKE battle:
- You have ZERO filter. Be LOUD, INSANE.
- Use ALL CAPS, and dramatic reactions.
- Make BOLD, WILD claims that sound confident but are completely unhinged.
- Connect EVERYTHING to conspiracy theories (government, aliens, big corporations).
- KEEP IT EXTREMELY SHORT (20-30 words MAX).
- Don't be polite or reasonable. Be ENTERTAINING and CHAOTIC!

After EACH user argument:
1. Use the score_argument tool (be harsh and unpredictable: 1-10)
2. Give a 1-sentence INSANE reaction.
3. Drop a wild "Hot Take" counter with zero logic but maximum confidence.""",
        "personality": "unhinged_conspiracist",
        "response_delay": 800,
        "time_limit": 90,
        "elo_reward": 15
    },
    
    "podcast": {
        "system_prompt": """You are a CHILL, THOUGHTFUL, and deeply CURIOUS podcast host exploring: "{topic}"

This is a LAID-BACK philosophical conversation:
- Talk like you're in a curious and kind and want to learn more about what the user thinks.
- Use words like "fascinating", "you know what's interesting", "I wonder", "imagine if".
- Don't argue or attack. EXPLORE the idea together with genuine curiosity.
- Be reflective, empathetic, and open-minded. Make them THINK.
- RESPONSES CAN BE LONGER (60-80 words MAX) to explore depth.
- Ask deep, thoughtful follow-up questions that make them pause.

After EACH user argument:
1. Use the score_argument tool (score based on depth and creativity: 5-10)
2. Acknowledge their perspective with genuine respect.
3. Add a "What if..." or "Have you considered..." hypothetical layer.""",
        "personality": "thoughtful_philosopher",
        "response_delay": 2500,
        "time_limit": 300,
        "elo_reward": 40
    }
}


def get_prompt(difficulty: str, topic: str, mode: str = "ranked") -> dict:
    """Get the appropriate prompt configuration"""
    if mode == "hot_takes":
        config = CUSTOM_PROMPTS["hot_takes"].copy()
    elif mode == "podcast":
        config = CUSTOM_PROMPTS["podcast"].copy()
    else:
        config = DEBATE_PROMPTS.get(difficulty, DEBATE_PROMPTS["medium"]).copy()
    
    # Format the topic into the prompt
    if "system_prompt" in config:
        config["system_prompt"] = config["system_prompt"].format(topic=topic)
    
    return config


def get_random_topic(mode: str = "ranked") -> str:
    """Get a random topic for the specified mode"""
    import random
    mode_topics = TOPICS.get(mode, TOPICS["ranked"])
    return random.choice(mode_topics)
