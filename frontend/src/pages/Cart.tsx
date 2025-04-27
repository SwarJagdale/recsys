import React, { useEffect, useState } from 'react';
import { Box, Typography, List, ListItem, ListItemText, IconButton, Divider, Button, CircularProgress } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface CartItem {
  product_id: string;
  name: string;
  price: number;
  quantity: number;
}

const Cart: React.FC = () => {
  const { user } = useAuth();
  const [cart, setCart] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCart = async () => {
      if (!user) return;
      setLoading(true);
      try {
        const res = await axios.get(`http://localhost:5000/api/cart_interactions/${user.userId}`);
        // Group by product_id and count quantity
        const grouped = res.data.cart_interactions.reduce((acc: any, curr: any) => {
          const pid = curr.product_id;
          if (!acc[pid]) acc[pid] = { product_id: pid, quantity: 0 };
          acc[pid].quantity += 1;
          return acc;
        }, {});
        const cartItems = Object.values(grouped);
        // Fetch product details for each product_id
        const detailedCart = await Promise.all(
          cartItems.map(async (item: any) => {
            try {
              const prodRes = await axios.get(`http://localhost:5000/api/products/${item.product_id}`);
              return {
                ...item,
                name: prodRes.data.name,
                price: prodRes.data.price
              };
            } catch (e) {
              return { ...item, name: 'Unknown Product', price: 0 };
            }
          })
        );
        setCart(detailedCart);
      } catch (err) {
        setCart([]);
      } finally {
        setLoading(false);
      }
    };
    fetchCart();
  }, [user]);

  const handleRemove = (product_id: string) => {
    setCart(cart.filter(item => item.product_id !== product_id));
    // Optionally: call backend to remove item from cart
  };

  const total = cart.reduce((sum, item) => sum + (item.price || 0) * (item.quantity || 1), 0);

  if (loading) {
    return (
      <Box p={3} display="flex" justifyContent="center"><CircularProgress /></Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Your Cart
      </Typography>
      {cart.length === 0 ? (
        <Typography variant="body1">Your cart is currently empty.</Typography>
      ) : (
        <>
          <List>
            {cart.map(item => (
              <React.Fragment key={item.product_id}>
                <ListItem
                  secondaryAction={
                    <IconButton edge="end" aria-label="delete" onClick={() => handleRemove(item.product_id)}>
                      <DeleteIcon />
                    </IconButton>
                  }
                >
                  <ListItemText
                    primary={`${item.name} (x${item.quantity})`}
                    secondary={`$${item.price?.toFixed(2) || '0.00'} each`}
                  />
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
          <Box mt={2} display="flex" justifyContent="space-between">
            <Typography variant="h6">Total: ${total.toFixed(2)}</Typography>
            <Button variant="contained" color="primary" disabled={cart.length === 0}>
              Checkout
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
};

export default Cart;
