import pandas as pd
import numpy as np
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

def migrate_csv_to_mongodb(
    csv_dir="data",
    mongo_uri="mongodb://localhost:27017/",
    db_name="ecommerce_db"
):
    """
    Migrate CSV data to MongoDB collections
    
    Parameters:
    - csv_dir: Directory containing the CSV files
    - mongo_uri: MongoDB connection URI
    - db_name: MongoDB database name
    """
    print(f"Connecting to MongoDB at {mongo_uri}")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # 1. Migrate products
    products_file = os.path.join(csv_dir, "products.csv")
    if os.path.exists(products_file):
        print(f"Importing products from {products_file}")
        products_df = pd.read_csv(products_file)
        
        # Convert product IDs to int if they're numeric
        if 'product_id' in products_df.columns:
            try:
                products_df['product_id'] = products_df['product_id'].astype(int)
            except:
                pass
        
        # Convert DataFrame to list of dictionaries
        products = products_df.to_dict('records')
        
        # Insert into MongoDB
        if products:
            db.products.drop()  # Remove existing collection
            result = db.products.insert_many(products)
            print(f"Inserted {len(result.inserted_ids)} products")
    else:
        print(f"Products file not found: {products_file}")
    
    # 2. Migrate users
    users_file = os.path.join(csv_dir, "users.csv")
    if os.path.exists(users_file):
        print(f"Importing users from {users_file}")
        users_df = pd.read_csv(users_file)
        
        # Create ObjectIds for users if needed
        if '_id' not in users_df.columns:
            users_df['_id'] = [ObjectId() for _ in range(len(users_df))]
        
        # Convert DataFrame to list of dictionaries
        users = users_df.to_dict('records')
        
        # Insert into MongoDB
        if users:
            db.users.drop()  # Remove existing collection
            result = db.users.insert_many(users)
            print(f"Inserted {len(result.inserted_ids)} users")
    else:
        print(f"Users file not found: {users_file}")
    
    # 3. Migrate interactions
    interactions_file = os.path.join(csv_dir, "interactions.csv")
    if os.path.exists(interactions_file):
        print(f"Importing interactions from {interactions_file}")
        interactions_df = pd.read_csv(interactions_file)
        
        # Convert user_id to ObjectId string format if it's not already
        # This assumes the user_id in interactions matches the _id in users
        if 'user_id' in interactions_df.columns:
            # If the user_id looks like an ObjectId, keep it as is
            if not interactions_df['user_id'].astype(str).str.match(r'^[0-9a-f]{24}$').all():
                print("Converting user_ids to ObjectId compatible format")
                # Map user IDs from interactions to user ObjectIds
                user_id_mapping = {str(u['user_id']): str(u['_id']) 
                                  for u in db.users.find({}, {'_id': 1, 'user_id': 1})}
                
                # If we have a mapping, use it; otherwise, generate new ObjectIds
                if user_id_mapping:
                    interactions_df['user_id'] = interactions_df['user_id'].astype(str).map(
                        lambda x: user_id_mapping.get(x, str(ObjectId())))
                else:
                    interactions_df['user_id'] = interactions_df['user_id'].apply(
                        lambda x: str(ObjectId()))
        
        # Convert product_id to int if possible
        if 'product_id' in interactions_df.columns:
            try:
                interactions_df['product_id'] = interactions_df['product_id'].astype(int)
            except:
                pass
        
        # Convert timestamp to datetime if it exists
        if 'timestamp' in interactions_df.columns:
            try:
                interactions_df['timestamp'] = pd.to_datetime(interactions_df['timestamp'])
            except:
                interactions_df['timestamp'] = datetime.utcnow()
        else:
            interactions_df['timestamp'] = datetime.utcnow()
        
        # Convert DataFrame to list of dictionaries
        interactions = interactions_df.to_dict('records')
        
        # Insert into MongoDB
        if interactions:
            db.interactions.drop()  # Remove existing collection
            result = db.interactions.insert_many(interactions)
            print(f"Inserted {len(result.inserted_ids)} interactions")
    else:
        print(f"Interactions file not found: {interactions_file}")
    
    print("Migration completed!")

if __name__ == "__main__":
    migrate_csv_to_mongodb()
    print("You can now use the recommender system with MongoDB!") 