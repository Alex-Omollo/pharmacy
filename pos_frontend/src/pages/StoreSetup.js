// pos_frontend/src/pages/StoreSetup.js

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './StoreSetup.css';

const StoreSetup = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    store: {
      name: '',
      description: '',
      address: '',
      phone: '',
      email: '',
      business_registration: '',
      tax_id: ''
    },
    first_name: '',
    last_name: '',
    phone: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    if (name.startsWith('store_')) {
      const storeField = name.replace('store_', '');
      setFormData(prev => ({
        ...prev,
        store: {
          ...prev.store,
          [storeField]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/setup/complete/', formData);
      
      console.log('Setup completed:', response.data);
      alert('Store setup completed successfully!');
      
      // Redirect to dashboard
      navigate('/dashboard');
    } catch (err) {
      console.error('Setup error:', err);
      setError(err.response?.data?.error || 'Error completing setup');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="setup-container">
      <div className="setup-card">
        <div className="setup-header">
          <h1>🏪 Welcome to FeedsHub POS</h1>
          <p>Let's set up your store to get started</p>
        </div>

        {error && (
          <div className="error-message">{error}</div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Store Information */}
          <div className="section">
            <h3>📍 Store Information</h3>
            
            <div className="form-group">
              <label>Store Name *</label>
              <input
                type="text"
                name="store_name"
                value={formData.store.name}
                onChange={handleChange}
                placeholder="e.g., FeedsHub Main Branch"
                required
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                name="store_description"
                value={formData.store.description}
                onChange={handleChange}
                rows="3"
                placeholder="Brief description of your store..."
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Phone Number</label>
                <input
                  type="tel"
                  name="store_phone"
                  value={formData.store.phone}
                  onChange={handleChange}
                  placeholder="+254 700 000000"
                />
              </div>
              
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  name="store_email"
                  value={formData.store.email}
                  onChange={handleChange}
                  placeholder="store@feedshub.com"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Physical Address</label>
              <textarea
                name="store_address"
                value={formData.store.address}
                onChange={handleChange}
                rows="2"
                placeholder="Street, City, Country"
              />
            </div>
          </div>

          {/* Business Details */}
          <div className="section">
            <h3>📄 Business Details (Optional)</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>Business Registration Number</label>
                <input
                  type="text"
                  name="store_business_registration"
                  value={formData.store.business_registration}
                  onChange={handleChange}
                  placeholder="REG-123456"
                />
              </div>
              
              <div className="form-group">
                <label>Tax ID / VAT Number</label>
                <input
                  type="text"
                  name="store_tax_id"
                  value={formData.store.tax_id}
                  onChange={handleChange}
                  placeholder="TAX-123456"
                />
              </div>
            </div>
          </div>

          {/* Admin Profile Update */}
          <div className="section">
            <h3>👤 Your Profile (Optional)</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>First Name</label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  placeholder="John"
                />
              </div>
              
              <div className="form-group">
                <label>Last Name</label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  placeholder="Doe"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Phone Number</label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+254 700 000000"
              />
            </div>
          </div>

          <div className="form-actions">
            <button 
              type="submit" 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Setting up...' : '✓ Complete Setup'}
            </button>
          </div>

          <div className="setup-note">
            <p>
              💡 <strong>Note:</strong> You can add more stores later from the dashboard.
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StoreSetup;