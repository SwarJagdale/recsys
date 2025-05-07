"""Interface module for HybridRecommender package"""

from .base import RecommenderInterface
from .core import HybridRecommender
from .recency import get_recency_scores
from .collaborative import _get_collaborative_scores
from .context import get_context_recommendations
from .demographic import get_demographic_recommendations

# bind strategies into the class with proper naming convention
HybridRecommender._get_recency_scores = get_recency_scores
HybridRecommender._get_collaborative_scores = _get_collaborative_scores
HybridRecommender._get_context_recommendations = get_context_recommendations
HybridRecommender._get_demographic_recommendations = get_demographic_recommendations

_recommender = HybridRecommender()

def init_app(app):
    """Initialize the recommender with Flask app"""
    _recommender.init_app(app)

def recommend(user_id, k=20):
    """Get recommendations for a user"""
    return _recommender.recommend(user_id, k)

def add_recommender_interaction(user_id, product_id, interaction_type):
    """Add a new interaction and update recommendations"""
    _recommender.add_interaction(user_id, product_id, interaction_type)
