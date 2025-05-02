import numpy as np
from datetime import datetime
from collections import defaultdict, deque

def sigmoid(x):
    x = np.clip(x, -50, 50)
    return 1 / (1 + np.exp(-x))


class MatrixFactorization:
    def __init__(
        self,
        n_users: int,
        n_items: int,
        item_metadata: dict,
        n_factors: int = 20,
        lr: float = 0.01,
        reg: float = 0.1,
        epochs: int = 20,
        recency_alpha: float = 0.101,
        cat_weight: float = 0.6,
        brand_weight: float = 0.2
    ):
        self.n_users = n_users
        self.n_items = n_items
        self.n_factors = n_factors
        self.lr = lr if lr is not None else 0.005  # Lowered default learning rate for stability
        self.reg = reg
        self.epochs = epochs
        self.recency_alpha = recency_alpha
        self.cat_weight = cat_weight
        self.brand_weight = brand_weight

        # Latent factors
        self.user_factors = np.random.normal(scale=0.1, size=(n_users, n_factors))
        self.item_factors = np.random.normal(scale=0.1, size=(n_items, n_factors))

        # Metadata
        self.item_metadata = item_metadata
        # Pre-extract arrays of categories & brands for vectorized boosting
        cats = [item_metadata.get(i, {}).get("category", None) for i in range(n_items)]
        brands = [item_metadata.get(i, {}).get("brand", None)    for i in range(n_items)]
        self.item_categories = np.array(cats, dtype=object)
        self.item_brands     = np.array(brands, dtype=object)

        # Per‐user recent history (deque auto‐caps at 10 items)
        self.user_recent_cats   = defaultdict(lambda: deque(maxlen=10))
        self.user_recent_brands = defaultdict(lambda: deque(maxlen=10))

    def recency_weight(self, ts):
        """Compute exponential decay weight for a timestamp."""
        if ts is None:
            return 1.0
        now = datetime.utcnow().timestamp()
        t = ts.timestamp() if isinstance(ts, datetime) else ts
        exp_arg = -self.recency_alpha * (now - t)
        exp_arg = np.clip(exp_arg, -50, 50)
        return np.exp(exp_arg)

    def _sgd_update(self, u, i, weight):
        """Single SGD update on user u and item i with given sample weight."""
        # Debug: Check for NaNs/Infs before update
        if (np.isnan(self.user_factors[u]).any() or np.isnan(self.item_factors[i]).any() or
            np.isinf(self.user_factors[u]).any() or np.isinf(self.item_factors[i]).any()):
            print(f"[WARN] NaN/Inf detected in factors BEFORE update for user {u}, item {i}. Repairing...")
            self.user_factors[u] = np.nan_to_num(self.user_factors[u], nan=0.0, posinf=0.1, neginf=-0.1)
            self.item_factors[i] = np.nan_to_num(self.item_factors[i], nan=0.0, posinf=0.1, neginf=-0.1)

        pred = sigmoid(self.user_factors[u].dot(self.item_factors[i]))
        err = weight * (1 - pred)
        # gradients
        grad_u = err * self.item_factors[i] - self.reg * self.user_factors[u]
        grad_i = err * self.user_factors[u]    - self.reg * self.item_factors[i]
        # Gradient clipping
        grad_u = np.clip(grad_u, -1.0, 1.0)
        grad_i = np.clip(grad_i, -1.0, 1.0)
        # apply updates
        self.user_factors[u] += self.lr * grad_u
        self.item_factors[i] += self.lr * grad_i
        # Debug: Check for NaNs/Infs after update
        if (np.isnan(self.user_factors[u]).any() or np.isnan(self.item_factors[i]).any() or
            np.isinf(self.user_factors[u]).any() or np.isinf(self.item_factors[i]).any()):
            print(f"[WARN] NaN/Inf detected in factors AFTER update for user {u}, item {i}. Repairing...")
            self.user_factors[u] = np.nan_to_num(self.user_factors[u], nan=0.0, posinf=0.1, neginf=-0.1)
            self.item_factors[i] = np.nan_to_num(self.item_factors[i], nan=0.0, posinf=0.1, neginf=-0.1)

    def train(self, interactions):
        """
        interactions: list of (user_idx, item_idx, timestamp)
        """
        for epoch in range(self.epochs):
            np.random.shuffle(interactions)
            for u, i, ts in interactions:
                w = self.recency_weight(ts)
                self._sgd_update(u, i, w)

                # update recent history
                meta = self.item_metadata.get(i, {})
                cat   = meta.get("category", None)
                brand = meta.get("brand",    None)
                if cat is not None:
                    self.user_recent_cats[u].append(cat)
                if brand is not None:
                    self.user_recent_brands[u].append(brand)

    def recommend(self, u, k=9, interacted=set()):
        """
        Return top-k item indices for user u, excluding any in `interacted`.
        """
        # 1) Base scores via MF
        scores = sigmoid(self.item_factors.dot(self.user_factors[u]))
        # Debug: Check for NaNs/Infs in scores
        if np.isnan(scores).any() or np.isinf(scores).any():
            print(f"[WARN] NaN/Inf detected in recommendation scores for user {u}. Repairing...")
            scores = np.nan_to_num(scores, nan=0.0, posinf=1.0, neginf=0.0)
        print(scores)
        # 2) Hybrid boosting (vectorized)
        recent_cats   = set(self.user_recent_cats.get(u, []))
        recent_brands = set(self.user_recent_brands.get(u, []))
        if recent_cats:
            mask_cat = np.isin(self.item_categories, list(recent_cats))
            scores[mask_cat] += self.cat_weight
        if recent_brands:
            mask_brand = np.isin(self.item_brands, list(recent_brands))
            scores[mask_brand] += self.brand_weight

        # 3) Exclude already interacted
        if interacted:
            scores[list(interacted)] = -np.inf

        # 4) Top-k via argpartition
        top_k = np.argpartition(-scores, k)[:k]
        print([(a,b) for a,b in zip(top_k,scores[:k])])
        return top_k[np.argsort(-scores[top_k])]
        # if recent_brands:
        #     mask_brand = np.isin(self.item_brands, list(recent_brands))
        #     scores[mask_brand] += self.brand_weight

        # # 3) Exclude already interacted
        # if interacted:
        #     scores[list(interacted)] = -np.inf

        # # 4) Top-k via argpartition
        # top_k = np.argpartition(-scores, k)[:k]
        # print([(a,b) for a,b in zip(top_k,scores[:k])])
        # return top_k[np.argsort(-scores[top_k])]

    def update_one(self, u, i, interacted_update, ts=None, n_steps=10):
        """
        Incremental update for a single (u, i) interaction.
        - interacted_update: dict mapping user -> set of items they've seen
        """
        w = self.recency_weight(ts)
        for _ in range(n_steps):
            self._sgd_update(u, i, w)

        # Update recent history
        meta = self.item_metadata.get(i, {})
        cat   = meta.get("category", None)
        brand = meta.get("brand",    None)
        if cat is not None:
            self.user_recent_cats[u].append(cat)
        if brand is not None:
            self.user_recent_brands[u].append(brand)

        # Mark as interacted
        if u in interacted_update:
            interacted_update[u].add(i)
        else:
            interacted_update[u] = {i}
