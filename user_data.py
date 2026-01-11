"""
User Data Management for YAPBATTLE
Handles user stats, ranks, streaks, and persistence
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any


class UserData:
    """Manages user profile and statistics"""
    
    def __init__(self, data_file="user_data.json"):
        self.data_file = data_file
        self.data = self.load_data()
    
    def load_data(self) -> Dict[str, Any]:
        """Load user data from file or create new"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return self.create_default_data()
        return self.create_default_data()
    
    def create_default_data(self) -> Dict[str, Any]:
        """Create default user profile"""
        return {
            "username": "Player",
            "rank": "Bronze",
            "elo": 0,  # Start at 0 ELO
            "streak_days": 0,
            "last_played": None,
            "total_debates": 0,
            "wins": 0,
            "losses": 0,
            "hot_takes_played": 0,
            "ranked_played": 0,
            "podcast_played": 0,
            "best_streak": 0,
            "average_score": 0.0,
            "created_at": datetime.now().isoformat()
        }
    
    def save_data(self):
        """Save user data to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def update_streak(self):
        """Update daily streak"""
        today = datetime.now().date()
        
        if self.data["last_played"]:
            last_played = datetime.fromisoformat(self.data["last_played"]).date()
            days_diff = (today - last_played).days
            
            if days_diff == 0:
                # Already played today
                return
            elif days_diff == 1:
                # Consecutive day
                self.data["streak_days"] += 1
            else:
                # Streak broken
                self.data["streak_days"] = 1
        else:
            # First time playing
            self.data["streak_days"] = 1
        
        # Update best streak
        if self.data["streak_days"] > self.data["best_streak"]:
            self.data["best_streak"] = self.data["streak_days"]
        
        self.data["last_played"] = datetime.now().isoformat()
        self.save_data()
    
    def calculate_elo_gain(self, overall_score: float, difficulty: str) -> int:
        """Calculate ELO gain based on argument scores and difficulty
        
        Args:
            overall_score: Average score (0-10)
            difficulty: 'easy', 'medium', or 'hard'
        
        Returns:
            ELO points gained (can be negative for poor performance)
        """
        # Base multipliers per difficulty
        multipliers = {
            'easy': 1.0,
            'medium': 1.5,
            'hard': 2.0
        }
        
        multiplier = multipliers.get(difficulty, 1.0)
        
        # NEW CLEAR SCORE-BASED ELO CALCULATION
        # Score ranges and base ELO:
        # 0-3.9: LOSS (-15 to -5 base)
        # 4-5.9: MINOR WIN (+5 to +10 base)  
        # 6-7.9: SOLID WIN (+12 to +18 base)
        # 8-10: DOMINANT WIN (+20 to +30 base)
        
        if overall_score < 4:
            # Poor performance - lose ELO proportionally
            # Score 0 = -15, Score 3.9 = -5
            base_elo = int(-15 + (overall_score * 2.5))
        elif overall_score < 6:
            # Below average win - small gain
            # Score 4 = +5, Score 5.9 = +10
            base_elo = int(5 + ((overall_score - 4) * 2.5))
        elif overall_score < 8:
            # Good performance - medium gain
            # Score 6 = +12, Score 7.9 = +18
            base_elo = int(12 + ((overall_score - 6) * 3))
        else:
            # Excellent performance - large gain
            # Score 8 = +20, Score 10 = +30
            base_elo = int(20 + ((overall_score - 8) * 5))
        
        # Apply difficulty multiplier
        elo_gain = int(base_elo * multiplier)
        
        # Ensure minimum/maximum bounds
        elo_gain = max(-20, min(60, elo_gain))
        
        print(f"📊 ELO Calculation: Score {overall_score:.1f} | Difficulty {difficulty} | Base {base_elo} | Multiplier {multiplier}x | Final {elo_gain:+d}")
        
        return elo_gain
    
    def record_debate(self, mode: str, overall_score: float, difficulty: str = 'medium'):
        """Record a completed debate with ELO calculation"""
        self.data["total_debates"] += 1
        
        # Calculate win/loss (score >= 6 is a win)
        won = overall_score >= 6.0
        
        if won:
            self.data["wins"] += 1
        else:
            self.data["losses"] += 1
        
        # Update mode-specific counter
        mode_key = f"{mode}_played"
        if mode_key in self.data:
            self.data[mode_key] += 1
        
        # Update ELO ONLY for ranked mode
        elo_change = 0
        if mode == "ranked":
            elo_change = self.calculate_elo_gain(overall_score, difficulty)
            self.data["elo"] = max(0, self.data["elo"] + elo_change)  # Can't go below 0
            self.update_rank()
            print(f"📈 Ranked Debate Complete: Score={overall_score:.1f} | Won={won} | ELO Change={elo_change:+d} | New ELO={self.data['elo']} | Rank={self.data['rank']}")
        else:
            print(f"🎮 {mode.title()} Debate Complete: Score={overall_score:.1f} | Won={won} (No ELO change for this mode)")
        
        # Update average score
        total = self.data["total_debates"]
        current_avg = self.data["average_score"]
        self.data["average_score"] = ((current_avg * (total - 1)) + overall_score) / total
        
        self.update_streak()
        self.save_data()
        
        return {
            'elo_change': elo_change,
            'new_elo': self.data["elo"],
            'new_rank': self.data["rank"],
            'won': won
        }
    
    def update_rank(self):
        """Update rank based on ELO - Bronze/Silver/Gold system"""
        elo = self.data["elo"]
        
        # Simple 3-rank system: Bronze (0-99), Silver (100-199), Gold (200+)
        if elo < 100:
            self.data["rank"] = "Bronze"
        elif elo < 200:
            self.data["rank"] = "Silver"
        else:
            self.data["rank"] = "Gold"  # Gold is highest, ELO can go past 200
    
    def get_rank_icon(self) -> str:
        """Get Font Awesome icon class for current rank"""
        rank = self.data["rank"]
        if rank == "Bronze":
            return "fa-solid fa-shield"
        elif rank == "Silver":
            return "fa-solid fa-shield"
        elif rank == "Gold":
            return "fa-solid fa-shield"
        return "fa-solid fa-trophy"
    
    def get_rank_color(self) -> str:
        """Get color for current rank"""
        rank = self.data["rank"]
        if rank == "Bronze":
            return "#cd7f32"  # Bronze color
        elif rank == "Silver":
            return "#c0c0c0"  # Silver color
        elif rank == "Gold":
            return "#ffd700"  # Gold color
        return "#94a3b8"
    
    def get_rank_progress(self) -> dict:
        """Get progress toward next rank"""
        elo = self.data["elo"]
        rank = self.data["rank"]
        
        if rank == "Bronze":
            return {
                "current": elo,
                "needed": 100,
                "percentage": min(100, elo),
                "next_rank": "Silver"
            }
        elif rank == "Silver":
            return {
                "current": elo - 100,
                "needed": 100,
                "percentage": min(100, elo - 100),
                "next_rank": "Gold"
            }
        else:  # Gold
            return {
                "current": elo,
                "needed": None,
                "percentage": 100,
                "next_rank": "MAX RANK!"
            }
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage"""
        total = self.data["wins"] + self.data["losses"]
        if total == 0:
            return 0.0
        return (self.data["wins"] / total) * 100
    
    def __getitem__(self, key):
        """Allow dict-like access"""
        return self.data[key]
    
    def __setitem__(self, key, value):
        """Allow dict-like assignment"""
        self.data[key] = value
        self.save_data()
