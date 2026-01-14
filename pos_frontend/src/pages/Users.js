import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import api from '../services/api';
import PageHeader from '../components/PageHeader';
import './Users.css';

const Users = () => {
  const { user: currentUser } = useSelector((state) => state.auth);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    phone: '',
    role: '',
  });
  
  const [passwordData, setPasswordData] = useState({
    new_password: '',
    new_password2: '',
  });
  
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await api.get('/users/');
      // Filter out hidden super admin from regular view (optional)
      const visibleUsers = response.data.filter(u => u.username !== 'superadmin');
      setUsers(visibleUsers);
    } catch (err) {
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await api.get('/roles/');
      setRoles(response.data);
    } catch (err) {
      console.error('Error fetching roles:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.password2) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password && formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    try {
      await api.post('/users/register/', formData);
      setShowModal(false);
      setFormData({
        username: '',
        email: '',
        password: '',
        password2: '',
        first_name: '',
        last_name: '',
        phone: '',
        role: '',
      });
      fetchUsers();
      alert('User created successfully! They can change their password after first login.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating user');
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError('');

    if (passwordData.new_password !== passwordData.new_password2) {
      setError('Passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    try {
      // For changing another user's password (admin only)
      await api.post(`/users/${selectedUser.id}/reset-password/`, {
        new_password: passwordData.new_password,
      });
      
      setShowPasswordModal(false);
      setPasswordData({ new_password: '', new_password2: '' });
      alert('Password changed successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error changing password');
    }
  };

  const openPasswordModal = (user) => {
    setSelectedUser(user);
    setPasswordData({ new_password: '', new_password2: '' });
    setError('');
    setShowPasswordModal(true);
  };

  const openDeleteModal = (user) => {
    setSelectedUser(user);
    setError('');
    setShowDeleteModal(true);
  };

  const handleDelete = async () => {
    if (!selectedUser) return;

    try {
      await api.delete(`/users/${selectedUser.id}/`);
      setShowDeleteModal(false);
      setSelectedUser(null);
      fetchUsers();
      alert('User deleted successfully');
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.detail || 'Error deleting user';
      setError(errorMsg);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handlePasswordDataChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value,
    });
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="users-container">
      <PageHeader title="User Management" subtitle="Manage system users and permissions">
        <button onClick={() => setShowModal(true)} className="btn-primary">
          Add New User
        </button>
      </PageHeader>

      <div className="users-info-box">
        <p><strong>ℹ️ Password Management:</strong></p>
        <ul>
          <li>New users are created with a default password</li>
          <li>Users should change their password after first login</li>
          <li>Admins can reset passwords using the 🔑 button</li>
          <li>Password must be at least 8 characters</li>
        </ul>
      </div>

      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>
                  <strong>{user.username}</strong>
                  {user.username === currentUser?.username && (
                    <span className="badge-current-user"> (You)</span>
                  )}
                </td>
                <td>{`${user.first_name} ${user.last_name}`}</td>
                <td>{user.email}</td>
                <td>
                  <span className={`role-badge role-${user.role_name}`}>
                    {user.role_display}
                  </span>
                </td>
                <td>{user.phone || '-'}</td>
                <td>
                  <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{new Date(user.date_joined).toLocaleDateString()}</td>
                <td>
                  <div className="user-actions">
                    <button
                      onClick={() => openPasswordModal(user)}
                      className="btn-password"
                      title="Change Password"
                    >
                      🔑
                    </button>
                    <button
                      onClick={() => openDeleteModal(user)}
                      className="btn-delete-user"
                      title="Delete User"
                      disabled={user.username === currentUser?.username}
                    >
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Add New User</h3>
              <button onClick={() => setShowModal(false)} className="close-btn">
                ×
              </button>
            </div>
            
            {error && <div className="error-message">{error}</div>}
            
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>Username *</label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>First Name</label>
                  <input
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                  />
                </div>
                <div className="form-group">
                  <label>Last Name</label>
                  <input
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Initial Password * (min 8 characters)</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    minLength="8"
                  />
                  <small style={{ color: '#666', fontSize: '12px' }}>
                    User should change this after first login
                  </small>
                </div>
                <div className="form-group">
                  <label>Confirm Password *</label>
                  <input
                    type="password"
                    name="password2"
                    value={formData.password2}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                  />
                </div>
                <div className="form-group">
                  <label>Role *</label>
                  <select
                    name="role"
                    value={formData.role}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select Role</option>
                    {roles.map((role) => (
                      <option key={role.id} value={role.id}>
                        {role.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {showPasswordModal && selectedUser && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Change Password</h3>
              <button onClick={() => setShowPasswordModal(false)} className="close-btn">
                ×
              </button>
            </div>
            
            <div className="user-info-display">
              <p><strong>User:</strong> {selectedUser.username}</p>
              <p><strong>Name:</strong> {selectedUser.first_name} {selectedUser.last_name}</p>
            </div>

            {error && <div className="error-message">{error}</div>}
            
            <form onSubmit={handlePasswordChange}>
              <div className="form-group">
                <label>New Password * (min 8 characters)</label>
                <input
                  type="password"
                  name="new_password"
                  value={passwordData.new_password}
                  onChange={handlePasswordDataChange}
                  required
                  minLength="8"
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label>Confirm New Password *</label>
                <input
                  type="password"
                  name="new_password2"
                  value={passwordData.new_password2}
                  onChange={handlePasswordDataChange}
                  required
                />
              </div>

              <div className="password-requirements">
                <p><strong>Password Requirements:</strong></p>
                <ul>
                  <li>At least 8 characters long</li>
                  <li>Should contain letters and numbers</li>
                  <li>Avoid common passwords</li>
                </ul>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowPasswordModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Change Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedUser && (
        <div className="modal-overlay">
          <div className="modal modal-small">
            <div className="modal-header">
              <h3>⚠️ Confirm Delete</h3>
              <button onClick={() => setShowDeleteModal(false)} className="close-btn">
                ×
              </button>
            </div>
            
            {error && <div className="error-message">{error}</div>}
            
            <div className="delete-warning">
              <p>Are you sure you want to delete this user?</p>
              <div className="user-info-display">
                <p><strong>Username:</strong> {selectedUser.username}</p>
                <p><strong>Name:</strong> {selectedUser.first_name} {selectedUser.last_name}</p>
                <p><strong>Role:</strong> {selectedUser.role_display}</p>
              </div>
              <p className="warning-text">
                ⚠️ This action cannot be undone. All user data will be permanently removed.
              </p>
            </div>

            <div className="modal-footer">
              <button 
                type="button" 
                onClick={() => setShowDeleteModal(false)} 
                className="btn-secondary"
              >
                Cancel
              </button>
              <button 
                type="button"
                onClick={handleDelete} 
                className="btn-delete"
              >
                Delete User
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;