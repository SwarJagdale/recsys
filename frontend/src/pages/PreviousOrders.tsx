import React, { useEffect, useState } from 'react';
import { Box, Typography, List, ListItem, ListItemText, Divider, Paper, CircularProgress } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface OrderItem {
  name: string;
  price: number;
  quantity: number;
}

interface Order {
  order_id: string;
  date: string;
  items: OrderItem[];
  total: number;
}

const PreviousOrders: React.FC = () => {
  const { user } = useAuth();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrders = async () => {
      if (!user) return;
      setLoading(true);
      try {
        const res = await axios.get(`http://localhost:5000/api/previous_orders/${user.userId}`);
        let orders = res.data.previous_orders || [];
        // Normalize timestamp from MongoDB extended JSON
        orders = orders.map((order: any) => {
          let ts = order.timestamp;
          if (ts && ts.$date) {
            ts = ts.$date;
          }
          return { ...order, timestamp: ts };
        });
        // Sort by timestamp descending (newest first)
        orders.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        setOrders(orders);
      } catch (err) {
        setOrders([]);
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, [user]);

  if (loading) {
    return (
      <Box p={3} display="flex" justifyContent="center"><CircularProgress /></Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Previous Orders
      </Typography>
      {orders.length === 0 ? (
        <Typography variant="body1">You have no previous orders.</Typography>
      ) : (
        <List>
          {orders.map((order, idx) => {
            const dateObj = new Date(order.timestamp);
            return (
              <Paper key={order._id?.$oid || order._id || idx} elevation={2} sx={{ mb: 2, p: 2 }}>
                <Typography variant="h6">Order for Product ID: {order.product_id}</Typography>
                <Typography variant="subtitle2">
                  Date: {dateObj.toLocaleDateString()}<br />
                  Time: {dateObj.toLocaleTimeString()}
                </Typography>
                <Divider />
              </Paper>
            );
          })}
        </List>
      )}
    </Box>
  );
};

export default PreviousOrders;
