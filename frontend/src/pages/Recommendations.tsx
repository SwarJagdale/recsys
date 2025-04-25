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
                  {rec.brand}
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
    </Container>
  );
};

export default Recommendations; 