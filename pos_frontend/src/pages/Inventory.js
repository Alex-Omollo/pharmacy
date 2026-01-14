import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import PageHeader from '../components/PageHeader';
import './Inventory.css';

const Inventory = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [medicines, setMedicines] = useState([]);
  const [batches, setBatches] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [stockMovements, setStockMovements] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modals
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [showSupplierModal, setShowSupplierModal] = useState(false);
  const [showReceiveStockModal, setShowReceiveStockModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  
  // Selected items
  const [selectedMedicine, setSelectedMedicine] = useState(null);
  const [selectedBatch, setSelectedBatch] = useState(null);
  
  // Form data
  const [adjustmentData, setAdjustmentData] = useState({
    adjustment_type: 'add',
    quantity: '',
    reason: '',
    reference_number: ''
  });
  
  const [supplierData, setSupplierData] = useState({
    name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: ''
  });
  
  // Stock receiving form (creates batch)
  const [receiveStockData, setReceiveStockData] = useState({
    medicine_id: '',
    batch_number: '',
    expiry_date: '',
    quantity: '',
    purchase_cost: '',
    selling_price: '',
    supplier_id: '',
    invoice_number: '',
    notes: ''
  });
  
  // Batch adjustment form
  const [batchAdjustData, setBatchAdjustData] = useState({
    adjustment_type: 'damage',
    quantity: '',
    reason: ''
  });
  
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const statsRes = await api.get('/inventory/stats/');
      setStats(statsRes.data);
      
      if (activeTab === 'overview') {
        const medicinesRes = await api.get('/medicines/?exclude_children=true');
        setMedicines(medicinesRes.data);
        const alertsRes = await api.get('/inventory/alerts/');
        setAlerts(alertsRes.data);
      } else if (activeTab === 'batches') {
        const batchesRes = await api.get('/batches/');
        setBatches(batchesRes.data);
      } else if (activeTab === 'suppliers') {
        const suppliersRes = await api.get('/inventory/suppliers/');
        setSuppliers(suppliersRes.data);
      } else if (activeTab === 'stock-receiving') {
        const medicinesRes = await api.get('/medicines/?is_active=true');
        setMedicines(medicinesRes.data);
        const suppliersRes = await api.get('/inventory/suppliers/?is_active=true');
        setSuppliers(suppliersRes.data);
      } else if (activeTab === 'movements') {
        const movementsRes = await api.get('/inventory/stock-movements/');
        setStockMovements(movementsRes.data);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStockAdjustment = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await api.post('/inventory/stock-adjustment/', {
        medicine_id: selectedMedicine.id,
        ...adjustmentData,
        quantity: parseInt(adjustmentData.quantity)
      });
      
      setShowAdjustModal(false);
      setAdjustmentData({
        adjustment_type: 'add',
        quantity: '',
        reason: '',
        reference_number: ''
      });
      fetchData();
      alert('Stock adjusted successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error adjusting stock');
    }
  };

  const handleCreateSupplier = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await api.post('/inventory/suppliers/', supplierData);
      setShowSupplierModal(false);
      setSupplierData({
        name: '',
        contact_person: '',
        email: '',
        phone: '',
        address: ''
      });
      fetchData();
      alert('Supplier created successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating supplier');
    }
  };

  // PHARMACY: Receive stock - creates batch and increases quantity
  const handleReceiveStock = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await api.post('/batches/receive-stock/', {
        ...receiveStockData,
        quantity: parseInt(receiveStockData.quantity),
        purchase_cost: parseFloat(receiveStockData.purchase_cost),
        selling_price: parseFloat(receiveStockData.selling_price)
      });
      
      setShowReceiveStockModal(false);
      setReceiveStockData({
        medicine_id: '',
        batch_number: '',
        expiry_date: '',
        quantity: '',
        purchase_cost: '',
        selling_price: '',
        supplier_id: '',
        invoice_number: '',
        notes: ''
      });
      fetchData();
      alert('Stock received and batch created successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error receiving stock');
    }
  };

  // PHARMACY: Adjust batch quantity
  const handleBatchAdjustment = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await api.post(`/batches/${selectedBatch.id}/adjust/`, {
        ...batchAdjustData,
        quantity: parseInt(batchAdjustData.quantity)
      });
      
      setShowBatchModal(false);
      setBatchAdjustData({
        adjustment_type: 'damage',
        quantity: '',
        reason: ''
      });
      fetchData();
      alert('Batch adjusted successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error adjusting batch');
    }
  };

  const openAdjustModal = (medicine) => {
    setSelectedMedicine(medicine);
    setShowAdjustModal(true);
  };

  const openBatchAdjustModal = (batch) => {
    setSelectedBatch(batch);
    setShowBatchModal(true);
  };

  const getExpiryStatus = (expiryDate) => {
    const today = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return { status: 'expired', class: 'badge-expired', text: 'Expired' };
    if (diffDays <= 90) return { status: 'expiring-soon', class: 'badge-warning', text: `${diffDays} days left` };
    return { status: 'active', class: 'badge-success', text: 'Active' };
  };

  if (loading && !stats) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="inventory-container">
      <PageHeader 
        title="📦 Inventory Management" 
        subtitle="Track medicine stock, batches, and expiry dates"
      />

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>{stats.total_medicines || 0}</h3>
            <p>Total Medicines</p>
          </div>
          <div className="stat-card">
            <h3>{stats.total_batches || 0}</h3>
            <p>Active Batches</p>
          </div>
          <div className="stat-card">
            <h3>KSh {parseFloat(stats.total_stock_value || 0).toFixed(2)}</h3>
            <p>Stock Value</p>
          </div>
          <div className="stat-card alert">
            <h3>{stats.low_stock_count || 0}</h3>
            <p>Low Stock Medicines</p>
          </div>
          <div className="stat-card warning">
            <h3>{stats.expiring_soon_count || 0}</h3>
            <p>Expiring Soon (90 days)</p>
          </div>
          <div className="stat-card danger">
            <h3>{stats.expired_batches_count || 0}</h3>
            <p>Expired Batches</p>
          </div>
        </div>
      )}

      <div className="tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'batches' ? 'active' : ''}
          onClick={() => setActiveTab('batches')}
        >
          Batch Management
        </button>
        <button
          className={activeTab === 'stock-receiving' ? 'active' : ''}
          onClick={() => setActiveTab('stock-receiving')}
        >
          Stock Receiving
        </button>
        <button
          className={activeTab === 'suppliers' ? 'active' : ''}
          onClick={() => setActiveTab('suppliers')}
        >
          Suppliers
        </button>
        <button
          className={activeTab === 'movements' ? 'active' : ''}
          onClick={() => setActiveTab('movements')}
        >
          Stock Movements
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'overview' && (
          <>
            {alerts.length > 0 && (
              <div className="alerts-section">
                <h3>⚠️ Stock Alerts</h3>
                <div className="alerts-list">
                  {alerts.map(alert => (
                    <div key={alert.id} className="alert-item">
                      <div>
                        <strong>{alert.medicine_name}</strong>
                        <span className="sku">SKU: {alert.medicine_sku}</span>
                        {alert.alert_type === 'expiring' && (
                          <span className="alert-type">⏰ Expiring Soon</span>
                        )}
                      </div>
                      <div className="alert-details">
                        <span className="stock-level">Stock: {alert.current_stock}</span>
                        {alert.alert_level && (
                          <span className="alert-level">Min: {alert.alert_level}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="medicines-section">
              <h3>Medicine Stock Levels</h3>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Medicine</th>
                    <th>SKU</th>
                    <th>Total Stock</th>
                    <th>Batches</th>
                    <th>Min Level</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {medicines.map(medicine => (
                    <tr key={medicine.id}>
                      <td>
                        <strong>{medicine.brand_name}</strong>
                        <br />
                        <small style={{ color: '#666' }}>{medicine.generic_name}</small>
                      </td>
                      <td>{medicine.sku}</td>
                      <td>{medicine.total_stock || 0}</td>
                      <td>{medicine.batches_count || 0}</td>
                      <td>{medicine.min_stock_level}</td>
                      <td>
                        {(medicine.total_stock || 0) === 0 ? (
                          <span className="badge badge-danger">Out of Stock</span>
                        ) : medicine.is_low_stock ? (
                          <span className="badge badge-warning">Low Stock</span>
                        ) : (
                          <span className="badge badge-success">In Stock</span>
                        )}
                      </td>
                      <td>
                        <button
                          onClick={() => openAdjustModal(medicine)}
                          className="btn-small"
                        >
                          Adjust
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {activeTab === 'batches' && (
          <div className="batches-section">
            <div className="section-header">
              <h3>📦 Medicine Batches</h3>
              <button onClick={() => setActiveTab('stock-receiving')} className="btn-primary">
                + Receive New Stock
              </button>
            </div>

            <table className="data-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Batch Number</th>
                  <th>Expiry Date</th>
                  <th>Days to Expiry</th>
                  <th>Quantity</th>
                  <th>Selling Price</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {batches.map(batch => {
                  const expiryStatus = getExpiryStatus(batch.expiry_date);
                  return (
                    <tr key={batch.id} className={expiryStatus.status === 'expired' ? 'expired-row' : ''}>
                      <td>
                        <strong>{batch.medicine_name}</strong>
                        <br />
                        <small style={{ color: '#666' }}>{batch.medicine_generic_name}</small>
                      </td>
                      <td>{batch.batch_number}</td>
                      <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
                      <td>{batch.days_until_expiry}</td>
                      <td>{batch.quantity}</td>
                      <td>KSh {parseFloat(batch.selling_price).toFixed(2)}</td>
                      <td>
                        <span className={`badge ${expiryStatus.class}`}>
                          {expiryStatus.text}
                        </span>
                      </td>
                      <td>
                        <button
                          onClick={() => openBatchAdjustModal(batch)}
                          className="btn-small"
                          disabled={expiryStatus.status === 'expired'}
                        >
                          Adjust
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {batches.length === 0 && (
              <div className="no-data">
                <p>No batches found</p>
                <p style={{ fontSize: '14px', color: '#666' }}>
                  Receive stock to create batches
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'stock-receiving' && (
          <div className="stock-receiving-section">
            <div className="section-header">
              <h3>📥 Receive Stock from Supplier</h3>
              <button onClick={() => setShowReceiveStockModal(true)} className="btn-primary">
                + Receive Stock
              </button>
            </div>

            <div className="receiving-info">
              <div className="info-card">
                <h4>ℹ️ Stock Receiving Process</h4>
                <ul>
                  <li>Select medicine and supplier</li>
                  <li>Enter batch number and expiry date</li>
                  <li>Specify quantity and pricing</li>
                  <li>System creates batch automatically</li>
                  <li>Stock quantity updated</li>
                  <li>Movement recorded for audit</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'suppliers' && (
          <div className="suppliers-section">
            <div className="section-header">
              <h3>Suppliers</h3>
              <button onClick={() => setShowSupplierModal(true)} className="btn-primary">
                + Add Supplier
              </button>
            </div>
            <div className="suppliers-grid">
              {suppliers.map(supplier => (
                <div key={supplier.id} className="supplier-card">
                  <h4>{supplier.name}</h4>
                  {supplier.contact_person && <p>Contact: {supplier.contact_person}</p>}
                  {supplier.email && <p>Email: {supplier.email}</p>}
                  {supplier.phone && <p>Phone: {supplier.phone}</p>}
                  <span className={`badge ${supplier.is_active ? 'badge-success' : 'badge-danger'}`}>
                    {supplier.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'movements' && (
          <div className="movements-section">
            <h3>Stock Movements</h3>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Medicine</th>
                  <th>Batch</th>
                  <th>Type</th>
                  <th>Quantity</th>
                  <th>Previous</th>
                  <th>New</th>
                  <th>User</th>
                  <th>Reference</th>
                </tr>
              </thead>
              <tbody>
                {stockMovements.map(movement => (
                  <tr key={movement.id}>
                    <td>{new Date(movement.created_at).toLocaleString()}</td>
                    <td>{movement.medicine_name}</td>
                    <td>{movement.batch_number || '-'}</td>
                    <td>
                      <span className={`badge badge-${movement.movement_type}`}>
                        {movement.movement_type_display}
                      </span>
                    </td>
                    <td className={movement.quantity > 0 ? 'positive' : 'negative'}>
                      {movement.quantity > 0 ? '+' : ''}{movement.quantity}
                    </td>
                    <td>{movement.previous_quantity}</td>
                    <td>{movement.new_quantity}</td>
                    <td>{movement.user_name}</td>
                    <td>{movement.reference_number || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Stock Adjustment Modal */}
      {showAdjustModal && selectedMedicine && (
        <div className="modal-overlay" onClick={() => setShowAdjustModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Adjust Stock - {selectedMedicine.brand_name}</h3>
              <button onClick={() => setShowAdjustModal(false)} className="close-btn">×</button>
            </div>

            {error && <div className="error-message">{error}</div>}

            <form onSubmit={handleStockAdjustment}>
              <div className="form-group">
                <label>Current Stock: <strong>{selectedMedicine.total_stock || 0}</strong></label>
              </div>

              <div className="form-group">
                <label>Adjustment Type *</label>
                <select
                  value={adjustmentData.adjustment_type}
                  onChange={(e) => setAdjustmentData({...adjustmentData, adjustment_type: e.target.value})}
                  required
                >
                  <option value="add">Add Stock</option>
                  <option value="remove">Remove Stock</option>
                  <option value="set">Set Stock Level</option>
                </select>
              </div>

              <div className="form-group">
                <label>Quantity *</label>
                <input
                  type="number"
                  value={adjustmentData.quantity}
                  onChange={(e) => setAdjustmentData({...adjustmentData, quantity: e.target.value})}
                  required
                  min="0"
                />
              </div>

              <div className="form-group">
                <label>Reason *</label>
                <textarea
                  value={adjustmentData.reason}
                  onChange={(e) => setAdjustmentData({...adjustmentData, reason: e.target.value})}
                  required
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>Reference Number</label>
                <input
                  type="text"
                  value={adjustmentData.reference_number}
                  onChange={(e) => setAdjustmentData({...adjustmentData, reference_number: e.target.value})}
                />
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowAdjustModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Adjust Stock
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Batch Adjustment Modal */}
      {showBatchModal && selectedBatch && (
        <div className="modal-overlay" onClick={() => setShowBatchModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Adjust Batch - {selectedBatch.batch_number}</h3>
              <button onClick={() => setShowBatchModal(false)} className="close-btn">×</button>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="batch-info-display">
              <p><strong>Medicine:</strong> {selectedBatch.medicine_name}</p>
              <p><strong>Current Quantity:</strong> {selectedBatch.quantity}</p>
              <p><strong>Expiry:</strong> {new Date(selectedBatch.expiry_date).toLocaleDateString()}</p>
            </div>

            <form onSubmit={handleBatchAdjustment}>
              <div className="form-group">
                <label>Adjustment Type *</label>
                <select
                  value={batchAdjustData.adjustment_type}
                  onChange={(e) => setBatchAdjustData({...batchAdjustData, adjustment_type: e.target.value})}
                  required
                >
                  <option value="damage">Damage</option>
                  <option value="loss">Loss/Theft</option>
                  <option value="return">Return to Supplier</option>
                  <option value="correction">Stock Correction</option>
                </select>
              </div>

              <div className="form-group">
                <label>Quantity to Adjust *</label>
                <input
                  type="number"
                  value={batchAdjustData.quantity}
                  onChange={(e) => setBatchAdjustData({...batchAdjustData, quantity: e.target.value})}
                  required
                  min="1"
                  max={selectedBatch.quantity}
                />
              </div>

              <div className="form-group">
                <label>Reason *</label>
                <textarea
                  value={batchAdjustData.reason}
                  onChange={(e) => setBatchAdjustData({...batchAdjustData, reason: e.target.value})}
                  required
                  rows="3"
                  placeholder="Explain why this adjustment is needed..."
                />
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowBatchModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Adjust Batch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Supplier Modal */}
      {showSupplierModal && (
        <div className="modal-overlay" onClick={() => setShowSupplierModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Supplier</h3>
              <button onClick={() => setShowSupplierModal(false)} className="close-btn">×</button>
            </div>

            {error && <div className="error-message">{error}</div>}

            <form onSubmit={handleCreateSupplier}>
              <div className="form-group">
                <label>Supplier Name *</label>
                <input
                  type="text"
                  value={supplierData.name}
                  onChange={(e) => setSupplierData({...supplierData, name: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label>Contact Person</label>
                <input
                  type="text"
                  value={supplierData.contact_person}
                  onChange={(e) => setSupplierData({...supplierData, contact_person: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={supplierData.email}
                  onChange={(e) => setSupplierData({...supplierData, email: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Phone</label>
                <input
                  type="tel"
                  value={supplierData.phone}
                  onChange={(e) => setSupplierData({...supplierData, phone: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Address</label>
                <textarea
                  value={supplierData.address}
                  onChange={(e) => setSupplierData({...supplierData, address: e.target.value})}
                  rows="3"
                />
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowSupplierModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Supplier
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Stock Receiving Modal */}
      {showReceiveStockModal && (
        <div className="modal-overlay" onClick={() => setShowReceiveStockModal(false)}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📥 Receive Stock</h3>
              <button onClick={() => setShowReceiveStockModal(false)} className="close-btn">×</button>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="info-banner">
              <p>💡 This will create a new batch and add stock to the selected medicine</p>
            </div>

            <form onSubmit={handleReceiveStock}>
              <div className="form-group">
                <label>Medicine *</label>
                <select
                  value={receiveStockData.medicine_id}
                  onChange={(e) => setReceiveStockData({...receiveStockData, medicine_id: e.target.value})}
                  required
                >
                  <option value="">Select Medicine</option>
                  {medicines.map(med => (
                    <option key={med.id} value={med.id}>
                      {med.brand_name} ({med.generic_name}) - {med.strength}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Batch Number *</label>
                  <input
                    type="text"
                    value={receiveStockData.batch_number}
                    onChange={(e) => setReceiveStockData({...receiveStockData, batch_number: e.target.value})}
                    required
                    placeholder="e.g., BATCH2024001"
                  />
                </div>
                <div className="form-group">
                  <label>Expiry Date *</label>
                  <input
                    type="date"
                    value={receiveStockData.expiry_date}
                    onChange={(e) => setReceiveStockData({...receiveStockData, expiry_date: e.target.value})}
                    required
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Quantity *</label>
                  <input
                    type="number"
                    value={receiveStockData.quantity}
                    onChange={(e) => setReceiveStockData({...receiveStockData, quantity: e.target.value})}
                    required
                    min="1"
                  />
                </div>
                <div className="form-group">
                  <label>Supplier *</label>
                  <select
                    value={receiveStockData.supplier_id}
                    onChange={(e) => setReceiveStockData({...receiveStockData, supplier_id: e.target.value})}
                    required
                  >
                    <option value="">Select Supplier</option>
                    {suppliers.map(sup => (
                      <option key={sup.id} value={sup.id}>{sup.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Purchase Cost (per unit) *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={receiveStockData.purchase_cost}
                    onChange={(e) => setReceiveStockData({...receiveStockData, purchase_cost: e.target.value})}
                    required
                    min="0"
                  />
                </div>
                <div className="form-group">
                  <label>Selling Price (per unit) *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={receiveStockData.selling_price}
                    onChange={(e) => setReceiveStockData({...receiveStockData, selling_price: e.target.value})}
                    required
                    min="0"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Invoice Number</label>
                <input
                  type="text"
                  value={receiveStockData.invoice_number}
                  onChange={(e) => setReceiveStockData({...receiveStockData, invoice_number: e.target.value})}
                  placeholder="Supplier invoice number"
                />
              </div>

              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={receiveStockData.notes}
                  onChange={(e) => setReceiveStockData({...receiveStockData, notes: e.target.value})}
                  rows="3"
                  placeholder="Additional notes about this stock receipt..."
                />
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowReceiveStockModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Receive Stock
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;