import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import SearchBar from '../components/SearchBar';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line, CartesianGrid
} from 'recharts';

interface Product {
  product_id: string;
  product_name: string;
  category: string;
  brand: string;
  price: number;
  // score: number;
  recommendation_category	: string;
  description: string;
}

const Recommendations: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchRecommendations();
    console.log('hihihi');
  }, []);

  const fetchRecommendations = async () => {
    if (!user) return;
    try {
      const response = await axios.get(`http://localhost:5000/api/recommendations/${user.userId}`);
      setRecommendations(response.data.recommendations || []);
    } catch (err) {
      setError('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (searchResults: Product[]) => {
    setRecommendations(searchResults);
  };

  const handleInteraction = async (productId: string, interactionType: string) => {
    if (!user) return;
    try {
      await axios.post('http://localhost:5000/api/interactions', {
        user_id: user.userId,
        product_id: productId,
        interaction_type: interactionType,
      });
      setSelectedProduct(null);
    } catch (error) {
      console.error('Error recording interaction:', error);
    }
  };

  const handleCardClick = async (product: Product) => {
    setSelectedProduct(product);
    
    // Record view interaction when product modal is opened
    if (user) {
      try {
        await axios.post('http://localhost:5000/api/interactions', {
          user_id: user.userId,
          product_id: product.product_id,
          interaction_type: 'view'
        });
      } catch (error) {
        console.error('Error recording view interaction:', error);
      }
    }
  };

  const handleClose = () => {
    setSelectedProduct(null);
  };

  // Calculate data for charts
  const categoryData = recommendations.reduce((acc: any[], rec) => {
    const existing = acc.find(item => item.name === rec.category);
    if (existing) {
      existing.count++;
    } else {
      acc.push({ name: rec.category, count: 1 });
    }
    return acc;
  }, []);

  const priceRanges = ['0-50', '51-100', '101-200', '201-500', '500+'];
  const priceData = priceRanges.map(range => {
    const [min, max] = range.split('-').map(Number);
    const count = recommendations.filter(rec => {
      if (max) {
        return rec.price >= min && rec.price <= max;
      }
      return rec.price >= min;
    }).length;
    return { range, count };
  });

  if (loading) {
    return (
      <div className="container loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>Personalized Recommendations</h1>
      
      <SearchBar onSearch={handleSearch} />
      
      <div className="grid">
        {recommendations.map((rec) => (
          <div key={rec.product_id} className="card product-card" onClick={() => handleCardClick(rec)}>
            <img
              className="card-media"
              src={`https://via.placeholder.com/300x200?text=${rec.brand}`}
              alt={rec.brand}
            />
            <div className="card-content">
              <h2>{rec.product_name}</h2>
              <p className="product-meta">
                {rec.category} 
              </p>
              <p className="recommendation-source">
                Recommended by: {rec.recommendation_category}
              </p>
              <p className="price">${rec.price.toFixed(2)}</p>
            </div>
          </div>
        ))}
      </div>

      {selectedProduct && (
        <div className="modal" onClick={handleClose}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedProduct.product_name}</h2>
              <button className="close-button" onClick={handleClose}>×</button>
            </div>
            <div className="modal-body">
              <div className="product-detail-grid">
                <div className="product-image-container">
                  <img
                    src={`https://via.placeholder.com/600x400?text=${selectedProduct.brand}`}
                    alt={selectedProduct.product_name}
                    className="product-detail-image"
                  />
                </div>
                <div className="product-info">
                  <p className="product-meta">
                    Category: {selectedProduct.category}<br />
                    Brand: {selectedProduct.brand}<br />
                    {/* Score: {(selectedProduct.score * 100).toFixed(1)}% */}
                  </p>
                  <p className="recommendation-source">
                    Recommended by: {selectedProduct.recommendation_category}
                  </p>
                  <p className="price">${selectedProduct.price.toFixed(2)}</p>
                  <p className="product-description">{selectedProduct.description}</p>
                  <div className="product-actions">
                    <button
                      className="btn-primary"
                      onClick={() => handleInteraction(selectedProduct.product_id, 'add_to_cart')}
                    >
                      Add to Cart
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => handleInteraction(selectedProduct.product_id, 'purchase')}
                    >
                      Purchase
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="charts-section">
        <h2>Recommendation Insights</h2>
        <div className="chart-container">
          <h3>Recommendations by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categoryData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={60} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Price Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={priceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" angle={-45} textAnchor="end" height={60} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#ff7300" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Recommendations;