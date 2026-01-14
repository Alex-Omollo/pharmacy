import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import api from '../services/api';
import BulkUpload from '../components/BulkUpload';
import './Products.css';
import PageHeader from '../components/PageHeader';
// import BulkProducts from '../components/BulkProducts';

const Products = () => {
  const { user } = useSelector((state) => state.auth);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showBulkUpload, setShowBulkUpload] = useState(false);
  const [showChildrenModal, setShowChildrenModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [parentWithChildren, setParentWithChildren] = useState(null);
  const [stockInfo, setStockInfo] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterLowStock, setFilterLowStock] = useState(false);
  const [filterProductType, setFilterProductType] = useState('all');
  const [showChildProducts, setShowChildProducts] = useState(false);
  
  // Form data for regular products
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    barcode: '',
    category: '',
    description: '',
    product_type: 'simple',
    base_unit: 'pcs',
    unit_quantity: '1',
    price: '',
    cost_price: '',
    tax_rate: '0',
    stock_quantity: '0',
    min_stock_level: '10',
    is_active: true,
  });
  
  // Form for child products
  const [childrenForm, setChildrenForm] = useState([
    { unit_quantity: '', price: '', cost_price: '' }
  ]);
  
  const [error, setError] = useState('');

  const canModify = user?.role === 'admin' || user?.role === 'manager';

  useEffect(() => {
    fetchProducts();
    fetchCategories();
  }, [searchTerm, filterCategory, filterLowStock, filterProductType, showChildProducts]);

  const fetchProducts = async () => {
    try {
      let url = '/products/?';
      if (searchTerm) url += `search=${searchTerm}&`;
      if (filterCategory) url += `category=${filterCategory}&`;
      if (filterLowStock) url += `low_stock=true&`;
      if (!showChildProducts) {
        url += 'exclude_children=true&';
      } else {
        url += 'exclude_children=false&';
      }
      
      const response = await api.get(url);
      
      // Filter by product type if needed
      let filteredProducts = response.data;
      if (filterProductType !== 'all') {
        filteredProducts = response.data.filter(p => p.product_type === filterProductType);
      }
      
      setProducts(filteredProducts);
    } catch (err) {
      console.error('Error fetching products:', err);
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
      const submitData = { ...formData };
      
      // For parent products, use the bulk endpoint
      if (formData.product_type === 'parent') {
        if (editMode) {
          await api.patch(`/products/${selectedProduct.id}/`, submitData);
        } else {
          await api.post('/products/bulk/create-parent/', submitData);
        }
      } else {
        // Regular product creation
        if (editMode) {
          await api.patch(`/products/${selectedProduct.id}/`, submitData);
        } else {
          await api.post('/products/create/', submitData);
        }
      }
      
      setShowModal(false);
      resetForm();
      fetchProducts();
    } catch (err) {
      setError(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Error saving product');
    }
  };

  const handleEdit = (product) => {
    setSelectedProduct(product);
    setFormData({
      name: product.name || '',
      sku: product.sku || '',
      barcode: product.barcode || '',
      category: product.category || '',
      description: product.description || '',
      product_type: product.product_type || 'simple',
      base_unit: product.base_unit || 'pcs',
      unit_quantity: product.unit_quantity ? String(product.unit_quantity) : '1',
      price: product.price ? String(product.price) : '',
      cost_price: product.cost_price ? String(product.cost_price) : '',
      tax_rate: product.tax_rate ? String(product.tax_rate) : '0',
      stock_quantity: product.stock_quantity !== undefined && product.stock_quantity !== null 
        ? String(product.stock_quantity) 
        : '0',
      min_stock_level: product.min_stock_level ? String(product.min_stock_level) : '10',
      is_active: product.is_active !== undefined ? product.is_active : true,
    });
    setEditMode(true);
    setShowModal(true);
  };


  const handleDelete = async (id) => {
    const product = products.find(p => p.id === id);
    
    if (window.confirm(`Are you sure you want to delete "${product.name}"?`)) {
      try {
        const response = await api.delete(`/products/${id}/`);
        
        // Check if it was soft-deleted or hard-deleted
        if (response.status === 200) {
          // Soft delete - product was deactivated
          alert(response.data.message + '\n\n' + response.data.note);
        } else {
          // Hard delete - product was permanently removed
          alert('Product deleted successfully!');
        }
        
        fetchProducts();
      } catch (err) {
        // Handle different error scenarios
        const errorMsg = err.response?.data?.detail || 
                        err.response?.data?.error || 
                        'Error deleting product';
        
        if (err.response?.status === 400) {
          alert(`Cannot delete product:\n\n${errorMsg}\n\nThe product will be deactivated instead.`);
          
          // Try to deactivate instead
          try {
            const deactivateResponse = await api.post(`/products/${id}/deactivate/`);
            alert(deactivateResponse.data.message);
            fetchProducts();
          } catch (deactivateErr) {
            alert('Failed to deactivate product');
          }
        } else {
          alert(errorMsg);
        }
      }
    }
  };

  const toggleProductStatus = async (product) => {
    const action = product.is_active ? 'deactivate' : 'reactivate';
    const actionText = product.is_active ? 'Deactivate' : 'Reactivate';
    
    if (window.confirm(`${actionText} "${product.name}"?`)) {
      try {
        const response = await api.post(`/products/${product.id}/${action}/`);
        alert(response.data.message);
        fetchProducts();
      } catch (err) {
        alert(`Error: ${err.response?.data?.error || 'Failed to update product status'}`);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      sku: '',
      barcode: '',
      category: '',
      description: '',
      product_type: 'simple',
      base_unit: 'pcs',
      unit_quantity: '1',
      price: '',
      cost_price: '',
      tax_rate: '0',
      stock_quantity: '0',
      min_stock_level: '10',
      is_active: true,
    });
    setEditMode(false);
    setSelectedProduct(null);
    setError('');
  };

  const handleNumericChange = (e) => {
    const { name, value } = e.target;
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

  // Parent-Child Management Functions
  const viewChildProducts = async (parent) => {
    try {
      const response = await api.get(`/products/bulk/parent/${parent.id}/children/`);
      setParentWithChildren(response.data);
      setShowChildrenModal(true);
    } catch (err) {
      alert('Error loading child products');
    }
  };

  const createChildProducts = async () => {
    if (!parentWithChildren) return;
    
    setLoading(true);
    try {
      const validChildren = childrenForm.filter(c => c.unit_quantity && c.price);
      
      if (validChildren.length === 0) {
        alert('Please fill in at least unit quantity and price for one child product');
        setLoading(false);
        return;
      }
      
      await api.post('/products/bulk/create-children/', {
        parent_id: parentWithChildren.parent?.id || parentWithChildren.id,
        child_products: validChildren
      });
      
      alert('Child products created successfully!');
      setChildrenForm([{ unit_quantity: '', price: '', cost_price: '' }]);
      
      // Refresh parent with updated children
      await viewChildProducts({ id: parentWithChildren.parent?.id || parentWithChildren.id });
      fetchProducts();
    } catch (err) {
      const errorMsg = err.response?.data?.errors 
        ? err.response.data.errors.join(', ')
        : err.response?.data?.detail || err.message;
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

  const viewStockDetails = async (product) => {
    try {
      const response = await api.get(`/products/${product.id}/stock-info/`);
      setStockInfo(response.data);
      setShowStockModal(true);
    } catch (err) {
      alert('Error loading stock details');
    }
  };

  const updateParentStock = async (parentId, newStock) => {
    try {
      await api.post(`/products/bulk/parent/${parentId}/update-stock/`, {
        stock_quantity: newStock
      });
      fetchProducts();
      if (stockInfo && stockInfo.id === parentId) {
        viewStockDetails({ id: parentId });
      }
    } catch (err) {
      alert('Error updating stock');
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="products-container">
      <PageHeader 
        title="Product Management" 
        subtitle="Manage your product catalog, pricing, and inventory"
      >
        {canModify && (
          <>
            <button onClick={() => setShowBulkUpload(true)} className="btn-secondary">
              Bulk Upload
            </button>
            <button onClick={() => { resetForm(); setShowModal(true); }} className="btn-primary">
              + Add Product
            </button>
          </>
        )}
      </PageHeader>

      <div className="products-filters">
        <input
          type="text"
          placeholder="Search products..."
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

        <select
          value={filterProductType}
          onChange={(e) => setFilterProductType(e.target.value)}
          className="filter-select"
        >
          <option value="all">All Types</option>
          <option value="simple">Simple Products</option>
          <option value="parent">Parent/Bulk Products</option>
        </select>

        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={filterLowStock}
            onChange={(e) => setFilterLowStock(e.target.checked)}
          />
          Low Stock Only
        </label>
        <label className='filter-checkbox filter-checkbox-children'>
          <input
            type='checkbox'
            checked={showChildProducts}
            onChange={(e) => setShowChildProducts(e.target.checked)}
          />
          <span className='checkbox-label-text'>
            Show Child Products
            <span className='checkbox-hint'>
              (Derived from parent products)
            </span>
          </span>
        </label>
      </div>

      {!showChildProducts && (
        <div className='products-info-banner'>
          <span className='info-icon'>ℹ️</span>
          <div className='info-text'>
            <strong>Child products are hidden.</strong>
            Check 'Show Child Products' above to view products derived from parent/bulk items.
          </div>
        </div>
      )}

      <div className="products-grid">
        {products.map((product) => (
          <div key={product.id} className={`product-card ${product.product_type === 'parent' ? 'parent-product' : product.product_type === 'child' ? 'child-product' : ''}`}>
            <div className="product-image">
              {product.image ? (
                <img src={product.image} alt={product.name} />
              ) : (
                <div className="no-image">
                  {product.product_type === 'parent' ? '📦' : product.product_type === 'child' ? '📋' : '🏷️'}
                </div>
              )}
            </div>
            
            <div className="product-info">
              <div className="product-type-badge">{product.product_type}</div>
              <h3>{product.name}</h3>
              <p className="product-sku">SKU: {product.sku}</p>
              {product.parent_name && (
                <p className="parent-ref">From: {product.parent_name}</p>
              )}
              <p className="product-category">{product.category_name || 'Uncategorized'}</p>
              
              {product.product_type === 'parent' && (
                <div className="bulk-info">
                  <span className="unit-info">{product.unit_quantity}{product.base_unit} per unit</span>
                  <span className="total-info">
                    Total: {parseFloat(product.stock_quantity) * parseFloat(product.unit_quantity)}{product.base_unit}
                  </span>
                </div>
              )}
              
              {product.product_type === 'child' && (
                <div className="child-info">
                  <span className="unit-info">{product.unit_quantity}{product.base_unit}</span>
                </div>
              )}
              
              <div className="product-price">
                <span className="price">ksh {parseFloat(product.price).toFixed(2)}</span>
              </div>
              
              <div className="product-stock">
                <span className={product.is_low_stock ? 'low-stock' : 'in-stock'}>
                  {product.product_type === 'parent' ? `${product.stock_quantity} units` : 
                   product.product_type === 'child' ? `${product.available_stock} available` :
                   `Stock: ${product.stock_quantity}`}
                  {product.is_low_stock && ' ⚠️'}
                </span>
              </div>
              
              {!product.is_active && (
                <div className="inactive-badge">Inactive</div>
              )}
            </div>

            {canModify && (
              <div className="product-actions">
                {product.product_type === 'parent' && (
                  <button 
                    onClick={() => viewChildProducts(product)} 
                    className="btn-manage-children"
                    title="Manage child products"
                  >
                    Children
                  </button>
                )}
                <button 
                  onClick={() => viewStockDetails(product)} 
                  className="btn-stock-info"
                  title="View stock details"
                >
                  📊
                </button>
                <button onClick={() => handleEdit(product)} className="btn-edit">
                  Edit
                </button>
                {/* Show activate/deactivate toggle */}
                <button 
                  onClick={() => toggleProductStatus(product)} 
                  className={product.is_active ? "btn-deactivate" : "btn-activate"}
                  title={product.is_active ? "Deactivate product" : "Reactivate product"}
                >
                  {product.is_active ? '🔒 Hide' : '✓ Show'}
                </button>
                {/* Only show delete for products without history */}
                <button 
                  onClick={() => handleDelete(product.id)} 
                  className="btn-delete"
                  title="Delete product (only if no transaction history)"
                >
                  Delete
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {products.length === 0 && (
        <div className="no-products">
          <p>No products found</p>
          {!showChildProducts && (
            <p className='hint'>
              Try checking "Show Child Products" to see more items
            </p>
          )}
        </div>
      )}

      {/* Product Create/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => { setShowModal(false); resetForm(); }}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editMode ? 'Edit Product' : 'Add New Product'}</h3>
              <button onClick={() => { setShowModal(false); resetForm(); }} className="close-btn">×</button>
            </div>
            
            {error && <div className="error-message">{error}</div>}
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Product Type *</label>
                <select
                  name="product_type"
                  value={formData.product_type}
                  onChange={handleChange}
                  disabled={editMode}
                >
                  <option value="simple">Simple Product</option>
                  <option value="parent">Parent/Bulk Product</option>
                </select>
                <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
                  {formData.product_type === 'parent' 
                    ? 'Parent products hold bulk inventory (e.g., 50kg Rice Bag)'
                    : 'Simple products are standalone items'}
                </small>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Product Name *</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>SKU {formData.product_type === 'simple' ? '*' : '(optional)'}</label>
                  <input
                    type="text"
                    name="sku"
                    value={formData.sku}
                    onChange={handleChange}
                    readOnly={editMode}
                    required={formData.product_type === 'simple'}
                  />
                </div>
              </div>

              {formData.product_type === 'parent' && (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Base Unit *</label>
                      <select
                        name="base_unit"
                        value={formData.base_unit}
                        onChange={handleChange}
                      >
                        <option value="kg">Kilograms (kg)</option>
                        <option value="g">Grams (g)</option>
                        <option value="l">Liters (l)</option>
                        <option value="ml">Milliliters (ml)</option>
                        <option value="pcs">Pieces</option>
                        <option value="box">Box</option>
                        <option value="pack">Pack</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Unit Quantity *</label>
                      <input
                        type="text"
                        // step="0.001"
                        name="unit_quantity"
                        value={formData.unit_quantity}
                        onChange={handleNumericChange}
                        required
                      />
                      <small style={{ color: '#666' }}>e.g., 50 for 50kg bag</small>
                    </div>
                  </div>
                </>
              )}

              <div className="form-row">
                <div className="form-group">
                  <label>Barcode</label>
                  <input
                    type="text"
                    name="barcode"
                    value={formData.barcode}
                    onChange={handleChange}
                  />
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
                <label>Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows="3"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Selling Price *</label>
                  <input
                    type="text"
                    // step="0.01"
                    name="price"
                    value={formData.price}
                    onChange={handleNumericChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Buying Price *</label>
                  <input
                    type="text"
                    // step="0.01"
                    name="cost_price"
                    value={formData.cost_price}
                    onChange={handleNumericChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Tax Rate (%)</label>
                  <input
                    type="text"
                    // step="0.01"
                    name="tax_rate"
                    value={formData.tax_rate}
                    onChange={handleNumericChange}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Stock Quantity *</label>
                  <input
                    type="text"
                    name="stock_quantity"
                    value={formData.stock_quantity}
                    onChange={handleNumericChange}
                    required
                  />
                  {formData.product_type === 'parent' && formData.unit_quantity && formData.stock_quantity && (
                    <small style={{ color: '#667eea', fontWeight: '600' }}>
                      Total: {parseFloat(formData.unit_quantity) * parseFloat(formData.stock_quantity)}{formData.base_unit}
                    </small>
                  )}
                </div>
                <div className="form-group">
                  <label>Min Stock Level</label>
                  <input
                    type="text"
                    name="min_stock_level"
                    value={formData.min_stock_level}
                    onChange={handleNumericChange}
                  />
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
                  Active Product
                </label>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => { setShowModal(false); resetForm(); }} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editMode ? 'Update Product' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Children Management Modal */}
      {showChildrenModal && parentWithChildren && (
        <div className="modal-overlay" onClick={() => setShowChildrenModal(false)}>
          <div className="modal modal-xl" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Manage Child Products</h3>
              <button onClick={() => setShowChildrenModal(false)} className="close-btn">×</button>
            </div>

            <div className="parent-info-box">
              <h4>Parent Product: {parentWithChildren.parent?.name || parentWithChildren.name}</h4>
              <div className="parent-stats">
                <span>Stock: {parentWithChildren.parent?.stock_quantity || parentWithChildren.stock_quantity} × {parentWithChildren.parent?.unit_quantity || parentWithChildren.unit_quantity}{parentWithChildren.parent?.base_unit || parentWithChildren.base_unit}</span>
                <span className="total-highlight">
                  Total: {parentWithChildren.parent?.total_base_units || (parseFloat(parentWithChildren.stock_quantity) * parseFloat(parentWithChildren.unit_quantity))}{parentWithChildren.parent?.base_unit || parentWithChildren.base_unit}
                </span>
              </div>
            </div>

            {parentWithChildren.children && parentWithChildren.children.length > 0 && (
              <div className="existing-children">
                <h4>Existing Child Products ({parentWithChildren.children.length})</h4>
                <div className="children-grid">
                  {parentWithChildren.children.map(child => (
                    <div key={child.id} className={`child-card ${child.available_stock === 0 ? 'out-of-stock' : ''}`}>
                      <div className="child-header">
                        <strong>{child.name}</strong>
                        <span className="child-unit">({child.unit_quantity}{child.base_unit})</span>
                      </div>
                      <div className="child-details">
                        <span className="child-price">ksh {parseFloat(child.price).toFixed(2)}</span>
                        <span className={`child-stock ${child.available_stock === 0 ? 'out' : child.is_low_stock ? 'low' : 'good'}`}>
                          {child.available_stock === 0 ? '❌ Out' : `✅ ${child.available_stock}`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="add-children-section">
              <h4>Add New Child Products</h4>
              {childrenForm.map((child, index) => (
                <div key={index} className="child-form-row">
                  <div className="child-form-header">
                    <span>Child Product {index + 1}</span>
                    {childrenForm.length > 1 && (
                      <button onClick={() => removeChildRow(index)} className="btn-remove-child">×</button>
                    )}
                  </div>
                  <div className="child-form-inputs">
                    <input
                      type="text"
                      step="0.001"
                      placeholder={`Unit Quantity (${parentWithChildren.parent?.base_unit || parentWithChildren.base_unit})*`}
                      value={child.unit_quantity}
                      onChange={(e) => updateChildRow(index, 'unit_quantity', e.target.value)}
                    />
                    <input
                      type="text"
                      // step="0.01"
                      placeholder="Selling Price*"
                      value={child.price}
                      onChange={(e) => updateChildRow(index, 'price', e.target.value)}
                    />
                    <input
                      type="text"
                      // step="0.01"
                      placeholder="Buying price"
                      value={child.cost_price}
                      onChange={(e) => updateChildRow(index, 'cost_price', e.target.value)}
                    />
                  </div>

                  {child.unit_quantity && (
                    <div className="available-preview">
                      ✓ Available: {Math.floor(((parentWithChildren.parent?.total_base_units || (parseFloat(parentWithChildren.stock_quantity) * parseFloat(parentWithChildren.unit_quantity)))) / parseFloat(child.unit_quantity || 1))} units
                      <span style={{ marginLeft: '15px', color: '#667eea', fontWeight: '600' }}>
                        → Name: {(() => {
                          const qty = parseFloat(child.unit_quantity);
                          const baseUnit = parentWithChildren.parent?.base_unit || parentWithChildren.base_unit;
                          const parentName = parentWithChildren.parent?.name || parentWithChildren.name;
                          
                          if (qty < 1 && (baseUnit === 'kg' || baseUnit === 'l')) {
                            const smallQty = qty * 1000;
                            const smallUnit = baseUnit === 'kg' ? 'g' : 'ml';
                            return `${parentName} ${Math.round(smallQty)}${smallUnit}`;
                          }
                          return `${parentName} ${qty}${baseUnit}`;
                        })()}
                      </span>
                    </div>
                  )}
                </div>
              ))}

              <button onClick={addChildRow} className="btn-add-child">+ Add Another Child</button>
            </div>

            <div className="modal-footer">
              <button onClick={() => setShowChildrenModal(false)} className="btn-secondary">Close</button>
              <button 
                onClick={createChildProducts} 
                className="btn-primary"
                disabled={loading || !childrenForm.some(c => c.unit_quantity && c.price)}
              >
                {loading ? 'Creating...' : 'Create Children'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stock Details Modal */}
      {showStockModal && stockInfo && (
        <div className="modal-overlay" onClick={() => setShowStockModal(false)}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📊 Stock Details</h3>
              <button onClick={() => setShowStockModal(false)} className="close-btn">×</button>
            </div>

            <div className="stock-info-card">
              <h4>{stockInfo.name}</h4>
              <div className="info-grid">
                <div className="info-item"><span>SKU:</span><strong>{stockInfo.sku}</strong></div>
                <div className="info-item"><span>Type:</span><strong style={{ textTransform: 'capitalize' }}>{stockInfo.product_type}</strong></div>
                <div className="info-item"><span>Unit:</span><strong>{stockInfo.unit_quantity}{stockInfo.base_unit}</strong></div>
                <div className="info-item"><span>Price:</span><strong className="price-highlight">ksh {parseFloat(stockInfo.price).toFixed(2)}</strong></div>
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
                    className="btn-update-stock"
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
                            <span className="price">ksh {parseFloat(child.price).toFixed(2)}</span>
                            <span className={`stock ${child.available_stock === 0 ? 'out' : child.is_low_stock ? 'low' : 'good'}`}>
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

            <div className="modal-footer">
              <button onClick={() => setShowStockModal(false)} className="btn-primary">Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Upload Modal */}
      {showBulkUpload && (
        <div className="modal-overlay" onClick={() => setShowBulkUpload(false)}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <BulkUpload 
              onClose={() => setShowBulkUpload(false)}
              onSuccess={fetchProducts}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Products;