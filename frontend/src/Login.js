import React, { useState } from 'react';

const API_BASE = '';

export default function Login({ onLoginSuccess }) {
  const [selectedUser, setSelectedUser] = useState(null);
  const [authUrl, setAuthUrl] = useState('');
  const [authCode, setAuthCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleLogin = async (u) => {
    setSelectedUser(u);
    setAuthCode('');
    setError('');
    setAuthUrl('');
    setSuccess(false);
    try {
      const res = await fetch(`${API_BASE}/auth-url?user=${u}`);
      const data = await res.json();
      setAuthUrl(data.auth_url);
    } catch (e) {
      setError('Failed to fetch auth URL.');
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);
    try {
      const res = await fetch(`${API_BASE}/generate-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: selectedUser, code: authCode })
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to generate access token.');
      }
      setSuccess(true);
      if (onLoginSuccess) onLoginSuccess(selectedUser);
    } catch (e) {
      setError(e.message || 'Failed to generate access token.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ width: '100%', maxWidth: 420, margin: '0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <h2 style={{ marginBottom: 32, color: '#fff' }}>Login to Upstox</h2>
      <div className="login-btn-group" style={{ display: 'flex', gap: 16, marginBottom: 32 }}>
        <button
          className={`sidebar-btn${selectedUser === 'emperor' ? ' active' : ''}`}
          onClick={() => handleLogin('emperor')}
        >
          Login as Emperor
        </button>
        <button
          className={`sidebar-btn${selectedUser === 'king' ? ' active' : ''}`}
          onClick={() => handleLogin('king')}
        >
          Login as King
        </button>
      </div>
      {authUrl && (
        <div style={{ marginBottom: 24, textAlign: 'center' }}>
          <a
            href={authUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: '#61dafb', fontWeight: 500, fontSize: 16 }}
          >
            Open Upstox Login
          </a>
          <div style={{ color: '#bbb', fontSize: 13, marginTop: 8 }}>
            Complete login, copy the <b>auth code</b> from the Google redirect URL, and paste below.
          </div>
        </div>
      )}
      {selectedUser && (
        <div style={{ width: '100%' }}>
          <input
            type="text"
            placeholder="Paste auth code here"
            value={authCode}
            onChange={e => { setAuthCode(e.target.value); setSuccess(false); setError(''); }}
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: 8,
              border: '1px solid #444',
              background: '#181a1b',
              color: '#fff',
              fontSize: 16,
              marginBottom: 12
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={!authCode || loading}
            style={{
              width: '100%',
              padding: '12px 0',
              borderRadius: 8,
              border: 'none',
              background: !authCode || loading ? '#444' : '#61dafb',
              color: !authCode || loading ? '#bbb' : '#181a1b',
              fontWeight: 600,
              fontSize: 16,
              cursor: !authCode || loading ? 'not-allowed' : 'pointer',
              marginBottom: 8,
              marginTop: 4
            }}
          >
            {loading ? 'Submitting...' : 'Submit'}
          </button>
          {success && (
            <div style={{ color: '#4caf50', fontSize: 14, marginTop: 4 }}>
              Access token generated and stored!
            </div>
          )}
          {authCode && !success && (
            <div style={{ color: '#61dafb', fontSize: 14, marginTop: 4 }}>
              Auth code ready for next step.
            </div>
          )}
        </div>
      )}
      {error && <div style={{ color: 'red', marginTop: 16 }}>{error}</div>}
    </div>
  );
} 