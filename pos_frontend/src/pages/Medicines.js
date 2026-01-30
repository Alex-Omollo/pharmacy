import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import api from '../services/api';
import PageHeader from '../components/PageHeader';
import './Medicines.css';

const Medicines = () => {
  const { user } = useSelector((state) => state.auth);
  const [medicines, setMedicines] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [showAddBatchModal, setShowAddBatchModal] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedMedicine, setSelectedMedicine] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterExpiring, setFilterExpiring] = useState(false);
  const [batches, setBatches] = useState([]);
  const [loadingBatches, setLoadingBatches] = useState(false);
  const [editBatchMode, setEditBatchMode] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [suppliers, setSuppliers] = useState([]);
  
  const [batchFormData, setBatchFormData] = useState({
    medicine: '',
    batch_number: '',
    supplier: '',
    manufacture_date: '',
    expiry_date: '',
    quantity: '',
    purchase_price: '',
    selling_price: '',
    is_blocked: false,
    block_reason: ''
  });
    
  const [formData, setFormData] = useState({
    b_name: '',
    generic_name: '',
    sku: '',
    category: '',
    description: '',
    dosage_form: 'tablet',
    strength: '',
    manufacturer: '',
    selling_price: '',
    buying_price: '',
    is_prescription: false,
    is_controlled: false,
    min_stock_level: '10',
    is_active: true,
  });
  
  const [error, setError] = useState('');
  const [batchError, setBatchError] = useState('');

  const canModify = user?.role === 'admin' || user?.role === 'manager';

  useEffect(() => {
    fetchMedicines();
    fetchCategories();
    fetchSuppliers();
  }, [searchTerm, filterCategory, filterExpiring]);

  const fetchMedicines = async () => {
    try {
      let url = '/medicines/?';
      if (searchTerm) url += `search=${searchTerm}&`;
      if (filterCategory) url += `category=${filterCategory}&`;
      if (filterExpiring) url += `expiring_soon=true&`;
      
      const response = await api.get(url);
      setMedicines(response.data);
    } catch (err) {
      console.error('Error fetching medicines:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories/');
      setCategories(response.data);
    } catch (err) {
      console.error('Error fetching categories:', err);
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

  const fetchBatches = async (medicineId) => {
    setLoadingBatches(true);
    try {
      const response = await api.get(`/batches/?medicine=${medicineId}`);
      setBatches(response.data);
    } catch (err) {
      console.error('Error fetching batches:', err);
      alert('Failed to load batches');
    } finally {
      setLoadingBatches(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (editMode) {
        await api.patch(`/medicines/${selectedMedicine.id}/`, formData);
      } else {
        await api.post('/medicines/create/', formData);
      }
      
      setShowModal(false);
      resetForm();
      fetchMedicines();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving medicine');
    }
  };

  const handleBatchSubmit = async (e) => {
    e.preventDefault();
    setBatchError('');

    try {
      const batchData = {
        ...batchFormData,
        medicine: selectedMedicine.id,
      };

      if (editBatchMode) {
        await api.patch(`/batches/${selectedBatch.id}/`, {
          selling_price: batchFormData.selling_price,
          is_blocked: batchFormData.is_blocked || false,
          block_reason: batchFormData.block_reason || '',
        });
        alert('Batch updated successfully');
      } else {
        await api.post('/batches/create/', batchData);
        alert('Batch created successfully');
      }
      
      setShowAddBatchModal(false);
      resetBatchForm();
      fetchBatches(selectedMedicine.id);
      fetchMedicines(); // Refresh medicines to update stock counts
    } catch (err) {
      setBatchError(err.response?.data?.detail || Object.values(err.response?.data || {}).flat().join(', ') || 'Error saving batch');
    }
  };

  const handleEdit = (medicine) => {
    setSelectedMedicine(medicine);
    setFormData({
      b_name: medicine.b_name || '',
      generic_name: medicine.generic_name || '',
      sku: medicine.sku || '',
      category: medicine.category || '',
      description: medicine.description || '',
      dosage_form: medicine.dosage_form || 'tablet',
      strength: medicine.strength || '',
      manufacturer: medicine.manufacturer || '',
      selling_price: medicine.selling_price ? String(medicine.selling_price) : '',
      buying_price: medicine.buying_price ? String(medicine.buying_price) : '',
      is_prescription: medicine.schedule === 'prescription' || medicine.schedule === 'controlled',
      is_controlled: medicine.schedule === 'controlled',
      min_stock_level: medicine.min_stock_level ? String(medicine.min_stock_level) : '10',
      is_active: medicine.is_active !== undefined ? medicine.is_active : true,
    });
    setEditMode(true);
    setShowModal(true);
  };

  const handleEditBatch = (batch) => {
    setSelectedBatch(batch);
    setBatchFormData({
      batch_number: batch.batch_number,
      supplier: batch.supplier || '',
      manufacture_date: batch.manufacture_date || '',
      expiry_date: batch.expiry_date,
      quantity: String(batch.quantity),
      purchase_price: String(batch.purchase_price),
      selling_price: String(batch.selling_price),
      is_blocked: batch.is_blocked || false,
      block_reason: batch.block_reason || '',
    });
    setEditBatchMode(true);
    setShowAddBatchModal(true);
  };

  const toggleBatchBlock = async (batch) => {
    const action = batch.is_blocked ? 'unblock' : 'block';
    const reason = action === 'block' ? prompt('Enter reason for blocking:') : null;
    
    if (action === 'block' && !reason) return;

    try {
      await api.post(`/batches/${batch.id}/${action}/`, { reason });
      alert(`Batch ${action}ed successfully`);
      fetchBatches(selectedMedicine.id);
    } catch (err) {
      alert(`Error: ${err.response?.data?.error || 'Failed to update batch status'}`);
    }
  };

  const toggleMedicineStatus = async (medicine) => {
    const action = medicine.is_active ? 'deactivate' : 'reactivate';
    const actionText = medicine.is_active ? 'Deactivate' : 'Reactivate';
    
    if (window.confirm(`${actionText} "${medicine.b_name}"?`)) {
      try {
        const response = await api.post(`/medicines/${medicine.id}/${action}/`);
        alert(response.data.message);
        fetchMedicines();
      } catch (err) {
        alert(`Error: ${err.response?.data?.error || 'Failed to update medicine status'}`);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      b_name: '',
      generic_name: '',
      sku: '',
      category: '',
      description: '',
      dosage_form: 'tablet',
      strength: '',
      manufacturer: '',
      selling_price: '',
      buying_price: '',
      is_prescription: false,
      is_controlled: false,
      min_stock_level: '10',
      is_active: true,
    });
    setEditMode(false);
    setSelectedMedicine(null);
    setError('');
  };

  const resetBatchForm = () => {
    setBatchFormData({
      batch_number: '',
      supplier: '',
      manufacture_date: '',
      expiry_date: '',
      quantity: '',
      purchase_price: '',
      selling_price: '',
    });
    setEditBatchMode(false);
    setSelectedBatch(null);
    setBatchError('');
  };

  const handleNumericChange = (e) => {
    const {name, value} = e.target;
    if (value === '' || !isNaN(value)) {
      setFormData(prev => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleBatchNumericChange = (e) => {
    const {name, value} = e.target;
    if (value === '' || !isNaN(value)) {
      setBatchFormData(prev => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleBatchChange = (e) => {
    const { name, value, type, checked } = e.target;
    setBatchFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const viewBatches = async (medicine) => {
    setSelectedMedicine(medicine);
    setShowBatchModal(true);
    await fetchBatches(medicine.id);
  };

  const getBatchStatusClass = (batch) => {
    if (batch.is_blocked) return 'blocked';
    if (batch.status === 'expired') return 'expired';
    if (batch.status === 'near_expiry') return 'near-expiry';
    if (batch.quantity === 0) return 'depleted';
    return 'available';
  };

  const getBatchStatusText = (batch) => {
    if (batch.is_blocked) return `🔒 Blocked: ${batch.block_reason}`;
    if (batch.status === 'expired') return 'Expired';
    if (batch.status === 'near_expiry') return `Expiring in ${batch.days_to_expiry} days`;
    if (batch.quantity === 0) return 'Depleted';
    return '✅ Available';
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="medicines-container">
      <PageHeader title="💊 Medicine Management" subtitle="Manage your pharmacy medicine catalog">
        {canModify && (
          <button onClick={() => { resetForm(); setShowModal(true); }} className="btn-primary">
            + Add Medicine
          </button>
        )}
      </PageHeader>

      <div className="medicines-filters">
        <input
          type="text"
          placeholder="Search by brand name, generic name, or SKU..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="filter-select"
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>

        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={filterExpiring}
            onChange={(e) => setFilterExpiring(e.target.checked)}
          />
          Near Expiry Only
        </label>
      </div>

      <div className="medicines-grid">
        {medicines.map((medicine) => (
          <div key={medicine.id} className="medicine-card">
            <div className="medicine-header">
              <div className="medicine-badges">
                {(medicine.schedule === 'prescription' || medicine.schedule === 'controlled') && (
                  <span className="badge badge-prescription">℞ Rx</span>
                )}
                {medicine.schedule === 'controlled' && (
                  <span className="badge badge-controlled">⚠️ Controlled</span>
                )}
                {!medicine.is_active && (
                  <span className="badge badge-inactive">Inactive</span>
                )}
              </div>
            </div>
            
            <div className="medicine-info">
              <h3>{medicine.b_name}</h3>
              <p className="generic-name">{medicine.generic_name}</p>
              <p className="medicine-sku">SKU: {medicine.sku}</p>
              <p className="medicine-strength">{medicine.strength} • {medicine.dosage_form}</p>
              <p className="medicine-category">{medicine.category_name || 'Uncategorized'}</p>
              
              <div className="medicine-stock">
                <div className="stock-summary">
                  <span className="total-stock">Total Stock: {medicine.total_stock || 0}</span>
                  {medicine.active_batches_count > 0 && (
                    <span className="batches-count">{medicine.active_batches_count} batches</span>
                  )}
                </div>
              </div>
            </div>

            {canModify && (
              <div className="medicine-actions">
                <button 
                  onClick={() => viewBatches(medicine)} 
                  className="btn-batches"
                  title="View batches"
                >
                  Batches
                </button>
                <button onClick={() => handleEdit(medicine)} className="btn-edit">
                  Edit
                </button>
                <button 
                  onClick={() => toggleMedicineStatus(medicine)} 
                  className={medicine.is_active ? "btn-deactivate" : "btn-activate"}
                >
                  {medicine.is_active ? '🔒' : '✓'}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {medicines.length === 0 && (
        <div className="no-medicines">
          <p>No medicines found</p>
        </div>
      )}

      {/* Medicine Create/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => { setShowModal(false); resetForm(); }}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editMode ? 'Edit Medicine' : 'Add New Medicine'}</h3>
              <button onClick={() => { setShowModal(false); resetForm(); }} className="close-btn">×</button>
            </div>
            
            {error && <div className="error-message">{error}</div>}
            
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>Brand Name *</label>
                  <input
                    type="text"
                    name="b_name"
                    value={formData.b_name}
                    onChange={handleChange}
                    required
                    placeholder="e.g., Panadol"
                  />
                </div>
                <div className="form-group">
                  <label>Generic Name *</label>
                  <input
                    type="text"
                    name="generic_name"
                    value={formData.generic_name}
                    onChange={handleChange}
                    required
                    placeholder="e.g., Paracetamol"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>SKU {editMode ? '(read-only)' : '(auto-generated if empty)'}</label>
                  <input
                    type="text"
                    name="sku"
                    value={formData.sku}
                    onChange={handleChange}
                    readOnly={editMode}
                    placeholder="Auto-generated"
                  />
                </div>
                <div className="form-group">
                  <label>Strength *</label>
                  <input
                    type="text"
                    name="strength"
                    value={formData.strength}
                    onChange={handleChange}
                    required
                    placeholder="e.g., 500mg"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Dosage Form *</label>
                  <select
                    name="dosage_form"
                    value={formData.dosage_form}
                    onChange={handleChange}
                    required
                  >
                    <option value="tablet">Tablet</option>
                    <option value="capsule">Capsule</option>
                    <option value="syrup">Syrup</option>
                    <option value="injection">Injection</option>
                    <option value="cream">Cream/Ointment</option>
                    <option value="drops">Drops</option>
                    <option value="inhaler">Inhaler</option>
                    <option value="suppository">Suppository</option>
                    <option value="powder">Powder</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Category</label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                  >
                    <option value="">Select Category</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Manufacturer</label>
                <input
                  type="text"
                  name="manufacturer"
                  value={formData.manufacturer}
                  onChange={handleChange}
                  placeholder="e.g., GSK"
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows="3"
                  placeholder="Usage, indications, etc."
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Selling Price *</label>
                  <input
                    type="text"
                    name="selling_price"
                    value={formData.selling_price}
                    onChange={handleNumericChange}
                    required
                    placeholder="0.00"
                  />
                </div>
                <div className="form-group">
                  <label>Buying Price *</label>
                  <input
                    type="text"
                    name="buying_price"
                    value={formData.buying_price}
                    onChange={handleNumericChange}
                    required
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Min Stock Level</label>
                  <input
                    type="number"
                    name="min_stock_level"
                    value={formData.min_stock_level}
                    onChange={handleChange}
                    min="0"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="is_prescription"
                      checked={formData.is_prescription}
                      onChange={handleChange}
                    />
                    Prescription Medicine
                  </label>
                </div>
                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="is_controlled"
                      checked={formData.is_controlled}
                      onChange={handleChange}
                    />
                    Controlled Drug
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleChange}
                  />
                  Active Medicine
                </label>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => { setShowModal(false); resetForm(); }} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editMode ? 'Update Medicine' : 'Create Medicine'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Batch Management Modal */}
      {showBatchModal && selectedMedicine && (
        <div className="modal-overlay" onClick={() => { setShowBatchModal(false); setBatches([]); }}>
          <div className="modal modal-xl" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📦 Batches - {selectedMedicine.b_name}</h3>
              <button onClick={() => { setShowBatchModal(false); setBatches([]); }} className="close-btn">×</button>
            </div>

            <div className="medicine-info-box">
              <h4>{selectedMedicine.b_name} ({selectedMedicine.generic_name})</h4>
              <p>{selectedMedicine.strength} • {selectedMedicine.dosage_form}</p>
              <p>Total Stock: <strong>{selectedMedicine.total_stock || 0}</strong></p>
            </div>

            {canModify && (
              <div style={{ marginBottom: '20px' }}>
                <button 
                  onClick={() => { resetBatchForm(); setShowAddBatchModal(true); }} 
                  className="btn-primary"
                >
                  + Add New Batch
                </button>
              </div>
            )}

            <div className="batches-list">
              {loadingBatches ? (
                <p style={{textAlign: 'center', padding: '40px', color: '#666'}}>
                  Loading batches...
                </p>
              ) : batches.length === 0 ? (
                <p style={{textAlign: 'center', padding: '40px', color: '#666'}}>
                  No batches found for this medicine
                </p>
              ) : (
                <table className="report-table">
                  <thead>
                    <tr>
                      <th>Batch Number</th>
                      <th>Expiry Date</th>
                      <th>Quantity</th>
                      <th>Selling Price</th>
                      <th>Purchase Price</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batches.map((batch) => (
                      <tr key={batch.id} className={getBatchStatusClass(batch)}>
                        <td><strong>{batch.batch_number}</strong></td>
                        <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
                        <td>{batch.quantity}</td>
                        <td>KSh {parseFloat(batch.selling_price).toFixed(2)}</td>
                        <td>KSh {parseFloat(batch.purchase_price).toFixed(2)}</td>
                        <td>{getBatchStatusText(batch)}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '5px' }}>
                            {canModify && (
                              <>
                                <button 
                                  onClick={() => handleEditBatch(batch)}
                                  className="btn-small"
                                  style={{ padding: '4px 8px', fontSize: '12px' }}
                                >
                                  Edit
                                </button>
                                {batch.status !== 'expired' && (
                                  <button 
                                    onClick={() => toggleBatchBlock(batch)}
                                    className="btn-small"
                                    style={{ 
                                      padding: '4px 8px', 
                                      fontSize: '12px',
                                      background: batch.is_blocked ? '#4CAF50' : '#FFC107'
                                    }}
                                  >
                                    {batch.is_blocked ? '🔓 Unblock' : '🔒 Block'}
                                  </button>
                                )}
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="modal-footer">
              <button onClick={() => { setShowBatchModal(false); setBatches([]); }} className="btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Batch Modal */}
      {showAddBatchModal && selectedMedicine && (
        <div className="modal-overlay" onClick={() => { setShowAddBatchModal(false); resetBatchForm(); }}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editBatchMode ? 'Edit Batch' : `Add New Batch - ${selectedMedicine.b_name}`}</h3>
              <button onClick={() => { setShowAddBatchModal(false); resetBatchForm(); }} className="close-btn">×</button>
            </div>

            {batchError && <div className="error-message">{batchError}</div>}

            <form onSubmit={handleBatchSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>Batch Number *</label>
                  <input
                    type="text"
                    name="batch_number"
                    value={batchFormData.batch_number}
                    onChange={handleBatchChange}
                    required
                    readOnly={editBatchMode}
                    placeholder="e.g., BATCH001"
                  />
                </div>
                <div className="form-group">
                  <label>Supplier</label>
                  <select
                    name="supplier"
                    value={batchFormData.supplier}
                    onChange={handleBatchChange}
                    disabled={editBatchMode}
                  >
                    <option value="">Select Supplier</option>
                    {suppliers.map((supplier) => (
                      <option key={supplier.id} value={supplier.id}>{supplier.name}</option>
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
                    value={batchFormData.manufacture_date}
                    onChange={handleBatchChange}
                    max={new Date().toISOString().split('T')[0]}
                    disabled={editBatchMode}
                  />
                </div>
                <div className="form-group">
                  <label>Expiry Date *</label>
                  <input
                    type="date"
                    name="expiry_date"
                    value={batchFormData.expiry_date}
                    onChange={handleBatchChange}
                    required
                    min={new Date().toISOString().split('T')[0]}
                    disabled={editBatchMode}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Quantity *</label>
                  <input
                    type="text"
                    name="quantity"
                    value={batchFormData.quantity}
                    onChange={handleBatchNumericChange}
                    required
                    min="1"
                    disabled={editBatchMode}
                    placeholder="0"
                  />
                </div>
                <div className="form-group">
                  <label>Purchase Price *</label>
                  <input
                    type="text"
                    name="purchase_price"
                    value={batchFormData.purchase_price}
                    onChange={handleBatchNumericChange}
                    required
                    disabled={editBatchMode}
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Selling Price *</label>
                <input
                  type="text"
                  name="selling_price"
                  value={batchFormData.selling_price}
                  onChange={handleBatchNumericChange}
                  required
                  placeholder="0.00"
                />
              </div>

              {editBatchMode && (
                <>
                  <div className="form-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        name="is_blocked"
                        checked={batchFormData.is_blocked}
                        onChange={handleBatchChange}
                      />
                      Block this batch
                    </label>
                  </div>

                  {batchFormData.is_blocked && (
                    <div className="form-group">
                      <label>Block Reason</label>
                      <textarea
                        name="block_reason"
                        value={batchFormData.block_reason}
                        onChange={handleBatchChange}
                        rows="2"
                        placeholder="Reason for blocking this batch..."
                      />
                    </div>
                  )}
                </>
              )}

              <div className="modal-footer">
                <button type="button" onClick={() => { setShowAddBatchModal(false); resetBatchForm(); }} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editBatchMode ? 'Update Batch' : 'Create Batch'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Medicines;