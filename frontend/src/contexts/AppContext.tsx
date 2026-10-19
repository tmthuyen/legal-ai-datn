import React from 'react';
import { ColorProvider } from './ColorContext';
import { AuthProvider } from './AuthContext';

function AppContext({ children }: { children: React.ReactNode }) {
  return (
    <ColorProvider>
      <AuthProvider>{children}</AuthProvider>
    </ColorProvider>
  );
}

export default AppContext;
