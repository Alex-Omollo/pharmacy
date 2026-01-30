import React, { useState, useEffect } from 'react';
import api from '../services/api';
import PageHeader from '../components/PageHeader';
import './Batches.css';

const Batches = () => {
  const [batches, setBatches] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [suppliers, setSuppliers] = useState([])
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    medicine: '',
    batch_number: '',
    supplier: '',
    manufacture_date: '',
    expiry_date: '',
    quantity: '',
    purchase_price: '',
    selling_price: '',
  });

  useEffect(() => {
    fetchBatches();
    fetchMedicines();
    fetchSuppliers();
  }, []);

  const fetchBatches = async () => {
    try {
      const response = await api.get('/batches/');
      setBatches(response.data);
    } catch (err) {
      console.error('Error fetching batches:', err);
      setError('Failed to load batches');
    } finally {
      setLoading(false);
    }
  };

  const fetchMedicines = async () => {
    try {
      const response = await api.get('/medicines/');
      setMedicines(response.data);
    } catch (err) {
      console.error('Error fetching medicines:', err);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const response = await api.get('/inventory/suppliers/');
      setSuppliers(response.data);
    } catch (err) {
      console.error('Error fetching suppliers:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate form data
    if (!formData.medicine) {
      setError('Please select a medicine');
      return;
    }

    if (!formData.batch_number.trim()) {
      setError('Batch number is required');
      return;
    }

    if (!formData.expiry_date) {
      setError('Expiry date is required');
      return;
    }

    if (!formData.quantity || formData.quantity <= 0) {
      setError('Quantity must be greater than 0');
      return;
    }

    if (!formData.selling_price || formData.selling_price <= 0) {
      setError('Selling price must be greater than 0');
      return;
    }

    try {
      // Prepare data for API
      const batchData = {
        medicine: parseInt(formData.medicine),
        batch_number: formData.batch_number.trim(),
        supplier: formData.supplier ? parseInt(formData.supplier) : null,
        manufacture_date: formData.manufacture_date || null,
        expiry_date: formData.expiry_date,
        initial_quantity: parseInt(formData.quantity),
        quantity: parseInt(formData.quantity),
        purchase_price: parseFloat(formData.purchase_price) || 0,
        selling_price: parseFloat(formData.selling_price),
      };

      console.log('📤 Sending batch data:', batchData);

      const response = await api.post('/batches/create/', batchData);
      
      console.log('✅ Batch created:', response.data);
      
      alert(response.data.message || 'Batch created successfully!');
      setShowModal(false);
      resetForm();
      fetchBatches();
    } catch (err) {
      console.error('Error creating batch:', err);
      
      if (err.response?.data) {
        // Handle validation errors
        if (err.response.data.details) {
          const errorMessages = Object.entries(err.response.data.details)
            .map(([field, errors]) => `${field}: ${errors.join(', ')}`)
            .join('\n');
          setError(errorMessages);
        } else if (err.response.data.error) {
          setError(err.response.data.error);
        } else {
          setError('Error creating batch. Please check your input.');
        }
      } else {
        setError('Network error. Please try again.');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      medicine: '',
      batch_number: '',
      supplier: '',
      manufacture_date: '',
      expiry_date: '',
      quantity: '',
      purchase_price: '',
      selling_price: '',
    });
    setError('');
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const getBadgeClass = (batch) => {
    if (batch.is_expired) return 'badge-expired';
    if (batch.is_near_expiry) return 'badge-warning';
    return 'badge-active';
  };

  const getBadgeText = (batch) => {
    if (batch.is_expired) return 'Expired';
    if (batch.is_near_expiry) return 'Expiring Soon';
    return 'Active';
  };

  if (loading) {
    return <div className="loading">Loading batches...</div>;
  }

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
              <th>Selling Price</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {batches.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '40px' }}>
                  No batches found. Create your first batch.
                </td>
              </tr>
            ) : (
              batches.map(batch => (
                <tr key={batch.id} className={batch.is_expired ? 'expired-row' : ''}>
                  <td>{batch.medicine}</td>
                  <td>{batch.batch_number}</td>
                  <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
                  <td>{batch.quantity}</td>
                  <td>KSh {parseFloat(batch.selling_price).toFixed(2)}</td>
                  <td>
                    <span className={`badge ${getBadgeClass(batch)}`}>
                      {getBadgeText(batch)}
                    </span>
                  </td>
                  <td>
                    <button className="btn-small">View</button>
                  </td>
                </tr>
              ))
            )}
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

            {error && (
              <div className="error-message" style={{ whiteSpace: 'pre-line' }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Medicine *</label>
                <select
                  name="medicine"
                  value={formData.medicine}
                  onChange={handleChange}
                  required
                >
                  <option value="">Select Medicine</option>
                  {medicines.map(med => (
                    <option key={med.id} value={med.id}>
                      {med.b_name} ({med.generic_name}) - {med.strength}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Batch Number *</label>
                  <input
                    type="text"
                    name="batch_number"
                    value={formData.batch_number}
                    onChange={handleChange}
                    placeholder="BAT001"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Supplier</label>
                  <select
                    name="supplier"
                    value={formData.supplier}
                    onChange={handleChange}
                  >
                    <option value="">Select Supplier (Optional)</option>
                    {suppliers.map(sup => (
                      <option key={sup.id} value={sup.id}>{sup.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Manufacture Date</label>
                  <input
                    type="date"
                    name="manufacture_date"
                    value={formData.manufacture_date}
                    onChange={handleChange}
                    max={new Date().toISOString().split('T')[0]}
                  />
                </div>

                <div className="form-group">
                  <label>Expiry Date *</label>
                  <input
                    type="date"
                    name="expiry_date"
                    value={formData.expiry_date}
                    onChange={handleChange}
                    required
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Quantity *</label>
                <input
                  type="number"
                  name="quantity"
                  value={formData.quantity}
                  onChange={handleChange}
                  required
                  min="1"
                  placeholder="100"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Purchase Price (Cost)</label>
                  <input
                    type="number"
                    name="purchase_price"
                    value={formData.purchase_price}
                    onChange={handleChange}
                    step="0.01"
                    min="0"
                    placeholder="50.00"
                  />
                </div>
                <div className="form-group">
                  <label>Selling Price *</label>
                  <input
                    type="number"
                    name="selling_price"
                    value={formData.selling_price}
                    onChange={handleChange}
                    required
                    step="0.01"
                    min="0.01"
                    placeholder="80.00"
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button 
                  type="button" 
                  onClick={() => { setShowModal(false); resetForm(); }} 
                  className="btn-secondary"
                >
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