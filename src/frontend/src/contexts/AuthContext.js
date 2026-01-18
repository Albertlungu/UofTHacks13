import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const API_BASE = 'http://localhost:5001/api/auth';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      } else {
        logout();
      }
    } catch (err) {
      console.error('Failed to fetch user:', err);
    }
  };

  const signup = async (username, password, email = '') => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password, email })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        localStorage.setItem('token', data.token);
        setToken(data.token);
        setUser({ username: data.username });
        return { success: true };
      } else {
        setError(data.error);
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = 'Failed to connect to server';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        localStorage.setItem('token', data.token);
        setToken(data.token);
        setUser({ username: data.username, user_id: data.user_id });
        return { success: true };
      } else {
        setError(data.error);
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMsg = 'Failed to connect to server';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setError(null);
  };

  const getProfile = async (password) => {
    if (!token) return { success: false, error: 'Not authenticated' };
    
    try {
      // Note: Using POST instead of GET to properly send password in body
      const response = await fetch(`${API_BASE}/profile`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password, action: 'get' })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        return { success: true, profile: data.profile };
      } else {
        return { success: false, error: data.error };
      }
    } catch (err) {
      return { success: false, error: 'Failed to fetch profile' };
    }
  };

  const updateProfile = async (password, profile) => {
    if (!token) return { success: false, error: 'Not authenticated' };
    
    try {
      const response = await fetch(`${API_BASE}/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password, profile })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        return { success: true, message: data.message };
      } else {
        return { success: false, error: data.error };
      }
    } catch (err) {
      return { success: false, error: 'Failed to update profile' };
    }
  };

  const value = {
    user,
    token,
    loading,
    error,
    signup,
    login,
    logout,
    getProfile,
    updateProfile,
    isAuthenticated: !!token && !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
