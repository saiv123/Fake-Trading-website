import { useCallback, useEffect, useState } from 'react';
import client from '../api/client.js';
import { formatMoney, formatDate } from '../utils/format.js';

const CARD = 'rounded-lg border border-slate-200 bg-white p-6 shadow-sm';
const ERROR_BANNER = 'rounded-md bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm';

function EstimateRow({ label, value, bold }) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-2 last:border-0">
      <span className={`text-sm ${bold ? 'font-semibold text-slate-900' : 'text-slate-500'}`}>{label}</span>
      <span className={`text-sm ${bold ? 'font-semibold text-slate-900' : 'text-slate-700'}`}>{value}</span>
    </div>
  );
}

export default function Tax() {
  const [estimate, setEstimate] = useState(null);
  const [estimateLoading, setEstimateLoading] = useState(true);
  const [estimateError, setEstimateError] = useState(null);

  const [history, setHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState(null);

  const loadEstimate = useCallback(async () => {
    setEstimateLoading(true);
    setEstimateError(null);
    try {
      const res = await client.get('/api/tax/estimate');
      setEstimate(res.data);
    } catch (err) {
      setEstimateError(err.response?.data?.error || 'Failed to load tax estimate.');
    } finally {
      setEstimateLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const res = await client.get('/api/tax/history');
      setHistory(res.data);
    } catch (err) {
      setHistoryError(err.response?.data?.error || 'Failed to load settlement history.');
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEstimate();
    loadHistory();
  }, [loadEstimate, loadHistory]);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-slate-900">Tax</h1>

      <div className={CARD}>
        <h2 className="text-lg font-semibold text-slate-900">
          {estimate ? `${estimate.year} year-to-date estimate` : 'Year-to-date estimate'}
        </h2>

        {estimateError && <div className={`mt-4 ${ERROR_BANNER}`}>{estimateError}</div>}

        {estimateLoading ? (
          <p className="mt-4 text-sm text-slate-500">Loading…</p>
        ) : estimate ? (
          <div className="mt-4">
            <EstimateRow label="Net short-term gain" value={formatMoney(estimate.net_short_gain)} />
            <EstimateRow label="Net long-term gain" value={formatMoney(estimate.net_long_gain)} />
            <EstimateRow label="Dividends" value={formatMoney(estimate.dividends)} />
            <EstimateRow label="Taxable short-term" value={formatMoney(estimate.taxable_short)} />
            <EstimateRow label="Taxable long-term" value={formatMoney(estimate.taxable_long)} />
            <EstimateRow label="Federal tax" value={formatMoney(estimate.federal_tax)} />
            <EstimateRow label={`State tax (${estimate.state})`} value={formatMoney(estimate.state_tax)} />
            <EstimateRow label="Total estimated tax" value={formatMoney(estimate.total_tax)} bold />
          </div>
        ) : null}
      </div>

      <div className={CARD}>
        <h2 className="text-lg font-semibold text-slate-900">Settlement history</h2>

        {historyError && <div className={`mt-4 ${ERROR_BANNER}`}>{historyError}</div>}

        {historyLoading ? (
          <p className="mt-4 text-sm text-slate-500">Loading…</p>
        ) : history && history.length > 0 ? (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="py-2 pr-4 font-medium">Date</th>
                  <th className="py-2 pr-4 font-medium">Amount paid</th>
                  <th className="py-2 pr-4 font-medium">Notes</th>
                </tr>
              </thead>
              <tbody>
                {history.map((tx) => (
                  <tr key={tx.tx_id} className="border-b border-slate-100">
                    <td className="py-2 pr-4 text-slate-700">{formatDate(tx.executed_at)}</td>
                    <td className="py-2 pr-4 font-medium text-red-600">
                      {formatMoney(Math.abs(parseFloat(tx.total_value)))}
                    </td>
                    <td className="py-2 pr-4 text-slate-500">{tx.notes || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-500">No prior settlements yet.</p>
        )}
      </div>
    </div>
  );
}
