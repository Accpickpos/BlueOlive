'use client';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, X, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { useDebouncedValue } from '@/lib/hooks/useDebouncedValue';

export interface SearchComboboxProps<T> {
  /** Called once with the chosen item when the user selects a result. */
  onSelect: (item: T) => void;
  /** Fetches results for the given (already-debounced) query string. */
  searchFn: (query: string) => Promise<T[]>;
  /** Stable identity for a result row (used as the React key). */
  getId: (item: T) => string | number;
  /** Main display text — used for the input's placeholder-replacement value after selection. */
  getLabel: (item: T) => string;
  /** Custom row rendering; falls back to a plain label if omitted. */
  renderOption?: (item: T, isActive: boolean) => ReactNode;
  /** React Query cache key prefix — keep unique per entity type. */
  queryKeyPrefix: string;
  /** Minimum characters typed before searching. Default 0 (search immediately, including empty query). */
  minChars?: number;
  /** Debounce delay in ms. Default 300. */
  debounceMs?: number;
  placeholder?: string;
  label?: string;
  disabled?: boolean;
  /** Extra content rendered below the input, above any dropdown — e.g. a "Recent items" panel shown when the query is empty. */
  emptyQuerySlot?: ReactNode;
}

/**
 * Generic inline-dropdown search/typeahead. The one shared search UI for
 * debtors, stock items, creditors, and anywhere else "search and pick an
 * entity" is needed — see DebtorPicker / StockItemPicker / CreditorPicker
 * for the entity-specific wrappers around this.
 */
export function SearchCombobox<T>({
  onSelect,
  searchFn,
  getId,
  getLabel,
  renderOption,
  queryKeyPrefix,
  minChars = 0,
  debounceMs = 300,
  placeholder = 'Search...',
  label,
  disabled = false,
  emptyQuerySlot,
}: SearchComboboxProps<T>) {
  const [query, setQuery] = useState('');
  const [selectedLabel, setSelectedLabel] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebouncedValue(query, debounceMs);
  const searchReady = debouncedQuery.trim().length >= minChars;

  const { data: results = [], isFetching } = useQuery({
    queryKey: [queryKeyPrefix, 'search', debouncedQuery],
    queryFn: () => searchFn(debouncedQuery.trim()),
    enabled: isOpen && searchReady,
    staleTime: 10_000,
  });

  useEffect(() => {
    setActiveIndex(0);
  }, [results]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (item: T) => {
    onSelect(item);
    setSelectedLabel(getLabel(item));
    setQuery('');
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex((prev) => (prev < results.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex((prev) => (prev > 0 ? prev - 1 : prev));
        break;
      case 'Enter':
        e.preventDefault();
        if (results[activeIndex]) handleSelect(results[activeIndex]);
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  const showEmptyQuerySlot = isOpen && !debouncedQuery.trim() && !!emptyQuerySlot;
  const showResults = isOpen && searchReady && results.length > 0;
  const showNoResults = isOpen && searchReady && !isFetching && results.length === 0 && debouncedQuery === query;

  return (
    <div className="relative" ref={wrapperRef}>
      {label && (
        <label className="block text-sm font-medium mb-1.5 text-gray-700">{label}</label>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          type="text"
          value={query || selectedLabel}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelectedLabel('');
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="pl-10 pr-10"
          autoComplete="off"
        />
        {isFetching && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-gray-400" />
        )}
        {!isFetching && (query || selectedLabel) && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setSelectedLabel('');
              setIsOpen(false);
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2"
          >
            <X className="h-4 w-4 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {showEmptyQuerySlot && (
        <Card className="absolute z-50 w-full mt-1 shadow-lg border-gray-200">
          <CardContent className="p-3">{emptyQuerySlot}</CardContent>
        </Card>
      )}

      {showResults && (
        <Card className="absolute z-50 w-full mt-1 shadow-lg border-gray-200 max-h-80 overflow-y-auto">
          <CardContent className="p-0">
            {results.map((item, index) => (
              <button
                key={getId(item)}
                type="button"
                onClick={() => handleSelect(item)}
                onMouseEnter={() => setActiveIndex(index)}
                className={`w-full text-left px-4 py-3 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors ${
                  index === activeIndex ? 'bg-blue-50' : ''
                }`}
              >
                {renderOption ? renderOption(item, index === activeIndex) : getLabel(item)}
              </button>
            ))}
          </CardContent>
        </Card>
      )}

      {showNoResults && (
        <Card className="absolute z-50 w-full mt-1 shadow-lg border-gray-200">
          <CardContent className="p-4 text-center text-gray-500">
            {debouncedQuery.trim() ? `No results for "${debouncedQuery}"` : 'No results'}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default SearchCombobox;
