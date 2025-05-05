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

  const handleSearch = async (query: string) => {
    try {
      const response = await axios.get(`http://localhost:5000/api/products/search?query=${query}`);
      const products = response.data.products.map((p: Product) => ({
        product_id: p.product_id,
        product_name: p.product_name,
        category: p.category,
        brand: p.brand,
        price: p.price,
        description: p.description
      }));
      onSearch(products);
    } catch (error) {
      console.error('Error searching products:', error);
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
            onKeyPress={(e) => e.key === 'Enter' && handleSearch(searchText)}
          />
          <button className="btn-primary search-button" onClick={() => handleSearch(searchText)}>
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