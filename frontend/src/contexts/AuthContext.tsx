import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

interface User {
  user_id: string;
  email: string;
  name: string;
  interactions: {
    product_id: string;
    interaction_type: string;
    timestamp: string;
  }[];
  preferences: any;
  location?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string, location: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const getInitialUser = () => {
  try {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  } catch {
    return null;
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(getInitialUser());
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
    }
  }, [user]);

  const login = async (email: string, password: string) => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/api/login`, { email, password });
      const { user_id, preferences } = response.data;
      const user = { user_id, email, name: '', preferences, interactions: [], location: '' };
      setUser(user);
      setToken(null);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const signup = async (email: string, password: string, name: string, location: string) => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/api/signup`, { 
        email, 
        password, 
        name,
        location 
      });
      const { user_id, email: userEmail, name: userName, preferences, interactions, location: userLocation } = response.data;
      const user = { 
        user_id, 
        email: userEmail, 
        name: userName, 
        preferences, 
        interactions, 
        location: userLocation 
      };
      setUser(user);
      setToken(null);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } catch (error) {
      console.error('Signup failed:', error);
      throw error;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      login,
      signup,
      logout,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};