import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import SearchBar from '../components/SearchBar';

interface Product {
  product_id: string;
  product_name: string;
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
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get<{ products: Product[] }>('http://localhost:5000/api/products');
      setProducts(response.data.products);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (searchResults: SearchProduct[]) => {
    // Transform search results back to ApiProduct format
    const transformedProducts: Product[] = searchResults.map(p => ({
      product_id: p.product_id,
      product_name: p.product_name,
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
        user_id: user.user_id,
        product_id: productId,
        interaction_type: interactionType
      });
      // Refresh products
      const response = await axios.get('http://localhost:5000/api/products');
      setProducts(response.data.products);
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
      {/* <SearchBar onSearch={handleSearch} /> */}
      <div className="grid">
        {products.map((product) => (
          <div key={product.product_id} className="card product-card">
            <img
              className="card-media"
              src={product.image || 'https://via.placeholder.com/300x200'}
              alt={product.product_name}
            />
            <div className="card-content">
              <h2 className="product-title">{product.product_name}</h2>
              <p className="product-category">{product.category} • {product.brand}</p>
              <p className="product-description">{product.description}</p>
              <p className="price">${product.price.toFixed(2)}</p>
              <div className="product-actions">
                <button 
                  className="btn-secondary"
                  onClick={() => handleInteraction(product.product_id, 'view')}
                >
                  View Details
                </button>
                <button
                  className="btn-primary"
                  onClick={() => handleInteraction(product.product_id, 'add_to_cart')}
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