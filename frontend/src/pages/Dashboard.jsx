import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client.js';
import { formatMoney, formatDateTime } from '../utils/format.js';

const CARD = 'rounded-lg border border-slate-200 bg-white p-6 shadow-sm';
const PRIMARY_BUTTON =
  'rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed';
const SECONDARY_BUTTON =
  'rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed';
const ERROR_BANNER = 'rounded-md bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm';

function pnlColor(value) {
  return parseFloat(value) >= 0 ? 'text-emerald-600' : 'text-red-600';
}

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState(null);
  const [portfolioLoading, setPortfolioLoading] = useState(true);
  const [portfolioError, setPortfolioError] = useState(null);
  const [dripBusyTicker, setDripBusyTicker] = useState(null);
  const [enableAllBusy, setEnableAllBusy] = useState(false);

  const [history, setHistory] = useState(null);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState(null);

  const loadPortfolio = useCallback(async () => {
    setPortfolioLoading(true);
    setPortfolioError(null);
    try {
      const res = await client.get('/api/portfolio');
      setPortfolio(res.data);
    } catch (err) {
      setPortfolioError(err.response?.data?.error || 'Failed to load portfolio.');
    } finally {
      setPortfolioLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async (page) => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const res = await client.get('/api/portfolio/history', { params: { page } });
      setHistory(res.data);
    } catch (err) {
      setHistoryError(err.response?.data?.error || 'Failed to load transaction history.');
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPortfolio();
  }, [loadPortfolio]);

  useEffect(() => {
    loadHistory(historyPage);
  }, [loadHistory, historyPage]);

  async function toggleDrip(ticker, nextValue) {
    setDripBusyTicker(ticker);
    try {
      await client.patch(`/api/portfolio/${ticker}/drip`, { drip_enabled: nextValue });
      await loadPortfolio();
    } catch (err) {
      setPortfolioError(err.response?.data?.error || 'Failed to update DRIP.');
    } finally {
      setDripBusyTicker(null);
    }
  }

  async function enableAllDrip() {
    setEnableAllBusy(true);
    try {
      await client.post('/api/portfolio/drip/enable-all');
      await loadPortfolio();
    } catch (err) {
      setPortfolioError(err.response?.data?.error || 'Failed to enable DRIP for all positions.');
    } finally {
      setEnableAllBusy(false);
    }
  }

  const totalPages = history ? Math.max(1, Math.ceil(history.total / history.page_size)) : 1;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-slate-900">Portfolio</h1>

      {portfolioError && <div className={ERROR_BANNER}>{portfolioError}</div>}

      {portfolioLoading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : portfolio ? (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className={CARD}>
              <p className="text-sm text-slate-500">Cash balance</p>
              <p className="mt-1 text-xl font-semibold text-slate-900">
                {formatMoney(portfolio.cash_balance)}
              </p>
            </div>
            <div className={CARD}>
              <p className="text-sm text-slate-500">Market value</p>
              <p className="mt-1 text-xl font-semibold text-slate-900">
                {formatMoney(portfolio.total_market_value)}
              </p>
            </div>
            <div className={CARD}>
              <p className="text-sm text-slate-500">Total equity</p>
              <p className="mt-1 text-xl font-semibold text-slate-900">
                {formatMoney(portfolio.total_equity)}
              </p>
            </div>
            <div className={CARD}>
              <p className="text-sm text-slate-500">Unrealized P&amp;L</p>
              <p className={`mt-1 text-xl font-semibold ${pnlColor(portfolio.total_unrealized)}`}>
                {formatMoney(portfolio.total_unrealized)}
              </p>
            </div>
          </div>

          <div className={CARD}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Holdings</h2>
              <button
                type="button"
                onClick={enableAllDrip}
                disabled={enableAllBusy || portfolio.positions.length === 0}
                className={SECONDARY_BUTTON}
              >
                {enableAllBusy ? 'Enabling…' : 'Enable DRIP for all'}
              </button>
            </div>

            {portfolio.positions.length === 0 ? (
              <p className="text-sm text-slate-500">
                No positions yet — head to{' '}
                <Link to="/trade" className="text-blue-600 hover:underline">
                  Trade
                </Link>{' '}
                to place your first order.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500">
                      <th className="py-2 pr-4 font-medium">Ticker</th>
                      <th className="py-2 pr-4 font-medium">Shares</th>
                      <th className="py-2 pr-4 font-medium">ACB</th>
                      <th className="py-2 pr-4 font-medium">Current price</th>
                      <th className="py-2 pr-4 font-medium">Market value</th>
                      <th className="py-2 pr-4 font-medium">Unrealized P&amp;L</th>
                      <th className="py-2 pr-4 font-medium">DRIP</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.positions.map((pos) => (
                      <tr key={pos.ticker} className="border-b border-slate-100">
                        <td className="py-2 pr-4 font-medium text-slate-900">{pos.ticker}</td>
                        <td className="py-2 pr-4 text-slate-700">{pos.shares}</td>
                        <td className="py-2 pr-4 text-slate-700">{formatMoney(pos.acb)}</td>
                        <td className="py-2 pr-4 text-slate-700">{formatMoney(pos.current_price)}</td>
                        <td className="py-2 pr-4 text-slate-700">{formatMoney(pos.market_value)}</td>
                        <td className={`py-2 pr-4 font-medium ${pnlColor(pos.unrealized_pnl)}`}>
                          {formatMoney(pos.unrealized_pnl)}
                        </td>
                        <td className="py-2 pr-4">
                          <label className="inline-flex cursor-pointer items-center gap-2">
                            <input
                              type="checkbox"
                              checked={pos.drip_enabled}
                              disabled={dripBusyTicker === pos.ticker}
                              onChange={(e) => toggleDrip(pos.ticker, e.target.checked)}
                              className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                            />
                          </label>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      ) : null}

      <div className={CARD}>
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Transaction history</h2>

        {historyError && <div className={`${ERROR_BANNER} mb-4`}>{historyError}</div>}

        {historyLoading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : history && history.transactions.length === 0 ? (
          <p className="text-sm text-slate-500">No transactions yet.</p>
        ) : history ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500">
                    <th className="py-2 pr-4 font-medium">Date</th>
                    <th className="py-2 pr-4 font-medium">Type</th>
                    <th className="py-2 pr-4 font-medium">Ticker</th>
                    <th className="py-2 pr-4 font-medium">Quantity</th>
                    <th className="py-2 pr-4 font-medium">Price/share</th>
                    <th className="py-2 pr-4 font-medium">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {history.transactions.map((tx) => (
                    <tr key={tx.tx_id} className="border-b border-slate-100">
                      <td className="py-2 pr-4 text-slate-700">{formatDateTime(tx.executed_at)}</td>
                      <td className="py-2 pr-4 text-slate-700">{tx.type}</td>
                      <td className="py-2 pr-4 text-slate-700">{tx.ticker || '—'}</td>
                      <td className="py-2 pr-4 text-slate-700">{tx.quantity ?? '—'}</td>
                      <td className="py-2 pr-4 text-slate-700">
                        {tx.price_per_share ? formatMoney(tx.price_per_share) : '—'}
                      </td>
                      <td className={`py-2 pr-4 font-medium ${pnlColor(tx.total_value)}`}>
                        {formatMoney(tx.total_value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                disabled={historyPage <= 1}
                className={SECONDARY_BUTTON}
              >
                Prev
              </button>
              <span className="text-sm text-slate-500">
                Page {history.page} of {totalPages}
              </span>
              <button
                type="button"
                onClick={() => setHistoryPage((p) => Math.min(totalPages, p + 1))}
                disabled={historyPage >= totalPages}
                className={SECONDARY_BUTTON}
              >
                Next
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
