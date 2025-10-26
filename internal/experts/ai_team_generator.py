import numpy as np
import os
from django.conf import settings
from django.db.models import Avg, Count, Q
from sentence_transformers import SentenceTransformer, util
from system.users.models import User
from shared.projects.models import Project, ProjectEvaluation


class AITeamGenerator:
    """
    AI-powered team generation using semantic similarity and user metrics.
    """
    
    # Weights for scoring - balanced approach with semantic priority
    SEMANTIC_WEIGHT = 0.55  # Combined degree + expertise matching
    RATING_WEIGHT = 0.30    # Past performance quality
    AVAILABILITY_WEIGHT = 0.15  # Current workload
    
    # Minimum semantic similarity threshold (0-1 scale)
    MIN_SEMANTIC_SCORE = 0.25  # Reject matches below 25% similarity
    
    # Model path
    MODEL_NAME = 'all-MiniLM-L6-v2'
    MODEL_CACHE_DIR = os.path.join(settings.BASE_DIR, 'internal', 'experts', 'ai_model')
    
    def __init__(self):
        """Initialize the sentence transformer model."""
        self.model = None
    
    def _load_model(self):
        """Lazy load the model only when needed."""
        if self.model is None:
            # Ensure cache directory exists
            os.makedirs(self.MODEL_CACHE_DIR, exist_ok=True)
            self.model = SentenceTransformer(self.MODEL_NAME, cache_folder=self.MODEL_CACHE_DIR)
        return self.model
    
    def _normalize(self, values):
        """
        Normalize a list of values to 0-1 range.
        If all values are the same, returns 0.5 for all (neutral).
        """
        values = np.array(values, dtype=float)
        min_val = np.min(values)
        max_val = np.max(values)
        
        if max_val != min_val:
            return (values - min_val) / (max_val - min_val)
        # If all values are the same, return neutral score instead of 0
        return np.full_like(values, 0.5)
    
    def _normalize_rating(self, avg_rating):
        """
        Convert average rating to 0-1 scale.
        Rating is 1-5, so: (rating - 1) / 4
        5.0 rating = 1.0 (best)
        3.0 rating = 0.5 (neutral)
        1.0 rating = 0.0 (worst)
        """
        return (avg_rating - 1.0) / 4.0
    
    def _calculate_availability_score(self, total_projects, ongoing_projects):
        """
        Calculate availability score based on workload.
        
        Logic:
        - If user has 0 projects: 1.0 (fully available, but might lack experience)
        - If user has projects but none ongoing: 0.9 (good availability)
        - For each ongoing project, reduce availability
        
        Formula: max(0, 1.0 - (ongoing / max(total, 1)) * 0.5)
        
        Examples:
        - 0 ongoing out of 5 total: 1.0 (fully available)
        - 1 ongoing out of 5 total: 0.9 (very available)
        - 3 ongoing out of 5 total: 0.7 (moderately available)
        - 5 ongoing out of 5 total: 0.5 (busy, but still available)
        """
        if total_projects == 0:
            return 1.0
        
        # Calculate workload ratio
        workload_ratio = ongoing_projects / max(total_projects, 1)
        
        # Reduce availability based on workload (max reduction is 0.5, so min score is 0.5)
        availability = max(0.5, 1.0 - (workload_ratio * 0.5))
        
        return availability
    
    def generate_team(self, keywords, campus_filter=None, college_filter=None, num_participants=5):
        """
        Generate optimal team based on keywords and filters.
        
        Args:
            keywords (str): Keywords to match against degree and expertise
            campus_filter (str): Campus code to filter by (optional)
            college_filter (int): College ID to filter by (optional)
            num_participants (int): Number of team members to return
            
        Returns:
            list: List of dictionaries containing user data and scores
        """
        # Load model
        model = self._load_model()
        
        # Fetch expert users
        users = User.objects.filter(is_expert=True)
        
        # Apply filters
        if campus_filter:
            users = users.filter(campus=campus_filter)
        if college_filter:
            users = users.filter(college_id=college_filter)
        
        if not users.exists():
            return []
        
        # Prepare data
        user_data = []
        for user in users:
            # Get projects where user is leader or provider
            user_projects = Project.objects.filter(
                Q(project_leader=user) | Q(providers=user)
            ).distinct()
            
            # Count total projects and ongoing projects
            total_projects = user_projects.count()
            ongoing_projects = user_projects.filter(
                status__in=['NOT_STARTED', 'IN_PROGRESS']
            ).count()
            
            # Get average rating from project evaluations
            # Get all projects this user is involved in
            project_ids = user_projects.values_list('id', flat=True)
            avg_rating = ProjectEvaluation.objects.filter(
                project_id__in=project_ids
            ).aggregate(Avg('rating'))['rating__avg'] or 0
            
            user_data.append({
                'id': user.id,
                'user': user,
                'name': user.get_full_name(),
                'campus': user.get_campus_display() if user.campus else '',
                'college': user.college.name if user.college else '',
                'degree': user.degree or '',
                'expertise': user.expertise or '',
                'total_projects': total_projects,
                'ongoing_projects': ongoing_projects,
                'avg_rating': avg_rating,
            })
        
        if not user_data:
            return []
        
        # Compute semantic similarity
        keyword_embedding = model.encode(keywords, convert_to_tensor=True)
        
        # Combine degree and expertise for better semantic matching
        combined_texts = [
            f"{u['degree']} {u['expertise']}" for u in user_data
        ]
        
        combined_embeddings = model.encode(combined_texts, convert_to_tensor=True)
        semantic_scores = util.cos_sim(keyword_embedding, combined_embeddings)[0].cpu().numpy()
        
        # Filter out users below minimum semantic threshold
        filtered_data = []
        for i, user in enumerate(user_data):
            if semantic_scores[i] >= self.MIN_SEMANTIC_SCORE:
                user['semantic_score'] = float(semantic_scores[i])
                filtered_data.append(user)
        
        if not filtered_data:
            return []
        
        user_data = filtered_data
        
        # Calculate rating scores (0-1 scale where 1 is best)
        for user in user_data:
            user['normalized_rating'] = self._normalize_rating(user['avg_rating'])
            user['availability_score'] = self._calculate_availability_score(
                user['total_projects'], 
                user['ongoing_projects']
            )
        
        # Compute final scores
        for user in user_data:
            user['final_score'] = (
                user['semantic_score'] * self.SEMANTIC_WEIGHT +
                user['normalized_rating'] * self.RATING_WEIGHT +
                user['availability_score'] * self.AVAILABILITY_WEIGHT
            )
        
        # Sort by final score and return top N
        user_data.sort(key=lambda x: x['final_score'], reverse=True)
        
        return user_data[:num_participants]


# Singleton instance
_generator = None

def get_team_generator():
    """Get or create the team generator singleton."""
    global _generator
    if _generator is None:
        _generator = AITeamGenerator()
    return _generator
