import pandas as pd
import numpy as np
from pymongo import MongoClient
from .base import RecommenderInterface

class HybridRecommender(RecommenderInterface):
    def __init__(self):
        self.user_item_matrix = None
        self.product_df = None
        self.mongo = None
        self.recency_weight = 0.6
        self.collab_weight = 0.4

    def init_app(self, app):
        self.mongo = MongoClient(app.config["MONGO_URI"])
        self.db = self.mongo.get_database()
        self._update_matrices()

    def _update_matrices(self):
        interactions = pd.DataFrame(list(self.db.interactions.find()))
        products = pd.DataFrame(list(self.db.products.find()))

        if not interactions.empty:
            interactions['product_id'] = pd.to_numeric(interactions['product_id'])
            weights = {'view': 1, 'add_to_cart': 3, 'purchase': 5}
            interactions['weight'] = interactions['interaction_type'].map(weights)
            self.user_item_matrix = interactions.pivot_table(
                index='user_id',
                columns='product_id',
                values='weight',
                aggfunc='sum',
                fill_value=0
            )

        if not products.empty:
            products['product_id'] = pd.to_numeric(products['product_id'])
            self.product_df = products.set_index('product_id')

    def recommend(self, user_id, k=20):
        """Generate hybrid recommendations for a user"""
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            print(f"Invalid user_id format: {user_id}")
            return pd.DataFrame()

        # Check if user has any interactions
        user_interactions = self.db.interactions.find_one({'user_id': user_id})
        
        if not user_interactions:
            # New user - use demographic and context recommendations
            demographic_scores = self._get_demographic_recommendations(user_id, k)
            context_scores = self._get_context_recommendations(user_id, k)
            
            # Track which strategy gave higher score for each product
            recommendation_sources = pd.Series('demographic', index=demographic_scores.index)
            context_wins = context_scores > demographic_scores
            recommendation_sources[context_wins] = 'context'
            
            # Combine scores with weights
            scores = demographic_scores * 0.7 + context_scores * 0.3
        else:
            # Get scores from each strategy
            collab_scores = self._get_collaborative_scores(user_id, k)
            recency_scores = self._get_recency_scores(user_id, k)
            
            # Get top 10 from each strategy
            ITEMS_PER_STRATEGY = 10
            top_collab = collab_scores.nlargest(ITEMS_PER_STRATEGY)
            
            # Remove collaborative items from recency scores to avoid duplicates
            recency_scores[top_collab.index] = 0
            top_recency = recency_scores.nlargest(ITEMS_PER_STRATEGY)
            
            # Combine scores and mark sources
            scores = pd.Series(0, index=self.product_df.index)
            recommendation_sources = pd.Series('', index=self.product_df.index)
            
            # Add collaborative recommendations
            scores[top_collab.index] = top_collab
            recommendation_sources[top_collab.index] = 'collaborative'
            
            # Add recency recommendations
            scores[top_recency.index] = top_recency
            recommendation_sources[top_recency.index] = 'recency'

        # Get top k recommendations
        if scores.empty:
            return pd.DataFrame()
            
        try:
            top_products = scores.nlargest(k).index
            recommendations = self.product_df.loc[top_products].copy()
            recommendations['score'] = scores[top_products]
            recommendations['recommendation_source'] = recommendation_sources[top_products]
            return recommendations.sort_values('score', ascending=False)
            
        except KeyError:
            print("Error accessing product information")
            return pd.DataFrame(columns=self.product_df.columns.tolist() + ['score', 'recommendation_source'])

