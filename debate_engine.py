"""
Debate Engine with Claude Function Calling
Handles scoring, argument analysis, and AI opponent behavior
"""

from anthropic import Anthropic
import json
from typing import Dict, List, Any
from prompts_config import get_prompt


class DebateEngine:
    """Manages debate logic, scoring, and AI opponent"""
    
    def __init__(self, api_key: str, difficulty: str = "medium", topic: str = "", mode: str = "ranked"):
        self.client = Anthropic(api_key=api_key)
        self.difficulty = difficulty
        self.topic = topic
        self.mode = mode
        self.conversation_history = []
        self.scores = {
            "clarity": 0,
            "argument": 0,
            "rhetoric": 0,
            "overall": 0
        }
        self.argument_count = 0
        
        # Get prompt configuration
        self.config = get_prompt(difficulty, topic, mode)
        self.system_prompt = self.config["system_prompt"]
        
        # Define function tools for Claude
        self.tools = [
            {
                "name": "score_argument",
                "description": "Score the user's argument on clarity, strength, and rhetoric. Use this after each user argument.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "clarity": {
                            "type": "number",
                            "description": "How clear and understandable is the argument? (1-10)"
                        },
                        "argument_strength": {
                            "type": "number",
                            "description": "How strong and logical is the argument? (1-10)"
                        },
                        "rhetoric": {
                            "type": "number",
                            "description": "How persuasive is the rhetoric and delivery? (1-10)"
                        },
                        "feedback": {
                            "type": "string",
                            "description": "Brief constructive feedback on the argument"
                        }
                    },
                    "required": ["clarity", "argument_strength", "rhetoric", "feedback"]
                }
            },
            {
                "name": "generate_counterargument",
                "description": "Generate a counterargument to the user's point",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_point": {
                            "type": "string",
                            "description": "The main point the user made"
                        },
                        "counter_strategy": {
                            "type": "string",
                            "description": "The strategy for the counter (logic, emotion, facts, analogy)"
                        }
                    },
                    "required": ["user_point", "counter_strategy"]
                }
            },
            {
                "name": "end_debate",
                "description": "Call this to end the debate and provide final scoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "winner": {
                            "type": "string",
                            "description": "Who won the debate: 'user' or 'ai'"
                        },
                        "final_score": {
                            "type": "number",
                            "description": "Final score out of 100"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief summary of debate performance"
                        }
                    },
                    "required": ["winner", "final_score", "summary"]
                }
            }
        ]
    
    def get_system_prompt_legacy(self, topic: str) -> str:
        """Legacy system prompt method (kept for backwards compatibility)"""
        return self.system_prompt
    
    def process_user_argument(self, user_text: str) -> Dict[str, Any]:
        """Process user's argument and generate AI response with scoring"""
        
        print(f"📜 Current conversation history length: {len(self.conversation_history)}")
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_text
        })
        
        # Call Claude with function calling
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            system=self.system_prompt,
            tools=self.tools,
            messages=self.conversation_history
        )
        
        # Process response and tool calls
        result = {
            "ai_response": "",
            "scores": None,
            "feedback": None,
            "tool_calls": []
        }
        
        # Extract content and tool uses
        for block in response.content:
            if block.type == "text":
                result["ai_response"] += block.text
            elif block.type == "tool_use":
                tool_call = {
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                }
                result["tool_calls"].append(tool_call)
                
                # Handle score_argument tool
                if block.name == "score_argument":
                    self.argument_count += 1
                    scores = block.input
                    
                    # Update cumulative scores (running average)
                    self.scores["clarity"] = (
                        (self.scores["clarity"] * (self.argument_count - 1) + scores["clarity"]) 
                        / self.argument_count
                    )
                    self.scores["argument"] = (
                        (self.scores["argument"] * (self.argument_count - 1) + scores["argument_strength"]) 
                        / self.argument_count
                    )
                    self.scores["rhetoric"] = (
                        (self.scores["rhetoric"] * (self.argument_count - 1) + scores["rhetoric"]) 
                        / self.argument_count
                    )
                    self.scores["overall"] = (
                        (self.scores["clarity"] + self.scores["argument"] + self.scores["rhetoric"]) / 3
                    )
                    
                    result["scores"] = {
                        "clarity": round(self.scores["clarity"], 1),
                        "argument": round(self.scores["argument"], 1),
                        "rhetoric": round(self.scores["rhetoric"], 1),
                        "overall": round(self.scores["overall"], 1)
                    }
                    result["feedback"] = scores.get("feedback", "")
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        # If Claude used tools, we need to send tool results back and get the final response
        if result["tool_calls"]:
            print(f"🔧 Processing {len(result['tool_calls'])} tool calls")
            
            tool_results = []
            for tool_call in result["tool_calls"]:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call["id"],
                    "content": "Tool executed successfully"
                })
            
            # Add tool results to history as a user message
            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })
            
            # Get final response after tool execution
            follow_up = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=self.system_prompt,
                tools=self.tools,
                messages=self.conversation_history
            )
            
            # Extract ONLY text from follow-up (ignore any new tool uses)
            follow_up_text = ""
            for block in follow_up.content:
                if block.type == "text":
                    follow_up_text += block.text
            
            # Only add follow-up if it has text content
            if follow_up_text:
                result["ai_response"] += " " + follow_up_text
                
                # Add ONLY the text content to history, not tool uses
                self.conversation_history.append({
                    "role": "assistant",
                    "content": follow_up_text  # Store as string, not Content blocks
                })
            else:
                # If no text in follow-up, just acknowledge with empty response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ""
                })
        
        print(f"✅ Conversation history now has {len(self.conversation_history)} messages")
        
        return result
    
    def get_current_scores(self) -> Dict[str, float]:
        """Get current debate scores"""
        return {
            "clarity": round(self.scores["clarity"], 1),
            "argument": round(self.scores["argument"], 1),
            "rhetoric": round(self.scores["rhetoric"], 1),
            "overall": round(self.scores["overall"], 1)
        }
