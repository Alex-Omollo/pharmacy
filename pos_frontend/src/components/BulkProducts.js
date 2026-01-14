import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import './BulkProducts.css';

const BulkProducts = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedParent, setSelectedParent] = useState(null);
  const [showCreateParent, setShowCreateParent] = useState(false);
  const [showCreateChildren, setShowCreateChildren] = useState(false);
  const [showStockInfo, setShowStockInfo] = useState(false);
  const [stockInfo, setStockInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Parent product form
  const [parentForm, setParentForm] = useState({
    name: '',
    category: '',
    base_unit: 'l',
    unit_quantity: '',
    price: '',
    cost_price: '',
    stock_quantity: '',
    min_stock_level: '10'
  });
  
  // Child products form - name will be auto-generated
  const [childrenForm, setChildrenForm] = useState([
    { unit_quantity: '', price: '', cost_price: '' }
  ]);

  useEffect(() => {
    fetchParentProducts();
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories/');
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchParentProducts = async () => {
    try {
      const response = await api.get('/products/');
      const parentProducts = response.data.filter(p => p.product_type === 'parent');
      setProducts(parentProducts);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const createParentProduct = async () => {
    setLoading(true);
    try {
      await api.post('/products/bulk/create-parent/', {
        ...parentForm,
        product_type: 'parent',
        sku: `${parentForm.name.substring(0, 3).toUpperCase()}-${Date.now().toString().slice(-4)}`
      });
      
      alert('Parent product created successfully!');
      setShowCreateParent(false);
      setParentForm({
        name: '',
        category: '',
        base_unit: 'l',
        unit_quantity: '',
        price: '',
        cost_price: '',
        stock_quantity: '',
        min_stock_level: '10'
      });
      fetchParentProducts();
    } catch (error) {
      alert('Error creating parent product: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const createChildProducts = async () => {
    if (!selectedParent) {
      alert('Please select a parent product first');
      return;
    }

    // Filter to only include children with unit_quantity and price
    const validChildren = childrenForm.filter(c => c.unit_quantity && c.price);
    
    if (validChildren.length === 0) {
      alert('Please fill in at least unit quantity and price for one child product');
      return;
    }

    setLoading(true);
    try {
      // Send only unit_quantity, price, and cost_price (no name field)
      const response = await api.post('/products/bulk/create-children/', {
        parent_id: selectedParent.parent?.id || selectedParent.id,
        child_products: validChildren  // Should only have unit_quantity, price, cost_price
      });
      
      alert(`Created ${response.data.created.length} child products successfully!`);
      setShowCreateChildren(false);
      setChildrenForm([{ unit_quantity: '', price: '', cost_price: '' }]);
      await viewChildProducts({ id: selectedParent.parent?.id || selectedParent.id });
      fetchParentProducts();
    } catch (error) {
      const errorMsg = error.response?.data?.errors 
        ? error.response.data.errors.map(e => `${e.error}`).join(', ')
        : error.response?.data?.detail || error.message;
      alert('Error creating child products: ' + errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const addChildRow = () => {
    setChildrenForm([...childrenForm, { unit_quantity: '', price: '', cost_price: '' }]);
  };

  const removeChildRow = (index) => {
    setChildrenForm(childrenForm.filter((_, i) => i !== index));
  };

  const updateChildRow = (index, field, value) => {
    const updated = [...childrenForm];
    updated[index][field] = value;
    setChildrenForm(updated);
  };

  const viewChildProducts = async (parent) => {
    try {
      const response = await api.get(`/products/bulk/parent/${parent.id}/children/`);
      setSelectedParent(response.data);
      setShowCreateChildren(true);
    } catch (err) {
      alert('Error loading child products');
    }
  };

  const viewStockDetails = async (productId) => {
    try {
      const response = await api.get(`/products/${productId}/stock-info/`);
      setStockInfo(response.data);
      setShowStockInfo(true);
    } catch (error) {
      console.error('Error fetching stock info:', error);
    }
  };

  const updateParentStock = async (parentId, newStock) => {
    try {
      await api.post(`/products/bulk/parent/${parentId}/update-stock/`, {
        stock_quantity: newStock
      });
      alert('Stock updated successfully!');
      fetchParentProducts();
      if (selectedParent && selectedParent.id === parentId) {
        await viewChildProducts(selectedParent);
      }
    } catch (error) {
      alert('Error updating stock: ' + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div className="bulk-products-container">
      <div className="bulk-products-inner">
        {/* Header */}
        <div className="bulk-products-header">
          <div className="bulk-products-header-content">
            <h1>📦 Bulk Product Management</h1>
            <p>Create parent products (bulk) and child products (retail sizes) with automatic stock tracking</p>
          </div>
          <Link to="/dashboard" className="btn-back-dashboard">
            ← Dashboard
          </Link>
        </div>
        
        {/* Action Buttons */}
        <div className="bulk-products-actions">
          <button onClick={() => setShowCreateParent(true)} className="btn-create-parent">
            + Create Parent Product
          </button>
          
          <button onClick={fetchParentProducts} className="btn-refresh">
            🔄 Refresh
          </button>
        </div>

        {/* Parent Products List */}
        <div className="parent-products-section">
          <h2>Parent Products ({products.length})</h2>
          
          {products.length === 0 ? (
            <div className="no-products-message">
              <p>No parent products yet</p>
              <p>Create a parent product to get started</p>
            </div>
          ) : (
            <div className="parent-products-grid">
              {products.map(product => (
                <div key={product.id} className="parent-product-card">
                  <h3>{product.name}</h3>
                  
                  <div className="parent-product-details">
                    <div className="parent-detail-row">
                      <span>SKU:</span>
                      <strong>{product.sku}</strong>
                    </div>
                    <div className="parent-detail-row">
                      <span>Unit Size:</span>
                      <strong>{product.unit_quantity}{product.base_unit}</strong>
                    </div>
                    <div className="parent-detail-row">
                      <span>Stock:</span>
                      <strong className={product.stock_quantity === 0 ? 'stock-out-of-stock' : 'stock-in-stock'}>
                        {product.stock_quantity} units
                      </strong>
                    </div>
                    <div className="parent-total-available">
                      <div>
                        <span>Total Available:</span>
                        <strong>
                          {parseFloat(product.stock_quantity) * parseFloat(product.unit_quantity)}{product.base_unit}
                        </strong>
                      </div>
                    </div>
                  </div>
                  
                  <div className="parent-product-actions">
                    <button
                      onClick={() => {
                        viewChildProducts(product);
                        setShowCreateChildren(true);
                      }}
                      className="btn-manage-children"
                    >
                      Children
                    </button>
                    
                    <button
                      onClick={() => viewStockDetails(product.id)}
                      className="btn-view-stock"
                      title="View Stock Details"
                    >
                      📊
                    </button>
                    
                    <button
                      onClick={() => {
                        const newStock = prompt(`Current stock: ${product.stock_quantity}\nEnter new stock quantity:`);
                        if (newStock !== null && !isNaN(newStock)) {
                          updateParentStock(product.id, parseInt(newStock));
                        }
                      }}
                      className="btn-update-stock"
                      title="Update Stock"
                    >
                      📝
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Create Parent Modal */}
        {showCreateParent && (
          <div className="bulk-modal-overlay" onClick={() => setShowCreateParent(false)}>
            <div className="bulk-modal" onClick={(e) => e.stopPropagation()}>
              <div className="bulk-modal-header">
                <h2>Create Parent Product</h2>
                <button onClick={() => setShowCreateParent(false)} className="bulk-modal-close">
                  ×
                </button>
              </div>
              
              <p className="bulk-modal-description">
                Parent products hold the bulk inventory. Child products will be created from this.
              </p>
              
              <div className="bulk-form-group">
                <label>Product Name *</label>
                <input
                  type="text"
                  value={parentForm.name}
                  onChange={(e) => setParentForm({ ...parentForm, name: e.target.value })}
                  className="bulk-form-input"
                  placeholder="e.g., Milk 20L Can"
                />
              </div>

              <div className="bulk-form-group">
                <label>Category</label>
                <select
                  value={parentForm.category}
                  onChange={(e) => setParentForm({ ...parentForm, category: e.target.value })}
                  className="bulk-form-select"
                >
                  <option value="">Select Category</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              <div className="bulk-form-group">
                <label>Base Unit *</label>
                <select
                  value={parentForm.base_unit}
                  onChange={(e) => setParentForm({ ...parentForm, base_unit: e.target.value })}
                  className="bulk-form-select"
                >
                  <option value="l">Liters (l)</option>
                  <option value="ml">Milliliters (ml)</option>
                  <option value="kg">Kilograms (kg)</option>
                  <option value="g">Grams (g)</option>
                  <option value="pcs">Pieces</option>
                </select>
              </div>

              <div className="bulk-form-group">
                <label>Unit Quantity *</label>
                <input
                  type="number"
                  step="0.001"
                  value={parentForm.unit_quantity}
                  onChange={(e) => setParentForm({ ...parentForm, unit_quantity: e.target.value })}
                  className="bulk-form-input"
                  placeholder="e.g., 20 (for 20L)"
                />
              </div>

              <div className="bulk-form-group">
                <label>Price *</label>
                <input
                  type="number"
                  step="0.01"
                  value={parentForm.price}
                  onChange={(e) => setParentForm({ ...parentForm, price: e.target.value })}
                  className="bulk-form-input"
                  placeholder="Selling price"
                />
              </div>

              <div className="bulk-form-group">
                <label>Cost Price *</label>
                <input
                  type="number"
                  step="0.01"
                  value={parentForm.cost_price}
                  onChange={(e) => setParentForm({ ...parentForm, cost_price: e.target.value })}
                  className="bulk-form-input"
                  placeholder="Purchase cost"
                />
              </div>

              <div className="bulk-form-group">
                <label>Initial Stock Quantity *</label>
                <input
                  type="number"
                  value={parentForm.stock_quantity}
                  onChange={(e) => setParentForm({ ...parentForm, stock_quantity: e.target.value })}
                  className="bulk-form-input"
                  placeholder="Number of bulk units (e.g., 20 cans)"
                />
                {parentForm.unit_quantity && parentForm.stock_quantity && (
                  <small className="bulk-form-hint">
                    Total: {parseFloat(parentForm.unit_quantity) * parseFloat(parentForm.stock_quantity)}{parentForm.base_unit}
                  </small>
                )}
              </div>

              <div className="bulk-modal-footer">
                <button onClick={() => setShowCreateParent(false)} className="btn-cancel">
                  Cancel
                </button>
                <button
                  onClick={createParentProduct}
                  disabled={loading}
                  className="btn-submit"
                >
                  {loading ? 'Creating...' : 'Create Parent'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Create Children Modal */}
        {showCreateChildren && selectedParent && (
          <div className="bulk-modal-overlay" onClick={() => {
            setShowCreateChildren(false);
            setSelectedParent(null);
            setChildrenForm([{ unit_quantity: '', price: '', cost_price: '' }]);
          }}>
            <div className="bulk-modal bulk-modal-large" onClick={(e) => e.stopPropagation()}>
              <div className="bulk-modal-header">
                <h2>Manage Child Products</h2>
                <button onClick={() => {
                  setShowCreateChildren(false);
                  setSelectedParent(null);
                  setChildrenForm([{ unit_quantity: '', price: '', cost_price: '' }]);
                }} className="bulk-modal-close">×</button>
              </div>

              <div className="parent-info-box">
                <h4>Parent: {selectedParent.parent?.name || selectedParent.name}</h4>
                <div className="parent-stats">
                  <span>Stock: {selectedParent.parent?.stock_quantity || selectedParent.stock_quantity} × {selectedParent.parent?.unit_quantity || selectedParent.unit_quantity}{selectedParent.parent?.base_unit || selectedParent.base_unit}</span>
                  <span>Total Available: {selectedParent.parent?.total_base_units || (parseFloat(selectedParent.stock_quantity) * parseFloat(selectedParent.unit_quantity))}{selectedParent.parent?.base_unit || selectedParent.base_unit}</span>
                </div>
              </div>

              {/* Existing Children */}
              {selectedParent.children && selectedParent.children.length > 0 && (
                <div className="existing-children-section">
                  <h4>Existing Child Products ({selectedParent.children.length})</h4>
                  <div className="existing-children-grid">
                    {selectedParent.children.map(child => (
                      <div
                        key={child.id}
                        className={`existing-child-card ${child.available_stock === 0 ? 'out-of-stock' : ''}`}
                      >
                        <div className="existing-child-header">
                          <div className="existing-child-info">
                            <strong>{child.name}</strong>
                            <span className="existing-child-unit">({child.unit_quantity}{child.base_unit})</span>
                          </div>
                          <div className="existing-child-details">
                            <div className="existing-child-price">
                              ksh {parseFloat(child.price).toFixed(2)}
                            </div>
                            <div className={`existing-child-stock ${child.available_stock === 0 ? 'out' : child.is_low_stock ? 'low' : 'good'}`}>
                              {child.available_stock === 0 ? '❌ OUT OF STOCK' : `✅ ${child.available_stock} units`}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Add New Children */}
              <div className="add-children-section">
                <h4>Add New Child Products</h4>
                
                {childrenForm.map((child, index) => (
                  <div key={index} className="child-form-row">
                    <div className="child-form-header">
                      <span>Child Product {index + 1}</span>
                      {childrenForm.length > 1 && (
                        <button onClick={() => removeChildRow(index)} className="btn-remove-child">
                          ×
                        </button>
                      )}
                    </div>

                    <div className="child-form-inputs">
                      <input
                        type="number"
                        step="0.001"
                        placeholder={`Unit Quantity (${selectedParent.parent?.base_unit || selectedParent.base_unit})*`}
                        value={child.unit_quantity}
                        onChange={(e) => updateChildRow(index, 'unit_quantity', e.target.value)}
                        style={{ flex: 1.5 }}
                      />
                      <input
                        type="number"
                        step="0.01"
                        placeholder="Price*"
                        value={child.price}
                        onChange={(e) => updateChildRow(index, 'price', e.target.value)}
                        style={{ flex: 1 }}
                      />
                      <input
                        type="number"
                        step="0.01"
                        placeholder="Cost"
                        value={child.cost_price}
                        onChange={(e) => updateChildRow(index, 'cost_price', e.target.value)}
                        style={{ flex: 1 }}
                      />
                    </div>

                    {child.unit_quantity && (
                      <div style={{ marginTop: '8px', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <div className="available-preview">
                          ✓ Available: {Math.floor(((selectedParent.parent?.total_base_units || (parseFloat(selectedParent.stock_quantity) * parseFloat(selectedParent.unit_quantity)))) / parseFloat(child.unit_quantity || 1))} units
                        </div>
                        <div style={{ fontSize: '13px', color: '#667eea', fontWeight: '500' }}>
                          → Name: {(() => {
                            const qty = parseFloat(child.unit_quantity);
                            const baseUnit = selectedParent.parent?.base_unit || selectedParent.base_unit;
                            const parentName = selectedParent.parent?.name || selectedParent.name;
                            
                            if (qty < 1 && (baseUnit === 'kg' || baseUnit === 'l')) {
                              const smallQty = qty * 1000;
                              const smallUnit = baseUnit === 'kg' ? 'g' : 'ml';
                              return `${parentName} ${Math.round(smallQty)}${smallUnit}`;
                            }
                            return `${parentName} ${qty}${baseUnit}`;
                          })()}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                <button onClick={addChildRow} className="btn-add-child">
                  + Add Another Child Product
                </button>
              </div>

              <div className="bulk-modal-footer">
                <button onClick={() => {
                  setShowCreateChildren(false);
                  setSelectedParent(null);
                  setChildrenForm([{ unit_quantity: '', price: '', cost_price: '' }]);
                }} className="btn-cancel">
                  Close
                </button>
                <button 
                  onClick={createChildProducts} 
                  className="btn-submit"
                  disabled={loading || !childrenForm.some(c => c.unit_quantity && c.price)}
                >
                  {loading ? 'Creating...' : 'Create Children'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stock Info Modal */}
        {showStockInfo && stockInfo && (
          <div className="bulk-modal-overlay" onClick={() => setShowStockInfo(false)}>
            <div className="bulk-modal bulk-modal-large" onClick={(e) => e.stopPropagation()}>
              <div className="bulk-modal-header">
                <h2>📊 Stock Details</h2>
                <button onClick={() => setShowStockInfo(false)} className="bulk-modal-close">×</button>
              </div>

              <div className="stock-info-card">
                <h4>{stockInfo.name}</h4>
                <div className="stock-info-grid">
                  <div className="stock-info-item">
                    <span>SKU:</span>
                    <strong>{stockInfo.sku}</strong>
                  </div>
                  <div className="stock-info-item">
                    <span>Type:</span>
                    <strong style={{ textTransform: 'capitalize' }}>{stockInfo.product_type}</strong>
                  </div>
                  <div className="stock-info-item">
                    <span>Unit:</span>
                    <strong>{stockInfo.unit_quantity}{stockInfo.base_unit}</strong>
                  </div>
                  <div className="stock-info-item">
                    <span>Price:</span>
                    <strong className="stock-price-highlight">ksh {parseFloat(stockInfo.price).toFixed(2)}</strong>
                  </div>
                </div>
              </div>

              {stockInfo.product_type === 'parent' && (
                <>
                  <div className="parent-stock-card">
                    <div className="stock-row">
                      <span>Stock Quantity:</span>
                      <strong className="stock-value">{stockInfo.stock_quantity} units</strong>
                    </div>
                    <div className="stock-row total">
                      <span>Total Available:</span>
                      <strong className="total-value">{stockInfo.total_base_units}{stockInfo.base_unit}</strong>
                    </div>
                    <button 
                      onClick={() => {
                        const newStock = prompt(`Enter new stock quantity (current: ${stockInfo.stock_quantity}):`);
                        if (newStock !== null && !isNaN(newStock)) {
                          updateParentStock(stockInfo.id, parseInt(newStock));
                        }
                      }}
                      className="btn-update-parent-stock"
                    >
                      Update Stock
                    </button>
                  </div>

                  {stockInfo.children && stockInfo.children.length > 0 && (
                    <div className="children-stock-section">
                      <h4>Child Products ({stockInfo.children.length})</h4>
                      <div className="children-stock-list">
                        {stockInfo.children.map(child => (
                          <div key={child.id} className={`child-stock-item ${child.available_stock === 0 ? 'out' : ''}`}>
                            <div className="child-name-unit">
                              <strong>{child.name}</strong>
                              <span className="unit-size">{child.unit_quantity}{stockInfo.base_unit}</span>
                            </div>
                            <div className="child-price-stock">
                              <span className="child-price">ksh {parseFloat(child.price).toFixed(2)}</span>
                              <span className={`child-stock ${child.available_stock === 0 ? 'out' : child.is_low_stock ? 'low' : 'good'}`}>
                                {child.available_stock} units
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {stockInfo.product_type === 'child' && (
                <>
                  <div className="parent-ref-card">
                    <h4>Parent Product</h4>
                    <div className="parent-details">
                      <strong>{stockInfo.parent.name}</strong>
                      <div className="parent-stock-info">
                        Stock: {stockInfo.parent.stock_quantity} × {stockInfo.parent.unit_quantity}{stockInfo.base_unit} = {stockInfo.parent.total_base_units}{stockInfo.base_unit}
                      </div>
                    </div>
                  </div>

                  <div className="child-availability-card">
                    <div className="availability-row">
                      <span>Available Stock:</span>
                      <strong className="available-value">{stockInfo.available_stock} units</strong>
                    </div>
                  </div>

                  {stockInfo.calculation && (
                    <div className="calculation-box">
                      <strong>Calculation:</strong>
                      <code>{stockInfo.calculation}</code>
                    </div>
                  )}
                </>
              )}

              <div className="bulk-modal-footer">
                <button onClick={() => setShowStockInfo(false)} className="btn-submit">Close</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BulkProducts;