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
  const [editMode, setEditMode] = useState(false);
  const [selectedMedicine, setSelectedMedicine] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterExpiring, setFilterExpiring] = useState(false);
  
  const [formData, setFormData] = useState({
    brand_name: '',
    generic_name: '',
    sku: '',
    category: '',
    description: '',
    dosage_form: 'tablet',
    strength: '',
    manufacturer: '',
    price: '',
    cost_price: '',
    is_prescription: false,
    is_controlled: false,
    min_stock_level: '10',
    is_active: true,
  });
  
  const [error, setError] = useState('');

  const canModify = user?.role === 'admin' || user?.role === 'manager';

  useEffect(() => {
    fetchMedicines();
    fetchCategories();
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

  const handleEdit = (medicine) => {
    setSelectedMedicine(medicine);
    setFormData({
      brand_name: medicine.brand_name || '',
      generic_name: medicine.generic_name || '',
      sku: medicine.sku || '',
      category: medicine.category || '',
      description: medicine.description || '',
      dosage_form: medicine.dosage_form || 'tablet',
      strength: medicine.strength || '',
      manufacturer: medicine.manufacturer || '',
      price: medicine.price ? String(medicine.price): '',
      cost_price: medicine.cost_price ? String(medicine.cost_price) : '',
      is_prescription: medicine.is_prescription || false,
      is_controlled: medicine.is_controlled || false,
      min_stock_level: medicine.min_stock_level ? String(medicine.min_stock_level) : '10',
      is_active: medicine.is_active !== undefined ? medicine.is_active : true,
    });
    setEditMode(true);
    setShowModal(true);
  };

  const toggleMedicineStatus = async (medicine) => {
    const action = medicine.is_active ? 'deactivate' : 'reactivate';
    const actionText = medicine.is_active ? 'Deactivate' : 'Reactivate';
    
    if (window.confirm(`${actionText} "${medicine.brand_name}"?`)) {
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
      brand_name: '',
      generic_name: '',
      sku: '',
      category: '',
      description: '',
      dosage_form: 'tablet',
      strength: '',
      manufacturer: '',
      price: '',
      cost_price: '',
      is_prescription: false,
      is_controlled: false,
      min_stock_level: '10',
      is_active: true,
    });
    setEditMode(false);
    setSelectedMedicine(null);
    setError('');
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

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const viewBatches = (medicine) => {
    setSelectedMedicine(medicine);
    setShowBatchModal(true);
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
                {medicine.is_prescription && (
                  <span className="badge badge-prescription">℞ Rx</span>
                )}
                {medicine.is_controlled && (
                  <span className="badge badge-controlled">⚠️ Controlled</span>
                )}
                {!medicine.is_active && (
                  <span className="badge badge-inactive">Inactive</span>
                )}
              </div>
            </div>
            
            <div className="medicine-info">
              <h3>{medicine.brand_name}</h3>
              <p className="generic-name">{medicine.generic_name}</p>
              <p className="medicine-sku">SKU: {medicine.sku}</p>
              <p className="medicine-strength">{medicine.strength} • {medicine.dosage_form}</p>
              <p className="medicine-category">{medicine.category_name || 'Uncategorized'}</p>
              
              <div className="medicine-stock">
                <div className="stock-summary">
                  <span className="total-stock">Total Stock: {medicine.total_stock || 0}</span>
                  {medicine.batches_count > 0 && (
                    <span className="batches-count">{medicine.batches_count} batches</span>
                  )}
                </div>
                
                {medicine.nearest_expiry && (
                  <div className={`expiry-info ${medicine.is_expiring_soon ? 'warning' : ''}`}>
                    ⏰ Nearest expiry: {new Date(medicine.nearest_expiry).toLocaleDateString()}
                  </div>
                )}
              </div>
            </div>

            {canModify && (
              <div className="medicine-actions">
                <button 
                  onClick={() => viewBatches(medicine)} 
                  className="btn-batches"
                  title="View batches"
                >
                  📦 Batches
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
                    name="brand_name"
                    value={formData.brand_name}
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
                  <label>SKU {formData.brand_name === '' ? '*' : '(optional)'}</label>
                  <input
                    type="text"
                    name="sku"
                    value={formData.sku}
                    onChange={handleChange}
                    required={formData.brand_name === ''}
                    readOnly={editMode}
                    placeholder="MED001"
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

              <div className='form -row'>
                <div className='form-group'>
                  <label>Selling Price *</label>
                  <input
                    type='text'
                    name='price'
                    value={formData.price}
                    onChange={handleNumericChange}
                    required
                  />
                </div>
                <div className='form-group'>
                  <label>Buying Price *</label>
                  <input
                    type='text'
                    name='cost_price'
                    value={formData.cost_price}
                    onChange={handleNumericChange}
                    required
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
        <div className="modal-overlay" onClick={() => setShowBatchModal(false)}>
          <div className="modal modal-xl" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📦 Batches - {selectedMedicine.brand_name}</h3>
              <button onClick={() => setShowBatchModal(false)} className="close-btn">×</button>
            </div>

            <div className="medicine-info-box">
              <h4>{selectedMedicine.brand_name} ({selectedMedicine.generic_name})</h4>
              <p>{selectedMedicine.strength} • {selectedMedicine.dosage_form}</p>
              <p>Total Stock: <strong>{selectedMedicine.total_stock || 0}</strong></p>
            </div>

            {/* Batches will be loaded here - to be implemented */}
            <div className="batches-list">
              <p style={{textAlign: 'center', color: '#666', padding: '40px'}}>
                Batch management coming next...
              </p>
            </div>

            <div className="modal-footer">
              <button onClick={() => setShowBatchModal(false)} className="btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Medicines;