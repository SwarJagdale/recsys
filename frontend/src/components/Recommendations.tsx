import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

interface Recommendation {
  id:string;
  product_id: string;
  product_name: string;
  category: string;
  brand: string;
  price: number;
  score: number;
  recommendation_category: string;
  description: string;
}

const Recommendations: React.FC = () => {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [actionSuccess, setActionSuccess] = useState('');

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!user) return;
      setLoading(true);
      setError('');
      try {
        const response = await axios.get(`http://localhost:5000/api/recommendations/${user.user_id}`);
        setRecommendations(response.data.recommendations || []);
      } catch (err) {
        setError('Failed to fetch recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [user]);

  const handleInteraction = async (productId: string, interactionType: string) => {
    try {
      await axios.post('http://localhost:5000/api/interactions', {
        user_id: user?.user_id,
        product_id: productId,
        interaction_type: interactionType,
      });
      setActionSuccess('Action recorded successfully');
      setTimeout(() => setActionSuccess(''), 3000);
    } catch (err) {
      setActionError('Failed to record interaction');
      setTimeout(() => setActionError(''), 3000);
    }
  };

  if (loading) {
    return (
      <div className="container loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="container">
      {error && (
        <div className="alert alert-error">{error}</div>
      )}
      {actionError && (
        <div className="alert alert-error">{actionError}</div>
      )}
      {actionSuccess && (
        <div className="alert alert-success">{actionSuccess}</div>
      )}

      <div className="grid">
        {recommendations.map((rec) => (
          <div key={rec.product_id} className="card product-card">
            <img
              className="card-media"
              src={`https://via.placeholder.com/300x200?text=${rec.brand}`}
              alt={rec.brand}
            />
            <div className="card-content">
              <h2>{rec.brand} ({rec.category})</h2>
              <p className="product-meta">Product ID: {rec.product_id}</p>
              <p className="price">${rec.price.toFixed(2)}</p>
              <div className="product-actions">
                <button 
                  className="btn-secondary"
                  onClick={() => handleInteraction(rec.product_id, 'view')}
                >
                  View
                </button>
                <button 
                  className="btn-primary"
                  onClick={() => handleInteraction(rec.product_id, 'add_to_cart')}
                >
                  Add to Cart
                </button>
                <button 
                  className="btn-secondary"
                  onClick={() => handleInteraction(rec.product_id, 'purchase')}
                >
                  Purchase
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Recommendations;