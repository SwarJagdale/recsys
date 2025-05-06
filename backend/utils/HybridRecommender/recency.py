import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_recency_scores(self, user_id, n_items=20):
    recent_cutoff = datetime.now() - timedelta(days=30)
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return pd.Series(0.0, index=self.product_df.index)

    recent_interactions = pd.DataFrame(list(
        self.db.interactions.find({
            'user_id': user_id,
            'timestamp': {'$gte': recent_cutoff}
        }).sort('timestamp', -1)
    ))

    if recent_interactions.empty:
        return pd.Series(0.0, index=self.product_df.index)

    recent_interactions['product_id'] = pd.to_numeric(recent_interactions['product_id'])
    recent_interactions['timestamp'] = pd.to_datetime(recent_interactions['timestamp'])
    now = datetime.now()
    time_diff_secs = (now - recent_interactions['timestamp']).dt.total_seconds()
    recent_interactions['time_decay'] = np.exp(-0.05 * time_diff_secs)

    weights = {'view': 1, 'add_to_cart': 3, 'purchase': 5}
    recent_interactions['weight'] = recent_interactions['interaction_type'].map(weights)
    recent_interactions['final_weight'] = recent_interactions['time_decay'] * recent_interactions['weight']

    # Category and brand aggregation
    category_weights = recent_interactions.merge(
        self.product_df, left_on='product_id', right_index=True
    ).groupby('category')['final_weight'].sum()

    brand_weights = recent_interactions.merge(
        self.product_df, left_on='product_id', right_index=True
    ).groupby('brand')['final_weight'].sum()

    scores = pd.Series(0.0, index=self.product_df.index)

    for category, w in category_weights.items():
        mask = self.product_df['category'] == category
        scores[mask] += np.log1p(w) * 0.3
        for other_cat in self.product_df.loc[~mask, 'category'].unique():
            scores[self.product_df['category'] == other_cat] += np.random.uniform(0.05, 0.15)

    for brand, w in brand_weights.items():
        mask = self.product_df['brand'] == brand
        scores[mask] += np.log1p(w) * 0.25
        scores[self.product_df['brand'] != brand] += np.random.uniform(0.03, 0.1)

    # exploration & diversity
    scores += np.random.uniform(0.03, 0.1, size=len(scores))
    recent_ids = set(recent_interactions['product_id'])
    diversity_boost = pd.Series(0.2, index=self.product_df.index)
    diversity_boost.loc[list(recent_ids)] = 0
    scores += diversity_boost

    if scores.max() > 0:
        scores /= scores.max()

    return scores

