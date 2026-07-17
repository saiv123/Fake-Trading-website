import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import client from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';

const BALANCE_MIN = 1000;
const BALANCE_MAX = 100000;
const BALANCE_PRESETS = [1000, 10000, 25000, 100000];

const US_STATES = [
  ['AL', 'Alabama'], ['AK', 'Alaska'], ['AZ', 'Arizona'], ['AR', 'Arkansas'],
  ['CA', 'California'], ['CO', 'Colorado'], ['CT', 'Connecticut'], ['DE', 'Delaware'],
  ['DC', 'District of Columbia'], ['FL', 'Florida'], ['GA', 'Georgia'], ['HI', 'Hawaii'],
  ['ID', 'Idaho'], ['IL', 'Illinois'], ['IN', 'Indiana'], ['IA', 'Iowa'],
  ['KS', 'Kansas'], ['KY', 'Kentucky'], ['LA', 'Louisiana'], ['ME', 'Maine'],
  ['MD', 'Maryland'], ['MA', 'Massachusetts'], ['MI', 'Michigan'], ['MN', 'Minnesota'],
  ['MS', 'Mississippi'], ['MO', 'Missouri'], ['MT', 'Montana'], ['NE', 'Nebraska'],
  ['NV', 'Nevada'], ['NH', 'New Hampshire'], ['NJ', 'New Jersey'], ['NM', 'New Mexico'],
  ['NY', 'New York'], ['NC', 'North Carolina'], ['ND', 'North Dakota'], ['OH', 'Ohio'],
  ['OK', 'Oklahoma'], ['OR', 'Oregon'], ['PA', 'Pennsylvania'], ['RI', 'Rhode Island'],
  ['SC', 'South Carolina'], ['SD', 'South Dakota'], ['TN', 'Tennessee'], ['TX', 'Texas'],
  ['UT', 'Utah'], ['VT', 'Vermont'], ['VA', 'Virginia'], ['WA', 'Washington'],
  ['WV', 'West Virginia'], ['WI', 'Wisconsin'], ['WY', 'Wyoming'],
];

export default function Register() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();

  const registrationInfo = location.state;

  const [displayName, setDisplayName] = useState(registrationInfo?.display_name || '');
  const [startingBalance, setStartingBalance] = useState(10000);
  const [state, setState] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!registrationInfo) {
      navigate('/login', { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [registrationInfo]);

  if (!registrationInfo) {
    return null;
  }

  function handleBalanceInput(value) {
    const n = Number(value);
    if (Number.isNaN(n)) {
      setStartingBalance('');
      return;
    }
    setStartingBalance(Math.min(BALANCE_MAX, Math.max(BALANCE_MIN, n)));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    const balance = Number(startingBalance);
    if (Number.isNaN(balance) || balance < BALANCE_MIN || balance > BALANCE_MAX) {
      setError(`Starting balance must be between $${BALANCE_MIN} and $${BALANCE_MAX}`);
      return;
    }
    if (!state) {
      setError('Please select a state');
      return;
    }
    if (!displayName.trim()) {
      setError('Please enter a display name');
      return;
    }

    setSubmitting(true);
    try {
      const res = await client.post('/api/auth/oauth/register', {
        provider: registrationInfo.provider,
        provider_id: registrationInfo.provider_id,
        email: registrationInfo.email,
        display_name: displayName.trim(),
        state,
        starting_balance: balance,
      });
      login(res.data.token);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Create your account</h1>
        <p className="mt-1 text-sm text-slate-500">{registrationInfo.email}</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="display_name" className="block text-sm font-medium text-slate-700">
              Display name
            </label>
            <input
              id="display_name"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <span className="block text-sm font-medium text-slate-700">Starting balance</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {BALANCE_PRESETS.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setStartingBalance(preset)}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                    Number(startingBalance) === preset
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  ${preset.toLocaleString()}
                </button>
              ))}
            </div>
            <input
              type="number"
              min={BALANCE_MIN}
              max={BALANCE_MAX}
              value={startingBalance}
              onChange={(e) => handleBalanceInput(e.target.value)}
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
            <p className="mt-1 text-xs text-slate-400">
              Between ${BALANCE_MIN.toLocaleString()} and ${BALANCE_MAX.toLocaleString()}
            </p>
          </div>

          <div>
            <label htmlFor="state" className="block text-sm font-medium text-slate-700">
              State (for tax calculation)
            </label>
            <select
              id="state"
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="">Select a state…</option>
              {US_STATES.map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
  );
}
