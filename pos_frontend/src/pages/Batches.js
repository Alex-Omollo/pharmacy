import React, { useState, useEffect } from 'react';
import api from '../services/api';
import PageHeader from '../components/PageHeader';
import './Batches.css';

const Batches = () => {
  const [batches, setBatches] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [showModal, setShowModal] = useState(false);
  
  const [formData, setFormData] = useState({
    medicine_id: '',
    batch_number: '',
    expiry_date: '',
    quantity: '',
    purchase_cost: '',
    selling_price: '',
    supplier: '',
  });

  useEffect(() => {
    fetchBatches();
    fetchMedicines();
  }, []);

  const fetchBatches = async () => {
    const response = await api.get('/batches/');
    setBatches(response.data);
  };

  const fetchMedicines = async () => {
    const response = await api.get('/medicines/');
    setMedicines(response.data);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.post('/batches/create/', formData);
    setShowModal(false);
    fetchBatches();
  };

  return (
    <div className="batches-container">
      <PageHeader title="📦 Batch Management">
        <button onClick={() => setShowModal(true)} className="btn-primary">
          + Add Batch
        </button>
      </PageHeader>

      <div className="batches-table">
        <table>
          <thead>
            <tr>
              <th>Medicine</th>
              <th>Batch Number</th>
              <th>Expiry Date</th>
              <th>Quantity</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {batches.map(batch => (
              <tr key={batch.id} className={batch.is_expired ? 'expired-row' : ''}>
                <td>{batch.medicine_name}</td>
                <td>{batch.batch_number}</td>
                <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
                <td>{batch.quantity}</td>
                <td>
                  {batch.is_expired ? (
                    <span className="badge badge-expired">Expired</span>
                  ) : batch.is_expiring_soon ? (
                    <span className="badge badge-warning">Expiring Soon</span>
                  ) : (
                    <span className="badge badge-active">Active</span>
                  )}
                </td>
                <td>
                  <button className="btn-small">View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Batch Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Batch</h3>
              <button onClick={() => setShowModal(false)} className="close-btn">×</button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Medicine *</label>
                <select
                  value={formData.medicine_id}
                  onChange={(e) => setFormData({...formData, medicine_id: e.target.value})}
                  required
                >
                  <option value="">Select Medicine</option>
                  {medicines.map(med => (
                    <option key={med.id} value={med.id}>{med.brand_name} ({med.generic_name})</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Batch Number *</label>
                <input
                  type="text"
                  value={formData.batch_number}
                  onChange={(e) => setFormData({...formData, batch_number: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label>Expiry Date *</label>
                <input
                  type="date"
                  value={formData.expiry_date}
                  onChange={(e) => setFormData({...formData, expiry_date: e.target.value})}
                  required
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>

              <div className="form-group">
                <label>Quantity *</label>
                <input
                  type="number"
                  value={formData.quantity}
                  onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                  required
                  min="1"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Purchase Cost</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.purchase_cost}
                    onChange={(e) => setFormData({...formData, purchase_cost: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Selling Price *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.selling_price}
                    onChange={(e) => setFormData({...formData, selling_price: e.target.value})}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Supplier</label>
                <input
                  type="text"
                  value={formData.supplier}
                  onChange={(e) => setFormData({...formData, supplier: e.target.value})}
                />
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Batch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Batches;