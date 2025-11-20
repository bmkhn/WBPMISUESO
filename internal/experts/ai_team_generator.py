import numpy as np
import os
from django.conf import settings
from django.db.models import Q
from sentence_transformers import SentenceTransformer, util
from system.users.models import User
from shared.projects.models import Project


class AITeamGenerator:
    """
    AI-powered team generation using semantic similarity between:
    - Degree
    - Expertise
    - Project Titles (softmax-based multi-title scoring)
    """

    # Scoring Weights
    DEGREE_WEIGHT = 0.25
    EXPERTISE_WEIGHT = 0.35
    PROJECT_WEIGHT = 0.40

    # Minimum semantic similarity (0–1)
    MIN_SEMANTIC_SCORE = 0.20

    MODEL_NAME = 'all-MiniLM-L6-v2'
    MODEL_CACHE_DIR = os.path.join(settings.BASE_DIR, 'internal', 'experts', 'ai_model')


    def __init__(self):
        self.model = None


    # Load or get cached model
    def _load_model(self):
        if self.model is None:
            os.makedirs(self.MODEL_CACHE_DIR, exist_ok=True)
            self.model = SentenceTransformer(self.MODEL_NAME, cache_folder=self.MODEL_CACHE_DIR)
        return self.model
    

    # Softmax function for multi-title scoring
    def _softmax(self, x):
        x = np.array(x)
        exp = np.exp(x - np.max(x))
        return exp / exp.sum()


    # Cosine similarity between two embeddings
    def _sim(self, emb1, emb2):
        """Cosine similarity returning float."""
        return float(util.cos_sim(emb1, emb2)[0][0])


    # Score project titles with softmax-weighted similarity
    def _score_project_titles(self, keyword_emb, project_titles, model):
        """
        Softmax-weighted similarity over multiple project titles.
        """
        if not project_titles:
            return 0.0

        # Encode each title individually
        title_embs = model.encode(project_titles, convert_to_tensor=True)

        # Compute similarity for each title
        sims = [
            float(util.cos_sim(keyword_emb, t_emb)[0][0])
            for t_emb in title_embs
        ]

        # Softmax weights
        weights = self._softmax(sims)

        # Weighted score
        final_score = float(np.sum(np.array(sims) * weights))

        return final_score


    # Generate team method
    def generate_team(self, keywords, include_in_progress=False, campus_filter=None, college_filter=None, num_participants=5):
        """
        Generate team based on degree, expertise, and project titles.
        """
        model = self._load_model()
        keyword_emb = model.encode(keywords, convert_to_tensor=True)

        # ============================================================================
        # 1. Fetch Expert Users - must be is_expert=True and have an eligible role
        # ============================================================================

        eligible_roles = ['FACULTY', 'PROGRAM_HEAD', 'DEAN', 'COORDINATOR', 'DIRECTOR', 'VP']

        users = User.objects.filter(
            is_expert=True,
            role__in=eligible_roles
        )

        if campus_filter:
            try:
                campus_id = int(campus_filter)
                users = users.filter(college__campus_id=campus_id)
            except Exception:
                pass

        if college_filter:
            users = users.filter(college_id=college_filter)


        # ============================================================================
        # 2. Pre-fetch Projects for Users
        # ============================================================================

        project_map = {}

        all_projects = Project.objects.filter(
            Q(project_leader__in=users) | Q(providers__in=users)
        ).distinct()


        for p in all_projects.select_related("project_leader").prefetch_related("providers"):
            # Leader
            if p.project_leader_id:
                project_map.setdefault(p.project_leader_id, []).append(p)

            # Providers
            for provider in p.providers.all():
                project_map.setdefault(provider.id, []).append(p)


        # ============================================================================
        # 3. Process Each User
        # ============================================================================

        results = []

        for user in users:
            user_projects = project_map.get(user.id, [])

            # Filter: include users with ongoing projects?
            if not include_in_progress:
                # Strictly exclude users with any in-progress projects
                if any(p.status == "IN_PROGRESS" or p.status == "NOT_STARTED" for p in user_projects):
                    continue
                user_projects = [p for p in user_projects if p.status == "COMPLETED"]

            # User must still have at least 1 project
            if len(user_projects) == 0:
                continue

            # Gather data
            degree_text = user.degree or ""
            expertise_text = user.expertise or ""
            project_titles = [p.title for p in user_projects if p.title]

            # Encode main fields
            degree_emb = model.encode(degree_text, convert_to_tensor=True)
            expertise_emb = model.encode(expertise_text, convert_to_tensor=True)

            # ========================================================================
            # 4. Similarity Scoring
            # ========================================================================

            degree_score = self._sim(keyword_emb, degree_emb)
            expertise_score = self._sim(keyword_emb, expertise_emb)
            project_score = self._score_project_titles(keyword_emb, project_titles, model)

            # Reject if ALL signals are too weak
            if max(degree_score, expertise_score, project_score) < self.MIN_SEMANTIC_SCORE:
                continue

            final_score = (
                degree_score * self.DEGREE_WEIGHT +
                expertise_score * self.EXPERTISE_WEIGHT +
                project_score * self.PROJECT_WEIGHT
            )

            # Calculate per-project relevance scores
            project_details = []
            for p in user_projects:
                if not p.title:
                    continue
                p_emb = model.encode(p.title, convert_to_tensor=True)
                p_score = self._sim(keyword_emb, p_emb)
                project_details.append({
                    "id": p.id,
                    "title": p.title,
                    "status": p.status,
                    "start_date": p.start_date.strftime("%Y-%m-%d") if p.start_date else None,
                    "relevance_score": p_score,
                    "is_relevant": p_score >= self.MIN_SEMANTIC_SCORE
                })
            
            # Sort projects by relevance score (highest first)
            project_details.sort(key=lambda x: x["relevance_score"], reverse=True)

            results.append({
                "id": user.id,
                "name": user.get_full_name(),
                "user": user,
                "degree": user.degree,
                "expertise": user.expertise,
                "project_titles": project_titles,
                "degree_score": degree_score,
                "expertise_score": expertise_score,
                "project_title_score": project_score,
                "final_score": final_score,

                # Additional Information
                "campus": user.college.campus.name if getattr(user, 'college', None) and getattr(user.college, 'campus', None) and getattr(user.college.campus, 'name', None) else None,
                "college": user.college.name if getattr(user, 'college', None) and getattr(user.college, 'name', None) else None,
                "total_projects": len(user_projects),
                "ongoing_projects": len([p for p in user_projects if p.status == "IN_PROGRESS"]),
                "projects": project_details,
                # DEBUG: Weighted scores for inspection
                "_debug_weighted_scores": {
                    "degree_score": degree_score,
                    "expertise_score": expertise_score,
                    "project_title_score": project_score,
                    "final_score": final_score,
                    "weights": {
                        "degree": self.DEGREE_WEIGHT,
                        "expertise": self.EXPERTISE_WEIGHT,
                        "project": self.PROJECT_WEIGHT
                    }
                },
            })

        # Sort and return top N
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results[:num_participants]


# Singleton Instance
_generator = None

def get_team_generator():
    global _generator
    if _generator is None:
        _generator = AITeamGenerator()
    return _generator