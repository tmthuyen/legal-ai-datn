import React from 'react';
import { ColorContext } from '../contexts/ColorContext';

export function useColor() {
  const context = React.useContext(ColorContext);

  if (!context) {
    throw new Error('useColor must be used within ColorProvider');
  }

  return context;
}
