import React from 'react';
import AuthContext from '../contexts/AuthContext';

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  const { user } = context;
  if (!user) {
    return { user: null, isAdmin: false, isAuthenticated: false };
  }

  const isAdmin = user.role_codes.includes('ADMIN');
  const isAuthenticated = !!user;

  return { user, isAdmin, isAuthenticated };
};
