import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def _get_collaborative_scores(self, user_id, n_items=20):
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return pd.Series(0.0, index=self.product_df.index)

    if self.user_item_matrix is None or user_id not in self.user_item_matrix.index:
        return pd.Series(0.0, index=self.product_df.index)

    user_vec = self.user_item_matrix.loc[user_id].values.reshape(1, -1)
    sims = cosine_similarity(user_vec, self.user_item_matrix)[0]
    sim_users = pd.Series(sims, index=self.user_item_matrix.index).nlargest(6).iloc[1:]

    rec = pd.Series(0.0, index=self.user_item_matrix.columns)
    for sim_user, score in sim_users.items():
        rec += self.user_item_matrix.loc[sim_user] * score

    aligned = pd.Series(0.0, index=self.product_df.index)
    aligned.loc[rec.index] = rec
    if aligned.max() > 0:
        aligned /= aligned.max()
    return aligned
