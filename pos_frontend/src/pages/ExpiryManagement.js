import React, { useState, useEffect } from 'react';
import api from '../services/api';
import PageHeader from '../components/PageHeader';

const ExpiryManagement = () => {
  const [nearExpiry, setNearExpiry] = useState([]);
  const [expired, setExpired] = useState([]);
  const [activeTab, setActiveTab] = useState('near-expiry');

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    if (activeTab === 'near-expiry') {
      const response = await api.get('/expiry/near-expiry/');
      setNearExpiry(response.data);
    } else {
      const response = await api.get('/expiry/expired/');
      setExpired(response.data);
    }
  };

  const handleWriteOff = async (batchId) => {
    if (window.confirm('Write off this expired batch? This cannot be undone.')) {
      await api.post('/expiry/write-off/', { batch_id: batchId });
      fetchData();
    }
  };

  return (
    <div className="expiry-container">
      <PageHeader title="⏰ Expiry Management" />

      <div className="tabs">
        <button
          className={activeTab === 'near-expiry' ? 'active' : ''}
          onClick={() => setActiveTab('near-expiry')}
        >
          Near Expiry
        </button>
        <button
          className={activeTab === 'expired' ? 'active' : ''}
          onClick={() => setActiveTab('expired')}
        >
          Expired
        </button>
      </div>

      {activeTab === 'near-expiry' && (
        <div className="expiry-table">
          <h3>⚠️ Batches Expiring Within 3 Months</h3>
          <table>
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Batch Number</th>
                <th>Expiry Date</th>
                <th>Days Until Expiry</th>
                <th>Quantity</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {nearExpiry.map(batch => (
                <tr key={batch.id} className="warning-row">
                  <td>{batch.medicine_name}</td>
                  <td>{batch.batch_number}</td>
                  <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
                  <td>{batch.days_until_expiry} days</td>
                  <td>{batch.quantity}</td>
                  <td>
                    <button className="btn-small btn-warn">Notify</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'expired' && (
        <div className="expiry-table">
          <h3>❌ Expired Batches</h3>
          <table>
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Batch Number</th>
                <th>Expiry Date</th>
                <th>Quantity</th>
                <th>Value</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {expired.map(batch => (
                <tr key={batch.id} className="expired-row">
                  <td>{batch.medicine_name}</td>
                  <td>{batch.batch_number}</td>
                  <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
                  <td>{batch.quantity}</td>
                  <td>KSh {(batch.quantity * batch.selling_price).toFixed(2)}</td>
                  <td>
                    <button 
                      className="btn-small btn-danger"
                      onClick={() => handleWriteOff(batch.id)}
                    >
                      Write Off
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ExpiryManagement;