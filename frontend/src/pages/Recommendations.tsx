import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Typography,
  Box,
  IconButton,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  ShoppingCart,
  Favorite,
  Visibility,
} from '@mui/icons-material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line, CartesianGrid
} from 'recharts';

interface Recommendation {
  product_id: string;
  category: string;
  brand: string;
  price: number;
}

const Recommendations: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!user) return;

      try {
        const response = await axios.get(
          `http://localhost:5000/api/recommendations/${user.userId}`
        );
        setRecommendations(response.data.recommendations);
      } catch (error) {
        console.error('Error fetching recommendations:', error);
        setError('Failed to load recommendations. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [user]);

  const handleInteraction = async (productId: string, interactionType: string) => {
    if (!user) return;

    try {
      await axios.post('http://localhost:5000/api/interactions', {
        user_id: user.userId,
        product_id: productId,
        interaction_type: interactionType,
      });
    } catch (error) {
      console.error('Error recording interaction:', error);
    }
  };

  // Chart data computation
  const brandData = recommendations.reduce((acc, rec) => {
    const idx = acc.findIndex(item => item.brand === rec.brand);
    if (idx > -1) acc[idx].count += 1;
    else acc.push({ brand: rec.brand, count: 1 });
    return acc;
  }, [] as { brand: string; count: number }[]);

  const categoryData = recommendations.reduce((acc, rec) => {
    const idx = acc.findIndex(item => item.category === rec.category);
    if (idx > -1) acc[idx].count += 1;
    else acc.push({ category: rec.category, count: 1 });
    return acc;
  }, [] as { category: string; count: number }[]);

  const prices = recommendations.map(r => r.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const binCount = 10;
  const binWidth = (maxPrice - minPrice) / binCount || 1;
  const priceData = Array.from({ length: binCount }, (_, i) => {
    const start = minPrice + i * binWidth;
    const end = start + binWidth;
    const count = recommendations.filter(r => r.price >= start && r.price < end).length;
    return { range: `${start.toFixed(0)}-${end.toFixed(0)}`, count };
  });

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '80vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Personalized Recommendations
      </Typography>
      {/* Charts: Brand, Category, Price Distribution */}
     
      <Grid container spacing={4}>
        {recommendations.map((rec) => (
          <Grid item key={rec.product_id} xs={12} sm={6} md={4}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': {
                  transform: 'scale(1.02)',
                  transition: 'transform 0.2s ease-in-out',
                },
              }}
            >
              <CardMedia
                component="img"
                height="200"
                image={`https://via.placeholder.com/300x200?text=${rec.brand}`}
                alt={rec.brand}
              />
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography gutterBottom variant="h5" component="h2">
                  {rec.product_id} by {rec.brand}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Category: {rec.category}
                </Typography>
                <Typography variant="h6" color="primary" sx={{ mt: 2 }}>
                  ${rec.price.toFixed(2)}
                </Typography>
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
                  <IconButton
                    color="primary"
                    onClick={() => handleInteraction(rec.product_id, 'view')}
                  >
                    <Visibility />
                  </IconButton>
                  <IconButton
                    color="primary"
                    onClick={() => handleInteraction(rec.product_id, 'add_to_cart')}
                  >
                    <ShoppingCart />
                  </IconButton>
                  <IconButton
                    color="primary"
                    onClick={() => handleInteraction(rec.product_id, 'purchase')}
                  >
                    <Favorite />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      <Box sx={{ my: 4 }}>
        <Typography variant="h5" gutterBottom>Recommendations by Brand</Typography>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={brandData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <XAxis dataKey="brand" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>

        <Typography variant="h5" sx={{ mt: 4 }} gutterBottom>Recommendations by Category</Typography>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={categoryData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>

        <Typography variant="h5" sx={{ mt: 4 }} gutterBottom>Price Distribution</Typography>
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
      </Box>
    </Container>
  );
};

export default Recommendations;