import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function RegisterForm() {
  const navigate = useNavigate();
  const { register, loading, error } = useAuth();
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await register({ user_id: userId, password, email });
    navigate('/login');
  };

  return (
    <div className="card" style={{ maxWidth: 520, margin: '0 auto' }}>
      <h2>Create account</h2>
      <form onSubmit={handleSubmit} className="grid" style={{ gap: 12 }}>
        <label className="input-group">
          <span>User ID</span>
          <input value={userId} onChange={(e) => setUserId(e.target.value)} required />
        </label>
        <label className="input-group">
          <span>Email</span>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
        </label>
        <label className="input-group">
          <span>Password</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error ? <div className="notice">{error}</div> : null}
        <button className="button" type="submit" disabled={loading}>
          {loading ? 'Registering…' : 'Register'}
        </button>
      </form>
    </div>
  );
}
