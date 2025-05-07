import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface CartItem {
  product_id: string;
  product_name: string;
  price: number;
  quantity: number;
}

const Cart: React.FC = () => {
  const { user } = useAuth();
  const [cart, setCart] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCart = async () => {
      if (!user) return;
      setLoading(true);
      try {
        const res = await axios.get(`${process.env.REACT_APP_API_URL}/api/cart_interactions/${user.user_id}`);
        // Group by product_id and count quantity
        const grouped = res.data.cart_interactions.reduce((acc: any, curr: any) => {
          const pid = curr.product_id;
          if (!acc[pid]) {
            acc[pid] = {
              product_id: pid,
              product_name: curr.product_name,
              price: curr.price,
              quantity: 0
            };
          }
          acc[pid].quantity++;
          return acc;
        }, {});
        
        setCart(Object.values(grouped));
      } catch (error) {
        console.error('Error fetching cart:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCart();
  }, [user]);

  const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  const handleInteraction = async (productId: string, interactionType: string) => {
    if (!user) return;
    try {
      await axios.post(`${process.env.REACT_APP_API_URL}/api/interactions`, {
        user_id: user.user_id,
        product_id: productId,
        interaction_type: interactionType
      });
      // Refresh cart items
      const response = await axios.get(`${process.env.REACT_APP_API_URL}/api/cart_interactions/${user.user_id}`);
      setCart(response.data.cart_interactions);
    } catch (error) {
      console.error('Error recording interaction:', error);
    }
  };

  if (loading) {
    return (
      <div className="container loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>Shopping Cart</h1>
      {cart.length === 0 ? (
        <div className="empty-cart">
          <p>Your cart is empty</p>
        </div>
      ) : (
        <div className="cart-container">
          <div className="cart-items">
            {cart.map((item) => (
              <div key={item.product_id} className="cart-item">
                <div className="item-details">
                  <h3>{item.product_name}</h3>
                  <p className="price">${item.price?.toFixed(2) || '0.00'} each</p>
                  <p className="quantity">Quantity: {item.quantity}</p>
                </div>
                <div className="item-total">
                  ${(item.price * item.quantity).toFixed(2)}
                </div>
              </div>
            ))}
          </div>
          <div className="cart-summary">
            <div className="cart-total">
              <span>Total:</span>
              <span className="price">${total.toFixed(2)}</span>
            </div>
            <button 
              className="btn-primary checkout-button"
              disabled={cart.length === 0}
            >
              Checkout
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Cart;
