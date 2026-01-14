import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import api from '../services/api';
// import QZTrayReceipt from '../components/QZTrayReceipt';
import PageHeader from '../components/PageHeader';
import './Sales.css';

const Sales = () => {
  const { user } = useSelector((state) => state.auth);
  
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [amountPaid, setAmountPaid] = useState('');
  const [showCheckout, setShowCheckout] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stockError, setStockError] = useState('');
  
  // Receipt state
  const [showReceipt, setShowReceipt] = useState(false);
  const [completedSale, setCompletedSale] = useState(null);

  // Prescription tracking
  const [prescriptionSeen, setPrescriptionSeen] = useState(false);
  const [prescriptionNumber, setPrescriptionNumber] = useState('');

  useEffect(() => {
    if (searchTerm.length >= 2) {
      searchProducts();
    } else {
      setProducts([]);
    }
    // eslint-disable-next-line
  }, [searchTerm]);

  const searchProducts = async () => {
    try {
      const response = await api.get(`/products/search/?q=${searchTerm}`);
      setProducts(response.data.results);
    } catch (err) {
      console.error('Error searching products:', err);
    }
  };

  const addToCart = (medicine) => {
    // Check if medicine requires prescription
    if (medicine.is_prescription && !prescriptionSeen) {
      const confirmed = window.confirm(
        `${medicine.brand_name} requires a prescription. Have you seen the prescription?`
      );
      if (!confirmed) return;
      setPrescriptionSeen(true);
    }

    // Check if controlled drug and user authorized
    if (medicine.is_controlled && user?.role === 'cashier') {
      alert('Controlled drugs can only be dispensed by pharmacists or managers');
      return;
    }

    // Existing stock check logic
    if (medicine.total_stock === 0) {
      setStockError(`${medicine.brand_name} is out of stock!`);
      setTimeout(() => setStockError(''), 3000);
      return;
    }

    // Add to cart with FEFO batch selection
    const existingItem = cart.find(item => item.medicine.id === medicine.id);
    
    if (existingItem) {
      setCart(cart.map(item =>
        item.medicine.id === medicine.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, {
        medicine,
        quantity: 1,
        discount_percent: 0,
        batch_id: null, // Will be selected by backend using FEFO
        prescription_seen: medicine.is_prescription ? prescriptionSeen : null,
        prescription_number: prescriptionNumber || null
      }]);
    }
    
    setSearchTerm('');
    setProducts([]);
    setStockError('');
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity === '' || newQuantity === null || newQuantity === undefined) {
      setCart(cart.map(item =>
        item.product.id === productId
        ? {...item, quantity: '' }
        : item
      ));
      return;
    }

    // Convert to number
    const qty = parseInt(newQuantity);

    // Check if it's a valid number
    if (isNaN(qty)) {
      return; // Ignore invalid input
    }

    // Remove item if quantity is 0 or negative
    if (qty <= 0) {
      removeFromCart(productId);
      return;
    }

    const cartItem = cart.find(item => item.product.id === productId);

    // Check if new quantity exceeds available stock
    if (qty > cartItem.product.stock_quantity) {
      setStockError(`Only ${cartItem.product.stock_quantity} units of ${cartItem.product.name} available in stock.`);
      setTimeout(() => setStockError(''), 3000);
      return;
    }

    setCart(cart.map(item => 
      item.product.id === productId
      ? {...item, quantity: qty}
      : item
    ));
    setStockError('');

    // const cartItem = cart.find(item => item.product.id === productId);
    
    // Check if new quantity exceeds available stock
    // if (newQuantity > cartItem.product.stock_quantity) {
    //   setStockError(`Only ${cartItem.product.stock_quantity} units of ${cartItem.product.name} available in stock.`);
    //   setTimeout(() => setStockError(''), 3000);
    //   return;
    // }
    
    // setCart(cart.map(item =>
    //   item.product.id === productId
    //     ? { ...item, quantity: newQuantity }
    //     : item
    // ));
    // setStockError('');
  };

  const updateDiscount = (productId, discount) => {
    setCart(cart.map(item =>
      item.product.id === productId
        ? { ...item, discount_percent: parseFloat(discount) || 0 }
        : item
    ));
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product.id !== productId));
    setStockError('');
  };

  const clearCart = () => {
    setCart([]);
    setCustomerName('');
    setAmountPaid('');
    setShowCheckout(false);
    setStockError('');
  };

  const calculateTotals = () => {
    let subtotal = 0;
    let taxAmount = 0;
    let discountAmount = 0;

    cart.forEach(item => {
      const itemSubtotal = item.product.price * item.quantity;
      const itemDiscount = itemSubtotal * (item.discount_percent / 100);
      const taxRate = parseFloat(item.product.tax_rate) || 0;
      const itemTax = (itemSubtotal - itemDiscount) * (taxRate / 100);

      subtotal += itemSubtotal;
      discountAmount += itemDiscount;
      taxAmount += itemTax;
    });

    const total = parseFloat((subtotal - discountAmount + taxAmount).toFixed(2));
    const change = parseFloat(amountPaid || 0) - total;

    return { subtotal, taxAmount, discountAmount, total, change };
  };

  // Check if any items in cart exceed available stock
  const hasStockIssues = () => {
    return cart.some(item => item.quantity > item.product.stock_quantity);
  };

  // Check if any items are out of stock
  const hasOutOfStockItems = () => {
    return cart.some(item => item.product.stock_quantity === 0);
  };

  const getStockIssueMessage = () => {
    const issues = cart
      .filter(item => item.quantity > item.product.stock_quantity || item.product.stock_quantity === 0)
      .map(item => {
        if (item.product.stock_quantity === 0) {
          return `${item.product.name} is out of stock`;
        }
        return `${item.product.name}: only ${item.product.stock_quantity} available`;
      });
    
    return issues.join(', ');
  };

  const handleCheckout = () => {
    if (cart.length === 0) {
      setError('Cart is empty');
      return;
    }

    // Check for stock issues before proceeding to checkout
    if (hasStockIssues() || hasOutOfStockItems()) {
      setError(`Cannot proceed to checkout: ${getStockIssueMessage()}`);
      return;
    }

    setError('');
    
    // 🎯 AUTO-POPULATE: Set amount paid to the total automatically
    const { total } = calculateTotals();
    setAmountPaid(total.toFixed(2));
    
    setShowCheckout(true);
  };

  const completeSale = async () => {
    setError('');
    const { total } = calculateTotals();

    // Validate customer name for M-pesa
    if (paymentMethod === 'mobile' && !customerName.trim()) {
      setError('Customer name is required for M-Pesa payments');
      return;
    }

    // Final stock validation before completing sale
    if (hasStockIssues() || hasOutOfStockItems()) {
      setError(`Cannot complete sale: ${getStockIssueMessage()}`);
      return;
    }

    if (parseFloat(amountPaid) < total) {
      setError('Amount paid is less than total');
      return;
    }

    setLoading(true);

    try {
      const saleData = {
        customer_name: customerName,
        items: cart.map(item => ({
          medicine_id: item.medicine.id,
          quantity: item.quantity,
          discount_percent: item.discount_percent,
          prescription_seen: item.prescription_seen,
          prescription_number: item.prescription_number
        })),
        payment_method: paymentMethod,
        amount_paid: parseFloat(amountPaid),
        notes: '',
        dispenser_id: user.id
      };
      
      console.log("Sale Data Sent:", saleData);

      const response = await api.post('/sales/dispense/', saleData);
      
      // Show thermal receipt with auto-print
      setCompletedSale(response.data);
      setShowReceipt(true);
      
      // Clear cart
      clearCart();
      
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.items?.[0] || 'Error completing sale');
    } finally {
      setLoading(false);
    }
  };

  const handleCloseReceipt = () => {
    setShowReceipt(false);
    setCompletedSale(null);
  };

  const totals = calculateTotals();

  return (
    <div className="sales-container">
      <div className='sales-header'>
        <PageHeader title="💰 Point of Sale" showDashboardButton={false}>
          <div className='cashier-info'>
            <span>Cashier: {user?.username}</span>
            <Link to="/dashboard" className='btn-back'>
              Dashboard
            </Link>
          </div>
        </PageHeader>
      </div>

      <div className="sales-content">
        {/* Left Side - Product Search & Cart */}
        <div className="sales-left">
          <div className="search-section">
            <input
              type="text"
              placeholder="Search products by name, SKU, or barcode..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
              autoFocus
            />
            
            {products.length > 0 && (
              <div className="search-results">
                {products.map(product => (
                  <div
                    key={product.id}
                    className={`search-result-item ${product.stock_quantity === 0 ? 'out-of-stock' : ''}`}
                    onClick={() => addToCart(product)}
                  >
                    <div className="product-info">
                      <strong>{product.name}</strong>
                      <span className="sku">SKU: {product.sku}</span>
                    </div>
                    <div className="product-price">
                      ksh {parseFloat(product.price).toFixed(2)}
                      <span className={`stock ${product.stock_quantity === 0 ? 'out' : product.stock_quantity <= 10 ? 'low' : ''}`}>
                        {product.stock_quantity === 0 ? 'Out of Stock' : `Stock: ${product.stock_quantity}`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {stockError && (
            <div className="stock-error-message">
              ⚠️ {stockError}
            </div>
          )}

          <div className="cart-section">
            <h3>Cart ({cart.length} items)</h3>
            
            {cart.length === 0 ? (
              <div className="empty-cart">
                <p>Cart is empty</p>
                <p className="hint">Search and add products to start a sale</p>
              </div>
            ) : (
              <div className="cart-items">
                {cart.map(item => {
                  const itemSubtotal = item.product.price * item.quantity;
                  const itemDiscount = itemSubtotal * (item.discount_percent / 100);
                  const itemTotal = itemSubtotal - itemDiscount;
                  const isOverStock = item.quantity > item.product.stock_quantity;
                  const isOutOfStock = item.product.stock_quantity === 0;

                  return (
                    <div key={item.product.id} className={`cart-item ${isOverStock || isOutOfStock ? 'stock-issue' : ''}`}>
                      <div className="item-header">
                        <strong>{item.product.name}</strong>
                        <button
                          onClick={() => removeFromCart(item.product.id)}
                          className="btn-remove"
                        >
                          ×
                        </button>
                      </div>
                      
                      {(isOverStock || isOutOfStock) && (
                        <div className="stock-warning">
                          ⚠️ {isOutOfStock ? 'Out of stock!' : `Only ${item.product.stock_quantity} available`}
                        </div>
                      )}
                      
                      <div className="item-details">
                        <div className="item-row">
                          <span>Price:</span>
                          <span>ksh {parseFloat(item.product.price).toFixed(2)}</span>
                        </div>
                        
                        <div className="item-row">
                          <span>Available Stock:</span>
                          <span className={item.product.stock_quantity <= 10 ? 'low-stock-text' : ''}>
                            {item.product.stock_quantity}
                          </span>
                        </div>
                        
                        <div className="item-row">
                          <span>Quantity:</span>
                          <div className="quantity-controls">
                            <button onClick={() => updateQuantity(item.product.id, item.quantity - 1)}>
                              -
                            </button>
                            <input
                              type="text"
                              value={item.quantity}
                              onChange={(e) => updateQuantity(item.product.id, e.target.value)}
                              onBlur={(e) => {
                                if (e.target.value === '' || parseInt(e.target.value) <= 0) {
                                  updateQuantity(item.product.id, 1);
                                }
                              }}
                              min="1"
                              max={item.product.stock_quantity}
                            />
                            <button 
                              onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                              disabled={item.quantity >= item.product.stock_quantity}
                            >
                              +
                            </button>
                          </div>
                        </div>
                        
                        <div className="item-row">
                          <span>Discount (%):</span>
                          <input
                            type="text"
                            value={item.discount_percent}
                            onChange={(e) => updateDiscount(item.product.id, e.target.value)}
                            min="0"
                            max="100"
                            step="0.1"
                            className="discount-input"
                          />
                        </div>
                        
                        <div className="item-row total">
                          <strong>Subtotal:</strong>
                          <strong>ksh {itemTotal.toFixed(2)}</strong>
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
              <span>ksh {totals.subtotal.toFixed(2)}</span>
            </div>
            
            <div className="summary-row">
              <span>Discount:</span>
              <span className="negative">-ksh {totals.discountAmount.toFixed(2)}</span>
            </div>
            
            <div className="summary-row">
              <span>Tax:</span>
              <span>+ksh {totals.taxAmount.toFixed(2)}</span>
            </div>
            
            <div className="summary-row total">
              <strong>Total:</strong>
              <strong className="total-amount">ksh {totals.total.toFixed(2)}</strong>
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
                disabled={cart.length === 0 || hasStockIssues() || hasOutOfStockItems()}
                title={hasStockIssues() || hasOutOfStockItems() ? getStockIssueMessage() : ''}
              >
                Checkout
              </button>
            </div>
          ) : (
            <div className="checkout-section">
              <h3>Payment Details</h3>
              
              {error && <div className="error-message">{error}</div>}
              
              <div className="form-group">
                <label>
                  Customer Name {paymentMethod === 'mobile' && <span style={{ color: '#DC2626'}}>*</span>}
                  {paymentMethod === 'mobile' && (
                    <span style={{fontsize: '12px', color: '#DC2626', marginLeft: '8px'}}>
                      (Required for M-Pesa)
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder={paymentMethod === 'mobile' ? 'Required for M-Pesa' : "Enter customer name"}
                  required={paymentMethod === 'mobile'}
                  style={paymentMethod === 'mobile' && !customerName.trim() ? {
                    borderColor: '#DC2626',
                    borderWidth: '2px'
                  } : {}}
                />
                {paymentMethod === 'mobile' && !customerName.trim() && (
                  <small style={{color: '#DC2626', fontSize: '12px', marginTop: '5px', display: 'block'}}>
                    Please enter customer name for M-Pesa transactions
                  </small>
                )}
              </div>
              
              <div className="form-group">
                <label>Payment Method</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                >
                  <option value="cash">Cash</option>
                  <option value="mobile">M-Pesa</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Amount Paid *</label>
                <input
                  type="text"
                  step="0.01"
                  value={amountPaid}
                  onChange={(e) => setAmountPaid(e.target.value)}
                  placeholder="0.00"
                  required
                />
                <small style={{ color: '#666', fontSize: '12px', marginTop: '5px', display: 'block' }}>
                  💡 Pre-filled with total amount. Adjust if customer pays different amount.
                </small>
              </div>
              
              {amountPaid && parseFloat(amountPaid) >= totals.total && (
                <div className="change-display">
                  <span>Change:</span>
                  <span className="change-amount">ksh {totals.change.toFixed(2)}</span>
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
                    hasStockIssues() || 
                    hasOutOfStockItems() ||
                    (paymentMethod === 'mobile' && !customerName.trim())
                  }
                >
                  {loading ? 'Processing...' : '🖨️ Complete & Print'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Thermal Receipt Modal */}
      {/*{showReceipt && completedSale && (
        <QZTrayReceipt 
          saleData={completedSale}
          onClose={handleCloseReceipt}
          autoPrint={true}
        />
      )}*/}
    </div>
  );
};

export default Sales;