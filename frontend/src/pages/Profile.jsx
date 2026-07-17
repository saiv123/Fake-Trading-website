import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client.js';
import { formatMoney, formatDate, formatDateTime } from '../utils/format.js';

const CARD = 'rounded-lg border border-slate-200 bg-white p-6 shadow-sm';
const PRIMARY_BUTTON =
  'rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed';
const ERROR_BANNER = 'rounded-md bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm';
const SUCCESS_BANNER = 'rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 text-sm';

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState(null);

  const [displayName, setDisplayName] = useState('');
  const [savingName, setSavingName] = useState(false);
  const [nameSaved, setNameSaved] = useState(false);
  const [dripBusy, setDripBusy] = useState(false);

  const [notifications, setNotifications] = useState(null);
  const [notificationsLoading, setNotificationsLoading] = useState(true);
  const [notificationsError, setNotificationsError] = useState(null);

  const [stipend, setStipend] = useState(null);
  const [stipendLoading, setStipendLoading] = useState(true);
  const [stipendError, setStipendError] = useState(null);

  const loadProfile = useCallback(async () => {
    setProfileLoading(true);
    setProfileError(null);
    try {
      const res = await client.get('/api/user/me');
      setProfile(res.data);
      setDisplayName(res.data.display_name);
    } catch (err) {
      setProfileError(err.response?.data?.error || 'Failed to load profile.');
    } finally {
      setProfileLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();

    (async () => {
      setNotificationsLoading(true);
      setNotificationsError(null);
      try {
        const res = await client.get('/api/user/notifications');
        setNotifications(res.data);
      } catch (err) {
        setNotificationsError(err.response?.data?.error || 'Failed to load notifications.');
      } finally {
        setNotificationsLoading(false);
      }
    })();

    (async () => {
      setStipendLoading(true);
      setStipendError(null);
      try {
        const res = await client.get('/api/user/stipend/status');
        setStipend(res.data);
      } catch (err) {
        setStipendError(err.response?.data?.error || 'Failed to load stipend status.');
      } finally {
        setStipendLoading(false);
      }
    })();
  }, [loadProfile]);

  async function saveDisplayName(e) {
    e.preventDefault();
    setSavingName(true);
    setNameSaved(false);
    setProfileError(null);
    try {
      await client.put('/api/user/me', { display_name: displayName.trim() });
      setProfile((prev) => (prev ? { ...prev, display_name: displayName.trim() } : prev));
      setNameSaved(true);
    } catch (err) {
      setProfileError(err.response?.data?.error || 'Failed to update display name.');
    } finally {
      setSavingName(false);
    }
  }

  async function toggleDripAll(next) {
    setDripBusy(true);
    setProfileError(null);
    try {
      await client.put('/api/user/me', { drip_all: next });
      setProfile((prev) => (prev ? { ...prev, drip_all: next } : prev));
    } catch (err) {
      setProfileError(err.response?.data?.error || 'Failed to update DRIP setting.');
    } finally {
      setDripBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-slate-900">Profile</h1>

      {profileError && <div className={ERROR_BANNER}>{profileError}</div>}

      {profileLoading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : profile ? (
        <>
          <div className={CARD}>
            <h2 className="text-lg font-semibold text-slate-900">Account</h2>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <p className="text-sm text-slate-500">Email</p>
                <p className="text-sm font-medium text-slate-900">{profile.email}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">State</p>
                <p className="text-sm font-medium text-slate-900">{profile.state}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Balance</p>
                <p className="text-sm font-medium text-slate-900">{formatMoney(profile.balance)}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Starting balance</p>
                <p className="text-sm font-medium text-slate-900">
                  {formatMoney(profile.starting_balance)}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Member since</p>
                <p className="text-sm font-medium text-slate-900">{formatDate(profile.created_at)}</p>
              </div>
            </div>

            <form onSubmit={saveDisplayName} className="mt-6 border-t border-slate-100 pt-6">
              <label htmlFor="display_name" className="block text-sm font-medium text-slate-700">
                Display name
              </label>
              <div className="mt-2 flex gap-2">
                <input
                  id="display_name"
                  type="text"
                  value={displayName}
                  onChange={(e) => {
                    setDisplayName(e.target.value);
                    setNameSaved(false);
                  }}
                  className="w-full max-w-sm rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
                <button type="submit" disabled={savingName} className={PRIMARY_BUTTON}>
                  {savingName ? 'Saving…' : 'Save'}
                </button>
              </div>
              {nameSaved && <p className="mt-2 text-sm text-emerald-600">Saved.</p>}
            </form>

            <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-6">
              <div>
                <p className="text-sm font-medium text-slate-900">Reinvest dividends (DRIP) for all positions</p>
                <p className="text-sm text-slate-500">Applies automatically to newly opened positions.</p>
              </div>
              <label className="inline-flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={profile.drip_all}
                  disabled={dripBusy}
                  onChange={(e) => toggleDripAll(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
              </label>
            </div>

            <div className="mt-6 border-t border-slate-100 pt-6">
              <p className="text-sm font-medium text-slate-900">Discord</p>
              {profile.discord_linked ? (
                <p className="mt-1 text-sm text-emerald-600">Linked</p>
              ) : (
                <p className="mt-1 text-sm text-slate-500">
                  Not linked. Use <span className="font-mono">/link</span> in the Discord bot to get a
                  one-time linking URL, then open it here.{' '}
                  <Link to="/discord/link" className="text-blue-600 hover:underline">
                    Go to linking page
                  </Link>
                </p>
              )}
            </div>
          </div>

          <div className={CARD}>
            <h2 className="text-lg font-semibold text-slate-900">Monthly stipend</h2>
            {stipendError && <div className={`mt-4 ${ERROR_BANNER}`}>{stipendError}</div>}
            {stipendLoading ? (
              <p className="mt-4 text-sm text-slate-500">Loading…</p>
            ) : stipend ? (
              <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-sm text-slate-500">Amount</p>
                  <p className="text-sm font-medium text-slate-900">{formatMoney(stipend.amount)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Next credit date</p>
                  <p className="text-sm font-medium text-slate-900">{formatDate(stipend.next_stipend_date)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Status</p>
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      stipend.active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {stipend.active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Last active</p>
                  <p className="text-sm font-medium text-slate-900">
                    {formatDateTime(stipend.last_active_at)}
                  </p>
                </div>
              </div>
            ) : null}
          </div>

          <div className={CARD}>
            <h2 className="text-lg font-semibold text-slate-900">Notifications</h2>
            {notificationsError && <div className={`mt-4 ${ERROR_BANNER}`}>{notificationsError}</div>}
            {notificationsLoading ? (
              <p className="mt-4 text-sm text-slate-500">Loading…</p>
            ) : notifications && notifications.length > 0 ? (
              <ul className="mt-4 divide-y divide-slate-100">
                {notifications.map((n) => (
                  <li key={n.id} className="py-3">
                    <p className={`text-sm ${n.read ? 'text-slate-700' : 'font-semibold text-slate-900'}`}>
                      {n.title}
                    </p>
                    <p className="text-sm text-slate-500">{n.message}</p>
                    <p className="mt-1 text-xs text-slate-400">{formatDateTime(n.created_at)}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-4 text-sm text-slate-500">No notifications yet.</p>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}
