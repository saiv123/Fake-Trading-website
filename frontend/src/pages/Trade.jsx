import { useEffect, useState } from 'react';
import client from '../api/client.js';
import { formatMoney, formatPercent, formatDateTime } from '../utils/format.js';
import StockSearch from '../components/StockSearch.jsx';
import OrderForm from '../components/OrderForm.jsx';
import PendingOrdersList from '../components/PendingOrdersList.jsx';

const CARD = 'rounded-lg border border-slate-200 bg-white p-6 shadow-sm';
const ERROR_BANNER = 'rounded-md bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm';

function changeColor(value) {
  return parseFloat(value) >= 0 ? 'text-emerald-600' : 'text-red-600';
}

function QuoteCard({ quote }) {
  return (
    <div className={CARD}>
      <div className="flex items-baseline justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">{quote.ticker}</h2>
          <p className="text-sm text-slate-500">{quote.company_name}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-semibold text-slate-900">{formatMoney(quote.last_price)}</p>
          <p className={`text-sm font-medium ${changeColor(quote.change_amount)}`}>
            {quote.change_amount ? formatMoney(quote.change_amount) : '—'} (
            {formatPercent(quote.change_percent)})
          </p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
        <div>
          <p className="text-slate-500">Day range</p>
          <p className="font-medium text-slate-900">
            {formatMoney(quote.day_low)} – {formatMoney(quote.day_high)}
          </p>
        </div>
        <div>
          <p className="text-slate-500">52-week range</p>
          <p className="font-medium text-slate-900">
            {formatMoney(quote.week_52_low)} – {formatMoney(quote.week_52_high)}
          </p>
        </div>
        <div>
          <p className="text-slate-500">Volume</p>
          <p className="font-medium text-slate-900">{quote.volume ?? '—'}</p>
        </div>
        <div>
          <p className="text-slate-500">Bid / Ask</p>
          <p className="font-medium text-slate-900">
            {formatMoney(quote.bid)} / {formatMoney(quote.ask)}
          </p>
        </div>
        <div>
          <p className="text-slate-500">After hours</p>
          <p className="font-medium text-slate-900">
            {quote.after_hours_price ? formatMoney(quote.after_hours_price) : '—'}
          </p>
        </div>
        <div>
          <p className="text-slate-500">Last updated</p>
          <p className="font-medium text-slate-900">{formatDateTime(quote.last_updated)}</p>
        </div>
      </div>
    </div>
  );
}

export default function Trade() {
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [quote, setQuote] = useState(null);
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [quoteError, setQuoteError] = useState(null);
  const [ordersRefreshKey, setOrdersRefreshKey] = useState(0);

  useEffect(() => {
    if (!selectedTicker) return;

    let cancelled = false;
    setQuoteLoading(true);
    setQuoteError(null);
    setQuote(null);

    client
      .get(`/api/stocks/${selectedTicker}`)
      .then((res) => {
        if (!cancelled) setQuote(res.data);
      })
      .catch((err) => {
        if (!cancelled) setQuoteError(err.response?.data?.error || 'Failed to load quote.');
      })
      .finally(() => {
        if (!cancelled) setQuoteLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedTicker]);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-slate-900">Trade</h1>

      <div className={CARD}>
        <StockSearch onSelect={setSelectedTicker} />
      </div>

      {quoteError && <div className={ERROR_BANNER}>{quoteError}</div>}
      {quoteLoading && <p className="text-sm text-slate-500">Loading quote…</p>}

      {quote && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <QuoteCard quote={quote} />
          </div>
          <div>
            <OrderForm
              ticker={quote.ticker}
              onOrderPlaced={() => setOrdersRefreshKey((k) => k + 1)}
            />
          </div>
        </div>
      )}

      <PendingOrdersList refreshKey={ordersRefreshKey} />
    </div>
  );
}
