import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Typography,
  Button,
  Box,
  CircularProgress,
  Alert,
  Stack,
} from '@mui/material';

interface Recommendation {
  product_id: string;
  category: string;
  brand: string;
  price: number;
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
        const response = await axios.get(`http://localhost:5000/api/recommendations/${user.id}`);
        setRecommendations(response.data.recommendations || []);
      } catch (err) {
        setError('Failed to fetch recommendations.');
      } finally {
        setLoading(false);
      }
    };
    fetchRecommendations();
  }, [user]);

  const handleInteraction = async (productId: string, interactionType: string) => {
    setActionError('');
    setActionSuccess('');
    if (!user) return;
    try {
      await axios.post('http://localhost:5000/api/interactions', {
        user_id: user.id,
        product_id: productId,
        interaction_type: interactionType,
      });
      setActionSuccess(`Successfully recorded ${interactionType} interaction!`);
    } catch (err) {
      setActionError(`Failed to record ${interactionType} interaction.`);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!recommendations.length) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="info">No recommendations available.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Recommended for You
      </Typography>
      {actionError && <Alert severity="error" sx={{ mb: 2 }}>{actionError}</Alert>}
      {actionSuccess && <Alert severity="success" sx={{ mb: 2 }}>{actionSuccess}</Alert>}
      <Grid container spacing={4}>
        {recommendations.map((rec) => (
          <Grid item key={rec.product_id} xs={12} sm={6} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardMedia
                component="img"
                height="200"
                image={'https://via.placeholder.com/300x200'}
                alt={rec.category}
              />
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography gutterBottom variant="h6" component="h2">
                  {rec.brand} ({rec.category})
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Product ID: {rec.product_id}
                </Typography>
                <Typography variant="h6" color="primary" sx={{ mt: 2 }}>
                  ${rec.price.toFixed(2)}
                </Typography>
                <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                  <Button variant="outlined" onClick={() => handleInteraction(rec.product_id, 'view')}>
                    View
                  </Button>
                  <Button variant="contained" color="primary" onClick={() => handleInteraction(rec.product_id, 'add_to_cart')}>
                    Add to Cart
                  </Button>
                  <Button variant="contained" color="secondary" onClick={() => handleInteraction(rec.product_id, 'purchase')}>
                    Purchase
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default Recommendations; 