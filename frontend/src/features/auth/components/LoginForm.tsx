import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function LoginForm() {
  const navigate = useNavigate();
  const { login, loading, error } = useAuth();
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await login({ user_id: userId, password });
    navigate('/emotion/today');
  };

  return (
    <div className="card" style={{ maxWidth: 480, margin: '0 auto' }}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit} className="grid" style={{ gap: 12 }}>
        <label className="input-group">
          <span>User ID</span>
          <input value={userId} onChange={(e) => setUserId(e.target.value)} required />
        </label>
        <label className="input-group">
          <span>Password</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error ? <div className="notice">{error}</div> : null}
        <button className="button" type="submit" disabled={loading}>
          {loading ? 'Signing in…' : 'Login'}
        </button>
      </form>
    </div>
  );
}
