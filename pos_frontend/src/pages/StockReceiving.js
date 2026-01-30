import React, { useState, useEffect } from 'react';
import api from '../services/api';
import PageHeader from '../components/PageHeader';
// No separate CSS needed - using inline styles

const StockReceiving = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [receivings, setReceivings] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    supplier_id: '',
    supplier_invoice_number: '',
    invoice_date: '',
    notes: '',
  });
  
  const [items, setItems] = useState([
    {
      medicine_id: '',
      batch_number: '',
      expiry_date: '',
      manufacture_date: '',
      quantity_received: '',
      purchase_price: '',
      selling_price: ''
    }
  ]);
  
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [suppliersRes, medicinesRes, receivingsRes] = await Promise.all([
        api.get('/inventory/suppliers/'),
        api.get('/medicines/'),
        api.get('/stock-receiving/')
      ]);
      
      setSuppliers(suppliersRes.data);
      setMedicines(medicinesRes.data);
      setReceivings(receivingsRes.data);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Error loading data');
    }
  };

  const addItemRow = () => {
    setItems([...items, {
      medicine_id: '',
      batch_number: '',
      expiry_date: '',
      manufacture_date: '',
      quantity_received: '',
      purchase_price: '',
      selling_price: ''
    }]);
  };

  const removeItemRow = (index) => {
    if (items.length === 1) {
      alert('At least one item is required');
      return;
    }
    setItems(items.filter((_, i) => i !== index));
  };

  const updateItem = (index, field, value) => {
    const updated = [...items];
    updated[index][field] = value;
    setItems(updated);
  };

  const calculateTotals = () => {
    const totalCost = items.reduce((sum, item) => {
      const qty = parseFloat(item.quantity_received) || 0;
      const price = parseFloat(item.purchase_price) || 0;
      return sum + (qty * price);
    }, 0);
    
    return {
      totalItems: items.filter(i => i.medicine_id && i.quantity_received).length,
      totalCost: totalCost.toFixed(2)
    };
  };

  const handleSubmit = async () => {
    setError('');
    setLoading(true);

    try {
      // Validate
      const validItems = items.filter(item => 
        item.medicine_id && 
        item.batch_number && 
        item.expiry_date && 
        item.quantity_received && 
        item.purchase_price && 
        item.selling_price
      );

      if (!formData.supplier_id) {
        throw new Error('Please select a supplier');
      }

      if (validItems.length === 0) {
        throw new Error('Please add at least one valid item');
      }

      const payload = {
        supplier_id: parseInt(formData.supplier_id),
        supplier_invoice_number: formData.supplier_invoice_number,
        invoice_date: formData.invoice_date || null,
        notes: formData.notes,
        items: validItems.map(item => ({
          medicine_id: parseInt(item.medicine_id),
          batch_number: item.batch_number,
          expiry_date: item.expiry_date,
          manufacture_date: item.manufacture_date || null,
          quantity_received: parseInt(item.quantity_received),
          purchase_price: parseFloat(item.purchase_price),
          selling_price: parseFloat(item.selling_price)
        }))
      };

      await api.post('/stock-receiving/create/', payload);
      
      alert('Stock received successfully!');
      setShowModal(false);
      resetForm();
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error creating stock receiving');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      supplier_id: '',
      supplier_invoice_number: '',
      invoice_date: '',
      notes: '',
    });
    setItems([{
      medicine_id: '',
      batch_number: '',
      expiry_date: '',
      manufacture_date: '',
      quantity_received: '',
      purchase_price: '',
      selling_price: ''
    }]);
    setError('');
  };

  const totals = calculateTotals();

  return (
    <div style={styles.container}>
      {/* Header */}
      <PageHeader title="📥 Stock Receiving" subtitle="Receive stock from suppliers with batch tracking">
        <button onClick={() => setShowModal(true)} style={styles.btnPrimary}>
          + Receive Stock
        </button>
      </PageHeader>

      {/* Info Banner */}
      <div style={styles.infoBanner}>
        <span style={styles.infoIcon}>ℹ️</span>
        <div>
          <strong>FEFO Stock Management:</strong> Each item received creates a new batch with expiry tracking. 
          Oldest batches are automatically dispensed first.
        </div>
      </div>

      {/* Receivings List */}
      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.tableHeaderRow}>
              <th style={styles.th}>Receiving #</th>
              <th style={styles.th}>Supplier</th>
              <th style={styles.th}>Date</th>
              <th style={styles.th}>Items</th>
              <th style={styles.th}>Total Cost</th>
              <th style={styles.th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {receivings.length === 0 ? (
              <tr>
                <td colSpan="6" style={styles.noData}>
                  No stock receivings yet. Click "Receive Stock" to start.
                </td>
              </tr>
            ) : (
              receivings.map(receiving => (
                <tr key={receiving.id} style={styles.tableRow}>
                  <td style={styles.td}>{receiving.receiving_number}</td>
                  <td style={styles.td}>{receiving.supplier_name}</td>
                  <td style={styles.td}>
                    {new Date(receiving.received_date).toLocaleDateString()}
                  </td>
                  <td style={styles.td}>{receiving.total_items}</td>
                  <td style={styles.td}>KSh {parseFloat(receiving.total_cost).toFixed(2)}</td>
                  <td style={styles.td}>
                    <span style={styles.badgeCompleted}>{receiving.status}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Receiving Modal */}
      {showModal && (
        <div style={styles.modalOverlay} onClick={() => !loading && setShowModal(false)}>
          <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h3 style={styles.modalTitle}>Receive Stock from Supplier</h3>
              <button 
                onClick={() => setShowModal(false)} 
                style={styles.closeBtn}
                disabled={loading}
              >
                ×
              </button>
            </div>

            {error && (
              <div style={styles.errorMessage}>{error}</div>
            )}

            {/* Supplier & Invoice Info */}
            <div style={styles.section}>
              <h4 style={styles.sectionTitle}>Supplier Information</h4>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Supplier *</label>
                  <select
                    value={formData.supplier_id}
                    onChange={(e) => setFormData({...formData, supplier_id: e.target.value})}
                    style={styles.select}
                    disabled={loading}
                  >
                    <option value="">Select Supplier</option>
                    {suppliers.map(supplier => (
                      <option key={supplier.id} value={supplier.id}>
                        {supplier.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Invoice Number</label>
                  <input
                    type="text"
                    value={formData.supplier_invoice_number}
                    onChange={(e) => setFormData({...formData, supplier_invoice_number: e.target.value})}
                    style={styles.input}
                    placeholder="INV-001"
                    disabled={loading}
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Invoice Date</label>
                  <input
                    type="date"
                    value={formData.invoice_date}
                    onChange={(e) => setFormData({...formData, invoice_date: e.target.value})}
                    style={styles.input}
                    disabled={loading}
                  />
                </div>
              </div>
            </div>

            {/* Items */}
            <div style={styles.section}>
              <div style={styles.sectionHeader}>
                <h4 style={styles.sectionTitle}>Items ({totals.totalItems})</h4>
                <button
                  onClick={addItemRow}
                  style={styles.btnAddItem}
                  disabled={loading}
                >
                  + Add Item
                </button>
              </div>

              <div style={styles.itemsContainer}>
                {items.map((item, index) => (
                  <div key={index} style={styles.itemCard}>
                    <div style={styles.itemHeader}>
                      <span style={styles.itemNumber}>Item {index + 1}</span>
                      {items.length > 1 && (
                        <button
                          onClick={() => removeItemRow(index)}
                          style={styles.btnRemove}
                          disabled={loading}
                        >
                          ×
                        </button>
                      )}
                    </div>

                    <div style={styles.itemFields}>
                      {/* Medicine */}
                      <div style={{...styles.formGroup, gridColumn: '1 / -1'}}>
                        <label style={styles.label}>Medicine *</label>
                        <select
                          value={item.medicine_id}
                          onChange={(e) => updateItem(index, 'medicine_id', e.target.value)}
                          style={styles.select}
                          disabled={loading}
                        >
                          <option value="">Select Medicine</option>
                          {medicines.map(med => (
                            <option key={med.id} value={med.id}>
                              {med.b_name} ({med.generic_name}) {med.strength}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Batch Info */}
                      <div style={styles.formGroup}>
                        <label style={styles.label}>Batch Number *</label>
                        <input
                          type="text"
                          value={item.batch_number}
                          onChange={(e) => updateItem(index, 'batch_number', e.target.value)}
                          style={styles.input}
                          placeholder="BATCH001"
                          disabled={loading}
                        />
                      </div>
                      <div style={styles.formGroup}>
                        <label style={styles.label}>Expiry Date *</label>
                        <input
                          type="date"
                          value={item.expiry_date}
                          onChange={(e) => updateItem(index, 'expiry_date', e.target.value)}
                          style={styles.input}
                          min={new Date().toISOString().split('T')[0]}
                          disabled={loading}
                        />
                      </div>
                      <div style={styles.formGroup}>
                        <label style={styles.label}>Mfg Date</label>
                        <input
                          type="date"
                          value={item.manufacture_date}
                          onChange={(e) => updateItem(index, 'manufacture_date', e.target.value)}
                          style={styles.input}
                          max={new Date().toISOString().split('T')[0]}
                          disabled={loading}
                        />
                      </div>

                      {/* Pricing */}
                      <div style={styles.formGroup}>
                        <label style={styles.label}>Quantity *</label>
                        <input
                          type="number"
                          value={item.quantity_received}
                          onChange={(e) => updateItem(index, 'quantity_received', e.target.value)}
                          style={styles.input}
                          min="1"
                          disabled={loading}
                        />
                      </div>
                      <div style={styles.formGroup}>
                        <label style={styles.label}>Purchase Price *</label>
                        <input
                          type="number"
                          step="0.01"
                          value={item.purchase_price}
                          onChange={(e) => updateItem(index, 'purchase_price', e.target.value)}
                          style={styles.input}
                          min="0"
                          disabled={loading}
                        />
                      </div>
                      <div style={styles.formGroup}>
                        <label style={styles.label}>Selling Price *</label>
                        <input
                          type="number"
                          step="0.01"
                          value={item.selling_price}
                          onChange={(e) => updateItem(index, 'selling_price', e.target.value)}
                          style={styles.input}
                          min="0"
                          disabled={loading}
                        />
                      </div>
                    </div>

                    {/* Line Total */}
                    {item.quantity_received && item.purchase_price && (
                      <div style={styles.lineTotal}>
                        Line Total: KSh {(parseFloat(item.quantity_received) * parseFloat(item.purchase_price)).toFixed(2)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div style={styles.formGroup}>
              <label style={styles.label}>Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
                style={styles.textarea}
                rows="3"
                placeholder="Additional notes..."
                disabled={loading}
              />
            </div>

            {/* Totals */}
            <div style={styles.totalsBox}>
              <div style={styles.totalRow}>
                <span>Total Items:</span>
                <strong>{totals.totalItems}</strong>
              </div>
              <div style={{...styles.totalRow, ...styles.grandTotal}}>
                <strong>Total Cost:</strong>
                <strong>KSh {totals.totalCost}</strong>
              </div>
            </div>

            {/* Footer */}
            <div style={styles.modalFooter}>
              <button
                onClick={() => setShowModal(false)}
                style={styles.btnSecondary}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                style={styles.btnPrimary}
                disabled={loading}
              >
                {loading ? 'Processing...' : '✓ Complete Receiving'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Styles object (same as before)
const styles = {
  container: { padding: '20px', backgroundColor: '#F5F1E8', minHeight: '100vh' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' },
  title: { margin: 0, color: '#1B5E4C', fontSize: '24px' },
  subtitle: { margin: '5px 0 0 0', color: '#666', fontSize: '14px' },
  infoBanner: { display: 'flex', alignItems: 'flex-start', gap: '12px', background: '#E7F3FF', border: '1px solid #667eea', borderLeft: '4px solid #667eea', padding: '16px 20px', borderRadius: '8px', marginBottom: '20px', fontSize: '14px', lineHeight: '1.5' },
  infoIcon: { fontSize: '20px', flexShrink: 0 },
  btnPrimary: { background: 'linear-gradient(135deg, #1B5E4C 0%, #0D3D30 100%)', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer', fontSize: '14px', fontWeight: '600' },
  tableContainer: { background: 'white', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', overflow: 'hidden' },
  table: { width: '100%', borderCollapse: 'collapse' },
  tableHeaderRow: { background: 'linear-gradient(135deg, #1B5E4C 0%, #0D3D30 100%)', color: 'white' },
  th: { padding: '15px', textAlign: 'left', fontWeight: '600', fontSize: '14px' },
  tableRow: { borderBottom: '1px solid #eee' },
  td: { padding: '15px', fontSize: '14px' },
  noData: { padding: '60px 20px', textAlign: 'center', color: '#999', fontSize: '16px' },
  badgeCompleted: { display: 'inline-block', padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: '600', background: '#E6F4EA', color: '#1B5E4C', textTransform: 'capitalize' },
  modalOverlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, overflowY: 'auto', padding: '20px' },
  modal: { background: 'white', padding: '30px', borderRadius: '10px', maxWidth: '900px', width: '95%', maxHeight: '90vh', overflowY: 'auto' },
  modalHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', paddingBottom: '15px', borderBottom: '2px solid #eee' },
  modalTitle: { margin: 0, color: '#1B5E4C', fontSize: '20px' },
  closeBtn: { background: 'none', border: 'none', fontSize: '30px', cursor: 'pointer', color: '#999', lineHeight: 1, padding: 0 },
  errorMessage: { background: '#FFF3CD', color: '#856404', padding: '12px 15px', borderRadius: '5px', marginBottom: '20px', border: '1px solid #FFC107', fontSize: '14px' },
  section: { marginBottom: '25px', padding: '20px', background: '#F5F1E8', borderRadius: '8px' },
  sectionHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' },
  sectionTitle: { margin: '0 0 15px 0', color: '#1B5E4C', fontSize: '16px' },
  formRow: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' },
  formGroup: { display: 'flex', flexDirection: 'column' },
  label: { marginBottom: '5px', color: '#0D3D30', fontWeight: '500', fontSize: '14px' },
  input: { padding: '10px 12px', border: '2px solid #1B5E4C40', borderRadius: '5px', fontSize: '14px' },
  select: { padding: '10px 12px', border: '2px solid #1B5E4C40', borderRadius: '5px', fontSize: '14px' },
  textarea: { padding: '10px 12px', border: '2px solid #1B5E4C40', borderRadius: '5px', fontSize: '14px', fontFamily: 'inherit', resize: 'vertical' },
  btnAddItem: { background: '#1B5E4C', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '5px', cursor: 'pointer', fontSize: '14px', fontWeight: '500' },
  itemsContainer: { display: 'flex', flexDirection: 'column', gap: '15px' },
  itemCard: { background: 'white', padding: '15px', borderRadius: '8px', border: '1px solid #E0E0E0' },
  itemHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' },
  itemNumber: { fontWeight: '600', color: '#1B5E4C', fontSize: '14px' },
  btnRemove: { background: '#DC2626', color: 'white', border: 'none', width: '28px', height: '28px', borderRadius: '50%', cursor: 'pointer', fontSize: '20px', lineHeight: 1 },
  itemFields: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' },
  lineTotal: { marginTop: '10px', padding: '8px 12px', background: '#E6F4EA', borderRadius: '5px', textAlign: 'right', fontWeight: '600', color: '#1B5E4C' },
  totalsBox: { background: '#F5F1E8', padding: '20px', borderRadius: '8px', marginTop: '20px' },
  totalRow: { display: 'flex', justifyContent: 'space-between', padding: '8px 0', fontSize: '15px' },
  grandTotal: { borderTop: '2px solid #1B5E4C', marginTop: '10px', paddingTop: '15px', fontSize: '18px', color: '#1B5E4C' },
  modalFooter: { display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #eee' },
  btnSecondary: { background: '#F5F1E8', color: '#0D3D30', border: '2px solid #1B5E4C', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer', fontSize: '14px' },
};

export default StockReceiving;