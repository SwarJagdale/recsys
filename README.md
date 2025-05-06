# E-Commerce Recommender System

A complete e-commerce recommendation system with personalized product recommendations using a hybrid recommendation approach. This project consists of both frontend and backend components.

## Project Overview

This system implements a hybrid approach to product recommendations, combining:
- Collaborative filtering
- Recency-based recommendations
- Context-based recommendations 
- Demographic-based recommendations

The system intelligently selects between these strategies based on whether the user is new or has previous interactions.

## Project Structure

```
recsys/
├── backend/             # Flask backend API
│   ├── app.py           # Main Flask application
│   ├── models/          # Machine learning models
│   └── utils/           # Utility modules
│       ├── hybrid_recommender.py         # Original recommender implementation
│       └── HybridRecommender/            # Modular implementation
│           ├── core.py                   # Core recommender class
│           ├── collaborative.py          # Collaborative filtering strategy
│           ├── recency.py                # Recency-based strategy
│           ├── context.py                # Context-based strategy
│           └── demographic.py            # Demographic-based strategy
├── frontend/            # React TypeScript frontend
│   ├── public/          # Static files
│   └── src/             # Source code
│       ├── components/  # Reusable UI components
│       ├── contexts/    # React contexts
│       └── pages/       # Page components
└── data/                # Sample data files
    ├── products.csv     # Product catalog
    ├── users.csv        # User information
    ├── interactions.csv # User-product interactions
    └── context.csv      # Contextual information
```

## Features

### Backend
- User authentication (signup/login)
- Product catalog management
- User interaction tracking (view, add to cart, purchase)
- Hybrid recommendation system
- RESTful API endpoints

### Frontend
- User authentication (login/signup)
- Product browsing and search
- Personalized recommendations
- Product detail pages
- User interactions (view, add to cart, purchase)
- Responsive design
- Modern Material-UI components

## Tech Stack

### Backend
- Flask (Python web framework)
- MongoDB (Database)
- Pandas (Data processing)
- NumPy (Numerical computations)
- scikit-learn (Machine learning components)

### Frontend
- React
- TypeScript
- Material-UI
- React Router
- Axios
- Emotion (styled components)

## Setup Instructions

### Backend Setup

1. Install MongoDB on your system if not already installed
2. Create a virtual environment:
   ```bash
   cd backend
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

### Frontend Setup

1. Install Node.js (v14 or higher) and npm

2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open your browser and navigate to http://localhost:3000

## API Endpoints

### Authentication
- `POST /api/signup`: Create a new user account
- `POST /api/login`: Login to existing account

### Products
- `GET /api/products`: Get all products
- `GET /api/products/:id`: Get details of a specific product

### Interactions
- `POST /api/interactions`: Record user interactions (view, add_to_cart, purchase)

### Recommendations
- `GET /api/recommendations/:user_id`: Get personalized recommendations for a user

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

## Recommendation System

The hybrid recommendation system works as follows:

1. For new users (no previous interactions):
   - Uses demographic and context-based recommendations with weights 70% and 30% respectively

2. For existing users:
   - Uses collaborative filtering and recency-based recommendations
   - Takes top 10 items from each strategy while avoiding duplicates

3. Returns products along with their recommendation source (collaborative, recency, demographic, or context)

## Detailed Functionality Explanation

### Recommendation Strategies in Detail

#### 1. Collaborative Filtering
This strategy analyzes user-item interactions to identify patterns and similarities between users.
- **Implementation**: Uses cosine similarity to find users with similar preferences
- **User-Item Matrix**: Creates a matrix where rows are users, columns are products, and values are interaction weights
- **Process Flow**:
  1. Identifies users with similar interaction patterns
  2. Weighs recommendations based on similarity scores
  3. Normalizes final scores for ranking
- **Best For**: Users with established interaction history
- **Advantages**: Highly personalized, discovers non-obvious recommendations

#### 2. Recency-based Recommendations
This strategy prioritizes recently viewed or interacted products with time-decay functions.
- **Implementation**: Applies exponential time decay to recent user interactions
- **Weighting System**:
  - View: Weight of 1
  - Add to cart: Weight of 3
  - Purchase: Weight of 5
- **Additional Factors**:
  - Category preferences: Boosts products from categories the user recently engaged with (30% weight)
  - Brand preferences: Boosts products from brands the user recently engaged with (25% weight)
  - Diversity boost: Increases scores for products unlike those recently seen (20% boost)
- **Time-Awareness**: More recent interactions have exponentially higher influence
- **Exploration**: Includes small random factors to promote discovery

#### 3. Context-based Recommendations
This strategy uses situational context to make relevant recommendations.
- **Implementation**: Matches current user context with similar contexts from all users
- **Contextual Factors**:
  - Time of day: Morning, afternoon, evening, night
  - Device type: Mobile, tablet, desktop
  - Location: User's current location
- **Fallback Mechanism**: Uses popularity-based recommendations when context data is unavailable
- **Process Flow**:
  1. Identifies current user context
  2. Finds interactions from similar contexts
  3. Recommends products that performed well in those contexts

#### 4. Demographic-based Recommendations
This strategy groups users by demographic attributes to make recommendations.
- **Implementation**: Analyzes interactions from users within the same demographic group
- **Key Demographics**:
  - Location: Geographic location of the user
  - (Can be extended with age, gender, etc.)
- **Process Flow**:
  1. Identifies users in the same demographic group
  2. Analyzes their collective interaction patterns
  3. Recommends popular products within that group
- **Best For**: New users with minimal interaction history

### Hybrid System Integration

The system makes intelligent decisions about which recommendation strategies to employ:

#### For New Users (Cold Start Handling)
- **Detection**: Users with no recorded interactions
- **Strategy Mix**:
  - 70% weight to demographic recommendations
  - 30% weight to context recommendations
- **Labeling**: Each product is labeled with its primary recommendation source
- **Advantage**: Provides personalized recommendations even without user history

#### For Existing Users
- **Strategy Mix**:
  - Takes top 10 products from collaborative filtering
  - Takes top 10 products from recency-based recommendations (excluding duplicates)
- **Diversification**: Ensures diverse recommendation sources
- **Transparency**: Each product displays its recommendation source (collaborative or recency)

### User Interaction Tracking

The system records and analyzes three main types of interactions:

1. **View**: Basic product viewing
   - Lowest interaction weight (1)
   - Highest volume data point
   - Used primarily for understanding browsing patterns

2. **Add to Cart**: Intermediate interest
   - Medium interaction weight (3)
   - Strong signal of potential purchase intent
   - Used for identifying products users are considering

3. **Purchase**: Strongest interaction
   - Highest interaction weight (5)
   - Most valuable signal for recommendations
   - Creates connections between products for cross-selling

### Data Processing Pipeline

1. **Data Collection**:
   - User authentication data
   - Product catalog information
   - Real-time interaction tracking
   - Contextual information

2. **Data Transformation**:
   - MongoDB to Pandas DataFrames conversion
   - Type normalization (string IDs to numeric)
   - User-item matrix construction
   - Feature extraction

3. **Recommendation Generation**:
   - Strategy selection based on user status
   - Score calculation across multiple algorithms
   - Result merging and normalization
   - Sorting and top-k selection

4. **Response Formatting**:
   - JSON serialization of recommendations
   - Addition of metadata (scores, sources)
   - Delivery via RESTful API

### User Experience & Interface

The frontend delivers recommendations through multiple touchpoints:

1. **Homepage**: Shows personalized recommendations immediately after login
2. **Product Detail Pages**: Displays "You might also like" recommendations
3. **Recommendations Page**: Dedicated space for exploring more recommendations
4. **Cart View**: Shows complementary products based on cart contents

### Performance Optimization

The system implements several optimizations:

1. **In-Memory Matrices**: Keeps user-item matrices in memory for fast access
2. **Lazy Updating**: Only rebuilds matrices after new interactions
3. **Caching**: Caches recommendation results for repeated requests
4. **Asynchronous Processing**: Updates matrices in background threads
5. **Score Normalization**: Ensures consistent scoring across strategies

### System Integration

The recommender system integrates with other components:

1. **Authentication System**: Gets user identity for personalized recommendations
2. **Product Catalog**: Retrieves detailed product information
3. **Interaction Tracking**: Records user behaviors in real-time
4. **Analytics Dashboard**: Provides insights on recommendation performance

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request