# content_based_recommender.py (formerly hybrid_recommender.py)

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from pymongo import MongoClient

# Global variables
prod_df = None
user_df = None
inter_df = None
item_sim_matrix = None
product_ids = None
product_features = None

# MongoDB connection
client = None
mongo_db = None

def initialize_mongodb(mongo_uri='mongodb://localhost:27017/ecommerce_db'):
    """Initialize MongoDB connection and load data"""
    global client, mongo_db
    client = MongoClient(mongo_uri)
    mongo_db = client.get_database()
    load_data_from_mongodb()
    return mongo_db

def load_data_from_mongodb():
    """Load data from MongoDB and build the recommender model"""
    global prod_df, user_df, inter_df, item_sim_matrix, product_ids, product_features
    
    # Load data from MongoDB
    if mongo_db is None:
        print("MongoDB not initialized. Call initialize_mongodb() first.")
        return

    # Convert MongoDB collections to DataFrames
    prod_df = pd.DataFrame(list(mongo_db.products.find()))
    user_df = pd.DataFrame(list(mongo_db.users.find()))
    inter_df = pd.DataFrame(list(mongo_db.interactions.find()))

    print(f"Loaded from MongoDB: {len(inter_df)} interactions, {len(prod_df)} products, {len(user_df)} users")
    
    # If no product data, return early
    if prod_df.empty:
        print("Warning: No product data found in MongoDB")
        return

    # Convert IDs to string for consistency
    if 'user_id' in inter_df.columns:
        inter_df['user_id'] = inter_df['user_id'].astype(str)
    
    # Build content-based model
    build_content_model()

def build_content_model():
    """Build a content-based recommendation model using product features"""
    global prod_df, item_sim_matrix, product_ids, product_features
    
    try:
        # Create a feature string for each product
        if all(col in prod_df.columns for col in ['category', 'brand', 'price']):
            # Clean up any NaN values
            for col in ['category', 'brand']:
                if col in prod_df.columns:
                    prod_df[col] = prod_df[col].fillna('')
            
            # Create feature strings
            prod_df['features'] = (
                prod_df['category'].astype(str) + ' ' +
                prod_df['brand'].astype(str) + ' ' +
                prod_df['price'].astype(str)
            )
        else:
            # Use whatever columns are available
            prod_df['features'] = ' '.join([
                prod_df[col].astype(str) for col in prod_df.columns 
                if col not in ['_id', 'product_id', 'image', 'features']
            ])
        
        # Get product IDs
        if 'product_id' in prod_df.columns:
            product_ids = prod_df['product_id'].values
        else:
            product_ids = prod_df['_id'].values
            
        # Convert features to TF-IDF vectors
        tfidf = TfidfVectorizer(stop_words='english')
        product_features = tfidf.fit_transform(prod_df['features'])
        
        # Calculate similarity matrix
        item_sim_matrix = cosine_similarity(product_features)
        
        print(f"Built content-based model with {len(product_ids)} products")
    
    except Exception as e:
        print(f"Error building content-based model: {e}")
        item_sim_matrix = None
        product_ids = None
        product_features = None

def get_user_history(user_id):
    """Get a user's interaction history"""
    global inter_df
    
    # Convert to string for consistency
    user_id = str(user_id)
    
    if inter_df is None or inter_df.empty:
        return []
    
    # Get user's interactions
    user_interactions = inter_df[inter_df['user_id'] == user_id]
    
    if user_interactions.empty:
        return []
    
    return user_interactions['product_id'].tolist()

def recommend(user_id, k=10):
    """Get content-based recommendations for a user"""
    global prod_df, item_sim_matrix, product_ids
    
    print(f"Getting recommendations for user {user_id}, k={k}")
    
    # Safety check
    if prod_df is None or item_sim_matrix is None or product_ids is None:
        print("Recommender not initialized. Loading data from MongoDB.")
        load_data_from_mongodb()
        
        if prod_df is None or item_sim_matrix is None or product_ids is None:
            print("Failed to load product data. Returning empty recommendations.")
            return pd.DataFrame(columns=['category', 'brand', 'price'])
    
    # Get user history
    user_history = get_user_history(user_id)
    print(f"Found {len(user_history)} interactions for user {user_id}")
    
    # If no history, return popular products
    if not user_history:
        print("No history for user, using most popular products")
        try:
            # Get most common products from interactions
            if not inter_df.empty and 'product_id' in inter_df.columns:
                most_popular = inter_df['product_id'].value_counts().head(k).index.tolist()
            else:
                # Or just return first k products
                most_popular = product_ids[:k]
                
            if 'product_id' in prod_df.columns:
                result = prod_df[prod_df['product_id'].isin(most_popular)]
            else:
                result = prod_df[prod_df['_id'].isin(most_popular)]
                
            # Select only desired columns if they exist
            columns = [col for col in ['category', 'brand', 'price'] if col in result.columns]
            if not columns:
                columns = result.columns[:3]  # Just return first 3 columns as fallback
                
            return result[columns].head(k)
            
        except Exception as e:
            print(f"Error getting popular products: {e}")
            return pd.DataFrame(columns=['category', 'brand', 'price'])
    
    # Calculate average similarity with items in history
    scores = np.zeros(len(product_ids))
    
    for product_id in user_history:
        # Find the product's index
        try:
            if 'product_id' in prod_df.columns:
                idx = np.where(product_ids == product_id)[0][0]
            else:
                # Try to find by _id
                idx = prod_df[prod_df['_id'] == product_id].index[0]
                
            # Add similarity scores
            scores += item_sim_matrix[idx]
        except (IndexError, KeyError):
            # Product not found, skip it
            continue
    
    # Normalize scores
    if len(user_history) > 0:
        scores /= len(user_history)
    
    # Create (product_id, score) pairs
    scored_products = list(zip(product_ids, scores))
    
    # Sort by score and filter out history
    scored_products.sort(key=lambda x: x[1], reverse=True)
    recommendations = [p for p, s in scored_products if p not in user_history][:k]
    
    if not recommendations:
        print("No recommendations found. Returning popular products.")
        return pd.DataFrame(columns=['category', 'brand', 'price'])
    
    # Get recommended products
    try:
        if 'product_id' in prod_df.columns:
            result = prod_df[prod_df['product_id'].isin(recommendations)]
        else:
            result = prod_df[prod_df['_id'].isin(recommendations)]
            
        # Select only desired columns if they exist
        columns = [col for col in ['category', 'brand', 'price'] if col in result.columns]
        if not columns:
            columns = result.columns[:3]  # Just return first 3 columns as fallback
            
        return result[columns].head(k)
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return pd.DataFrame(columns=['category', 'brand', 'price'])

def add_interaction(user_id, product_id, interaction_type, timestamp=None):
    """Add a new interaction to MongoDB and update the model if needed"""
    global inter_df
    
    # Convert to appropriate types
    user_id = str(user_id)
    
    # Create interaction document
    interaction = {
        'user_id': user_id,
        'product_id': product_id,
        'interaction_type': interaction_type,
        'timestamp': timestamp or datetime.utcnow()
    }
    
    # Add to MongoDB
    if mongo_db is not None:
        try:
            mongo_db.interactions.insert_one(interaction)
            print(f"Added interaction: User {user_id}, Product {product_id}, Type {interaction_type}")
            
            # Update inter_df if it exists
            if inter_df is not None:
                inter_df = pd.concat([inter_df, pd.DataFrame([interaction])], ignore_index=True)
        except Exception as e:
            print(f"Error adding interaction to MongoDB: {e}")
    
    # No need to rebuild the model as this is content-based only

def init_app(app):
    """Initialize the recommender with a Flask app"""
    with app.app_context():
        mongo_uri = app.config.get('MONGO_URI', 'mongodb://localhost:27017/ecommerce_db')
        initialize_mongodb(mongo_uri)

# Example usage - only runs in standalone mode
if __name__ == '__main__':
    initialize_mongodb()
    print("Content-based recommender initialized with MongoDB data")
    
    if prod_df is not None and not prod_df.empty:
        print(f"Recommender has data for {len(prod_df)} products")
        
        # Test with a random user if we have user data
        if not user_df.empty and not inter_df.empty:
            test_user = inter_df['user_id'].iloc[0]
            print(f"Sample recommendation for user {test_user}:")
            print(recommend(test_user, k=5))
    else:
        print("No product data available for recommendations")
