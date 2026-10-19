import React from 'react';

type EventType = 'mousedown' | 'mouseup' | 'touchstart' | 'touchend' | 'focusin' | 'focusout';

function useClickOutside<T extends HTMLElement = HTMLElement>(
  ref: React.RefObject<T>,
  handler: (event: MouseEvent | TouchEvent | FocusEvent) => void,
  eventType: EventType = 'mousedown',
) {
  React.useEffect(() => {
    const root = window.document;

    const handleClickOutside = (event: MouseEvent | TouchEvent | FocusEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler(event);
        return;
      }
    };

    root.addEventListener(eventType, handleClickOutside);

    return () => {
      root.removeEventListener(eventType, handleClickOutside);
    };
  }, [ref]);
}

export default useClickOutside;
