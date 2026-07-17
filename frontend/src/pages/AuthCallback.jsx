import { useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();

  const userId = searchParams.get('user_id');
  const requiresRegistration = searchParams.get('requires_registration');

  useEffect(() => {
    if (userId) {
      login(userId);
      navigate('/', { replace: true });
      return;
    }

    if (requiresRegistration) {
      navigate('/register', {
        replace: true,
        state: {
          provider: searchParams.get('provider'),
          provider_id: searchParams.get('provider_id'),
          email: searchParams.get('email'),
          display_name: searchParams.get('display_name'),
        },
      });
    }
    // Only re-run if the query params actually change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, requiresRegistration]);

  if (!userId && !requiresRegistration) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
          <p className="text-sm text-red-700">Something went wrong signing you in.</p>
          <Link to="/login" className="mt-4 inline-block text-sm font-medium text-blue-600 hover:text-blue-700">
            Back to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <p className="text-sm text-slate-500">Signing you in…</p>
    </div>
  );
}
