import React, { useEffect } from "react";
import JsBarcode from "jsbarcode";
import "./ThermalReceipt.css";

const ThermalReceipt = ({ saleData, onClose, autoPrint = false }) => {
  useEffect(() => {
    if (autoPrint) {
      const timer = setTimeout(() => handlePrint(), 500);
      return () => clearTimeout(timer);
    }
  }, [autoPrint]);

  const handlePrint = () => {
    window.print();
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString("en-GB", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  return (
    <>
      {/* Screen Preview with Modal */}
      <div className="receipt-modal-overlay no-print" onClick={onClose}>
        <div className="receipt-modal" onClick={(e) => e.stopPropagation()}>
          <div className="receipt-modal-header">
            <h3>Receipt Preview</h3>
            <button onClick={onClose} className="close-btn">×</button>
          </div>

          <div className="receipt-preview-container">
            <div className="thermal-receipt-preview">
              <ThermalReceiptContent saleData={saleData} formatDate={formatDate} />
            </div>
          </div>

          <div className="receipt-modal-actions">
            <button onClick={onClose} className="btn-secondary">Close</button>
            <button onClick={handlePrint} className="btn-primary">🖨️ Print Receipt</button>
          </div>
        </div>
      </div>

      {/* Print View */}
      <div className="print-only">
        <ThermalReceiptContent saleData={saleData} formatDate={formatDate} />
      </div>
    </>
  );
};

const ThermalReceiptContent = ({ saleData, formatDate }) => {

  useEffect(() => {
    if (saleData?.invoice_number) {
      JsBarcode("#barcode", saleData.invoice_number, {
        format: "CODE128",
        displayValue: true,
        fontSize: 14,
        width: 2,
        height: 50,
        margin: 2,
      });
    }
  }, [saleData]);

  return (
    <div className="thermal-receipt">

      {/* Header */}
      <div className="receipt-header">
        <h1 className="store-name">FEEDSHUB</h1>
        <p className="store-address">Mamboleo Market - Kisumu, Kenya</p>
        <p className="store-contact">Tel: +254 712 345 678</p>
      </div>

      <div className="receipt-divider-double">================================</div>

      {/* Sale Info */}
      <div className="receipt-info">
        <div className="receipt-row">
          <span>Invoice:</span> <span className="receipt-value">{saleData.invoice_number}</span>
        </div>
        <div className="receipt-row">
          <span>Date:</span> <span className="receipt-value">{formatDate(saleData.created_at)}</span>
        </div>
        {saleData.customer_name && (
          <div className="receipt-row">
            <span>Customer:</span>
            <span className="receipt-value">{saleData.customer_name}</span>
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="receipt-items-header">
        <span className="col-item">ITEM</span>
        <span className="col-qty">QTY</span>
        <span className="col-price">PRICE</span>
        <span className="col-total">TOTAL</span>
      </div>

      <div className="receipt-divider-dashed">----------------------------------------</div>

      {/* Items List */}
      {saleData.items.map((item, index) => (
        <div key={index} className="receipt-item-line">
          <span className="col-item">{item.product_name}</span>
          <span className="col-qty">{item.quantity}</span>
          <span className="col-price">{parseFloat(item.unit_price).toFixed(2)}</span>
          <span className="col-total">{parseFloat(item.subtotal).toFixed(2)}</span>
        </div>
      ))}

      <div className="receipt-divider-double">================================</div>

      {/* Totals */}
      <div className="receipt-totals">
        <div className="receipt-total-row">
          <span>Subtotal:</span>
          <span>KSh {parseFloat(saleData.subtotal).toFixed(2)}</span>
        </div>

        {saleData.discount_amount > 0 && (
          <div className="receipt-total-row">
            <span>Discount:</span>
            <span>-KSh {parseFloat(saleData.discount_amount).toFixed(2)}</span>
          </div>
        )}

        {saleData.tax_amount > 0 && (
          <div className="receipt-total-row">
            <span>Tax:</span>
            <span>KSh {parseFloat(saleData.tax_amount).toFixed(2)}</span>
          </div>
        )}

        <div className="receipt-divider-dashed"></div>

        <div className="receipt-total-row receipt-grand-total">
          <span>TOTAL:</span>
          <span>KSh {parseFloat(saleData.total).toFixed(2)}</span>
        </div>
      </div>

      {/* Payment Info */}
      <div className="receipt-payment">
        <div className="receipt-total-row">
          <span>Payment:</span>
          <span className="payment-method">{saleData.payment_method}</span>
        </div>
        <div className="receipt-total-row">
          <span>Paid:</span>
          <span>KSh {parseFloat(saleData.amount_paid).toFixed(2)}</span>
        </div>
        <div className="receipt-total-row">
          <span>Change:</span>
          <span>KSh {parseFloat(saleData.change_amount).toFixed(2)}</span>
        </div>
      </div>

      {/* Footer */}
      <div className="receipt-footer">
        <div className="receipt-row">
          <span>Cashier:</span>
          <span className="receipt-value">{saleData.cashier_name}</span>
        </div>

        <div className="receipt-barcode">
          <svg id="barcode"></svg>
        </div>

        <p className="receipt-thank-you">Thank You for Your Purchase!</p>
        <p className="receipt-footer-text">Powered by FeedsHub POS</p>
      </div>
    </div>
  );
};

export default ThermalReceipt;
