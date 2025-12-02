import { Navigate, Route, Routes, useLocation, Link } from 'react-router-dom';
import LoginForm from '../features/auth/components/LoginForm';
import RegisterForm from '../features/auth/components/RegisterForm';
import UploadAndAnalyzeForm from '../features/emotion/components/UploadAndAnalyzeForm';
import HistoryView from '../features/emotion/components/HistoryView';
import { AuthProvider, useAuth } from '../features/auth/hooks/useAuth';

function Header() {
  const { user, logout, isAuthenticated } = useAuth();
  return (
    <header className="app-header">
      <Link to="/emotion/today" style={{ fontWeight: 800, letterSpacing: 0.4 }}>
        FHE Emotion Lab
      </Link>
      <nav>
        {isAuthenticated ? (
          <>
            <Link to="/emotion/today">Today</Link>
            <Link to="/emotion/history">History</Link>
            <span className="tag">{user?.user_id ?? 'anonymous'}</span>
            <button className="button secondary" onClick={logout}>
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </nav>
    </header>
  );
}

function RequireAuth({ children }: { children: JSX.Element }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <div className="app-shell">
        <Header />
        <main className="app-main">
          <Routes>
            <Route path="/login" element={<LoginForm />} />
            <Route path="/register" element={<RegisterForm />} />
            <Route
              path="/emotion/today"
              element={
                <RequireAuth>
                  <UploadAndAnalyzeForm />
                </RequireAuth>
              }
            />
            <Route
              path="/emotion/history"
              element={
                <RequireAuth>
                  <HistoryView />
                </RequireAuth>
              }
            />
            <Route path="/" element={<Navigate to="/emotion/today" replace />} />
            <Route path="*" element={<Navigate to="/emotion/today" replace />} />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  );
}
