function redirectToProvider(provider) {
  window.location.href = `${import.meta.env.VITE_API_URL}/api/auth/${provider}`;
}

export default function Login() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Mock Trading Platform</h1>
        <p className="mt-2 text-sm text-slate-500">
          A paper-trading simulation — no real money, no real securities.
        </p>

        <div className="mt-8 space-y-3">
          <button
            type="button"
            onClick={() => redirectToProvider('google')}
            className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Continue with Google
          </button>
          <button
            type="button"
            onClick={() => redirectToProvider('microsoft')}
            className="w-full rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            Continue with Microsoft
          </button>
        </div>
      </div>
    </div>
  );
}
