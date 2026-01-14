import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import api from '../services/api';
import PageHeader from '../components/PageHeader';
import './Categories.css';

const Categories = () => {
  const { user } = useSelector((state) => state.auth);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_active: true,
  });
  const [error, setError] = useState('');

  const canModify = user?.role === 'admin' || user?.role === 'manager';

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories/');
      setCategories(response.data);
    } catch (err) {
      console.error('Error fetching categories:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (editMode) {
        await api.patch(`/categories/${selectedCategory.id}/`, formData);
      } else {
        await api.post('/categories/', formData);
      }
      
      setShowModal(false);
      resetForm();
      fetchCategories();
    } catch (err) {
      setError(err.response?.data?.name?.[0] || 'Error saving category');
    }
  };

  const handleEdit = (category) => {
    setSelectedCategory(category);
    setFormData({
      name: category.name,
      description: category.description || '',
      is_active: category.is_active,
    });
    setEditMode(true);
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        await api.delete(`/categories/${id}/`);
        fetchCategories();
      } catch (err) {
        alert('Error deleting category. It may have associated products.');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      is_active: true,
    });
    setEditMode(false);
    setSelectedCategory(null);
    setError('');
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="categories-container">
      <PageHeader title="Category Management" subtitle="Organize products by categories">
        {canModify && (
          <button onClick={() => { resetForm(); setShowModal(true); }} className="btn-primary">
            + Add Category
          </button>
        )}
      </PageHeader>

      <div className="categories-grid">
        {categories.map((category) => (
          <div key={category.id} className="category-card">
            <div className="category-info">
              <h3>{category.name}</h3>
              <p className="category-description">
                {category.description || 'No description'}
              </p>
              <div className="category-meta">
                <span className="product-count">
                  {category.product_count} {category.product_count === 1 ? 'product' : 'products'}
                </span>
                {!category.is_active && (
                  <span className="inactive-badge">Inactive</span>
                )}
              </div>
            </div>

            {canModify && (
              <div className="category-actions">
                <button onClick={() => handleEdit(category)} className="btn-edit">
                  Edit
                </button>
                <button onClick={() => handleDelete(category.id)} className="btn-delete">
                  Delete
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {categories.length === 0 && (
        <div className="no-categories">
          <p>No categories found</p>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>{editMode ? 'Edit Category' : 'Add New Category'}</h3>
              <button onClick={() => { setShowModal(false); resetForm(); }} className="close-btn">
                ×
              </button>
            </div>
            
            {error && <div className="error-message">{error}</div>}
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Category Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows="4"
                />
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleChange}
                  />
                  Active Category
                </label>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => { setShowModal(false); resetForm(); }} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editMode ? 'Update Category' : 'Create Category'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Categories;