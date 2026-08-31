'use client';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, X, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { useDebouncedValue } from '@/lib/hooks/useDebouncedValue';

export interface SearchComboboxResults<T> {
  results: T[];
  /** Whether a next page exists beyond this one. */
  hasMore: boolean;
  /** Total matching count, if the backend provides one (used for "Page X of Y"). */
  count?: number;
}

export interface SearchComboboxProps<T> {
  /** Called once with the chosen item when the user selects a result. */
  onSelect: (item: T) => void;
  /** Fetches one page of results for the given (already-debounced) query string, starting at `offset`. */
  searchFn: (query: string, offset: number) => Promise<SearchComboboxResults<T>>;
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
  /** Results per page — must match what `searchFn` actually requests per page. Default 20. */
  pageSize?: number;
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
  pageSize = 20,
  placeholder = 'Search...',
  label,
  disabled = false,
  emptyQuerySlot,
}: SearchComboboxProps<T>) {
  const [query, setQuery] = useState('');
  const [selectedLabel, setSelectedLabel] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [offset, setOffset] = useState(0);
  const [coords, setCoords] = useState<{ top: number; left: number; width: number } | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebouncedValue(query, debounceMs);
  const searchReady = debouncedQuery.trim().length >= minChars;

  // Go back to page 1 whenever the search term actually changes.
  useEffect(() => {
    setOffset(0);
  }, [debouncedQuery]);

  const { data, isFetching } = useQuery({
    queryKey: [queryKeyPrefix, 'search', debouncedQuery, offset],
    queryFn: () => searchFn(debouncedQuery.trim(), offset),
    enabled: isOpen && searchReady,
    staleTime: 10_000,
  });

  const results = data?.results ?? [];
  const hasMore = data?.hasMore ?? false;
  const currentPage = Math.floor(offset / pageSize) + 1;

  useEffect(() => {
    setActiveIndex(0);
  }, [results]);

  // Position the dropdown against the input's real viewport location. This
  // component is used inside <table> cells throughout the app, and a plain
  // `position: absolute` dropdown gets silently clipped by any ancestor
  // with overflow set to non-visible (every table wrapper here uses
  // overflow-x-auto, which per the CSS overflow spec computes overflow-y
  // to auto too) — the search would fetch and find real results, but they'd
  // never actually be visible. Rendering through a portal with
  // `position: fixed`, computed from getBoundingClientRect(), sidesteps
  // ancestor clipping entirely.
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const updateCoords = () => {
      const rect = wrapperRef.current?.getBoundingClientRect();
      if (!rect) return;

      // The input itself is often a narrow table-cell column (stock/debtor
      // picker columns are typically ~150-200px), but result rows need
      // real room for a code, description, and price — so the dropdown
      // gets its own minimum width rather than inheriting the input's,
      // clamped so it never runs off either edge of the viewport.
      const minWidth = 320;
      const viewportWidth = window.innerWidth;
      const width = Math.min(Math.max(rect.width, minWidth), viewportWidth - 16);
      const left = Math.min(Math.max(rect.left, 8), viewportWidth - width - 8);

      setCoords({ top: rect.bottom, left, width });
    };

    updateCoords();
    window.addEventListener('scroll', updateCoords, true);
    window.addEventListener('resize', updateCoords);
    return () => {
      window.removeEventListener('scroll', updateCoords, true);
      window.removeEventListener('resize', updateCoords);
    };
  }, [isOpen]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      const insideWrapper = wrapperRef.current?.contains(target);
      const insideDropdown = dropdownRef.current?.contains(target);
      if (!insideWrapper && !insideDropdown) {
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
    setOffset(0);
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
  const showDropdown = showEmptyQuerySlot || showResults || showNoResults;

  const dropdown =
    showDropdown && coords
      ? createPortal(
          <div
            ref={dropdownRef}
            style={{
              position: 'fixed',
              top: coords.top + 4,
              left: coords.left,
              width: coords.width,
              zIndex: 9999,
            }}
          >
            {showEmptyQuerySlot && (
              <Card className="shadow-lg border-gray-200">
                <CardContent className="p-3">{emptyQuerySlot}</CardContent>
              </Card>
            )}

            {showResults && (
              <Card className="shadow-lg border-gray-200">
                <CardContent className="p-0 max-h-80 overflow-y-auto">
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
                {(currentPage > 1 || hasMore) && (
                  <div className="flex items-center justify-between px-3 py-2 border-t border-gray-100 text-sm text-gray-500">
                    <button
                      type="button"
                      onClick={() => setOffset((prev) => Math.max(0, prev - pageSize))}
                      disabled={currentPage === 1}
                      className="px-2 py-1 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                    >
                      Previous
                    </button>
                    <span>
                      Page {currentPage}
                      {typeof data?.count === 'number' ? ` of ${Math.max(1, Math.ceil(data.count / pageSize))}` : ''}
                    </span>
                    <button
                      type="button"
                      onClick={() => setOffset((prev) => prev + pageSize)}
                      disabled={!hasMore}
                      className="px-2 py-1 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                    >
                      Next
                    </button>
                  </div>
                )}
              </Card>
            )}

            {showNoResults && (
              <Card className="shadow-lg border-gray-200">
                <CardContent className="p-4 text-center text-gray-500">
                  {debouncedQuery.trim() ? `No results for "${debouncedQuery}"` : 'No results'}
                </CardContent>
              </Card>
            )}
          </div>,
          document.body
        )
      : null;

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

      {dropdown}
    </div>
  );
}

export default SearchCombobox;
