# content_based_recommender.py (formerly hybrid_recommender.py)

import pandas as pd
import numpy as np
from datetime import datetime
from pymongo import MongoClient

# --- Collaborative Filtering Model (Matrix Factorization) ---
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

class MatrixFactorization:
    def __init__(self, n_users, n_items, n_factors=20, lr=0.01, reg=0.1, epochs=20):
        self.n_users = n_users
        self.n_items = n_items
        self.n_factors = n_factors
        self.lr = lr
        self.reg = reg
        self.epochs = epochs
        self.user_factors = np.random.normal(scale=0.1, size=(n_users, n_factors))
        self.item_factors = np.random.normal(scale=0.1, size=(n_items, n_factors))

    def _sgd_update(self, u, i):
        pred = sigmoid(self.user_factors[u].dot(self.item_factors[i]))
        err = 1 - pred
        grad_u = err * self.item_factors[i] - self.reg * self.user_factors[u]
        grad_i = err * self.user_factors[u] - self.reg * self.item_factors[i]
        self.user_factors[u] += self.lr * grad_u
        self.item_factors[i] += self.lr * grad_i

    def train(self, interactions):
        for epoch in range(self.epochs):
            np.random.shuffle(interactions)
            for u, i in interactions:
                self._sgd_update(u, i)

    def recommend(self, u, k=9, interacted=set()):
        scores = sigmoid(self.item_factors.dot(self.user_factors[u]))
        if interacted:
            scores[list(interacted)] = -np.inf
        top_k = np.argpartition(-scores, k)[:k]
        return top_k[np.argsort(-scores[top_k])]

    def update_one(self, u, i, interacted_update):
        self._sgd_update(u, i)
        if u in interacted_update:
            interacted_update[u].add(i)
        else:
            interacted_update[u] = {i}

# --- ID Mapping Utilities ---
def map_ids(df, user_col, item_col):
    unique_users = df[user_col].unique()
    unique_items = df[item_col].unique()
    user2idx = {u: idx for idx, u in enumerate(unique_users)}
    item2idx = {i: idx for idx, i in enumerate(unique_items)}
    return user2idx, item2idx

# --- Globals for Model State ---
prod_df = None
user_df = None
inter_df = None
mf = None
user2idx = None
item2idx = None
idx2user = None
idx2item = None
user_interacted_idx = None

# MongoDB connection
global_client = None
global_mongo_db = None

def initialize_mongodb(mongo_uri='mongodb://localhost:27017/ecommerce_db'):
    """Initialize MongoDB connection and load data"""
    global global_client, global_mongo_db
    global_client = MongoClient(mongo_uri)
    global_mongo_db = global_client.get_database()
    load_data_from_mongodb()
    return global_mongo_db

def load_data_from_mongodb():
    """Load data from MongoDB and build the collaborative filtering model"""
    global prod_df, user_df, inter_df, mf, user2idx, item2idx, idx2user, idx2item, user_interacted_idx

    if global_mongo_db is None:
        print("MongoDB not initialized. Call initialize_mongodb() first.")
        return

    # Load collections
    prod_df = pd.DataFrame(list(global_mongo_db.products.find()))
    user_df = pd.DataFrame(list(global_mongo_db.users.find()))
    inter_df = pd.DataFrame(list(global_mongo_db.interactions.find()))

    print(f"Loaded from MongoDB: {len(inter_df)} interactions, {len(prod_df)} products, {len(user_df)} users")
    if prod_df.empty or inter_df.empty:
        print("Warning: No product or interaction data found in MongoDB")
        return

    # Use string IDs for mapping
    inter_df['user_id'] = inter_df['user_id'].astype(str)
    inter_df['product_id'] = inter_df['product_id'].astype(str)
    prod_df['product_id'] = prod_df['product_id'].astype(str)

    # Map user and item IDs to indices
    user2idx, item2idx = map_ids(inter_df, 'user_id', 'product_id')
    idx2user = {idx: u for u, idx in user2idx.items()}
    idx2item = {idx: i for i, idx in item2idx.items()}

    # Build interaction tuples
    interactions = [
        (user2idx[r.user_id], item2idx[r.product_id])
        for r in inter_df.itertuples()
        if r.user_id in user2idx and r.product_id in item2idx
    ]
    # Build user_interacted_idx
    user_interacted = inter_df.groupby('user_id')['product_id'].apply(set).to_dict()
    user_interacted_idx = {user2idx[u]: {item2idx[i] for i in items if i in item2idx} for u, items in user_interacted.items() if u in user2idx}

    # Initialize and train model
    mf = MatrixFactorization(n_users=len(user2idx), n_items=len(item2idx), n_factors=50, lr=0.01, reg=0.1, epochs=30)
    mf.train(interactions)
    print("MatrixFactorization model trained.")


def add_interaction(user_id, product_id, interaction_type, timestamp=None):
    """Add a new interaction to MongoDB and update the model incrementally or retrain if needed."""
    global inter_df, mf, user2idx, item2idx, user_interacted_idx
    user_id = str(user_id)
    product_id = str(product_id)
    interaction = {
        'user_id': user_id,
        'product_id': product_id,
        'interaction_type': interaction_type,
        'timestamp': timestamp or datetime.utcnow()
    }
    # Add to MongoDB
    if global_mongo_db is not None:
        try:
            global_mongo_db.interactions.insert_one(interaction)
            print(f"Added interaction: User {user_id}, Product {product_id}, Type {interaction_type}")
            # Update inter_df in memory
            if inter_df is not None:
                inter_df = pd.concat([inter_df, pd.DataFrame([interaction])], ignore_index=True)
        except Exception as e:
            print(f"Error adding interaction to MongoDB: {e}")
    # If either user or product is new, reload all data/mappings/model
    if (user2idx is None or user_id not in user2idx) or (item2idx is None or product_id not in item2idx):
        print("New user or product detected. Reloading data and retraining model.")
        load_data_from_mongodb()
    else:
        # Update model incrementally if user/item exist
        u_idx = user2idx[user_id]
        i_idx = item2idx[product_id]
        mf.update_one(u_idx, i_idx, user_interacted_idx)
        load_data_from_mongodb()

def init_app(app):
    """Initialize the recommender with a Flask app"""
    with app.app_context():
        mongo_uri = app.config.get('MONGO_URI', 'mongodb://localhost:27017/ecommerce_db')
        initialize_mongodb(mongo_uri)

def recommend(user_id, k=10):
    """Return a DataFrame of recommended products for the user using collaborative filtering."""
    global mf, user2idx, item2idx, idx2item, user_interacted_idx, prod_df
    user_id = str(user_id)
    if user2idx is None or item2idx is None or mf is None:
        print("Model not initialized. Reloading data.")
        load_data_from_mongodb()
    if user_id not in user2idx:
        print(f"User {user_id} not found in model. Returning popular products.")
        # Fallback: recommend most popular products
        popular = prod_df['product_id'].value_counts().index[:k]
        return prod_df[prod_df['product_id'].isin(popular)]
    u_idx = user2idx[user_id]
    interacted = user_interacted_idx.get(u_idx, set())
    rec_idxs = mf.recommend(u_idx, k=k, interacted=interacted)
    recommendations = [idx2item[i] for i in rec_idxs if i in idx2item]
    return prod_df[prod_df['product_id'].isin(recommendations)]

# Example usage - only runs in standalone mode
if __name__ == '__main__':
    initialize_mongodb()
    print("Collaborative filtering recommender initialized with MongoDB data")
    if prod_df is not None and not prod_df.empty:
        print(f"Recommender has data for {len(prod_df)} products")
        # Test with a random user if we have user data
        if not user_df.empty and not inter_df.empty:
            test_user = inter_df['user_id'].iloc[0]
            print(f"Sample recommendation for user {test_user}:")
            print(recommend(test_user, k=5))
    else:
        print("No product data available for recommendations")
