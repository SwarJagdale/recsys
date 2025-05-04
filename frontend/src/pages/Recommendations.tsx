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
  Dialog,
  DialogContent,
  DialogActions,
  Button,
  CardActionArea,
  AppBar,
  Toolbar,
  Slide,
} from '@mui/material';
import {
  ShoppingCart,
  Favorite,
  Close as CloseIcon,
} from '@mui/icons-material';
import { TransitionProps } from '@mui/material/transitions';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import SearchBar from '../components/SearchBar';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line, CartesianGrid
} from 'recharts';

const Transition = React.forwardRef(function Transition(
  props: TransitionProps & {
    children: React.ReactElement;
  },
  ref: React.Ref<unknown>,
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

interface Product {
  _id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  brand: string;
  image?: string;
}

interface Recommendation {
  product_id: string;
  category: string;
  brand: string;
  price: number;
  product_name: string;
  description: string;
  score: number;
  recommendation_category: string;
}

interface SelectedProduct extends Recommendation {
  open: boolean;
}

const Recommendations: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<SelectedProduct | null>(null);
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

  const handleCardClick = (product: Recommendation) => {
    setSelectedProduct({ ...product, open: true });
    handleInteraction(product.product_id, 'view');
  };

  const handleClose = () => {
    setSelectedProduct(null);
  };

  const handleSearch = (searchResults: Product[]) => {
    // Transform Product[] to Recommendation[] format
    const transformedResults: Recommendation[] = searchResults.map(product => ({
      product_id: product._id,
      product_name: product.name,
      description: product.description,
      price: product.price,
      category: product.category,
      brand: product.brand,
      score: 1, // Default score for searched items
      recommendation_category: 'Search Result'
    }));
    setRecommendations(transformedResults);
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
      
      <SearchBar onSearch={handleSearch} />
      
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
              <CardActionArea onClick={() => handleCardClick(rec)}>
                <CardMedia
                  component="img"
                  height="200"
                  image={`https://via.placeholder.com/300x200?text=${rec.brand}`}
                  alt={rec.brand}
                />
                <CardContent>
                  <Typography gutterBottom variant="h6" component="h2">
                    {rec.product_name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {rec.category} • Score: {(rec.score * 100).toFixed(1)}%
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Recommended by: {rec.recommendation_category}
                    </Typography>
                  </Box>
                  <Typography variant="h6" color="primary">
                    ${rec.price.toFixed(2)}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog
        fullScreen
        open={Boolean(selectedProduct)}
        onClose={handleClose}
        TransitionComponent={Transition}
      >
        {selectedProduct && (
          <>
            <AppBar sx={{ position: 'relative' }}>
              <Toolbar>
                <IconButton
                  edge="start"
                  color="inherit"
                  onClick={handleClose}
                  aria-label="close"
                >
                  <CloseIcon />
                </IconButton>
                <Typography sx={{ ml: 2, flex: 1 }} variant="h6" component="div">
                  {selectedProduct.product_name}
                </Typography>
                <Box>
                  <IconButton
                    color="inherit"
                    onClick={() => handleInteraction(selectedProduct.product_id, 'add_to_cart')}
                  >
                    <ShoppingCart />
                  </IconButton>
                  <IconButton
                    color="inherit"
                    onClick={() => handleInteraction(selectedProduct.product_id, 'purchase')}
                  >
                    <Favorite />
                  </IconButton>
                </Box>
              </Toolbar>
            </AppBar>
            <DialogContent>
              <Box sx={{ maxWidth: 'lg', margin: 'auto', mt: 4 }}>
                <Grid container spacing={4}>
                  <Grid item xs={12} md={6}>
                    <Box
                      component="img"
                      src={`https://via.placeholder.com/600x400?text=${selectedProduct.brand}`}
                      alt={selectedProduct.brand}
                      sx={{
                        width: '100%',
                        height: 'auto',
                        borderRadius: '8px'
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h4" gutterBottom>
                      {selectedProduct.product_name}
                    </Typography>
                    <Typography variant="h5" color="primary" gutterBottom>
                      ${selectedProduct.price.toFixed(2)}
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Recommendation Score: {(selectedProduct.score * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="subtitle1" gutterBottom>
                        Recommendation Type: {selectedProduct.recommendation_category}
                      </Typography>
                    </Box>
                    <Typography variant="h6" gutterBottom>
                      {selectedProduct.brand}
                    </Typography>
                    <Typography variant="subtitle1" gutterBottom>
                      Category: {selectedProduct.category}
                    </Typography>
                    <Typography variant="body1" paragraph sx={{ mt: 3 }}>
                      {selectedProduct.description}
                    </Typography>
                    <Box sx={{ mt: 4 }}>
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<ShoppingCart />}
                        onClick={() => handleInteraction(selectedProduct.product_id, 'add_to_cart')}
                        sx={{ mr: 2 }}
                      >
                        Add to Cart
                      </Button>
                      <Button
                        variant="outlined"
                        color="primary"
                        startIcon={<Favorite />}
                        onClick={() => handleInteraction(selectedProduct.product_id, 'purchase')}
                      >
                        Purchase Now
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            </DialogContent>
          </>
        )}
      </Dialog>

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