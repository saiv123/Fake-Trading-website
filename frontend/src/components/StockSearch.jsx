import { useEffect, useRef, useState } from 'react';
import client from '../api/client.js';
import { formatMoney } from '../utils/format.js';

const DEBOUNCE_MS = 300;

export default function StockSearch({ onSelect }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    clearTimeout(timerRef.current);

    const q = query.trim();
    if (!q) {
      setResults([]);
      setLoading(false);
      setError(null);
      return undefined;
    }

    timerRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await client.get('/api/stocks/search', { params: { q } });
        setResults(res.data);
        setOpen(true);
      } catch (err) {
        setError(err.response?.data?.error || 'Search failed');
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timerRef.current);
  }, [query]);

  function handleSelect(ticker) {
    setQuery('');
    setResults([]);
    setOpen(false);
    onSelect(ticker);
  }

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder="Search by ticker or company name…"
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
      />

      {loading && <p className="mt-1 text-xs text-slate-400">Searching…</p>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}

      {open && results.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-md border border-slate-200 bg-white shadow-lg">
          {results.map((r) => (
            <li key={r.ticker}>
              <button
                type="button"
                onClick={() => handleSelect(r.ticker)}
                className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-50"
              >
                <span>
                  <span className="font-semibold text-slate-900">{r.ticker}</span>{' '}
                  <span className="text-slate-500">{r.company_name}</span>
                </span>
                <span className="text-slate-600">
                  {r.last_price ? formatMoney(r.last_price) : '—'}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
