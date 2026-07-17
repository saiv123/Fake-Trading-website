import { createContext, useCallback, useContext, useState } from 'react';

const AuthContext = createContext(null);

const STORAGE_KEY = 'userId';

// The backend has no sessions/cookies — identity is just a user_id sent as the X-User-Id
// header (see api/client.js). "Logging in" here means persisting that id locally.
export function AuthProvider({ children }) {
  const [userId, setUserId] = useState(() => localStorage.getItem(STORAGE_KEY));

  const login = useCallback((id) => {
    localStorage.setItem(STORAGE_KEY, String(id));
    setUserId(String(id));
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUserId(null);
  }, []);

  const value = { userId, isAuthenticated: Boolean(userId), login, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
