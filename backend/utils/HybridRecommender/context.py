import pandas as pd

def get_context_recommendations(self, user_id, n_items=20):
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return pd.Series(0.0, index=self.product_df.index)

    context = self.db.context.find_one({'user_id': user_id})
    if not context:
        interactions = pd.DataFrame(list(self.db.interactions.find()))
        if interactions.empty:
            return pd.Series(0.0, index=self.product_df.index)
        interactions['product_id'] = pd.to_numeric(interactions['product_id'])
        popular = interactions['product_id'].value_counts()
        aligned = pd.Series(0.0, index=self.product_df.index)
        aligned.loc[popular.index] = popular
        if aligned.max() > 0:
            aligned /= aligned.max()
        return aligned

    ctx_int = pd.DataFrame(list(self.db.interactions.find({
        'context.time_of_day': context['time_of_day'],
        'context.device': context['device'],
        'context.location': context['location']
    })))
    if ctx_int.empty:
        return pd.Series(0.0, index=self.product_df.index)

    ctx_int['product_id'] = pd.to_numeric(ctx_int['product_id'])
    counts = ctx_int['product_id'].value_counts()
    aligned = pd.Series(0.0, index=self.product_df.index)
    aligned.loc[counts.index] = counts
    if aligned.max() > 0:
        aligned /= aligned.max()
    return aligned
