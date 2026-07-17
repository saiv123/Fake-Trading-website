import { Routes, Route } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import Navbar from './components/Navbar.jsx';
import Login from './pages/Login.jsx';
import AuthCallback from './pages/AuthCallback.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Trade from './pages/Trade.jsx';
import Tax from './pages/Tax.jsx';
import Profile from './pages/Profile.jsx';
import DiscordLink from './pages/DiscordLink.jsx';

function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/register" element={<Register />} />

      <Route element={<ProtectedRoute />}>
        <Route
          path="/"
          element={
            <AppLayout>
              <Dashboard />
            </AppLayout>
          }
        />
        <Route
          path="/trade"
          element={
            <AppLayout>
              <Trade />
            </AppLayout>
          }
        />
        <Route
          path="/tax"
          element={
            <AppLayout>
              <Tax />
            </AppLayout>
          }
        />
        <Route
          path="/profile"
          element={
            <AppLayout>
              <Profile />
            </AppLayout>
          }
        />
        <Route
          path="/discord/link"
          element={
            <AppLayout>
              <DiscordLink />
            </AppLayout>
          }
        />
      </Route>
    </Routes>
  );
}
