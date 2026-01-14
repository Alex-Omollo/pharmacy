import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import api from '../services/api';
import PageHeader from '../components/PageHeader';
import './Reports.css';

const COLORS = ['#1B5E4C', '#0D3D30', '#667eea', '#764ba2', '#43e97b', '#fa709a'];

const Reports = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });
  
  // Data states
  const [dashboardStats, setDashboardStats] = useState(null);
  const [salesReport, setSalesReport] = useState(null);
  const [medicinesReport, setMedicinesReport] = useState(null);
  const [cashierReport, setCashierReport] = useState(null);
  const [inventoryReport, setInventoryReport] = useState(null);
  const [expiryReport, setExpiryReport] = useState(null);
  const [prescriptionReport, setPrescriptionReport] = useState(null);
  const [controlledDrugsReport, setControlledDrugsReport] = useState(null);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line
  }, [activeTab, dateRange]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'dashboard') {
        const res = await api.get('/reports/dashboard/');
        setDashboardStats(res.data);
      } else if (activeTab === 'sales') {
        const res = await api.get(`/reports/sales/?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}&period=daily`);
        setSalesReport(res.data);
      } else if (activeTab === 'medicines') {
        const res = await api.get(`/reports/medicines/?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`);
        setMedicinesReport(res.data);
      } else if (activeTab === 'cashiers') {
        const res = await api.get(`/reports/cashiers/?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`);
        setCashierReport(res.data);
      } else if (activeTab === 'inventory') {
        const res = await api.get('/reports/inventory/');
        setInventoryReport(res.data);
      } else if (activeTab === 'expiry') {
        const res = await api.get('/reports/expiry/');
        setExpiryReport(res.data);
      } else if (activeTab === 'prescriptions') {
        const res = await api.get(`/reports/prescriptions/?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`);
        setPrescriptionReport(res.data);
      } else if (activeTab === 'controlled-drugs') {
        const res = await api.get(`/reports/controlled-drugs/?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`);
        setControlledDrugsReport(res.data);
      }
    } catch (err) {
      console.error('Error fetching report data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async (reportType) => {
    try {
      const response = await api.get(`/reports/export/${reportType}/?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${reportType}_report_${dateRange.start_date}_${dateRange.end_date}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error exporting CSV:', err);
    }
  };

  if (loading && !dashboardStats && !salesReport) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="reports-container">
      <PageHeader 
        title="📊 Reports & Analytics" 
        subtitle="Pharmacy performance, inventory, and compliance reports"
      />

      <div className="tabs">
        <button
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={activeTab === 'sales' ? 'active' : ''}
          onClick={() => setActiveTab('sales')}
        >
          Sales
        </button>
        <button
          className={activeTab === 'medicines' ? 'active' : ''}
          onClick={() => setActiveTab('medicines')}
        >
          Medicines
        </button>
        <button
          className={activeTab === 'cashiers' ? 'active' : ''}
          onClick={() => setActiveTab('cashiers')}
        >
          Dispensers
        </button>
        <button
          className={activeTab === 'inventory' ? 'active' : ''}
          onClick={() => setActiveTab('inventory')}
        >
          Inventory
        </button>
        <button
          className={activeTab === 'expiry' ? 'active' : ''}
          onClick={() => setActiveTab('expiry')}
        >
          Expiry
        </button>
        <button
          className={activeTab === 'prescriptions' ? 'active' : ''}
          onClick={() => setActiveTab('prescriptions')}
        >
          Prescriptions
        </button>
        <button
          className={activeTab === 'controlled-drugs' ? 'active' : ''}
          onClick={() => setActiveTab('controlled-drugs')}
        >
          Controlled Drugs
        </button>
      </div>

      {activeTab !== 'dashboard' && activeTab !== 'inventory' && activeTab !== 'expiry' && (
        <div className="date-filter">
          <div className="filter-group">
            <label>Start Date:</label>
            <input
              type="date"
              value={dateRange.start_date}
              onChange={(e) => setDateRange({...dateRange, start_date: e.target.value})}
            />
          </div>
          <div className="filter-group">
            <label>End Date:</label>
            <input
              type="date"
              value={dateRange.end_date}
              onChange={(e) => setDateRange({...dateRange, end_date: e.target.value})}
            />
          </div>
          <button onClick={() => handleExportCSV(activeTab)} className="btn-export">
            📥 Export CSV
          </button>
        </div>
      )}

      <div className="tab-content">
        {/* DASHBOARD TAB */}
        {activeTab === 'dashboard' && dashboardStats && (
          <div className="dashboard-tab">
            <div className="stats-grid">
              <div className="stat-card">
                <h3>{dashboardStats.today.sales}</h3>
                <p>Sales Today</p>
                <span className="amount">KSh {parseFloat(dashboardStats.today.revenue).toFixed(2)}</span>
              </div>
              <div className="stat-card">
                <h3>{dashboardStats.this_week.sales}</h3>
                <p>Sales This Week</p>
                <span className="amount">KSh {parseFloat(dashboardStats.this_week.revenue).toFixed(2)}</span>
              </div>
              <div className="stat-card">
                <h3>{dashboardStats.this_month.sales}</h3>
                <p>Sales This Month</p>
                <span className="amount">KSh {parseFloat(dashboardStats.this_month.revenue).toFixed(2)}</span>
              </div>
              <div className="stat-card">
                <h3>{dashboardStats.total_medicines}</h3>
                <p>Active Medicines</p>
              </div>
              <div className="stat-card alert">
                <h3>{dashboardStats.expiring_soon}</h3>
                <p>Expiring Soon (90 days)</p>
              </div>
              <div className="stat-card danger">
                <h3>{dashboardStats.expired_batches}</h3>
                <p>Expired Batches</p>
              </div>
            </div>

            {dashboardStats.sales_trend && dashboardStats.sales_trend.length > 0 && (
              <div className="chart-container">
                <h3>Sales Trend (Last 7 Days)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={dashboardStats.sales_trend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#1B5E4C" name="Revenue (KSh)" />
                    <Line yAxisId="right" type="monotone" dataKey="count" stroke="#667eea" name="Sales Count" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {dashboardStats.prescription_stats && (
              <div className="chart-container">
                <h3>Prescription vs OTC Sales</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Prescription', value: dashboardStats.prescription_stats.prescription_count },
                        { name: 'OTC', value: dashboardStats.prescription_stats.otc_count }
                      ]}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label
                    >
                      <Cell fill="#DC2626" />
                      <Cell fill="#1B5E4C" />
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* SALES TAB */}
        {activeTab === 'sales' && salesReport && (
          <div className="sales-tab">
            <div className="stats-summary">
              <div className="summary-card">
                <h4>Total Sales</h4>
                <p className="big-number">{salesReport.overall_stats.total_sales || 0}</p>
              </div>
              <div className="summary-card">
                <h4>Total Revenue</h4>
                <p className="big-number">KSh {parseFloat(salesReport.overall_stats.total_revenue || 0).toFixed(2)}</p>
              </div>
              <div className="summary-card">
                <h4>Average Sale</h4>
                <p className="big-number">KSh {parseFloat(salesReport.overall_stats.average_sale || 0).toFixed(2)}</p>
              </div>
              <div className="summary-card">
                <h4>Total Discount</h4>
                <p className="big-number">KSh {parseFloat(salesReport.overall_stats.total_discount || 0).toFixed(2)}</p>
              </div>
            </div>

            {salesReport.sales_by_period && salesReport.sales_by_period.length > 0 && (
              <div className="chart-container">
                <h3>Sales by Period</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={salesReport.sales_by_period}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="total_revenue" fill="#1B5E4C" name="Revenue (KSh)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {salesReport.payment_breakdown && salesReport.payment_breakdown.length > 0 && (
              <div className="chart-container">
                <h3>Payment Methods</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={salesReport.payment_breakdown}
                      dataKey="total"
                      nameKey="payment_method"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label
                    >
                      {salesReport.payment_breakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* MEDICINES TAB */}
        {activeTab === 'medicines' && medicinesReport && (
          <div className="medicines-tab">
            <h3>Top Selling Medicines</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Medicine (Brand)</th>
                  <th>Generic Name</th>
                  <th>SKU</th>
                  <th>Qty Dispensed</th>
                  <th>Revenue</th>
                  <th>Profit</th>
                  <th>Margin</th>
                </tr>
              </thead>
              <tbody>
                {medicinesReport.top_medicines && medicinesReport.top_medicines.map((medicine, index) => (
                  <tr key={index}>
                    <td>{medicine.medicine_brand_name}</td>
                    <td>{medicine.medicine_generic_name}</td>
                    <td>{medicine.medicine_sku}</td>
                    <td>{medicine.total_quantity}</td>
                    <td>KSh {parseFloat(medicine.total_revenue).toFixed(2)}</td>
                    <td className={medicine.profit >= 0 ? 'positive' : 'negative'}>
                      KSh {parseFloat(medicine.profit || 0).toFixed(2)}
                    </td>
                    <td>{medicine.profit_margin}%</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {medicinesReport.category_breakdown && medicinesReport.category_breakdown.length > 0 && (
              <div className="chart-container">
                <h3>Sales by Category</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={medicinesReport.category_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category_name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="total_revenue" fill="#1B5E4C" name="Revenue (KSh)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* DISPENSERS/CASHIERS TAB */}
        {activeTab === 'cashiers' && cashierReport && (
          <div className="cashiers-tab">
            <h3>Dispenser Performance</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Dispenser</th>
                  <th>Sales Count</th>
                  <th>Total Revenue</th>
                  <th>Avg Sale</th>
                  <th>Items Dispensed</th>
                  <th>Prescription Sales</th>
                </tr>
              </thead>
              <tbody>
                {cashierReport.dispenser_performance && cashierReport.dispenser_performance.map((dispenser, index) => (
                  <tr key={index}>
                    <td>{dispenser.dispenser_username}</td>
                    <td>{dispenser.total_sales}</td>
                    <td>KSh {parseFloat(dispenser.total_revenue).toFixed(2)}</td>
                    <td>KSh {parseFloat(dispenser.average_sale || 0).toFixed(2)}</td>
                    <td>{dispenser.total_items_dispensed}</td>
                    <td>{dispenser.prescription_sales_count || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* INVENTORY TAB */}
        {activeTab === 'inventory' && inventoryReport && (
          <div className="inventory-tab">
            <div className="stats-summary">
              <div className="summary-card">
                <h4>Total Stock Value</h4>
                <p className="big-number">KSh {parseFloat(inventoryReport.total_stock_value).toFixed(2)}</p>
              </div>
              <div className="summary-card">
                <h4>In Stock</h4>
                <p className="big-number">{inventoryReport.stock_status.in_stock}</p>
              </div>
              <div className="summary-card">
                <h4>Low Stock</h4>
                <p className="big-number warning">{inventoryReport.stock_status.low_stock}</p>
              </div>
              <div className="summary-card">
                <h4>Out of Stock</h4>
                <p className="big-number danger">{inventoryReport.stock_status.out_of_stock}</p>
              </div>
            </div>

            <h3>Top Value Items</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>SKU</th>
                  <th>Batches</th>
                  <th>Total Qty</th>
                  <th>Avg Cost</th>
                  <th>Total Value</th>
                </tr>
              </thead>
              <tbody>
                {inventoryReport.top_value_items && inventoryReport.top_value_items.map((item, index) => (
                  <tr key={index}>
                    <td>{item.brand_name}</td>
                    <td>{item.sku}</td>
                    <td>{item.batch_count}</td>
                    <td>{item.total_stock}</td>
                    <td>KSh {parseFloat(item.avg_cost).toFixed(2)}</td>
                    <td>KSh {parseFloat(item.stock_value).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3 style={{marginTop: '30px'}}>Fast Moving Medicines (Last 30 Days)</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>SKU</th>
                  <th>Qty Dispensed</th>
                  <th>Days in Stock</th>
                  <th>Turnover Rate</th>
                </tr>
              </thead>
              <tbody>
                {inventoryReport.fast_moving_medicines && inventoryReport.fast_moving_medicines.map((item, index) => (
                  <tr key={index}>
                    <td>{item.medicine_brand_name}</td>
                    <td>{item.medicine_sku}</td>
                    <td>{item.total_dispensed}</td>
                    <td>{item.days_in_period}</td>
                    <td>{item.turnover_rate}x</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* EXPIRY TAB */}
        {activeTab === 'expiry' && expiryReport && (
          <div className="expiry-tab">
            <div className="stats-summary">
              <div className="summary-card danger">
                <h4>Expired Batches</h4>
                <p className="big-number">{expiryReport.expired_count}</p>
                <span className="amount">Value: KSh {parseFloat(expiryReport.expired_value).toFixed(2)}</span>
              </div>
              <div className="summary-card warning">
                <h4>Expiring in 30 Days</h4>
                <p className="big-number">{expiryReport.expiring_30_days}</p>
                <span className="amount">Value: KSh {parseFloat(expiryReport.expiring_30_value).toFixed(2)}</span>
              </div>
              <div className="summary-card warning">
                <h4>Expiring in 90 Days</h4>
                <p className="big-number">{expiryReport.expiring_90_days}</p>
                <span className="amount">Value: KSh {parseFloat(expiryReport.expiring_90_value).toFixed(2)}</span>
              </div>
            </div>

            <h3>⚠️ Near Expiry Batches (Next 90 Days)</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Batch Number</th>
                  <th>Expiry Date</th>
                  <th>Days Until Expiry</th>
                  <th>Quantity</th>
                  <th>Value</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {expiryReport.near_expiry_batches && expiryReport.near_expiry_batches.map((batch, index) => (
                  <tr key={index} className={batch.days_until_expiry < 30 ? 'danger-row' : 'warning-row'}>
                    <td>{batch.medicine_name}</td>
                    <td>{batch.batch_number}</td>
                    <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
                    <td>{batch.days_until_expiry} days</td>
                    <td>{batch.quantity}</td>
                    <td>KSh {parseFloat(batch.value).toFixed(2)}</td>
                    <td>
                      <span className={`badge ${batch.days_until_expiry < 30 ? 'badge-danger' : 'badge-warning'}`}>
                        {batch.days_until_expiry < 30 ? 'Urgent' : 'Warning'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3 style={{marginTop: '30px'}}>❌ Expired Batches</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Batch Number</th>
                  <th>Expiry Date</th>
                  <th>Days Expired</th>
                  <th>Quantity</th>
                  <th>Value Lost</th>
                </tr>
              </thead>
              <tbody>
                {expiryReport.expired_batches && expiryReport.expired_batches.map((batch, index) => (
                  <tr key={index} className="expired-row">
                    <td>{batch.medicine_name}</td>
                    <td>{batch.batch_number}</td>
                    <td>{new Date(batch.expiry_date).toLocaleDateString()}</td>
                    <td>{Math.abs(batch.days_expired)} days</td>
                    <td>{batch.quantity}</td>
                    <td>KSh {parseFloat(batch.value).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* PRESCRIPTIONS TAB */}
        {activeTab === 'prescriptions' && prescriptionReport && (
          <div className="prescriptions-tab">
            <div className="stats-summary">
              <div className="summary-card">
                <h4>Total Prescription Sales</h4>
                <p className="big-number">{prescriptionReport.total_prescription_sales}</p>
              </div>
              <div className="summary-card">
                <h4>OTC Sales</h4>
                <p className="big-number">{prescriptionReport.total_otc_sales}</p>
              </div>
              <div className="summary-card">
                <h4>Prescription Compliance</h4>
                <p className="big-number">{prescriptionReport.compliance_rate}%</p>
              </div>
            </div>

            <h3>℞ Prescription Medicines Dispensed</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Invoice #</th>
                  <th>Medicine</th>
                  <th>Quantity</th>
                  <th>Prescription Seen</th>
                  <th>Prescription #</th>
                  <th>Dispenser</th>
                </tr>
              </thead>
              <tbody>
                {prescriptionReport.prescription_sales && prescriptionReport.prescription_sales.map((sale, index) => (
                  <tr key={index}>
                    <td>{new Date(sale.sale_date).toLocaleDateString()}</td>
                    <td>{sale.invoice_number}</td>
                    <td>{sale.medicine_name}</td>
                    <td>{sale.quantity}</td>
                    <td>
                      <span className={`badge ${sale.prescription_seen ? 'badge-success' : 'badge-danger'}`}>
                        {sale.prescription_seen ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td>{sale.prescription_number || '-'}</td>
                    <td>{sale.dispenser_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3 style={{marginTop: '30px'}}>Top Prescription Medicines</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Times Dispensed</th>
                  <th>Total Quantity</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {prescriptionReport.top_prescription_medicines && prescriptionReport.top_prescription_medicines.map((med, index) => (
                  <tr key={index}>
                    <td>{med.medicine_name}</td>
                    <td>{med.dispense_count}</td>
                    <td>{med.total_quantity}</td>
                    <td>KSh {parseFloat(med.total_revenue).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* CONTROLLED DRUGS TAB */}
        {activeTab === 'controlled-drugs' && controlledDrugsReport && (
          <div className="controlled-drugs-tab">
            <div className="stats-summary">
              <div className="summary-card danger">
                <h4>Controlled Drug Transactions</h4>
                <p className="big-number">{controlledDrugsReport.total_transactions}</p>
              </div>
              <div className="summary-card">
                <h4>Unique Medicines</h4>
                <p className="big-number">{controlledDrugsReport.unique_medicines}</p>
              </div>
              <div className="summary-card">
                <h4>Total Quantity Dispensed</h4>
                <p className="big-number">{controlledDrugsReport.total_quantity}</p>
              </div>
            </div>

            <h3>⚠️ Controlled Drug Movement Log</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Invoice #</th>
                  <th>Medicine</th>
                  <th>Batch Number</th>
                  <th>Quantity</th>
                  <th>Prescription #</th>
                  <th>Dispenser</th>
                  <th>Customer</th>
                </tr>
              </thead>
              <tbody>
                {controlledDrugsReport.transactions && controlledDrugsReport.transactions.map((transaction, index) => (
                  <tr key={index} className="controlled-row">
                    <td>{new Date(transaction.date_time).toLocaleString()}</td>
                    <td>{transaction.invoice_number}</td>
                    <td>
                      <strong>{transaction.medicine_name}</strong>
                      <br />
                      <small style={{color: '#666'}}>{transaction.generic_name}</small>
                    </td>
                    <td>{transaction.batch_number}</td>
                    <td>{transaction.quantity}</td>
                    <td>{transaction.prescription_number || '-'}</td>
                    <td>{transaction.dispenser_name}</td>
                    <td>{transaction.customer_name || 'Walk-in'}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3 style={{marginTop: '30px'}}>Controlled Drug Summary</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Times Dispensed</th>
                  <th>Total Quantity</th>
                  <th>Different Batches Used</th>
                  <th>Primary Dispenser</th>
                </tr>
              </thead>
              <tbody>
                {controlledDrugsReport.summary_by_medicine && controlledDrugsReport.summary_by_medicine.map((med, index) => (
                  <tr key={index}>
                    <td>{med.medicine_name}</td>
                    <td>{med.dispense_count}</td>
                    <td>{med.total_quantity}</td>
                    <td>{med.batch_count}</td>
                    <td>{med.primary_dispenser}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Reports;