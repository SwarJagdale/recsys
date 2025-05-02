import numpy as np
from collections import defaultdict

class TimeSVDpp:
    """
    Implementation of the TimeSVD++ algorithm for recommender systems.
    Reference: Yehuda Koren, "Collaborative Filtering with Temporal Dynamics", KDD 2009.
    """
    def __init__(self, n_factors=20, n_epochs=20, lr=0.001, reg=0.05, lr_b=0.001, reg_b=0.05, verbose=True):
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr = lr
        self.reg = reg
        self.lr_b = lr_b
        self.reg_b = reg_b
        self.verbose = verbose
        self.clip_value = 1.0  # For gradient clipping

    def fit(self, ratings, timestamps):
        """
        ratings: list of (user, item, rating)
        timestamps: list of timestamps corresponding to ratings
        """
        self.users = list(set([r[0] for r in ratings]))
        self.items = list(set([r[1] for r in ratings]))
        self.user_map = {u: i for i, u in enumerate(self.users)}
        self.item_map = {i: j for j, i in enumerate(self.items)}
        self.n_users = len(self.users)
        self.n_items = len(self.items)

        # Compute global mean
        self.global_mean = np.mean([r[2] for r in ratings])

        # Initialize parameters
        self.bu = np.zeros(self.n_users)
        self.bi = np.zeros(self.n_items)
        self.alpha_u = np.zeros(self.n_users)  # User time drift
        self.pu = np.random.normal(0, 0.01, (self.n_users, self.n_factors))
        self.qi = np.random.normal(0, 0.01, (self.n_items, self.n_factors))
        self.yj = np.random.normal(0, 0.01, (self.n_items, self.n_factors))

        # For time effects
        self.user_rating_times = defaultdict(list)
        for (u, i, r), t in zip(ratings, timestamps):
            self.user_rating_times[u].append(t)
        self.user_mean_time = {u: np.mean(ts) for u, ts in self.user_rating_times.items()}

        # Training
        for epoch in range(self.n_epochs):
            for idx, ((user, item, rating), time) in enumerate(zip(ratings, timestamps)):
                u = self.user_map[user]
                i = self.item_map[item]
                dev_u = self._dev(time, self.user_mean_time[user])
                implicit_sum = np.zeros(self.n_factors)
                # For implicit feedback (SVD++)
                N_u = [self.item_map[j] for (uu, j, rr), tt in zip(ratings, timestamps) if uu == user]
                if N_u:
                    implicit_sum = np.sum(self.yj[N_u], axis=0) / np.sqrt(len(N_u))
                pred = self.predict_single_idx(u, i, dev_u, implicit_sum)
                err = rating - pred
                # Update biases
                self.bu[u] += self.lr_b * (err - self.reg_b * self.bu[u])
                self.bi[i] += self.lr_b * (err - self.reg_b * self.bi[i])
                self.alpha_u[u] += self.lr_b * (err * dev_u - self.reg_b * self.alpha_u[u])
                # Update factors
                pu_old = self.pu[u].copy()
                # Gradient updates with clipping
                pu_update = self.lr * (err * self.qi[i] - self.reg * self.pu[u])
                qi_update = self.lr * (err * (pu_old + implicit_sum) - self.reg * self.qi[i])
                pu_update = np.clip(pu_update, -self.clip_value, self.clip_value)
                qi_update = np.clip(qi_update, -self.clip_value, self.clip_value)
                self.pu[u] += pu_update
                self.qi[i] += qi_update
                if N_u:
                    yj_update = self.lr * (err * self.qi[i] / np.sqrt(len(N_u)) - self.reg * self.yj[N_u])
                    yj_update = np.clip(yj_update, -self.clip_value, self.clip_value)
                    self.yj[N_u] += yj_update
            if self.verbose:
                print(f"Epoch {epoch+1}/{self.n_epochs} completed.")

    def predict(self, user, item, time=None, user_items=None):
        u = self.user_map.get(user, None)
        i = self.item_map.get(item, None)
        if u is None or i is None:
            return self.global_mean
        dev_u = 0
        if time is not None and user in self.user_mean_time:
            dev_u = self._dev(time, self.user_mean_time[user])
        implicit_sum = np.zeros(self.n_factors)
        if user_items:
            N_u = [self.item_map[j] for j in user_items if j in self.item_map]
            if N_u:
                implicit_sum = np.sum(self.yj[N_u], axis=0) / np.sqrt(len(N_u))
        return self.predict_single_idx(u, i, dev_u, implicit_sum)

    def predict_single_idx(self, u, i, dev_u, implicit_sum):
        return (self.global_mean + self.bu[u] + self.alpha_u[u] * dev_u + self.bi[i] +
                np.dot(self.qi[i], self.pu[u] + implicit_sum))

    def _dev(self, t, t_u):
        # Time deviation function as in Koren's paper
        sign = 1 if t - t_u >= 0 else -1
        return sign * abs(t - t_u) ** 0.4
