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
    ids = [u['user_id'] for u in loc_users]
    int_df = pd.DataFrame(list(self.db.interactions.find({'user_id': {'$in': ids}})))
    if int_df.empty:
        return pd.Series(0.0, index=self.product_df.index)

    int_df['product_id'] = pd.to_numeric(int_df['product_id'])
    weights = {'view': 1, 'add_to_cart': 3, 'purchase': 5}
    int_df['weight'] = int_df['interaction_type'].map(weights)
    scores = int_df.groupby('product_id')['weight'].sum()
    aligned = pd.Series(0.0, index=self.product_df.index)
    aligned.loc[scores.index] = scores
    if aligned.max() > 0:
        aligned /= aligned.max()
    return aligned
