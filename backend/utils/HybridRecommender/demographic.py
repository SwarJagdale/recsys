import pandas as pd
import numpy as np
from bson import json_util
import json

def get_demographic_recommendations(self, loc, n_items=20):
    
    # Get all interactions and users with proper datetime handling
    int_data = list(self.db.interactions.find())
    users_data = list(self.db.users.find({'location': loc}, {'user_id': 1}))
    
    int_df = pd.DataFrame(int_data)
    users_df = pd.DataFrame(users_data)
    
    # Filter interactions for users in the specified location
    int_df = int_df[int_df['user_id'].isin(users_df['user_id'])]
    
    #merge with products
    products_df = pd.DataFrame(list(self.db.products.find()))
    products_df['product_id'] = pd.to_numeric(products_df['product_id'])
    products_df = products_df.set_index('product_id')
    int_df = int_df.merge(products_df, left_on='product_id', right_index=True)
    
    # Assign weights based on interaction type
    interaction_weights = {
        'purchase': 3.0,    # Highest weight for purchases
        'add_to_cart': 2.0, # Medium weight for add to cart
        'view': 1.0        # Base weight for views
    }
    
    # Create weight column based on interaction type
    int_df['weight'] = int_df['interaction_type'].map(interaction_weights)
    
    # 1) Compute category weights
    cat_pop = int_df.groupby('category')['weight'].sum()
    cat_weights = cat_pop / cat_pop.sum()
    
    # 2) Allocate each category an integer number of slots
    cat_counts = (cat_weights * n_items).round().astype(int)
    
    # 3) Correct rounding so total = n_items
    diff = n_items - cat_counts.sum()
    if diff > 0:
        # Give extra slots to top categories
        for cat in cat_weights.nlargest(diff).index:
            cat_counts[cat] += 1
    elif diff < 0:
        # Remove slots from smallest-weight categories
        for cat in cat_weights.nsmallest(-diff).index:
            cat_counts[cat] -= 1
    
    # 4) For each category, pick the top-weighted products
    recommended_products = []
    for cat, cnt in cat_counts.items():
        if cnt <= 0:
            continue
        # Get products in category, weighted by interaction
        prod_weights = (
            int_df[int_df['category']==cat]
            .groupby('product_id')['weight']
            .sum()
        )
        if prod_weights.empty:
            # Fallback: take any cnt products at random
            picks = products_df[products_df['category']==cat].sample(cnt).index.tolist()
        else:
            # Deterministic: choose top cnt products
            picks = prod_weights.nlargest(cnt).index.tolist()
        recommended_products.extend(picks)
    
    # 5) Get full product details from MongoDB
    product_details = []
    for product_id in recommended_products:
        product = self.db.products.find_one({'product_id': product_id}, {'_id': 0})
        if product:
            product_details.append(product)
    
    # Convert to DataFrame
    recommendations_df = pd.DataFrame(product_details)
    
    print(recommendations_df)
    return recommendations_df
    
