import React, { useState, useEffect } from 'react';
import './PurchaseOrderForm.css';

const PurchaseOrderForm = ({ api, onClose, onSuccess }) => {
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [formData, setFormData] = useState({
    supplier_id: '',
    expected_delivery_date: '',
    notes: '',
  });
  const [items, setItems] = useState([
    { product_id: '', quantity: '', unit_cost: '' }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchTerms, setSearchTerms] = useState(['']);

  useEffect(() => {
    fetchSuppliers();
    fetchProducts();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const response = await api.get('/inventory/suppliers/');
      setSuppliers(response.data.filter(s => s.is_active));
    } catch (err) {
      console.error('Error fetching suppliers:', err);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await api.get('/products/?exclude_children=true');
      // Filter for active products only
      setProducts(response.data.filter(p => p.is_active));
    } catch (err) {
      console.error('Error fetching products:', err);
    }
  };

  const addItemRow = () => {
    setItems([...items, { product_id: '', quantity: '', unit_cost: '' }]);
    setSearchTerms([...searchTerms, '']);
  };

  const removeItemRow = (index) => {
    if (items.length === 1) {
      alert('At least one item is required');
      return;
    }
    setItems(items.filter((_, i) => i !== index));
    setSearchTerms(searchTerms.filter((_, i) => i !== index));
  };

  const updateItem = (index, field, value) => {
    const updated = [...items];
    updated[index][field] = value;
    setItems(updated);
  };

  const updateSearchTerm = (index, value) => {
    const updated = [...searchTerms];
    updated[index] = value;
    setSearchTerms(updated);
  };

  const selectProduct = (index, product) => {
    const updated = [...items];
    updated[index].product_id = product.id;
    updated[index].unit_cost = product.cost_price || product.price;
    setItems(updated);
    
    // Clear search term
    const updatedSearchTerms = [...searchTerms];
    updatedSearchTerms[index] = '';
    setSearchTerms(updatedSearchTerms);
  };

  const getFilteredProducts = (index) => {
    const searchTerm = searchTerms[index].toLowerCase();
    if (!searchTerm) return [];
    
    return products
      .filter(p => 
        p.name.toLowerCase().includes(searchTerm) ||
        p.sku.toLowerCase().includes(searchTerm)
      )
      .slice(0, 10);
  };

  const getProductById = (productId) => {
    return products.find(p => p.id === productId);
  };

  const calculateSubtotal = (item) => {
    const quantity = parseFloat(item.quantity) || 0;
    const cost = parseFloat(item.unit_cost) || 0;
    return quantity * cost;
  };

  const calculateTotals = () => {
    const subtotal = items.reduce((sum, item) => sum + calculateSubtotal(item), 0);
    const tax = subtotal * 0.00; // 16% tax
    const total = subtotal + tax;
    
    return {
      subtotal: subtotal.toFixed(2),
      tax: tax.toFixed(2),
      total: total.toFixed(2)
    };
  };

  const validateForm = () => {
    if (!formData.supplier_id) {
      setError('Please select a supplier');
      return false;
    }

    const validItems = items.filter(item => 
      item.product_id && item.quantity && item.unit_cost
    );

    if (validItems.length === 0) {
      setError('Please add at least one valid item');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Filter out incomplete items
      const validItems = items.filter(item => 
        item.product_id && item.quantity && item.unit_cost
      );

      const poData = {
        supplier_id: parseInt(formData.supplier_id),
        expected_delivery_date: formData.expected_delivery_date || null,
        notes: formData.notes,
        items: validItems.map(item => ({
          product_id: parseInt(item.product_id),
          quantity: parseInt(item.quantity),
          unit_cost: parseFloat(item.unit_cost)
        }))
      };

      await api.post('/inventory/purchase-orders/create/', poData);
      
      alert('Purchase Order created successfully!');
      onSuccess();
      onClose();
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        err.response?.data?.error ||
        'Error creating purchase order'
      );
    } finally {
      setLoading(false);
    }
  };

  const totals = calculateTotals();

  return (
    <div className="po-form-container">
      <div className="po-form-header">
        <h3>Create Purchase Order</h3>
        <button onClick={onClose} className="po-close-btn" disabled={loading}>
          ×
        </button>
      </div>

      {error && (
        <div className="po-error-message">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Supplier and Date Section */}
        <div className="po-form-section">
          <div className="po-form-row">
            <div className="po-form-group">
              <label>Supplier *</label>
              <select
                value={formData.supplier_id}
                onChange={(e) => setFormData({...formData, supplier_id: e.target.value})}
                required
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

            <div className="po-form-group">
              <label>Expected Delivery Date</label>
              <input
                type="date"
                value={formData.expected_delivery_date}
                onChange={(e) => setFormData({...formData, expected_delivery_date: e.target.value})}
                disabled={loading}
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
          </div>
        </div>

        {/* Items Section */}
        <div className="po-form-section">
          <div className="po-section-header">
            <h4>Order Items</h4>
            <button
              type="button"
              onClick={addItemRow}
              className="po-btn-add-item"
              disabled={loading}
            >
              + Add Item
            </button>
          </div>

          <div className="po-items-container">
            {items.map((item, index) => {
              const selectedProduct = getProductById(item.product_id);
              const filteredProducts = getFilteredProducts(index);
              
              return (
                <div key={index} className="po-item-row">
                  <div className="po-item-header">
                    <span className="po-item-number">Item {index + 1}</span>
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeItemRow(index)}
                        className="po-btn-remove-item"
                        disabled={loading}
                      >
                        ×
                      </button>
                    )}
                  </div>

                  <div className="po-item-fields">
                    {/* Product Search/Select */}
                    <div className="po-form-group po-product-search">
                      <label>Product *</label>
                      {selectedProduct ? (
                        <div className="po-selected-product">
                          <div className="po-selected-product-info">
                            <strong>{selectedProduct.name}</strong>
                            <span className="po-product-sku">SKU: {selectedProduct.sku}</span>
                            {selectedProduct.product_type !== 'simple' && (
                              <span className="po-product-type-badge">
                                {selectedProduct.product_type}
                              </span>
                            )}
                          </div>
                          <button
                            type="button"
                            onClick={() => updateItem(index, 'product_id', '')}
                            className="po-btn-clear-product"
                            disabled={loading}
                          >
                            Change
                          </button>
                        </div>
                      ) : (
                        <div className="po-product-search-input">
                          <input
                            type="text"
                            placeholder="Search product..."
                            value={searchTerms[index]}
                            onChange={(e) => updateSearchTerm(index, e.target.value)}
                            disabled={loading}
                          />
                          {searchTerms[index] && filteredProducts.length > 0 && (
                            <div className="po-product-dropdown">
                              {filteredProducts.map(product => (
                                <div
                                  key={product.id}
                                  className="po-product-option"
                                  onClick={() => selectProduct(index, product)}
                                >
                                  <div>
                                    <strong>{product.name}</strong>
                                    <span className="po-product-sku-small">
                                      {product.sku}
                                    </span>
                                  </div>
                                  <div className="po-product-price">
                                    ksh {parseFloat(product.cost_price || product.price).toFixed(2)}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Quantity */}
                    <div className="po-form-group">
                      <label>Quantity *</label>
                      <input
                        type="text"
                        min="1"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                        placeholder="0"
                        required
                        disabled={loading}
                      />
                    </div>

                    {/* Unit Cost */}
                    <div className="po-form-group">
                      <label>Unit Cost *</label>
                      <input
                        type="text"
                        // step="0.01"
                        min="0"
                        value={item.unit_cost}
                        onChange={(e) => updateItem(index, 'unit_cost', e.target.value)}
                        placeholder="0.00"
                        required
                        disabled={loading}
                      />
                    </div>

                    {/* Subtotal */}
                    <div className="po-form-group">
                      <label>Subtotal</label>
                      <div className="po-subtotal-display">
                        ksh {calculateSubtotal(item).toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Notes Section */}
        <div className="po-form-section">
          <div className="po-form-group">
            <label>Notes</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              rows="3"
              placeholder="Additional notes or instructions..."
              disabled={loading}
            />
          </div>
        </div>

        {/* Totals Section */}
        <div className="po-totals-section">
          <div className="po-totals-row">
            <span>Subtotal:</span>
            <span>ksh {totals.subtotal}</span>
          </div>
          {/* <div className="po-totals-row">
            <span>Tax (16%):</span>
            <span>ksh {totals.tax}</span>
          </div> */}
          <div className="po-totals-row po-totals-grand">
            <strong>Total:</strong>
            <strong>ksh {totals.total}</strong>
          </div>
        </div>

        {/* Footer Buttons */}
        <div className="po-form-footer">
          <button
            type="button"
            onClick={onClose}
            className="po-btn-cancel"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="po-btn-submit"
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Purchase Order'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PurchaseOrderForm;