import pandas as pd

def get_demographic_recommendations(self, user_id, n_items=20):
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return pd.Series(0.0, index=self.product_df.index)

    user = self.db.users.find_one({'user_id': user_id})
    if not user or 'location' not in user:
        return pd.Series(0.0, index=self.product_df.index)

    loc = user['location']
    loc_users = list(self.db.users.find({'location': loc}))
    ids = [int(u['user_id']) for u in loc_users]  # Convert to int to ensure type consistency
    
    # Lower the threshold for using pure location-based recommendations
    if len(ids) < 5:  # Reduced from 10 to 5
        all_users = list(self.db.users.find())
        all_ids = [int(u['user_id']) for u in all_users]
        int_df = pd.DataFrame(list(self.db.interactions.find({'user_id': {'$in': all_ids}})))
        if not int_df.empty:
            # Add stronger location boost for users from the same location
            int_df['location_boost'] = 0.2  # Lower base weight for non-location users
            int_df.loc[int_df['user_id'].isin(ids), 'location_boost'] = 8.0  # 40x relative boost
    else:
        # Only use interactions from this location's users
        int_df = pd.DataFrame(list(self.db.interactions.find({'user_id': {'$in': ids}})))
    
    if int_df.empty:
        return pd.Series(0.0, index=self.product_df.index)

    int_df['product_id'] = pd.to_numeric(int_df['product_id'])
    weights = {'view': 1, 'add_to_cart': 3, 'purchase': 5}
    int_df['weight'] = int_df['interaction_type'].map(weights)
    
    # Apply location boost if it exists
    if 'location_boost' in int_df.columns:
        int_df['weight'] = int_df['weight'] * int_df['location_boost']
    
    # Add location-specific category boost
    try:
        # Get popular categories in this location
        cat_popularity = int_df.merge(
            self.product_df[['category']], 
            left_on='product_id',
            right_index=True
        ).groupby('category')['weight'].sum()
        
        # Apply location-specific category boost
        for cat, weight in cat_popularity.nlargest(3).items():
            cat_mask = self.product_df['category'] == cat
            int_df.loc[int_df['product_id'].isin(self.product_df[cat_mask].index), 'weight'] *= 1.5
    except:
        pass  # Skip if we can't get categories
        
    scores = int_df.groupby('product_id')['weight'].sum()
    aligned = pd.Series(0.0, index=self.product_df.index)
    aligned.loc[scores.index] = scores
    if aligned.max() > 0:
        aligned /= aligned.max()
    return aligned
