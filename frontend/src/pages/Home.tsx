import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import SearchBar from '../components/SearchBar';

interface ApiProduct {
  _id: string;
  name: string;
  category: string;
  brand: string;
  price: number;
  description: string;
  image?: string;
}

interface SearchProduct {
  product_id: string;
  product_name: string;
  category: string;
  brand: string;
  price: number;
  score: number;
  recommendation_category: string;
  description: string;
}

const Home: React.FC = () => {
  const [products, setProducts] = useState<ApiProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get<{ products: ApiProduct[] }>('http://localhost:5000/api/products');
      setProducts(response.data.products);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (searchResults: SearchProduct[]) => {
    // Transform search results back to ApiProduct format
    const transformedProducts: ApiProduct[] = searchResults.map(p => ({
      _id: p.product_id,
      name: p.product_name,
      category: p.category,
      brand: p.brand,
      price: p.price,
      description: p.description
    }));
    setProducts(transformedProducts);
  };

  const handleInteraction = async (productId: string, interactionType: string) => {
    if (!user) return;
    try {
      await axios.post('http://localhost:5000/api/interactions', {
        user_id: user.id,
        product_id: productId,
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

  return (
    <div className="container">
      <h1>Browse Products</h1>
      <SearchBar onSearch={handleSearch} />
      <div className="grid">
        {products.map((product) => (
          <div key={product._id} className="card product-card">
            <img
              className="card-media"
              src={product.image || 'https://via.placeholder.com/300x200'}
              alt={product.name}
            />
            <div className="card-content">
              <h2 className="product-title">{product.name}</h2>
              <p className="product-category">{product.category} • {product.brand}</p>
              <p className="product-description">{product.description}</p>
              <p className="price">${product.price.toFixed(2)}</p>
              <div className="product-actions">
                <button 
                  className="btn-secondary"
                  onClick={() => handleInteraction(product._id, 'view')}
                >
                  View Details
                </button>
                <button
                  className="btn-primary"
                  onClick={() => handleInteraction(product._id, 'add_to_cart')}
                >
                  Add to Cart
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Home;