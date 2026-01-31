import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { logout } from '../store/authSlice';
import './Dashboard.css';

const Dashboard = () => {
  const { user } = useSelector((state) => state.auth);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const isAdmin = user?.role === 'admin';
  const isManager = user?.role === 'manager' || user?.role === 'admin';
  const isCashier = user?.role === 'cashier' || user?.role === 'manager' || user?.role === 'admin';

  return (
    <div className="dashboard-container">
      <nav className="dashboard-nav">
        <h1> Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.username} ({user?.role_display})</span>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </nav>
      
      <div className="dashboard-content">
        <h2>Welcome: </h2>
        <p>Select a module to get started</p>
        
        <div className="placeholder-cards">
          <Link to="/sales" className="card">
            <h3>💰 Sales</h3>
            <p>Process transactions</p>
          </Link>
          
          <Link to="/sales-history" className="card">
            <h3>📋 Sales History</h3>
            <p>View past transactions</p>
          </Link>
          
          {(isAdmin || isManager) && (
            <>
              {/* <Link to="/products" className="card">
                <h3>📦 Products</h3>
                <p>Manage product catalog</p>
              </Link> */}
              <Link to="/medicines" className='card'>
                <h3>💊 Medicines</h3>
                <p>Manage medicine catalog</p>
              </Link>

              <Link to="/batches" className="card">
                <h3>📦 Batch Management</h3>
                <p>Track medicine batches & expiry</p>
              </Link>

              <Link to="/stock-receiving" className="card">
                <h3>📥 Stock Receiving</h3>
                <p>Receive stock from suppliers</p>
              </Link>

              <Link to="/expiry-management" className="card">
                <h3>⏰ Expiry Management</h3>
                <p>Monitor expired & near-expiry stock</p>
              </Link>
              
              <Link to="/categories" className="card">
                <h3>📂 Categories</h3>
                <p>Manage categories</p>
              </Link>
              
              {/* <Link to="/inventory" className="card">
                <h3>📊 Inventory</h3>
                <p>Track stock levels</p>
              </Link> */}
              
              <Link to="/reports" className="card">
                <h3>📈 Reports</h3>
                <p>View analytics</p>
              </Link>
            </>
          )}
          
          {isAdmin && (
            <Link to="/users" className="card">
              <h3>👥 Users</h3>
              <p>Manage users</p>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;