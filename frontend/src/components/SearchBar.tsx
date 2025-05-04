import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Autocomplete,
  InputAdornment,
  IconButton,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import axios from 'axios';

interface Product {
  _id: string;
  name: string;
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
  const [category, setCategory] = useState<string | null>(null);
  const [brand, setBrand] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);

  useEffect(() => {
    // Fetch unique categories and brands
    const fetchFilters = async () => {
      try {
        const response = await axios.get<{ products: Product[] }>('http://localhost:5000/api/products');
        const products = response.data.products;
        
        // Extract unique categories and brands with proper typing
        const uniqueCategories = Array.from(new Set(products.map((p: Product) => p.category)));
        const uniqueBrands = Array.from(new Set(products.map((p: Product) => p.brand)));
        
        setCategories(uniqueCategories);
        setBrands(uniqueBrands);
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

      const response = await axios.get(`http://localhost:5000/api/products/search?${params.toString()}`);
      onSearch(response.data.products);
    } catch (error) {
      console.error('Error searching products:', error);
      onSearch([]);
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
      <TextField
        placeholder="Search products..."
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        sx={{ flexGrow: 1, minWidth: '200px' }}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton onClick={handleSearch}>
                <SearchIcon />
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
      <Autocomplete
        options={categories}
        value={category}
        onChange={(_, newValue) => setCategory(newValue)}
        renderInput={(params) => (
          <TextField {...params} label="Category" sx={{ minWidth: '200px' }} />
        )}
        sx={{ flexGrow: 1 }}
      />
      <Autocomplete
        options={brands}
        value={brand}
        onChange={(_, newValue) => setBrand(newValue)}
        renderInput={(params) => (
          <TextField {...params} label="Brand" sx={{ minWidth: '200px' }} />
        )}
        sx={{ flexGrow: 1 }}
      />
    </Box>
  );
};

export default SearchBar;