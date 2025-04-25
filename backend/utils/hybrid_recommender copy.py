# hybrid_recommender.py

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from pymongo import MongoClient

# Global variables
inter_df = None
prod_df = None
user_df = None
uid_list = None
pid_list = None
uid2idx = None
pid2idx = None
ui_mat = None
user_latent = None
item_latent = None
item_sim = None
popularity = None
weight_map = {'view': 1.0, 'add_to_cart': 2.0, 'purchase': 3.0}

# MongoDB connection
client = None
mongo_db = None

# half-life in hours: how quickly past events decay
RECENCY_HALF_LIFE_HRS = 6.0
# define your recency window
SESSION_WINDOW = timedelta(minutes=15)

def initialize_mongodb(mongo_uri='mongodb://localhost:27017/ecommerce_db'):
    """Initialize MongoDB connection and load data"""
    global client, mongo_db
    client = MongoClient(mongo_uri)
    mongo_db = client.get_database()
    load_data_from_mongodb()
    return mongo_db

def load_data_from_mongodb():
    """Load data from MongoDB and build the recommender model"""
    global inter_df, prod_df, user_df, uid_list, pid_list, uid2idx, pid2idx, ui_mat, user_latent, item_latent, item_sim, popularity

    # Load data from MongoDB
    if mongo_db is None:
        print("MongoDB not initialized. Call initialize_mongodb() first.")
        return

    # Convert MongoDB collections to DataFrames
    inter_df = pd.DataFrame(list(mongo_db.interactions.find()))
    prod_df = pd.DataFrame(list(mongo_db.products.find()))
    user_df = pd.DataFrame(list(mongo_db.users.find()))

    print(f"Loaded from MongoDB: {len(inter_df)} interactions, {len(prod_df)} products, {len(user_df)} users")
    
    # If no data, return early
    if inter_df.empty or prod_df.empty:
        print("Warning: No interaction or product data found in MongoDB")
        return

    # Process data and build models
    build_models()

def build_models():
    """Build recommendation models from current data"""
    global inter_df, prod_df, uid_list, pid_list, uid2idx, pid2idx, ui_mat, user_latent, item_latent, item_sim, popularity

    # Handle empty datasets gracefully
    if inter_df.empty or prod_df.empty:
        print("Warning: Empty data, skipping model building")
        return

    # Convert ObjectId to string for user_id
    if 'user_id' in inter_df.columns:
        inter_df['user_id'] = inter_df['user_id'].astype(str)

    # Ensure timestamp is datetime
    if 'timestamp' in inter_df.columns:
        inter_df['timestamp'] = pd.to_datetime(inter_df['timestamp'])

    # Map interaction_type → weight
    inter_df['weight'] = inter_df['interaction_type'].map(weight_map)

    # Get unique user and product IDs
    uid_list = sorted(inter_df.user_id.unique())
    if 'product_id' in prod_df.columns:
        pid_list = sorted(prod_df.product_id.unique())
    else:
        pid_list = sorted(prod_df._id.unique())

    # Map IDs to indices
    uid2idx = {u: i for i, u in enumerate(uid_list)}
    pid2idx = {p: i for i, p in enumerate(pid_list)}

    # Build user-item matrix
    try:
        rows = inter_df.user_id.map(uid2idx)
        cols = inter_df.product_id.map(pid2idx)
        data = inter_df.weight.values
        ui_mat = csr_matrix((data, (rows, cols)), shape=(len(uid_list), len(pid_list)))

        # Train CF latent factors via TruncatedSVD
        n_factors = min(50, min(ui_mat.shape) - 1)  # Ensure n_factors is valid
        svd = TruncatedSVD(n_components=n_factors, random_state=42)
        user_latent = svd.fit_transform(ui_mat)              # shape: (n_users, n_factors)
        item_latent = svd.components_.T                      # shape: (n_items, n_factors)
    except Exception as e:
        print(f"Error building user-item matrix: {e}")
        # Set fallback values
        user_latent = np.zeros((len(uid_list), 5)) if uid_list else np.zeros((1, 5))
        item_latent = np.zeros((len(pid_list), 5)) if pid_list else np.zeros((1, 5))

    # Build content-based item-item similarity
    try:
        # Prepare metadata for TF-IDF
        if 'category' in prod_df.columns and 'brand' in prod_df.columns and 'price' in prod_df.columns:
            prod_df['metadata'] = (
                prod_df['category'].fillna('') + ' ' +
                prod_df['brand'].fillna('') + ' price:' + prod_df['price'].astype(str)
            )
        else:
            prod_df['metadata'] = 'unknown'
        
        tfidf = TfidfVectorizer()
        item_tfidf = tfidf.fit_transform(prod_df['metadata'])
        item_sim = cosine_similarity(item_tfidf)           # shape: (n_items, n_items)
    except Exception as e:
        print(f"Error building item-item similarity: {e}")
        # Set fallback values
        item_sim = np.eye(len(pid_list)) if pid_list else np.eye(1)

    # Precompute popularity ranking
    try:
        popularity = (
            inter_df.groupby('product_id')['weight']
            .sum()
            .sort_values(ascending=False)
            .index
            .tolist()
        )
    except Exception as e:
        print(f"Error computing popularity: {e}")
        popularity = []

def recency_weight(ts):
    """Exponential decay: 1.0 now → 0.5 after half-life hours."""
    if pd.isna(ts):
        return 0.5  # Default weight for missing timestamps
    delta = (datetime.utcnow() - pd.to_datetime(ts)).total_seconds() / 3600.0
    return 2 ** (- delta / RECENCY_HALF_LIFE_HRS)

def get_user_vector(u_id):
    """Build a weighted sum of item_latents, with recency decay."""
    if inter_df is None or item_latent is None:
        return np.zeros(50)  # Return zero vector if not initialized
        
    hist = inter_df[inter_df.user_id == str(u_id)]
    
    if hist.empty or item_latent.size == 0:
        # cold-start: global mean latent or zeros
        return np.mean(item_latent, axis=0) if item_latent.size > 0 else np.zeros(item_latent.shape[1] if item_latent.ndim > 1 else 5)
    
    vecs, ws = [], []
    for _, row in hist.iterrows():
        pid = row.product_id
        if pid not in pid2idx:
            continue
        base_w = weight_map.get(row.interaction_type, 1.0)
        r_w = recency_weight(row.timestamp)
        w = base_w * r_w
        vecs.append(item_latent[pid2idx[pid]] * w)
        ws.append(w)
    
    if not ws:
        return np.mean(item_latent, axis=0) if item_latent.size > 0 else np.zeros(item_latent.shape[1] if item_latent.ndim > 1 else 5)
    
    return np.sum(vecs, axis=0) / (np.sum(ws) + 1e-6)

def recommend(user_id, k=10, alpha=0.7):
    """Get recommendations for a user"""
    global inter_df, prod_df, uid_list, pid_list, uid2idx, pid2idx, item_sim, popularity
    
    print(f"Getting recommendations for user {user_id}, k={k}")
    
    # Safety check for initialization
    if inter_df is None or prod_df is None:
        print("Recommender not initialized. Loading data from MongoDB.")
        load_data_from_mongodb()
        
        # If still not initialized, return empty recommendations
        if inter_df is None or prod_df is None or inter_df.empty or prod_df.empty:
            print("Failed to load data. Returning empty recommendations.")
            return pd.DataFrame(columns=['category', 'brand', 'price'])
    
    # Convert ObjectId to string if needed
    u_id = str(user_id)
    
    # 1. Grab full history
    hist = inter_df[inter_df.user_id == u_id].copy()  # Create a copy to avoid SettingWithCopyWarning
    print(f"Found {len(hist)} interactions for user {u_id}")
    
    if hist.empty:
        print("No history for user, using popularity fallback")
        # no history → popularity fallback
        recs = popularity[:k] if popularity else []
        if not recs:
            print("No popularity recommendations available")
            return pd.DataFrame(columns=['category', 'brand', 'price'])
        
        print(f"Returning {len(recs)} popularity recommendations")
        # Check if the product IDs exist in the product DataFrame
        valid_recs = [pid for pid in recs if pid in prod_df['product_id'].values]
        if not valid_recs:
            print(f"None of the recommended product IDs exist in products collection")
            return pd.DataFrame(columns=['category', 'brand', 'price'])
        
        # Debug the product lookup
        try:
            result = prod_df.set_index('product_id').loc[valid_recs][['category', 'brand', 'price']]
            print(f"Returning {len(result)} recommendations")
            return result
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            print(f"Valid recs: {valid_recs}")
            print(f"Product DataFrame head: {prod_df.head()}")
            return pd.DataFrame(columns=['category', 'brand', 'price'])

    # 2. Identify most recent interaction
    if 'timestamp' in hist.columns:
        hist.loc[:, 'timestamp'] = pd.to_datetime(hist['timestamp'])  # Use .loc to avoid SettingWithCopyWarning
    last = hist.sort_values('timestamp', ascending=False).iloc[0]
    pid_last, ts_last = last.product_id, last.timestamp

    # 3. If last event is *very* recent, do pure CB on that item
    if datetime.utcnow() - ts_last < SESSION_WINDOW:
        # get index of that product
        if pid_last not in pid2idx:
            recs = popularity[:k] if popularity else []
        else:
            i = pid2idx[pid_last]
            sims = item_sim[i]                    # TF–IDF similarity row
            tops = np.argsort(-sims)              # descending
            # skip itself
            tops = [j for j in tops if j != i][:k]
            recs = [pid_list[j] for j in tops]
        
        if not recs:
            return pd.DataFrame(columns=['category', 'brand', 'price'])
        return prod_df.set_index('product_id').loc[recs][['category', 'brand', 'price']]

    # 4. Otherwise, do your usual hybrid
    u_vec = get_user_vector(u_id)
    cf_scores = item_latent.dot(u_vec)
    cf_norm = (cf_scores - cf_scores.min()) / (np.ptp(cf_scores) + 1e-8)

    seen = set(hist.product_id)
    if seen:
        seen_idxs = [pid2idx[p] for p in seen if p in pid2idx]
        if seen_idxs:
            cb_raw = item_sim[:, seen_idxs].mean(axis=1)
            cb_norm = (cb_raw - cb_raw.min()) / (np.ptp(cb_raw) + 1e-8)
        else:
            cb_norm = np.zeros_like(cf_norm)
    else:
        cb_norm = np.zeros_like(cf_norm)

    hybrid = alpha * cf_norm + (1-alpha) * cb_norm

    # 5. Mask seen and return top-k
    candidates = [
        (pid, score) for pid, score in zip(pid_list, hybrid)
        if pid not in seen
    ]
    recs = [pid for pid, _ in sorted(candidates, key=lambda x: -x[1])[:k]]
    
    if not recs:
        # Fallback to popularity if no recommendations
        recs = [p for p in popularity if p not in seen][:k]
    
    if not recs:
        return pd.DataFrame(columns=['category', 'brand', 'price'])
    
    return prod_df.set_index('product_id').loc[recs][['category', 'brand', 'price']]

def add_interaction(user_id, product_id, interaction_type, timestamp=None):
    """Add a new interaction and update the model"""
    global inter_df
    
    # Safety check
    if inter_df is None:
        print("Recommender not initialized. Loading data from MongoDB.")
        load_data_from_mongodb()
    
    # Convert IDs to strings for consistency
    user_id = str(user_id)
    product_id = str(product_id) if isinstance(product_id, str) else product_id
    
    # Add to DataFrame
    w = weight_map.get(interaction_type, 1.0)
    new_row = {
        'user_id': user_id,
        'product_id': product_id,
        'interaction_type': interaction_type,
        'timestamp': timestamp or datetime.utcnow(),
        'weight': w
    }
    
    # Append to DataFrame
    inter_df = pd.concat([inter_df, pd.DataFrame([new_row])], ignore_index=True)
    
    # If this is a new user or product, rebuild indices
    if user_id not in uid_list or product_id not in pid_list:
        print(f"New user or product detected. Rebuilding models.")
        build_models()

# If this module is imported by Flask, initialize with MongoDB
def init_app(app):
    """Initialize the recommender with a Flask app"""
    with app.app_context():
        mongo_uri = app.config.get('MONGO_URI', 'mongodb://localhost:27017/ecommerce_db')
        initialize_mongodb(mongo_uri)

# 10. Example usage - only runs in standalone mode
if __name__ == '__main__':
    initialize_mongodb()
    print("Recommender initialized with MongoDB data")
    
    if uid_list and len(uid_list) > 0:
        print(f"Recommender has data for {len(uid_list)} users and {len(pid_list)} products")
        print(f"Sample recommendation for user {uid_list[0]}:\n", recommend(uid_list[0], k=5))
    else:
        print("No user data available for recommendations")
