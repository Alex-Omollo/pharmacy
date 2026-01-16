import React, { useState, useEffect } from 'react';
import { AlertTriangle, Calendar, XCircle, CheckCircle, FileText, Download } from 'lucide-react';
import PageHeader from '../components/PageHeader';

const ExpiryManagement = () => {
  const [activeTab, setActiveTab] = useState('near-expiry');
  const [nearExpiryBatches, setNearExpiryBatches] = useState([]);
  const [expiredBatches, setExpiredBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterDays, setFilterDays] = useState(90);
  const [showWriteOffModal, setShowWriteOffModal] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [writeOffReason, setWriteOffReason] = useState('');
  const [stats, setStats] = useState({
    nearExpiryCount: 0,
    nearExpiryValue: 0,
    expiredCount: 0,
    expiredValue: 0
  });

  // Mock API calls - replace with actual API endpoints
  const fetchNearExpiryBatches = async () => {
    // Mock data
    setNearExpiryBatches([
      {
        id: 1,
        medicine_name: 'Paracetamol 500mg',
        batch_number: 'BAT001',
        expiry_date: '2026-03-15',
        days_until_expiry: 58,
        quantity: 150,
        selling_price: 50,
        supplier: 'MediSupply Ltd'
      },
      {
        id: 2,
        medicine_name: 'Amoxicillin 250mg',
        batch_number: 'BAT002',
        expiry_date: '2026-02-28',
        days_until_expiry: 43,
        quantity: 75,
        selling_price: 120,
        supplier: 'PharmaCorp'
      },
      {
        id: 3,
        medicine_name: 'Ibuprofen 400mg',
        batch_number: 'BAT003',
        expiry_date: '2026-04-20',
        days_until_expiry: 94,
        quantity: 200,
        selling_price: 80,
        supplier: 'HealthPlus'
      }
    ]);
  };

  const fetchExpiredBatches = async () => {
    // Mock data
    setExpiredBatches([
      {
        id: 4,
        medicine_name: 'Cough Syrup 100ml',
        batch_number: 'BAT004',
        expiry_date: '2025-12-31',
        days_expired: 16,
        quantity: 30,
        selling_price: 250,
        purchase_price: 150,
        supplier: 'MediSupply Ltd'
      },
      {
        id: 5,
        medicine_name: 'Vitamin C 1000mg',
        batch_number: 'BAT005',
        expiry_date: '2025-11-15',
        days_expired: 62,
        quantity: 45,
        selling_price: 180,
        purchase_price: 100,
        supplier: 'VitaHealth'
      }
    ]);
  };

  const calculateStats = () => {
    const nearExpiryValue = nearExpiryBatches.reduce(
      (sum, batch) => sum + (batch.quantity * batch.selling_price),
      0
    );
    const expiredValue = expiredBatches.reduce(
      (sum, batch) => sum + (batch.quantity * (batch.purchase_price || batch.selling_price)),
      0
    );

    setStats({
      nearExpiryCount: nearExpiryBatches.length,
      nearExpiryValue,
      expiredCount: expiredBatches.length,
      expiredValue
    });
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      if (activeTab === 'near-expiry') {
        await fetchNearExpiryBatches();
      } else {
        await fetchExpiredBatches();
      }
      setLoading(false);
    };
    loadData();
  }, [activeTab, filterDays]);

  useEffect(() => {
    calculateStats();
  }, [nearExpiryBatches, expiredBatches]);

  const handleWriteOff = (batch) => {
    setSelectedBatch(batch);
    setShowWriteOffModal(true);
  };

  const confirmWriteOff = async () => {
    if (!writeOffReason.trim()) {
      alert('Please provide a reason for write-off');
      return;
    }

    // Mock API call
    console.log('Writing off batch:', selectedBatch.id, 'Reason:', writeOffReason);
    
    // Remove from expired batches
    setExpiredBatches(prev => prev.filter(b => b.id !== selectedBatch.id));
    
    setShowWriteOffModal(false);
    setSelectedBatch(null);
    setWriteOffReason('');
    
    alert('Batch written off successfully');
  };

  const exportReport = () => {
    const data = activeTab === 'near-expiry' ? nearExpiryBatches : expiredBatches;
    console.log('Exporting report:', data);
    alert('Export functionality would generate CSV/PDF here');
  };

  const getPriorityClass = (days) => {
    if (days <= 30) return 'critical';
    if (days <= 60) return 'high';
    return 'medium';
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      {/* <div className='expiry-container'>
        <PageHeader
          title="Expiry Management"
          subtitle="Monitor and manage medicine expiry dates"
        /> */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <Calendar size={32} color="#DC2626" />
          <div>
            <h1 style={styles.title}>⏰ Expiry Management</h1>
            <p style={styles.subtitle}>Monitor and manage medicine expiry dates</p>
          </div>
        </div>
        <button onClick={exportReport} style={styles.exportBtn}>
          <Download size={16} />
          Export Report
        </button>
      </div>

      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        <div style={{...styles.statCard, ...styles.warningCard}}>
          <div style={styles.statIcon}>
            <AlertTriangle size={24} color="#FACC15" />
          </div>
          <div>
            <p style={styles.statLabel}>Near Expiry (90 days)</p>
            <h3 style={styles.statValue}>{stats.nearExpiryCount} Batches</h3>
            <p style={styles.statAmount}>KSh {stats.nearExpiryValue.toFixed(2)}</p>
          </div>
        </div>

        <div style={{...styles.statCard, ...styles.dangerCard}}>
          <div style={styles.statIcon}>
            <XCircle size={24} color="#DC2626" />
          </div>
          <div>
            <p style={styles.statLabel}>Expired Batches</p>
            <h3 style={styles.statValue}>{stats.expiredCount} Batches</h3>
            <p style={styles.statAmount}>KSh {stats.expiredValue.toFixed(2)}</p>
          </div>
        </div>

        <div style={{...styles.statCard, ...styles.infoCard}}>
          <div style={styles.statIcon}>
            <CheckCircle size={24} color="#1B5E4C" />
          </div>
          <div>
            <p style={styles.statLabel}>Action Required</p>
            <h3 style={styles.statValue}>
              {stats.nearExpiryCount + stats.expiredCount}
            </h3>
            <p style={styles.statAmount}>Total Items</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={styles.tabs}>
        <button
          onClick={() => setActiveTab('near-expiry')}
          style={{
            ...styles.tab,
            ...(activeTab === 'near-expiry' ? styles.activeTab : {})
          }}
        >
          <AlertTriangle size={18} />
          Near Expiry ({stats.nearExpiryCount})
        </button>
        <button
          onClick={() => setActiveTab('expired')}
          style={{
            ...styles.tab,
            ...(activeTab === 'expired' ? styles.activeTab : {})
          }}
        >
          <XCircle size={18} />
          Expired ({stats.expiredCount})
        </button>
      </div>

      {/* Filters */}
      {activeTab === 'near-expiry' && (
        <div style={styles.filters}>
          <label style={styles.filterLabel}>
            Days Until Expiry:
            <select
              value={filterDays}
              onChange={(e) => setFilterDays(Number(e.target.value))}
              style={styles.filterSelect}
            >
              <option value={30}>30 Days</option>
              <option value={60}>60 Days</option>
              <option value={90}>90 Days</option>
              <option value={180}>180 Days</option>
            </select>
          </label>
        </div>
      )}

      {/* Content */}
      <div style={styles.content}>
        {loading ? (
          <div style={styles.loading}>Loading...</div>
        ) : (
          <>
            {activeTab === 'near-expiry' && (
              <div style={styles.tableContainer}>
                <h3 style={styles.tableTitle}>
                  ⚠️ Batches Expiring Within {filterDays} Days
                </h3>
                {nearExpiryBatches.length === 0 ? (
                  <div style={styles.emptyState}>
                    <CheckCircle size={48} color="#1B5E4C" />
                    <p>No batches expiring soon!</p>
                  </div>
                ) : (
                  <div style={styles.tableWrapper}>
                    <table style={styles.table}>
                      <thead>
                        <tr>
                          <th style={styles.th}>Priority</th>
                          <th style={styles.th}>Medicine</th>
                          <th style={styles.th}>Batch Number</th>
                          <th style={styles.th}>Expiry Date</th>
                          <th style={styles.th}>Days Left</th>
                          <th style={styles.th}>Quantity</th>
                          <th style={styles.th}>Value</th>
                          <th style={styles.th}>Supplier</th>
                        </tr>
                      </thead>
                      <tbody>
                        {nearExpiryBatches.map((batch) => (
                          <tr key={batch.id} style={styles.tr}>
                            <td style={styles.td}>
                              <span
                                style={{
                                  ...styles.priorityBadge,
                                  ...styles[getPriorityClass(batch.days_until_expiry)]
                                }}
                              >
                                {batch.days_until_expiry <= 30 ? 'CRITICAL' :
                                 batch.days_until_expiry <= 60 ? 'HIGH' : 'MEDIUM'}
                              </span>
                            </td>
                            <td style={styles.td}>
                              <strong>{batch.medicine_name}</strong>
                            </td>
                            <td style={styles.td}>{batch.batch_number}</td>
                            <td style={styles.td}>
                              {new Date(batch.expiry_date).toLocaleDateString()}
                            </td>
                            <td style={{...styles.td, fontWeight: 'bold', color: '#856404'}}>
                              {batch.days_until_expiry} days
                            </td>
                            <td style={styles.td}>{batch.quantity}</td>
                            <td style={styles.td}>
                              KSh {(batch.quantity * batch.selling_price).toFixed(2)}
                            </td>
                            <td style={styles.td}>{batch.supplier}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'expired' && (
              <div style={styles.tableContainer}>
                <h3 style={styles.tableTitle}>❌ Expired Batches Requiring Action</h3>
                {expiredBatches.length === 0 ? (
                  <div style={styles.emptyState}>
                    <CheckCircle size={48} color="#1B5E4C" />
                    <p>No expired batches!</p>
                  </div>
                ) : (
                  <div style={styles.tableWrapper}>
                    <table style={styles.table}>
                      <thead>
                        <tr>
                          <th style={styles.th}>Medicine</th>
                          <th style={styles.th}>Batch Number</th>
                          <th style={styles.th}>Expiry Date</th>
                          <th style={styles.th}>Days Expired</th>
                          <th style={styles.th}>Quantity</th>
                          <th style={styles.th}>Lost Value</th>
                          <th style={styles.th}>Supplier</th>
                          <th style={styles.th}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {expiredBatches.map((batch) => (
                          <tr key={batch.id} style={{...styles.tr, ...styles.expiredRow}}>
                            <td style={styles.td}>
                              <strong>{batch.medicine_name}</strong>
                            </td>
                            <td style={styles.td}>{batch.batch_number}</td>
                            <td style={styles.td}>
                              {new Date(batch.expiry_date).toLocaleDateString()}
                            </td>
                            <td style={{...styles.td, color: '#DC2626', fontWeight: 'bold'}}>
                              {batch.days_expired} days
                            </td>
                            <td style={styles.td}>{batch.quantity}</td>
                            <td style={{...styles.td, color: '#DC2626'}}>
                              KSh {(batch.quantity * (batch.purchase_price || batch.selling_price)).toFixed(2)}
                            </td>
                            <td style={styles.td}>{batch.supplier}</td>
                            <td style={styles.td}>
                              <button
                                onClick={() => handleWriteOff(batch)}
                                style={styles.writeOffBtn}
                              >
                                <FileText size={14} />
                                Write Off
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Write-Off Modal */}
      {showWriteOffModal && selectedBatch && (
        <div style={styles.modalOverlay} onClick={() => setShowWriteOffModal(false)}>
          <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h3 style={styles.modalTitle}>
                <XCircle size={24} color="#DC2626" />
                Write Off Expired Batch
              </h3>
              <button
                onClick={() => setShowWriteOffModal(false)}
                style={styles.closeBtn}
              >
                ×
              </button>
            </div>

            <div style={styles.modalBody}>
              <div style={styles.batchInfo}>
                <p><strong>Medicine:</strong> {selectedBatch.medicine_name}</p>
                <p><strong>Batch Number:</strong> {selectedBatch.batch_number}</p>
                <p><strong>Expiry Date:</strong> {new Date(selectedBatch.expiry_date).toLocaleDateString()}</p>
                <p><strong>Quantity:</strong> {selectedBatch.quantity}</p>
                <p><strong>Value Lost:</strong> KSh {(selectedBatch.quantity * (selectedBatch.purchase_price || selectedBatch.selling_price)).toFixed(2)}</p>
              </div>

              <div style={styles.warningBox}>
                <AlertTriangle size={20} color="#856404" />
                <div>
                  <strong>Warning:</strong> This action cannot be undone.
                  The batch will be marked as written off and removed from inventory.
                </div>
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>
                  Reason for Write-Off *
                </label>
                <textarea
                  value={writeOffReason}
                  onChange={(e) => setWriteOffReason(e.target.value)}
                  placeholder="Enter detailed reason for writing off this batch..."
                  rows={4}
                  style={styles.textarea}
                  required
                />
              </div>
            </div>

            <div style={styles.modalFooter}>
              <button
                onClick={() => setShowWriteOffModal(false)}
                style={styles.cancelBtn}
              >
                Cancel
              </button>
              <button
                onClick={confirmWriteOff}
                style={styles.confirmBtn}
                disabled={!writeOffReason.trim()}
              >
                Confirm Write-Off
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: '20px',
    maxWidth: '1400px',
    margin: '0 auto',
    backgroundColor: '#F5F1E8',
    minHeight: '100vh'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px',
    padding: '20px',
    backgroundColor: '#FFFFFF',
    borderRadius: '10px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '15px'
  },
  title: {
    margin: 0,
    color: '#1B5E4C',
    fontSize: '28px'
  },
  subtitle: {
    margin: '5px 0 0 0',
    color: '#666',
    fontSize: '14px'
  },
  exportBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 20px',
    backgroundColor: '#1B5E4C',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600'
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '20px',
    marginBottom: '30px'
  },
  statCard: {
    backgroundColor: '#FFFFFF',
    padding: '20px',
    borderRadius: '10px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    display: 'flex',
    gap: '15px',
    alignItems: 'center'
  },
  warningCard: {
    borderLeft: '4px solid #FACC15'
  },
  dangerCard: {
    borderLeft: '4px solid #DC2626'
  },
  infoCard: {
    borderLeft: '4px solid #1B5E4C'
  },
  statIcon: {
    width: '50px',
    height: '50px',
    borderRadius: '10px',
    backgroundColor: '#F5F1E8',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  statLabel: {
    margin: 0,
    fontSize: '13px',
    color: '#666',
    fontWeight: '500'
  },
  statValue: {
    margin: '5px 0',
    fontSize: '24px',
    color: '#1B5E4C',
    fontWeight: 'bold'
  },
  statAmount: {
    margin: 0,
    fontSize: '14px',
    color: '#0D3D30',
    fontWeight: '600'
  },
  tabs: {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
    backgroundColor: '#FFFFFF',
    padding: '10px',
    borderRadius: '10px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
  },
  tab: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '12px 20px',
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: '500',
    color: '#0D3D30',
    transition: 'all 0.3s'
  },
  activeTab: {
    backgroundColor: 'linear-gradient(135deg, #1B5E4C 0%, #0D3D30 100%)',
    background: 'linear-gradient(135deg, #1B5E4C 0%, #0D3D30 100%)',
    color: '#FFFFFF'
  },
  filters: {
    backgroundColor: '#FFFFFF',
    padding: '15px 20px',
    borderRadius: '10px',
    marginBottom: '20px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
  },
  filterLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '14px',
    fontWeight: '500',
    color: '#0D3D30'
  },
  filterSelect: {
    padding: '8px 12px',
    border: '2px solid #1B5E4C',
    borderRadius: '5px',
    fontSize: '14px',
    marginLeft: '10px'
  },
  content: {
    backgroundColor: '#FFFFFF',
    borderRadius: '10px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden'
  },
  tableContainer: {
    padding: '20px'
  },
  tableTitle: {
    margin: '0 0 20px 0',
    color: '#1B5E4C',
    fontSize: '20px'
  },
  tableWrapper: {
    overflowX: 'auto'
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse'
  },
  th: {
    padding: '12px',
    textAlign: 'left',
    backgroundColor: '#F5F1E8',
    color: '#0D3D30',
    fontWeight: '600',
    fontSize: '14px',
    borderBottom: '2px solid #1B5E4C'
  },
  tr: {
    borderBottom: '1px solid #E0E0E0',
    transition: 'background 0.2s'
  },
  expiredRow: {
    backgroundColor: '#FFF5F5'
  },
  td: {
    padding: '12px',
    fontSize: '14px',
    color: '#333'
  },
  priorityBadge: {
    display: 'inline-block',
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: '700',
    textTransform: 'uppercase'
  },
  critical: {
    backgroundColor: '#FEE2E2',
    color: '#DC2626'
  },
  high: {
    backgroundColor: '#FEF3C7',
    color: '#92400E'
  },
  medium: {
    backgroundColor: '#DBEAFE',
    color: '#1E40AF'
  },
  writeOffBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    padding: '6px 12px',
    backgroundColor: '#DC2626',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: '600'
  },
  emptyState: {
    textAlign: 'center',
    padding: '60px 20px',
    color: '#666'
  },
  loading: {
    textAlign: 'center',
    padding: '60px 20px',
    fontSize: '18px',
    color: '#1B5E4C'
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: '10px',
    maxWidth: '600px',
    width: '90%',
    maxHeight: '90vh',
    overflow: 'auto'
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px',
    borderBottom: '2px solid #F5F1E8'
  },
  modalTitle: {
    margin: 0,
    color: '#1B5E4C',
    fontSize: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px'
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    fontSize: '30px',
    cursor: 'pointer',
    color: '#999',
    lineHeight: 1
  },
  modalBody: {
    padding: '20px'
  },
  batchInfo: {
    backgroundColor: '#F5F1E8',
    padding: '15px',
    borderRadius: '8px',
    marginBottom: '20px'
  },
  warningBox: {
    display: 'flex',
    gap: '10px',
    padding: '15px',
    backgroundColor: '#FFF3CD',
    border: '1px solid #FFC107',
    borderRadius: '8px',
    marginBottom: '20px',
    color: '#856404',
    fontSize: '14px'
  },
  formGroup: {
    marginBottom: '15px'
  },
  label: {
    display: 'block',
    marginBottom: '8px',
    color: '#0D3D30',
    fontWeight: '500',
    fontSize: '14px'
  },
  textarea: {
    width: '100%',
    padding: '10px',
    border: '2px solid #1B5E4C',
    borderRadius: '5px',
    fontSize: '14px',
    fontFamily: 'inherit',
    resize: 'vertical',
    boxSizing: 'border-box'
  },
  modalFooter: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'flex-end',
    padding: '20px',
    borderTop: '1px solid #F5F1E8'
  },
  cancelBtn: {
    padding: '10px 20px',
    backgroundColor: '#F5F1E8',
    color: '#0D3D30',
    border: '2px solid #1B5E4C',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600'
  },
  confirmBtn: {
    padding: '10px 20px',
    backgroundColor: '#DC2626',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600'
  }
};

export default ExpiryManagement;




// import React, { useState, useEffect } from 'react';
// import api from '../services/api';
// import PageHeader from '../components/PageHeader';

// const ExpiryManagement = () => {
//   const [nearExpiry, setNearExpiry] = useState([]);
//   const [expired, setExpired] = useState([]);
//   const [activeTab, setActiveTab] = useState('near-expiry');

//   useEffect(() => {
//     fetchData();
//   }, [activeTab]);

//   const fetchData = async () => {
//     if (activeTab === 'near-expiry') {
//       const response = await api.get('/expiry/near-expiry/');
//       setNearExpiry(response.data);
//     } else {
//       const response = await api.get('/expiry/expired/');
//       setExpired(response.data);
//     }
//   };

//   const handleWriteOff = async (batchId) => {
//     if (window.confirm('Write off this expired batch? This cannot be undone.')) {
//       await api.post('/expiry/write-off/', { batch_id: batchId });
//       fetchData();
//     }
//   };

//   return (
//     <div className="expiry-container">
//       <PageHeader title="⏰ Expiry Management" />

//       <div className="tabs">
//         <button
//           className={activeTab === 'near-expiry' ? 'active' : ''}
//           onClick={() => setActiveTab('near-expiry')}
//         >
//           Near Expiry
//         </button>
//         <button
//           className={activeTab === 'expired' ? 'active' : ''}
//           onClick={() => setActiveTab('expired')}
//         >
//           Expired
//         </button>
//       </div>

//       {activeTab === 'near-expiry' && (
//         <div className="expiry-table">
//           <h3>⚠️ Batches Expiring Within 3 Months</h3>
//           <table>
//             <thead>
//               <tr>
//                 <th>Medicine</th>
//                 <th>Batch Number</th>
//                 <th>Expiry Date</th>
//                 <th>Days Until Expiry</th>
//                 <th>Quantity</th>
//                 <th>Action</th>
//               </tr>
//             </thead>
//             <tbody>
//               {nearExpiry.map(batch => (
//                 <tr key={batch.id} className="warning-row">
//                   <td>{batch.medicine_name}</td>
//                   <td>{batch.batch_number}</td>
//                   <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
//                   <td>{batch.days_until_expiry} days</td>
//                   <td>{batch.quantity}</td>
//                   <td>
//                     <button className="btn-small btn-warn">Notify</button>
//                   </td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>
//       )}

//       {activeTab === 'expired' && (
//         <div className="expiry-table">
//           <h3>❌ Expired Batches</h3>
//           <table>
//             <thead>
//               <tr>
//                 <th>Medicine</th>
//                 <th>Batch Number</th>
//                 <th>Expiry Date</th>
//                 <th>Quantity</th>
//                 <th>Value</th>
//                 <th>Action</th>
//               </tr>
//             </thead>
//             <tbody>
//               {expired.map(batch => (
//                 <tr key={batch.id} className="expired-row">
//                   <td>{batch.medicine_name}</td>
//                   <td>{batch.batch_number}</td>
//                   <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
//                   <td>{batch.quantity}</td>
//                   <td>KSh {(batch.quantity * batch.selling_price).toFixed(2)}</td>
//                   <td>
//                     <button 
//                       className="btn-small btn-danger"
//                       onClick={() => handleWriteOff(batch.id)}
//                     >
//                       Write Off
//                     </button>
//                   </td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>
//       )}
//     </div>
//   );
// };

// export default ExpiryManagement;