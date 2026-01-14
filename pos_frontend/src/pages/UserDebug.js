import React from 'react';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';

const UserDebug = () => {
  const { user, isAuthenticated, accessToken } = useSelector((state) => state.auth);

  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🔍 User Debug Information</h1>
      <Link to="/dashboard">← Back to Dashboard</Link>
      
      <div style={{ marginTop: '20px', background: '#f5f5f5', padding: '20px', borderRadius: '8px' }}>
        <h2>Authentication Status</h2>
        <p><strong>Is Authenticated:</strong> {isAuthenticated ? '✅ Yes' : '❌ No'}</p>
        <p><strong>Has Access Token:</strong> {accessToken ? '✅ Yes' : '❌ No'}</p>
      </div>

      <div style={{ marginTop: '20px', background: '#f5f5f5', padding: '20px', borderRadius: '8px' }}>
        <h2>User Object</h2>
        <pre style={{ background: '#333', color: '#0f0', padding: '15px', borderRadius: '5px', overflow: 'auto' }}>
          {JSON.stringify(user, null, 2)}
        </pre>
      </div>

      <div style={{ marginTop: '20px', background: '#f5f5f5', padding: '20px', borderRadius: '8px' }}>
        <h2>Role Checks</h2>
        <p><strong>User Role:</strong> {user?.role || 'No role'}</p>
        <p><strong>Is Admin:</strong> {user?.role === 'admin' ? '✅ Yes' : '❌ No'}</p>
        <p><strong>Is Manager:</strong> {user?.role === 'manager' ? '✅ Yes' : '❌ No'}</p>
        <p><strong>Is Cashier:</strong> {user?.role === 'cashier' ? '✅ Yes' : '❌ No'}</p>
        <p><strong>Can Access Management:</strong> {(user?.role === 'admin' || user?.role === 'manager') ? '✅ Yes' : '❌ No'}</p>
      </div>

      <div style={{ marginTop: '20px', background: '#f5f5f5', padding: '20px', borderRadius: '8px' }}>
        <h2>LocalStorage Data</h2>
        <pre style={{ background: '#333', color: '#0f0', padding: '15px', borderRadius: '5px', overflow: 'auto' }}>
          {JSON.stringify({
            user: localStorage.getItem('user'),
            accessToken: localStorage.getItem('accessToken') ? 'Present' : 'Missing',
            refreshToken: localStorage.getItem('refreshToken') ? 'Present' : 'Missing'
          }, null, 2)}
        </pre>
      </div>

      <div style={{ marginTop: '20px', background: '#fff3cd', padding: '20px', borderRadius: '8px', border: '1px solid #ffc107' }}>
        <h2>⚠️ Troubleshooting</h2>
        <p><strong>If role is null or undefined:</strong></p>
        <ul>
          <li>Logout and login again</li>
          <li>Check backend user has role assigned</li>
          <li>Run: python manage.py shell → check user.role</li>
        </ul>
        
        <p style={{ marginTop: '15px' }}><strong>If role is 'cashier' but should be 'admin':</strong></p>
        <ul>
          <li>Run the fix_users.py script</li>
          <li>Clear browser localStorage</li>
          <li>Login again</li>
        </ul>
      </div>
    </div>
  );
};

export default UserDebug;