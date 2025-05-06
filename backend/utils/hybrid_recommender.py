import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient
from bson import ObjectId

class HybridRecommender:
    def __init__(self):
        self.user_item_matrix = None
        self.product_df = None
        self.mongo = None
        self.recency_weight = 0.6  # 60% weight for recency
        self.collab_weight = 0.4   # 40% weight for collaborative filtering

    def init_app(self, app):
        """Initialize with MongoDB connection"""
        self.mongo = MongoClient(app.config["MONGO_URI"])
        self.db = self.mongo.get_database()
        self._update_matrices()

    def _update_matrices(self):
        """Update user-item interaction matrix and product dataframe"""
        interactions = pd.DataFrame(list(self.db.interactions.find()))
        products = pd.DataFrame(list(self.db.products.find()))
        
        if not interactions.empty:
            interactions['product_id'] = pd.to_numeric(interactions['product_id'])
            weights = {
                'view': 1,
                'add_to_cart': 3,
                'purchase': 5
            }
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

    def _get_recency_scores(self, user_id, n_items=20):
        """Calculate recency-based scores with smooth diversity and time decay"""
        recent_cutoff = datetime.now() - timedelta(minutes=3)  # Extended to 30 days
        
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            print(f"Invalid user_id format: {user_id}")
            return pd.Series(index=self.product_df.index)

        recent_interactions = pd.DataFrame(list(self.db.interactions.find({
            'user_id': user_id,
            'timestamp': {'$gte': recent_cutoff}
        }).sort('timestamp', -1)))

        if recent_interactions.empty:
            return pd.Series(index=self.product_df.index)

        recent_interactions['product_id'] = pd.to_numeric(recent_interactions['product_id'])
        
        try:
            recent_interactions['timestamp'] = pd.to_datetime(recent_interactions['timestamp'])
            now = datetime.now()
            time_diff_secs = (now - recent_interactions['timestamp']).dt.total_seconds()
            recent_interactions['time_decay'] = np.exp(-0.05 * time_diff_secs)
            
            weights = {
                'view': 1,
                'add_to_cart': 3,
                'purchase': 5
            }
            recent_interactions['weight'] = recent_interactions['interaction_type'].map(weights)
            recent_interactions['final_weight'] = recent_interactions['time_decay'] * recent_interactions['weight']
            
            category_weights = recent_interactions.merge(
                self.product_df, left_on='product_id', right_index=True
            ).groupby('category')['final_weight'].sum()
            
            brand_weights = recent_interactions.merge(
                self.product_df, left_on='product_id', right_index=True
            ).groupby('brand')['final_weight'].sum()
            
            scores = pd.Series(0.0, index=self.product_df.index)
            
            for category, weight in category_weights.items():
                category_mask = self.product_df['category'] == category
                scores[category_mask] += np.log1p(weight) * 0.3
                
                other_categories = self.product_df[~category_mask]['category'].unique()
                for other_cat in other_categories:
                    other_cat_mask = self.product_df['category'] == other_cat
                    scores[other_cat_mask] += np.random.uniform(0.05, 0.15, size=other_cat_mask.sum())

            for brand, weight in brand_weights.items():
                brand_mask = self.product_df['brand'] == brand
                scores[brand_mask] += np.log1p(weight) * 0.25
                
                other_brands_mask = self.product_df['brand'] != brand
                scores[other_brands_mask] += np.random.uniform(0.03, 0.1, size=other_brands_mask.sum())

            exploration_factor = np.random.uniform(0.03, 0.1, size=len(scores))
            scores += exploration_factor

            recent_product_ids = set(recent_interactions['product_id'])
            diversity_boost = pd.Series(0.2, index=self.product_df.index)
            diversity_boost[list(recent_product_ids)] = 0
            scores += diversity_boost

            if not scores.empty and scores.max() > 0:
                scores = scores / scores.max()
            return scores

        except KeyError:
            return pd.Series(index=self.product_df.index)

    def _get_collaborative_scores(self, user_id, n_items=20):
        """Calculate collaborative filtering scores"""
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            print(f"Invalid user_id format: {user_id}")
            return pd.Series(index=self.product_df.index)

        if self.user_item_matrix is None or user_id not in self.user_item_matrix.index:
            return pd.Series(index=self.product_df.index)

        user_vector = self.user_item_matrix.loc[user_id].values.reshape(1, -1)
        similarities = cosine_similarity(user_vector, self.user_item_matrix)
        similar_users = pd.Series(similarities[0], index=self.user_item_matrix.index)
        similar_users = similar_users.sort_values(ascending=False)[1:6]  # Top 5 similar users

        recommendations = pd.Series(0, index=self.user_item_matrix.columns)
        for sim_user, sim_score in similar_users.items():
            recommendations += self.user_item_matrix.loc[sim_user] * sim_score

        aligned_recommendations = pd.Series(0, index=self.product_df.index)
        try:
            aligned_recommendations[recommendations.index] = recommendations.values
        except KeyError:
            pass
        
        return aligned_recommendations / aligned_recommendations.max() if not aligned_recommendations.empty else aligned_recommendations

    def _get_context_recommendations(self, user_id, n_items=20):
        """Get recommendations based on context when user has no history"""
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            print(f"Invalid user_id format: {user_id}")
            return pd.Series(index=self.product_df.index)

        context = self.db.context.find_one({'user_id': user_id})
        if not context:
            interactions = pd.DataFrame(list(self.db.interactions.find()))
            if interactions.empty:
                return pd.Series(index=self.product_df.index)
            
            interactions['product_id'] = pd.to_numeric(interactions['product_id'])
            popular_products = interactions['product_id'].value_counts()
            
            aligned_scores = pd.Series(0, index=self.product_df.index)
            try:
                aligned_scores[popular_products.index] = popular_products.values
            except KeyError:
                pass
            return aligned_scores / aligned_scores.max() if not aligned_scores.empty else aligned_scores

        context_interactions = pd.DataFrame(list(self.db.interactions.find({
            'context.time_of_day': context.get('time_of_day'),
            'context.device': context.get('device'),
            'context.location': context.get('location')
        })))

        if context_interactions.empty:
            return pd.Series(index=self.product_df.index)

        context_interactions['product_id'] = pd.to_numeric(context_interactions['product_id'])
        context_scores = context_interactions['product_id'].value_counts()
        
        aligned_scores = pd.Series(0, index=self.product_df.index)
        try:
            aligned_scores[context_scores.index] = context_scores.values
        except KeyError:
            pass
        return aligned_scores / aligned_scores.max() if not aligned_scores.empty else aligned_scores

    def _get_demographic_recommendations(self, user_id, n_items=20):
        """Get recommendations based on user's location demographics"""
        try:
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                print(f"Invalid user_id format: {user_id}")
                return pd.Series(index=self.product_df.index)

            user = self.db.users.find_one({'user_id': user_id})
            if not user or not user.get('location'):
                return pd.Series(index=self.product_df.index)

            user_location = user['location']
            location_users = list(self.db.users.find({'location': user_location}))
            location_user_ids = [u['user_id'] for u in location_users]
            
            location_interactions = pd.DataFrame(list(self.db.interactions.find({
                'user_id': {'$in': location_user_ids}
            })))
            
            if location_interactions.empty:
                return pd.Series(index=self.product_df.index)
            
            location_interactions['product_id'] = pd.to_numeric(location_interactions['product_id'])
            
            weights = {
                'view': 1,
                'add_to_cart': 3,
                'purchase': 5
            }
            location_interactions['weight'] = location_interactions['interaction_type'].map(weights)
            
            product_scores = location_interactions.groupby('product_id')['weight'].sum()
            
            aligned_scores = pd.Series(0, index=self.product_df.index)
            try:
                aligned_scores[product_scores.index] = product_scores.values
            except KeyError:
                pass
                
            return aligned_scores / aligned_scores.max() if not aligned_scores.empty else aligned_scores
                
        except Exception as e:
            print(f"Error in demographic recommendations: {str(e)}")
            return pd.Series(index=self.product_df.index)

    def recommend(self, user_id, k=20):
        """Generate hybrid recommendations for a user"""
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            print(f"Invalid user_id format: {user_id}")
            return pd.DataFrame()

        user_interactions = self.db.interactions.find_one({'user_id': user_id})
        if not user_interactions:
            demographic_scores = self._get_demographic_recommendations(user_id, k)
            context_scores = self._get_context_recommendations(user_id, k)
            
            recommendation_sources = pd.Series('demographic', index=demographic_scores.index)
            context_wins = context_scores > demographic_scores
            recommendation_sources[context_wins] = 'context'
            
            scores = demographic_scores * 0.7 + context_scores * 0.3
        else:
            collab_scores = self._get_collaborative_scores(user_id, k)
            recency_scores = self._get_recency_scores(user_id, k)
            
            ITEMS_PER_STRATEGY = 10
            top_collab = collab_scores.nlargest(ITEMS_PER_STRATEGY)
            
            recency_scores[top_collab.index] = 0
            top_recency = recency_scores.nlargest(ITEMS_PER_STRATEGY)
            
            scores = pd.Series(0, index=self.product_df.index)
            recommendation_sources = pd.Series('', index=self.product_df.index)
            
            scores[top_collab.index] = top_collab
            recommendation_sources[top_collab.index] = 'collaborative'
            
            scores[top_recency.index] = top_recency
            recommendation_sources[top_recency.index] = 'recency'

        if scores.empty:
            return pd.DataFrame()
            
        try:
            top_products = scores.nlargest(k).index
            recommendations = self.product_df.loc[top_products].copy()
            recommendations['score'] = scores[top_products]
            recommendations['recommendation_source'] = recommendation_sources[top_products]
            return recommendations.sort_values('score', ascending=False)
            
        except KeyError:
            return pd.DataFrame(columns=self.product_df.columns.tolist() + ['score', 'recommendation_source'])

    def add_interaction(self, user_id, product_id, interaction_type):
        """Update recommendations when new interaction occurs"""
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            print(f"Invalid user_id format: {user_id}")
            return

        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            print(f"Invalid product_id format: {product_id}")
            return

        interaction = {
            'user_id': user_id,
            'product_id': product_id,
            'interaction_type': interaction_type,
            'timestamp': datetime.now()
        }
        self.db.interactions.insert_one(interaction)
        self._update_matrices()

# Global instance
_recommender = HybridRecommender()

def init_app(app):
    """Initialize the recommender with the Flask app"""
    _recommender.init_app(app)

def recommend(user_id, k=20):
    """Get recommendations for a user"""
    return _recommender.recommend(user_id, k)

def add_recommender_interaction(user_id, product_id, interaction_type):
    """Add a new interaction and update recommendations"""
    _recommender.add_interaction(user_id, product_id, interaction_type)