import { useCallback, useEffect, useState } from 'react';
import client from '../api/client.js';
import { formatMoney, formatDateTime } from '../utils/format.js';

const CARD = 'rounded-lg border border-slate-200 bg-white p-6 shadow-sm';
const ERROR_BANNER = 'rounded-md bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm';

const STATUS_BADGE = {
  PENDING: 'bg-amber-100 text-amber-800',
  FILLED: 'bg-emerald-100 text-emerald-800',
  EXPIRED: 'bg-slate-100 text-slate-600',
  CANCELLED: 'bg-slate-100 text-slate-600',
};

export default function PendingOrdersList({ refreshKey }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [cancellingId, setCancellingId] = useState(null);

  const loadOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await client.get('/api/orders');
      setOrders(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load orders.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrders();
  }, [loadOrders, refreshKey]);

  async function cancelOrder(id) {
    setCancellingId(id);
    try {
      await client.delete(`/api/orders/${id}`);
      await loadOrders();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to cancel order.');
    } finally {
      setCancellingId(null);
    }
  }

  return (
    <div className={CARD}>
      <h2 className="text-lg font-semibold text-slate-900">Orders</h2>

      {error && <div className={`mt-4 ${ERROR_BANNER}`}>{error}</div>}

      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading…</p>
      ) : orders.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No orders yet.</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2 pr-4 font-medium">Ticker</th>
                <th className="py-2 pr-4 font-medium">Side</th>
                <th className="py-2 pr-4 font-medium">Type</th>
                <th className="py-2 pr-4 font-medium">Qty</th>
                <th className="py-2 pr-4 font-medium">Limit / Stop</th>
                <th className="py-2 pr-4 font-medium">Status</th>
                <th className="py-2 pr-4 font-medium">Fill price</th>
                <th className="py-2 pr-4 font-medium">Placed</th>
                <th className="py-2 pr-4 font-medium">Expires</th>
                <th className="py-2 pr-4 font-medium" />
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-b border-slate-100">
                  <td className="py-2 pr-4 font-medium text-slate-900">{o.ticker}</td>
                  <td className="py-2 pr-4 text-slate-700">{o.direction}</td>
                  <td className="py-2 pr-4 text-slate-700">{o.order_type.replace('_', ' ')}</td>
                  <td className="py-2 pr-4 text-slate-700">{o.quantity}</td>
                  <td className="py-2 pr-4 text-slate-700">
                    {o.limit_price ? formatMoney(o.limit_price) : '—'}
                    {o.stop_price ? ` / ${formatMoney(o.stop_price)}` : ''}
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[o.status] || 'bg-slate-100 text-slate-600'}`}
                    >
                      {o.status}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-slate-700">
                    {o.fill_price ? formatMoney(o.fill_price) : '—'}
                  </td>
                  <td className="py-2 pr-4 text-slate-500">{formatDateTime(o.placed_at)}</td>
                  <td className="py-2 pr-4 text-slate-500">{formatDateTime(o.expires_at)}</td>
                  <td className="py-2 pr-4">
                    {o.status === 'PENDING' && (
                      <button
                        type="button"
                        onClick={() => cancelOrder(o.id)}
                        disabled={cancellingId === o.id}
                        className="text-sm font-medium text-red-600 hover:text-red-700 disabled:opacity-50"
                      >
                        {cancellingId === o.id ? 'Cancelling…' : 'Cancel'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
