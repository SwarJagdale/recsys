# E-Commerce Recommendation System Backend

This is the backend API for the e-commerce recommendation system, built with Flask and MongoDB.

## Setup Instructions

1. Install MongoDB on your system if not already installed
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start MongoDB service

5. Run the Flask application:
   ```bash
   python app.py
   ```

## API Endpoints

### Authentication
- `POST /api/signup`: Create a new user account
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "preferences": {}
  }
  ```

- `POST /api/login`: Login to existing account
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```

### Interactions
- `POST /api/interactions`: Record user interactions
  ```json
  {
    "user_id": "user_id_here",
    "product_id": "product_id_here",
    "interaction_type": "view|purchase|add_to_cart"
  }
  ```

### Recommendations
- `GET /api/recommendations/<user_id>`: Get personalized recommendations for a user

## Database Schema

### Users Collection
```json
{
  "_id": ObjectId,
  "email": String,
  "password": String,
  "created_at": DateTime,
  "preferences": Object,
  "interactions": Array
}
```

### Interactions Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "product_id": ObjectId,
  "interaction_type": String,
  "timestamp": DateTime
}
```

### Products Collection
```json
{
  "_id": ObjectId,
  "name": String,
  "description": String,
  "price": Number,
  "category": String,
  "features": Object
}
```
