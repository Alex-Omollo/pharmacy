import React, { useState } from 'react';
import api from '../services/api';
import './BulkUpload.css';

const BulkUpload = ({ onClose, onSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError('');
    } else {
      setError('Please select a valid CSV file');
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError('');
    setResult(null);

    const formData = new FormData();
    formData.append('csv_file', file);

    try {
      const response = await api.post('/products/bulk-upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setResult(response.data);
      
      if (response.data.errors.length === 0) {
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 2000);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error uploading file');
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    const template = `name,sku,barcode,category,description,price,cost_price,tax_rate,stock_quantity,min_stock_level
Laptop Computer,LAP001,123456789012,Electronics,High-performance laptop,999.99,750.00,16,50,10
Wireless Mouse,MOU001,123456789013,Electronics,Ergonomic wireless mouse,29.99,15.00,16,200,20`;
    
    const blob = new Blob([template], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'product_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="bulk-upload-container">
      <h3>Bulk Upload Products</h3>
      
      <div className="upload-instructions">
        <p>Upload a CSV file with product data. Download the template below to see the required format.</p>
        <button onClick={downloadTemplate} className="btn-template">
          📥 Download CSV Template
        </button>
      </div>

      <div className="file-input-container">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          disabled={uploading}
          id="csv-file"
        />
        <label htmlFor="csv-file" className="file-label">
          {file ? file.name : 'Choose CSV file...'}
        </label>
      </div>

      {error && <div className="error-message">{error}</div>}

      {result && (
        <div className={result.errors.length > 0 ? 'result-message warning' : 'result-message success'}>
          <p><strong>{result.message}</strong></p>
          <p>Created: {result.created_count} products</p>
          
          {result.errors.length > 0 && (
            <div className="error-list">
              <p><strong>Errors:</strong></p>
              <ul>
                {result.errors.map((err, index) => (
                  <li key={index}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="upload-actions">
        <button onClick={onClose} className="btn-secondary" disabled={uploading}>
          Cancel
        </button>
        <button onClick={handleUpload} className="btn-primary" disabled={!file || uploading}>
          {uploading ? 'Uploading...' : 'Upload Products'}
        </button>
      </div>
    </div>
  );
};

export default BulkUpload;