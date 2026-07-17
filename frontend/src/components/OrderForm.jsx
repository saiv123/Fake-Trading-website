import { useState } from 'react';
import client from '../api/client.js';

const ORDER_TYPES = ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT'];

const CARD = 'rounded-lg border border-slate-200 bg-white p-6 shadow-sm';
const INPUT =
  'w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none';
const ERROR_BANNER = 'rounded-md bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm';
const SUCCESS_BANNER =
  'rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 text-sm';

export default function OrderForm({ ticker, onOrderPlaced }) {
  const [direction, setDirection] = useState('BUY');
  const [orderType, setOrderType] = useState('MARKET');
  const [quantity, setQuantity] = useState('');
  const [limitPrice, setLimitPrice] = useState('');
  const [stopPrice, setStopPrice] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const needsLimit = orderType === 'LIMIT' || orderType === 'STOP_LIMIT';
  const needsStop = orderType === 'STOP' || orderType === 'STOP_LIMIT';

  const qtyValid = Number(quantity) > 0;
  const limitValid = !needsLimit || Number(limitPrice) > 0;
  const stopValid = !needsStop || Number(stopPrice) > 0;
  const canSubmit = qtyValid && limitValid && stopValid && !submitting;

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);
    try {
      const res = await client.post('/api/orders', {
        ticker,
        direction,
        order_type: orderType,
        quantity: Number(quantity),
        limit_price: needsLimit ? Number(limitPrice) : null,
        stop_price: needsStop ? Number(stopPrice) : null,
      });
      setSuccess(
        res.data.status === 'FILLED'
          ? `Order filled at $${res.data.fill_price}.`
          : 'Order placed and pending.',
      );
      setQuantity('');
      setLimitPrice('');
      setStopPrice('');
      onOrderPlaced?.();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to place order.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className={`${CARD} space-y-4`}>
      <h2 className="text-lg font-semibold text-slate-900">Place order — {ticker}</h2>

      {error && <div className={ERROR_BANNER}>{error}</div>}
      {success && <div className={SUCCESS_BANNER}>{success}</div>}

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setDirection('BUY')}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium ${
            direction === 'BUY'
              ? 'bg-emerald-600 text-white hover:bg-emerald-700'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          Buy
        </button>
        <button
          type="button"
          onClick={() => setDirection('SELL')}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium ${
            direction === 'SELL'
              ? 'bg-red-600 text-white hover:bg-red-700'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          Sell
        </button>
      </div>

      <div>
        <label htmlFor="order_type" className="block text-sm font-medium text-slate-700">
          Order type
        </label>
        <select
          id="order_type"
          value={orderType}
          onChange={(e) => setOrderType(e.target.value)}
          className={`${INPUT} mt-1 bg-white`}
        >
          {ORDER_TYPES.map((t) => (
            <option key={t} value={t}>
              {t.replace('_', ' ')}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="quantity" className="block text-sm font-medium text-slate-700">
          Quantity
        </label>
        <input
          id="quantity"
          type="number"
          step="0.0001"
          min="0"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          className={`${INPUT} mt-1`}
        />
      </div>

      {needsLimit && (
        <div>
          <label htmlFor="limit_price" className="block text-sm font-medium text-slate-700">
            Limit price
          </label>
          <input
            id="limit_price"
            type="number"
            step="0.01"
            min="0"
            value={limitPrice}
            onChange={(e) => setLimitPrice(e.target.value)}
            className={`${INPUT} mt-1`}
          />
        </div>
      )}

      {needsStop && (
        <div>
          <label htmlFor="stop_price" className="block text-sm font-medium text-slate-700">
            Stop price
          </label>
          <input
            id="stop_price"
            type="number"
            step="0.01"
            min="0"
            value={stopPrice}
            onChange={(e) => setStopPrice(e.target.value)}
            className={`${INPUT} mt-1`}
          />
        </div>
      )}

      <button
        type="submit"
        disabled={!canSubmit}
        className={`w-full rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-50 ${
          direction === 'BUY' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-red-600 hover:bg-red-700'
        }`}
      >
        {submitting ? 'Submitting…' : `${direction === 'BUY' ? 'Buy' : 'Sell'} ${ticker}`}
      </button>
    </form>
  );
}
