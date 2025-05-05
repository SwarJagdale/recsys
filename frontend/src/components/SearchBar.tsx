import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ApiProduct {
  _id: string;
  name: string;
  category: string;
  brand: string;
  price: number;
  description: string;
}

interface Product {
  product_id: string;
  product_name: string;
  category: string;
  brand: string;
  price: number;
  score: number;
  recommendation_category: string;
  description: string;
}

interface SearchBarProps {
  onSearch: (products: Product[]) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch }) => {
  const [searchText, setSearchText] = useState('');
  const [category, setCategory] = useState<string>('');
  const [brand, setBrand] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const response = await axios.get<{ products: ApiProduct[] }>('http://localhost:5000/api/products');
        const products = response.data.products;
        
        const uniqueCategories = [...new Set(products.map(p => p.category))];
        const uniqueBrands = [...new Set(products.map(p => p.brand))];
        
        setCategories(uniqueCategories.sort());
        setBrands(uniqueBrands.sort());
      } catch (error) {
        console.error('Error fetching filters:', error);
      }
    };
    fetchFilters();
  }, []);

  const handleSearch = async () => {
    try {
      const params = new URLSearchParams();
      if (searchText) params.append('query', searchText);
      if (category) params.append('category', category);
      if (brand) params.append('brand', brand);

      const response = await axios.get<{ products: ApiProduct[] }>(`http://localhost:5000/api/products/search?${params.toString()}`);
      
      // Transform API products to match the Product interface used in Recommendations
      const transformedProducts: Product[] = response.data.products.map(p => ({
        product_id: p._id,
        product_name: p.name,
        category: p.category,
        brand: p.brand,
        price: p.price,
        score: 1, // Default score for search results
        recommendation_category: 'Search Result',
        description: p.description
      }));

      onSearch(transformedProducts);
    } catch (error) {
      console.error('Error searching products:', error);
      onSearch([]);
    }
  };

  return (
    <div className="search-bar">
      <div className="search-container">
        <div className="search-input-group">
          <input
            type="text"
            className="input-field"
            placeholder="Search products..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="btn-primary search-button" onClick={handleSearch}>
            Search
          </button>
        </div>
        <div className="filter-container">
          <select
            className="input-field"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
          <select
            className="input-field"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
          >
            <option value="">All Brands</option>
            {brands.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

export default SearchBar;