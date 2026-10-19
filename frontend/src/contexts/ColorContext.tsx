'use client';

import React from 'react';

type ThemeColor = 'rose' | 'emerald' | 'blue' | 'violet' | 'orange';

export const ColorContext = React.createContext<{
  color: ThemeColor;
  changeColor: (color: ThemeColor) => void;
    } | null>(null);

export function ColorProvider({ children }: { children: React.ReactNode }) {
  const [color, setColor] = React.useState<ThemeColor>('blue');

  React.useEffect(() => {
    const storedColor = (localStorage.getItem('theme-color') as ThemeColor | null) || 'blue';

    document.documentElement.dataset.theme = storedColor;
    setColor(storedColor);
  }, []);

  const changeColor = (newColor: ThemeColor) => {
    document.documentElement.dataset.theme = newColor;
    localStorage.setItem('theme-color', newColor);
    setColor(newColor);
  };

  return <ColorContext.Provider value={{ color, changeColor }}>{children}</ColorContext.Provider>;
}
