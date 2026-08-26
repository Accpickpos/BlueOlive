'use client';

import { useEffect, useState } from 'react';

/**
 * Returns `value`, delayed by `delayMs` after it stops changing. Used to
 * debounce search-as-you-type inputs before firing a network request.
 */
export function useDebouncedValue<T>(value: T, delayMs: number = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

export default useDebouncedValue;
