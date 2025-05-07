import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_recency_scores(self, category_weights, brand_weights, n_items=20):
    

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
    
    diversity_boost = pd.Series(0.2, index=self.product_df.index)
    
    scores += diversity_boost

    if scores.max() > 0:
        scores /= scores.max()

    return scores

