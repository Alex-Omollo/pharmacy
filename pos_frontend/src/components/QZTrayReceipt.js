import React, { useState, useEffect } from 'react';
import qz from 'qz-tray';
import './QZTrayReceipt.css';

const QZTrayReceipt = ({ saleData, onClose, autoPrint = false }) => {
  const [printers, setPrinters] = useState([]);
  const [selectedPrinter, setSelectedPrinter] = useState('');
  const [status, setStatus] = useState('Connecting...');
  const [error, setError] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  // Connect to QZ Tray on mount
  useEffect(() => {
    connectQZ();
    return () => {
      if (qz.websocket.isActive()) {
        qz.websocket.disconnect();
      }
    };
  }, []);

  // Auto-print if enabled
  useEffect(() => {
    if (autoPrint && isConnected && selectedPrinter) {
      handlePrint();
    }
  }, [autoPrint, isConnected, selectedPrinter]);

  const connectQZ = async () => {
    try {
      // Set up certificate and signature
      qz.security.setCertificatePromise((resolve, reject) => {
        fetch('https://api.feedshub.co.ke/api/qz/certificate/')
          .then(res => res.text())
          .then(resolve)
          .catch(reject);
      });

      qz.security.setSignaturePromise((toSign) => {
        return (resolve, reject) => {
          fetch(`https://api.feedshub.co.ke/api/qz/sign/?data=${toSign}`)
            .then(res => res.json())
            .then(data => resolve(data.signature))
            .catch(reject);
        };
      });

      // Connect to QZ Tray
      if (!qz.websocket.isActive()) {
        await qz.websocket.connect();
      }

      setStatus('Connected to QZ Tray');
      setIsConnected(true);

      // Get available printers
      const printerList = await qz.printers.find();
      setPrinters(printerList);

      // Auto-select first thermal printer or first printer
      const thermalPrinter = printerList.find(p => 
        p.toLowerCase().includes('thermal') || 
        p.toLowerCase().includes('pos') ||
        p.toLowerCase().includes('receipt')
      );
      setSelectedPrinter(thermalPrinter || printerList[0]);

    } catch (err) {
      setError(`Connection failed: ${err.message}`);
      setStatus('Connection failed');
      setIsConnected(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const generateReceiptText = () => {
    const line = (text) => `${text}\n`;
    const center = (text) => {
      const width = 48;
      const padding = Math.max(0, Math.floor((width - text.length) / 2));
      return line(' '.repeat(padding) + text);
    };
    const divider = () => line('='.repeat(48));
    const dashed = () => line('-'.repeat(48));

    let receipt = '\x1B\x40'; // ESC @ - Initialize printer
    receipt += '\x1B\x61\x01'; // ESC a 1 - Center align

    // Header
    receipt += line('');
    receipt += center('FEEDSHUB');
    receipt += center('Mamboleo Market - Kisumu, Kenya');
    receipt += center('Tel: +254 712 345 678');
    receipt += line('');

    receipt += '\x1B\x61\x00'; // ESC a 0 - Left align
    receipt += divider();

    // Sale Info
    receipt += line(`Invoice: ${saleData.invoice_number}`);
    receipt += line(`Date: ${formatDate(saleData.created_at)}`);
    if (saleData.customer_name) {
      receipt += line(`Customer: ${saleData.customer_name}`);
    }
    receipt += line(`Cashier: ${saleData.cashier_name}`);
    receipt += dashed();

    // Items Header
    receipt += line('ITEM                QTY   PRICE    TOTAL');
    receipt += dashed();

    // Items
    saleData.items.forEach(item => {
      const name = item.product_name.substring(0, 20).padEnd(20);
      const qty = item.quantity.toString().padStart(3);
      const price = parseFloat(item.unit_price).toFixed(2).padStart(8);
      const total = parseFloat(item.subtotal).toFixed(2).padStart(8);
      receipt += line(`${name}${qty}${price}${total}`);
    });

    receipt += divider();

    // Totals
    const subtotal = parseFloat(saleData.subtotal).toFixed(2);
    const discount = parseFloat(saleData.discount_amount).toFixed(2);
    const tax = parseFloat(saleData.tax_amount).toFixed(2);
    const total = parseFloat(saleData.total).toFixed(2);
    const paid = parseFloat(saleData.amount_paid).toFixed(2);
    const change = parseFloat(saleData.change_amount).toFixed(2);

    receipt += line(`Subtotal:${subtotal.padStart(39)}`);
    if (parseFloat(discount) > 0) {
      receipt += line(`Discount:${('-' + discount).padStart(39)}`);
    }
    if (parseFloat(tax) > 0) {
      receipt += line(`Tax:${tax.padStart(43)}`);
    }
    receipt += dashed();
    
    receipt += '\x1B\x45\x01'; // ESC E 1 - Bold on
    receipt += line(`TOTAL:${('KSh ' + total).padStart(41)}`);
    receipt += '\x1B\x45\x00'; // ESC E 0 - Bold off
    
    receipt += line('');
    receipt += line(`Payment: ${saleData.payment_method.toUpperCase()}`);
    receipt += line(`Paid:${('KSh ' + paid).padStart(42)}`);
    receipt += line(`Change:${('KSh ' + change).padStart(40)}`);

    receipt += line('');
    receipt += divider();
    receipt += '\x1B\x61\x01'; // Center align
    receipt += line('');
    receipt += center('Thank You for Your Purchase!');
    receipt += center('Powered by FeedsHub POS');
    receipt += line('');
    receipt += line('');
    receipt += line('');

    receipt += '\x1D\x56\x00'; // GS V 0 - Cut paper

    return receipt;
  };

  const handlePrint = async () => {
    if (!selectedPrinter) {
      setError('Please select a printer');
      return;
    }

    try {
      setStatus('Printing...');

      const config = qz.configs.create(selectedPrinter, {
        encoding: 'UTF-8',
        size: { width: 72, height: null }
      });

      const receiptText = generateReceiptText();

      await qz.print(config, [{
        type: 'raw',
        format: 'plain',
        data: receiptText
      }]);

      setStatus('Printed successfully!');
      
      // Auto-close after successful print
      setTimeout(() => {
        onClose();
      }, 1500);

    } catch (err) {
      setError(`Print failed: ${err.message}`);
      setStatus('Print failed');
    }
  };

  return (
    <div className="qt-overlay" onClick={onClose}>
      <div className="qt-modal" onClick={(e) => e.stopPropagation()}>
        <div className="qt-header">
          <h3>🖨️ Print Receipt</h3>
          <button onClick={onClose} className="qt-close">×</button>
        </div>

        <div className="qt-content">
          {error && <div className="qt-error">{error}</div>}

          <div className="qt-form-group">
            <label>Select Printer:</label>
            <select 
              value={selectedPrinter} 
              onChange={(e) => setSelectedPrinter(e.target.value)}
              disabled={!isConnected}
            >
              <option value="">Choose a printer...</option>
              {printers.map(printer => (
                <option key={printer} value={printer}>{printer}</option>
              ))}
            </select>
          </div>

          <div className="qt-status">
            Status: {status}
          </div>

          <div className="qt-preview-box">
            <h4>Receipt Preview</h4>
            <div className="qt-receipt-preview">
              <pre>{generateReceiptText()}</pre>
            </div>
          </div>
        </div>

        <div className="qt-actions">
          <button onClick={onClose}>Close</button>
          <button onClick={handlePrint} disabled={!isConnected || !selectedPrinter}>
            {isConnected ? '🖨️ Print' : 'Connecting...'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default QZTrayReceipt;