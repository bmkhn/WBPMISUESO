# internal/experts/ai_team_gen_stub.py

import random
from typing import List, Dict, Any

def generate_teams_by_ai(users: List[Any], num_members: int, topic: str) -> List[Dict[str, Any]]:
    """
    STUB: Simulates the AI team selection logic. 
    It selects the best 'num_members' from the eligible users based on the topic.
    """
    if not users or num_members <= 0 or not topic:
        return []

    topic_lower = topic.lower().strip()
    
    # 1. Score Users by Topic Match
    scored_users = []
    for user in users:
        expertise = user.expertise.lower() if user.expertise else ""
        
        # Simple scoring simulation:
        match_score = 0
        if topic_lower in expertise:
            match_score = 100
        elif any(word in expertise for word in topic_lower.split()):
            match_score = 80
        else:
            match_score = random.randint(30, 70) 

        # We keep all scores for sorting the "best" members
        scored_users.append({'user': user, 'score': match_score})

    # Sort users by match score (highest match first)
    scored_users.sort(key=lambda x: x['score'], reverse=True)
    
    # 2. Select the Top N Members for the Team
    best_members_data = scored_users[:num_members]
    
    if not best_members_data:
        return []
    
    # 3. Format the Output for a Single Team
    team_members = [data['user'] for data in best_members_data]
    team_score_sum = sum(data['score'] for data in best_members_data)
    avg_score = round(team_score_sum / len(team_members), 1)

    # Returning as a list containing a single team dictionary
    return [{
        'team_name': f"Best Team for '{topic}' (Size: {len(team_members)})",
        'ai_score': avg_score,
        'rationale': f"The AI selected the top {len(team_members)} experts based on expertise match (average score: {avg_score}%) for the topic '{topic}'.",
        'members': [
            {
                'id': member.id,
                'name': member.get_full_name(),
                'expertise': member.expertise or 'General',
                'role': member.role
            } for member in team_members
        ]
    }]