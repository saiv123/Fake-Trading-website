import { createContext, useCallback, useContext, useState } from 'react';

const AuthContext = createContext(null);

const STORAGE_KEY = 'sessionToken';

// Identity is a signed session token minted by the backend at login (see api/client.js, which
// attaches it as Authorization: Bearer <token>). "Logging in" means persisting that token
// locally; there's no server-side revocation, so "logging out" is purely a local clear.
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY));

  const login = useCallback((sessionToken) => {
    localStorage.setItem(STORAGE_KEY, sessionToken);
    setToken(sessionToken);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
  }, []);

  const value = { isAuthenticated: Boolean(token), login, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
