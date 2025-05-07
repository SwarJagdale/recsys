import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface OrderItem {
  product_id: string;
  product_name: string;
  price: number;
  description: string;
  category: string;
  brand: string;
  timestamp: string;
}

const PreviousOrders: React.FC = () => {
  const { user } = useAuth();
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrders = async () => {
      if (!user) return;
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/api/previous_orders/${user.user_id}`);
        setOrders(response.data.previous_orders);
      } catch (error) {
        console.error('Error fetching orders:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, [user]);

  if (loading) {
    return (
      <div className="container loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>Previous Orders</h1>
      {orders.length === 0 ? (
        <div className="empty-orders">
          <p>No previous orders found</p>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map((order) => {
            const dateObj = new Date(order.timestamp);
            return (
              <div key={`${order.product_id}-${order.timestamp}`} className="order-item">
                <div className="order-header">
                  <h3>{order.product_name}</h3>
                  <span className="price">${order.price?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="order-details">
                  <p className="description">{order.description}</p>
                  <div className="meta-info">
                    <span className="category">Category: {order.category}</span>
                    <span className="brand">Brand: {order.brand}</span>
                  </div>
                  <div className="order-meta">
                    <span className="order-date">Ordered on: {dateObj.toLocaleDateString()} at {dateObj.toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default PreviousOrders;
