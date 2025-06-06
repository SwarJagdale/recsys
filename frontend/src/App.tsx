import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Home from './pages/Home';
import ProductDetail from './pages/ProductDetail';
import Recommendations from './pages/Recommendations';
import Cart from './pages/Cart';
import PreviousOrders from './pages/PreviousOrders';
import Profile from './pages/Profile';
import './App.css';

const AppRoutes: React.FC = () => {
  const { isAuthenticated } = useAuth();
  return (
    <>
      <Navbar />
      <Routes>
        {!isAuthenticated ? (
          <>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </>
        ) : (
          <>
            <Route path="/" element={<Navigate to="/recommendations" replace />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/home" element={<Home />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route path="/cart" element={<Cart />} />
            <Route path="/orders" element={<PreviousOrders />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="*" element={<Navigate to="/recommendations" replace />} />
          </>
        )}
      </Routes>
    </>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
};

export default App;