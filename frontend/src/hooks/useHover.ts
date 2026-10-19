'use client';
import React from 'react';

function useHover<T extends HTMLElement = HTMLElement>(
  elementRef: React.RefObject<T>,
): { isHovered: boolean } {
  const [isHovered, setIsHovered] = React.useState(false);

  React.useEffect(() => {
    const node = elementRef.current;

    if (!node) return;

    const handleMouseLeave = () => {
      setIsHovered(false);
    };
    const handleMouseEnter = () => {
      setIsHovered(true);
    };

    node.addEventListener('mouseenter', handleMouseEnter);
    node.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      node.removeEventListener('mouseenter', handleMouseEnter);
      node.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return { isHovered };
}

export default useHover;
