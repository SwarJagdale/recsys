import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface Product {
  product_id: string;
  product_name: string;
  description: string;
  price: number;
  category: string;
  brand: string;
  image?: string;
}

const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await axios.get(`http://localhost:5000/api/products/${id}`);
        setProduct(response.data);
        
        // Send view interaction when product is loaded
        if (user) {
          await axios.post('http://localhost:5000/api/interactions', {
            user_id: user.id,
            product_id: response.data.product_id,
            interaction_type: 'view',
          });
        }
      } catch (err) {
        setError('Failed to load product details');
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [id, user]);

  const handleInteraction = async (interactionType: string) => {
    if (!user || !product) return;

    try {
      await axios.post('http://localhost:5000/api/interactions', {
        user_id: user.id,
        product_id: product.product_id,
        interaction_type: interactionType,
      });
    } catch (error) {
      console.error('Error recording interaction:', error);
    }
  };

  if (loading) {
    return (
      <div className="container loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container">
        <div className="alert alert-error">Product not found</div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="back-button">
        <button className="btn-secondary" onClick={() => navigate(-1)}>
          ← Back
        </button>
      </div>

      <div className="product-detail-grid">
        <div className="product-image-container">
          <img
            src={product.image || `https://via.placeholder.com/600x400?text=${product.brand}`}
            alt={product.product_name}
            className="product-detail-image"
          />
        </div>

        <div className="product-info">
          <h1>{product.product_name}</h1>
          <p className="price">${product.price.toFixed(2)}</p>
          <p className="product-description">{product.description}</p>
          <div className="product-meta">
            <p>Category: {product.category}</p>
            <p>Brand: {product.brand}</p>
          </div>
          <div className="product-actions">
            <button 
              className="btn-primary"
              onClick={() => handleInteraction('add_to_cart')}
            >
              Add to Cart
            </button>
            <button
              className="btn-secondary"
              onClick={() => handleInteraction('purchase')}
            >
              Purchase
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;