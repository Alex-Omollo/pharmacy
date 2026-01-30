import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import api from '../services/api';
import PageHeader from '../components/PageHeader';
import './PharmacySales.css';

const PharmacySales = () => {
  const { user } = useSelector((state) => state.auth);
  
  // Search & medicines
  const [searchTerm, setSearchTerm] = useState('');
  const [medicines, setMedicines] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  
  // Cart state
  const [cart, setCart] = useState([]);
  
  // Customer & prescription info
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [hasPrescription, setHasPrescription] = useState(false);
  const [prescriptionNumber, setPrescriptionNumber] = useState('');
  const [prescriberName, setPrescriberName] = useState('');
  
  // Payment
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [amountPaid, setAmountPaid] = useState('');
  const [showCheckout, setShowCheckout] = useState(false);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [warnings, setWarnings] = useState([]);
  
  // Modals
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [selectedMedicine, setSelectedMedicine] = useState(null);
  const [availableBatches, setAvailableBatches] = useState([]);

  // Search medicines
  useEffect(() => {
    if (searchTerm.length >= 2) {
      searchMedicines();
    } else {
      setSearchResults([]);
    }
  }, [searchTerm]);

  const searchMedicines = async () => {
    try {
      const response = await api.get(`/medicines/?search=${searchTerm}`);
      setSearchResults(response.data);
    } catch (err) {
      console.error('Error searching medicines:', err);
    }
  };

  const fetchAvailableBatches = async (medicineId) => {
    try {
      const response = await api.get(`/batches/?medicine=${medicineId}&status=available`);
      return response.data;
    } catch (err) {
      console.error('Error fetching batches:', err);
      return [];
    }
  };

  const handleMedicineSelect = async (medicine) => {
    // Check if requires prescription
    if (medicine.requires_prescription && !hasPrescription) {
      const confirmed = window.confirm(
        `${medicine.b_name} requires a prescription. Have you verified the prescription?`
      );
      if (!confirmed) return;
      setHasPrescription(true);
    }

    // Check if controlled drug
    if (medicine.is_controlled_drug && user?.role === 'cashier') {
      alert('Controlled drugs can only be dispensed by pharmacists or managers');
      return;
    }

    // Check stock availability
    if (medicine.total_stock === 0) {
      alert(`${medicine.b_name} is out of stock!`);
      return;
    }

    // Fetch available batches
    const batches = await fetchAvailableBatches(medicine.id);
    
    if (batches.length === 0) {
      alert(`No available batches for ${medicine.b_name}`);
      return;
    }

    // Check if already in cart
    const existingItem = cart.find(item => item.medicine.id === medicine.id);
    
    if (existingItem) {
      // Increase quantity
      updateQuantity(medicine.id, existingItem.quantity + 1);
    } else {
      // Auto-select first batch (FEFO - already sorted by backend)
      const selectedBatch = batches[0];
      
      // Check for near expiry warning
      let expiryWarning = '';
      if (selectedBatch.days_to_expiry <= 30) {
        expiryWarning = `⚠️ Batch ${selectedBatch.batch_number} expires in ${selectedBatch.days_to_expiry} days`;
      }

      // Add to cart
      setCart([...cart, {
        medicine: medicine,
        batch: selectedBatch,
        quantity: 1,
        discount_percent: 0,
        prescription_verified: medicine.requires_prescription ? hasPrescription : false,
        expiry_warning: expiryWarning
      }]);

      if (expiryWarning) {
        setWarnings([...warnings, expiryWarning]);
      }
    }
    
    setSearchTerm('');
    setSearchResults([]);
  };

  const openBatchSelector = async (medicine) => {
    const batches = await fetchAvailableBatches(medicine.id);
    setAvailableBatches(batches);
    setSelectedMedicine(medicine);
    setShowBatchModal(true);
  };

  const selectBatch = (batch) => {
    // Find item in cart
    const itemIndex = cart.findIndex(item => item.medicine.id === selectedMedicine.id);
    if (itemIndex !== -1) {
      const updatedCart = [...cart];
      updatedCart[itemIndex].batch = batch;
      
      // Update expiry warning
      let expiryWarning = '';
      if (batch.days_to_expiry <= 30) {
        expiryWarning = `⚠️ Batch ${batch.batch_number} expires in ${batch.days_to_expiry} days`;
      }
      updatedCart[itemIndex].expiry_warning = expiryWarning;
      
      setCart(updatedCart);
    }
    
    setShowBatchModal(false);
    setSelectedMedicine(null);
  };

  const updateQuantity = (medicineId, newQuantity) => {
    if (newQuantity === '' || newQuantity === null) {
      setCart(cart.map(item =>
        item.medicine.id === medicineId
          ? { ...item, quantity: '' }
          : item
      ));
      return;
    }

    const qty = parseInt(newQuantity);
    if (isNaN(qty) || qty <= 0) {
      removeFromCart(medicineId);
      return;
    }

    const cartItem = cart.find(item => item.medicine.id === medicineId);
    
    // Check stock availability
    if (qty > cartItem.batch.quantity) {
      alert(`Only ${cartItem.batch.quantity} units available in batch ${cartItem.batch.batch_number}`);
      return;
    }

    setCart(cart.map(item =>
      item.medicine.id === medicineId
        ? { ...item, quantity: qty }
        : item
    ));
  };

  const updateDiscount = (medicineId, discount) => {
    setCart(cart.map(item =>
      item.medicine.id === medicineId
        ? { ...item, discount_percent: parseFloat(discount) || 0 }
        : item
    ));
  };

  const removeFromCart = (medicineId) => {
    setCart(cart.filter(item => item.medicine.id !== medicineId));
  };

  const clearCart = () => {
    setCart([]);
    setCustomerName('');
    setCustomerPhone('');
    setHasPrescription(false);
    setPrescriptionNumber('');
    setPrescriberName('');
    setAmountPaid('');
    setShowCheckout(false);
    setWarnings([]);
  };

  const calculateTotals = () => {
    let subtotal = 0;
    let discountAmount = 0;

    cart.forEach(item => {
      const itemSubtotal = item.batch.selling_price * item.quantity;
      const itemDiscount = itemSubtotal * (item.discount_percent / 100);

      subtotal += itemSubtotal;
      discountAmount += itemDiscount;
    });

    const total = parseFloat((subtotal - discountAmount).toFixed(2));
    const change = parseFloat(amountPaid || 0) - total;

    return { subtotal, discountAmount, total, change };
  };

  const handleCheckout = () => {
    if (cart.length === 0) {
      setError('Cart is empty');
      return;
    }

    // Check if prescription items need prescription
    const prescriptionItems = cart.filter(item => item.medicine.requires_prescription);
    if (prescriptionItems.length > 0 && !hasPrescription) {
      setError('Prescription required for some items. Please verify prescription.');
      return;
    }

    setError('');
    const { total } = calculateTotals();
    setAmountPaid(total.toFixed(2));
    setShowCheckout(true);
  };

  const completeSale = async () => {
    setError('');
    const { total } = calculateTotals();

    // Validate
    if (parseFloat(amountPaid) < total) {
      setError('Amount paid is less than total');
      return;
    }

    // Check for prescription requirements
    const prescriptionItems = cart.filter(item => item.medicine.requires_prescription);
    if (prescriptionItems.length > 0) {
      if (!hasPrescription) {
        setError('Prescription verification required');
        return;
      }
      if (!prescriptionNumber.trim()) {
        const confirm = window.confirm('No prescription number entered. Continue anyway?');
        if (!confirm) return;
      }
    }

    setLoading(true);

    try {
      const saleData = {
        customer_name: customerName.trim(),
        customer_phone: customerPhone.trim(),
        has_prescription: hasPrescription,
        prescription_number: prescriptionNumber.trim(),
        prescriber_name: prescriberName.trim(),
        items: cart.map(item => ({
          medicine_id: item.medicine.id,
          batch_id: item.batch.id,
          quantity: item.quantity,
          discount_percent: item.discount_percent,
          prescription_verified: item.prescription_verified
        })),
        payment_method: paymentMethod,
        amount_paid: parseFloat(amountPaid),
        notes: warnings.join('; ')
      };

      console.log('Sale Data:', saleData);

      const response = await api.post('/sales/create/', saleData);
      
      alert(`Sale completed successfully! Invoice: ${response.data.invoice_number}`);
      
      // Clear and reset
      clearCart();
      
    } catch (err) {
      console.error('Sale error:', err);
      setError(
        err.response?.data?.detail || 
        err.response?.data?.error ||
        Object.values(err.response?.data || {}).flat()[0] ||
        'Error completing sale'
      );
    } finally {
      setLoading(false);
    }
  };

  const totals = calculateTotals();

  return (
    <div className="pharmacy-sales-container">
      <PageHeader title="💊 Pharmacy Dispensing" showDashboardButton={false}>
        <div className="dispenser-info">
          <span>Dispenser: {user?.username}</span>
          <Link to="/dashboard" className="btn-back">
            Dashboard
          </Link>
        </div>
      </PageHeader>

      <div className="sales-content">
        {/* Left Side - Search & Cart */}
        <div className="sales-left">
          {/* Search Section */}
          <div className="search-section">
            <input
              type="text"
              placeholder="Search medicine by brand name, generic name, or SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
              autoFocus
            />
            
            {searchResults.length > 0 && (
              <div className="search-results">
                {searchResults.map(medicine => (
                  <div
                    key={medicine.id}
                    className={`search-result-item ${medicine.total_stock === 0 ? 'out-of-stock' : ''}`}
                    onClick={() => medicine.total_stock > 0 && handleMedicineSelect(medicine)}
                  >
                    <div className="medicine-info">
                      <strong>{medicine.b_name}</strong>
                      <span className="generic-name">{medicine.generic_name}</span>
                      <span className="strength">{medicine.strength} • {medicine.dosage_form}</span>
                      <div className="badges">
                        {medicine.requires_prescription && (
                          <span className="badge badge-prescription">℞ Rx</span>
                        )}
                        {medicine.is_controlled_drug && (
                          <span className="badge badge-controlled">⚠️ Controlled</span>
                        )}
                      </div>
                    </div>
                    <div className="medicine-price">
                      <strong>KSh {parseFloat(medicine.selling_price).toFixed(2)}</strong>
                      <span className={`stock ${medicine.total_stock === 0 ? 'out' : medicine.total_stock <= 10 ? 'low' : ''}`}>
                        {medicine.total_stock === 0 ? 'Out of Stock' : `Stock: ${medicine.total_stock}`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Warnings */}
          {warnings.length > 0 && (
            <div className="warnings-section">
              {warnings.map((warning, index) => (
                <div key={index} className="warning-item">
                  {warning}
                </div>
              ))}
            </div>
          )}

          {/* Cart Section */}
          <div className="cart-section">
            <h3>Cart ({cart.length} items)</h3>
            
            {cart.length === 0 ? (
              <div className="empty-cart">
                <p>Cart is empty</p>
                <p className="hint">Search and add medicines to dispense</p>
              </div>
            ) : (
              <div className="cart-items">
                {cart.map(item => {
                  const itemSubtotal = item.batch.selling_price * item.quantity;
                  const itemDiscount = itemSubtotal * (item.discount_percent / 100);
                  const itemTotal = itemSubtotal - itemDiscount;

                  return (
                    <div key={item.medicine.id} className="cart-item">
                      <div className="item-header">
                        <div>
                          <strong>{item.medicine.b_name}</strong>
                          <span className="generic-text">({item.medicine.generic_name})</span>
                        </div>
                        <button
                          onClick={() => removeFromCart(item.medicine.id)}
                          className="btn-remove"
                        >
                          ×
                        </button>
                      </div>

                      {item.expiry_warning && (
                        <div className="expiry-warning">
                          {item.expiry_warning}
                        </div>
                      )}

                      <div className="item-details">
                        <div className="item-row">
                          <span>Batch:</span>
                          <div className="batch-selector">
                            <span>{item.batch.batch_number}</span>
                            <button
                              onClick={() => openBatchSelector(item.medicine)}
                              className="btn-change-batch"
                              title="Change batch"
                            >
                              🔄
                            </button>
                          </div>
                        </div>

                        <div className="item-row">
                          <span>Expiry:</span>
                          <span>{new Date(item.batch.expiry_date).toLocaleDateString()}</span>
                        </div>

                        <div className="item-row">
                          <span>Price:</span>
                          <span>KSh {parseFloat(item.batch.selling_price).toFixed(2)}</span>
                        </div>

                        <div className="item-row">
                          <span>Available:</span>
                          <span className={item.batch.quantity <= 10 ? 'low-stock-text' : ''}>
                            {item.batch.quantity}
                          </span>
                        </div>

                        <div className="item-row">
                          <span>Quantity:</span>
                          <div className="quantity-controls">
                            <button onClick={() => updateQuantity(item.medicine.id, item.quantity - 1)}>
                              -
                            </button>
                            <input
                              type="text"
                              value={item.quantity}
                              onChange={(e) => updateQuantity(item.medicine.id, e.target.value)}
                              onBlur={(e) => {
                                if (e.target.value === '' || parseInt(e.target.value) <= 0) {
                                  updateQuantity(item.medicine.id, 1);
                                }
                              }}
                              min="1"
                              max={item.batch.quantity}
                            />
                            <button
                              onClick={() => updateQuantity(item.medicine.id, item.quantity + 1)}
                              disabled={item.quantity >= item.batch.quantity}
                            >
                              +
                            </button>
                          </div>
                        </div>

                        <div className="item-row">
                          <span>Discount (%):</span>
                          <input
                            type="number"
                            value={item.discount_percent}
                            onChange={(e) => updateDiscount(item.medicine.id, e.target.value)}
                            min="0"
                            max="100"
                            step="0.1"
                            className="discount-input"
                          />
                        </div>

                        <div className="item-row total">
                          <strong>Subtotal:</strong>
                          <strong>KSh {itemTotal.toFixed(2)}</strong>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Side - Summary & Checkout */}
        <div className="sales-right">
          <div className="summary-section">
            <h3>Order Summary</h3>
            
            <div className="summary-row">
              <span>Subtotal:</span>
              <span>KSh {totals.subtotal.toFixed(2)}</span>
            </div>
            
            <div className="summary-row">
              <span>Discount:</span>
              <span className="negative">-KSh {totals.discountAmount.toFixed(2)}</span>
            </div>
            
            <div className="summary-row total">
              <strong>Total:</strong>
              <strong className="total-amount">KSh {totals.total.toFixed(2)}</strong>
            </div>
          </div>

          {!showCheckout ? (
            <div className="actions-section">
              <button
                onClick={clearCart}
                className="btn-secondary"
                disabled={cart.length === 0}
              >
                Clear Cart
              </button>
              <button
                onClick={handleCheckout}
                className="btn-checkout"
                disabled={cart.length === 0}
              >
                Checkout
              </button>
            </div>
          ) : (
            <div className="checkout-section">
              <h3>Checkout</h3>
              
              {error && <div className="error-message">{error}</div>}

              {/* Prescription Info (if needed) */}
              {cart.some(item => item.medicine.requires_prescription) && (
                <div className="prescription-section">
                  <h4>℞ Prescription Required</h4>
                  
                  <div className="form-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={hasPrescription}
                        onChange={(e) => setHasPrescription(e.target.checked)}
                      />
                      Prescription Verified
                    </label>
                  </div>

                  {hasPrescription && (
                    <>
                      <div className="form-group">
                        <label>Prescription Number</label>
                        <input
                          type="text"
                          value={prescriptionNumber}
                          onChange={(e) => setPrescriptionNumber(e.target.value)}
                          placeholder="RX-12345"
                        />
                      </div>

                      <div className="form-group">
                        <label>Prescriber Name</label>
                        <input
                          type="text"
                          value={prescriberName}
                          onChange={(e) => setPrescriberName(e.target.value)}
                          placeholder="Dr. Name"
                        />
                      </div>
                    </>
                  )}
                </div>
              )}
              
              <div className="form-group">
                <label>Customer Name</label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Customer name"
                />
              </div>

              <div className="form-group">
                <label>Customer Phone</label>
                <input
                  type="tel"
                  value={customerPhone}
                  onChange={(e) => setCustomerPhone(e.target.value)}
                  placeholder="+254 700 000000"
                />
              </div>
              
              <div className="form-group">
                <label>Payment Method</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                >
                  <option value="cash">Cash</option>
                  <option value="mobile">M-Pesa</option>
                  <option value="card">Card</option>
                  <option value="insurance">Insurance</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Amount Paid *</label>
                <input
                  type="number"
                  step="0.01"
                  value={amountPaid}
                  onChange={(e) => setAmountPaid(e.target.value)}
                  placeholder="0.00"
                  required
                />
              </div>
              
              {amountPaid && parseFloat(amountPaid) >= totals.total && (
                <div className="change-display">
                  <span>Change:</span>
                  <span className="change-amount">KSh {totals.change.toFixed(2)}</span>
                </div>
              )}
              
              <div className="checkout-actions">
                <button
                  onClick={() => setShowCheckout(false)}
                  className="btn-secondary"
                  disabled={loading}
                >
                  Back
                </button>
                <button
                  onClick={completeSale}
                  className="btn-complete"
                  disabled={
                    loading ||
                    !amountPaid ||
                    parseFloat(amountPaid) < totals.total ||
                    (cart.some(item => item.medicine.requires_prescription) && !hasPrescription)
                  }
                >
                  {loading ? 'Processing...' : '✓ Complete Sale'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Batch Selection Modal */}
      {showBatchModal && selectedMedicine && (
        <div className="modal-overlay" onClick={() => setShowBatchModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Select Batch - {selectedMedicine.b_name}</h3>
              <button onClick={() => setShowBatchModal(false)} className="close-btn">
                ×
              </button>
            </div>

            <div className="batches-list">
              {availableBatches.map(batch => (
                <div
                  key={batch.id}
                  className={`batch-item ${batch.days_to_expiry <= 30 ? 'near-expiry' : ''}`}
                  onClick={() => selectBatch(batch)}
                >
                  <div className="batch-info">
                    <strong>Batch: {batch.batch_number}</strong>
                    <span>Expiry: {new Date(batch.expiry_date).toLocaleDateString()}</span>
                    <span className={batch.days_to_expiry <= 30 ? 'expiry-warning' : ''}>
                      {batch.days_to_expiry} days until expiry
                    </span>
                  </div>
                  <div className="batch-stock">
                    <strong>KSh {parseFloat(batch.selling_price).toFixed(2)}</strong>
                    <span>Available: {batch.quantity}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PharmacySales;