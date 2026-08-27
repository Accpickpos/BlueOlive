/**
 * Print Utilities
 * Functions to generate printable documents with shop branding
 */

import { getCurrentShopId } from './shopContext';
import { api } from './api';

/**
 * Format currency value
 */
function formatCurrency(value: number): string {
  return `R ${(value || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Escape a value for safe interpolation into an HTML string.
 * Used because generated HTML here is sunk via document.write(), where
 * unescaped `<script>` tags in user-controllable data would execute.
 */
function escapeHtml(value: unknown): string {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Validate that a logo URL is safe to use as an <img src> in
 * document.write()'d HTML. Only allow http(s) URLs or data:image/ URIs;
 * anything else (e.g. javascript:) is rejected.
 */
function isSafeImageUrl(value: unknown): value is string {
  if (typeof value !== 'string') return false;
  return /^https?:\/\//i.test(value) || /^data:image\//i.test(value);
}

/**
 * Get shop details including logo for printing
 */
export async function getShopForPrint(): Promise<{
  name: string;
  address: string;
  phone: string;
  logo: string | null;
} | null> {
  const shopId = getCurrentShopId();
  if (!shopId) return null;

  try {
    const response = await api.get(`/api/shops/${shopId}/`);
    const shop = response.data;
    return {
      name: shop.name || '',
      address: shop.address || '',
      phone: shop.phone || '',
      logo: shop.logo || null,
    };
  } catch (error) {
    console.error('Failed to fetch shop for print:', error);
    return null;
  }
}

/**
 * Get tenant details for printing (company info)
 */
export async function getTenantForPrint(): Promise<{
  company_name: string;
  company_address: string;
  vat_number: string;
  registration_number: string;
  phone: string;
  email: string;
} | null> {
  try {
    const response = await api.get('/api/tenants/current_tenant/');
    const tenant = response.data;
    if (!tenant || tenant.tenant) return null;
    
    return {
      company_name: tenant.company_name || '',
      company_address: tenant.company_address || '',
      vat_number: tenant.vat_number || '',
      registration_number: tenant.registration_number || '',
      phone: tenant.phone || '',
      email: tenant.email || '',
    };
  } catch (error) {
    console.error('Failed to fetch tenant for print:', error);
    return null;
  }
}

/**
 * Generate print-friendly HTML for an invoice
 */
export function generateInvoicePrintHTML(invoice: any, shop: any, tenant: any): string {
  const lineItems = invoice.line_items || [];
  const subtotal = lineItems.reduce((sum: number, item: any) => {
    const itemTotal = (item.quantity || 0) * (item.unit_price || item.selling_price || 0);
    const discount = itemTotal * ((item.discount_percentage || 0) / 100);
    return sum + itemTotal - discount;
  }, 0);
  const tax = invoice.tax_amount || 0;
  const total = invoice.total_amount || subtotal + tax;

  // Use shop logo if available, otherwise use tenant company info
  const companyName = shop?.name || tenant?.company_name || 'Company Name';
  const companyAddress = shop?.address || tenant?.company_address || '';
  const companyPhone = shop?.phone || tenant?.phone || '';
  const vatNumber = tenant?.vat_number || '';
  const regNumber = tenant?.registration_number || '';
  
  const logoUrl = isSafeImageUrl(shop?.logo) ? shop.logo : null;

  const itemsHtml = lineItems.map((item: any) => {
    const itemTotal = (item.quantity || 0) * (item.unit_price || item.selling_price || 0);
    const discountedTotal = itemTotal * (1 - (item.discount_percentage || 0) / 100);
    return `
        <tr>
          <td>${escapeHtml(item.description || item.stock_code || 'Item')}</td>
          <td class="text-center">${escapeHtml(item.quantity || 0)}</td>
          <td class="text-right">${formatCurrency(item.unit_price || item.selling_price || 0)}</td>
          <td class="text-right">${escapeHtml(item.discount_percentage || 0)}%</td>
          <td class="text-right">${formatCurrency(discountedTotal)}</td>
        </tr>
    `;
  }).join('');

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Invoice ${escapeHtml(invoice.invoice_number)}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; color: #333; }
    .invoice-container { max-width: 800px; margin: 0 auto; padding: 20px; }
    .header { display: flex; justify-content: space-between; margin-bottom: 30px; }
    .company-info { flex: 1; }
    .company-name { font-size: 24px; font-weight: bold; color: #1a1a1a; margin-bottom: 5px; }
    .company-details { font-size: 12px; color: #666; }
    .logo-container { width: 150px; height: 80px; display: flex; align-items: center; justify-content: flex-end; }
    .logo-container img { max-width: 100%; max-height: 100%; object-fit: contain; }
    .document-title { font-size: 28px; font-weight: bold; color: #333; text-align: right; margin-bottom: 5px; }
    .invoice-number { font-size: 14px; color: #666; text-align: right; }
    .details-section { display: flex; justify-content: space-between; margin-bottom: 30px; }
    .bill-to { flex: 1; }
    .invoice-details { text-align: right; }
    .label { font-weight: bold; color: #666; }
    .value { margin-bottom: 3px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th { background: #f5f5f5; padding: 10px; text-align: left; border-bottom: 2px solid #ddd; font-weight: bold; }
    td { padding: 10px; border-bottom: 1px solid #eee; }
    .text-right { text-align: right; }
    .text-center { text-align: center; }
    .totals { margin-left: auto; width: 300px; }
    .total-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
    .total-row.grand-total { font-size: 18px; font-weight: bold; border-top: 2px solid #333; border-bottom: none; }
    .footer { margin-top: 40px; text-align: center; font-size: 11px; color: #999; }
    .vat-info { margin-top: 20px; font-size: 11px; color: #666; }
    @media print {
      body { -webkit-print-color-adjust: exact; }
      .invoice-container { padding: 0; }
    }
  </style>
</head>
<body>
  <div class="invoice-container">
    <div class="header">
      <div class="company-info">
        ${logoUrl ? `
          <div class="logo-container" style="margin-bottom: 10px;">
            <img src="${escapeHtml(logoUrl)}" alt="${escapeHtml(companyName)}" />
          </div>
        ` : ''}
        <div class="company-name">${escapeHtml(companyName)}</div>
        ${companyAddress ? `<div class="company-details">${escapeHtml(companyAddress).replace(/\n/g, '<br>')}</div>` : ''}
        ${companyPhone ? `<div class="company-details">Tel: ${escapeHtml(companyPhone)}</div>` : ''}
        ${vatNumber ? `<div class="company-details">VAT Number: ${escapeHtml(vatNumber)}</div>` : ''}
        ${regNumber ? `<div class="company-details">Registration: ${escapeHtml(regNumber)}</div>` : ''}
      </div>
      <div>
        <div class="document-title">INVOICE</div>
        <div class="invoice-number">${escapeHtml(invoice.invoice_number || '')}</div>
      </div>
    </div>

    <div class="details-section">
      <div class="bill-to">
        <div class="label">Bill To:</div>
        <div style="font-weight: bold;">${escapeHtml(invoice.debtor_name || invoice.debtor?.name || 'Customer Name')}</div>
        ${invoice.debtor?.address ? `<div>${escapeHtml(invoice.debtor.address)}</div>` : ''}
        ${invoice.debtor?.phone ? `<div>Tel: ${escapeHtml(invoice.debtor.phone)}</div>` : ''}
        ${invoice.debtor?.vat_number ? `<div>VAT: ${escapeHtml(invoice.debtor.vat_number)}</div>` : ''}
      </div>
      <div class="invoice-details">
        <div class="value"><span class="label">Date:</span> ${escapeHtml(invoice.invoice_date || '')}</div>
        ${invoice.due_date ? `<div class="value"><span class="label">Due Date:</span> ${escapeHtml(invoice.due_date)}</div>` : ''}
        <div class="value"><span class="label">Status:</span> ${escapeHtml(invoice.status || 'Draft')}</div>
        ${invoice.customer_ref ? `<div class="value"><span class="label">Ref:</span> ${escapeHtml(invoice.customer_ref)}</div>` : ''}
      </div>
    </div>

    <table>
      <thead>
        <tr>
          <th>Description</th>
          <th class="text-center">Qty</th>
          <th class="text-right">Unit Price</th>
          <th class="text-right">Discount</th>
          <th class="text-right">Amount</th>
        </tr>
      </thead>
      <tbody>
        ${itemsHtml}
      </tbody>
    </table>

    <div class="totals">
      <div class="total-row">
        <span>Subtotal</span>
        <span>${formatCurrency(subtotal)}</span>
      </div>
      <div class="total-row">
        <span>VAT</span>
        <span>${formatCurrency(tax)}</span>
      </div>
      <div class="total-row grand-total">
        <span>Total</span>
        <span>${formatCurrency(total)}</span>
      </div>
    </div>

    ${invoice.notes ? `
      <div style="margin-top: 30px;">
        <div class="label">Notes:</div>
        <div>${escapeHtml(invoice.notes)}</div>
      </div>
    ` : ''}

    <div class="footer">
      <p>Thank you for your business!</p>
      <p>${escapeHtml(companyName)}</p>
    </div>
  </div>
</body>
</html>
  `;
}

/**
 * Generate print-friendly HTML for a receipt
 */
export function generateReceiptPrintHTML(receipt: any, shop: any, tenant: any): string {
  const companyName = shop?.name || tenant?.company_name || 'Company Name';
  const companyAddress = shop?.address || tenant?.company_address || '';
  const companyPhone = shop?.phone || tenant?.phone || '';
  const vatNumber = tenant?.vat_number || '';
  const logoUrl = isSafeImageUrl(shop?.logo) ? shop.logo : null;

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Receipt ${escapeHtml(receipt.receipt_number || receipt.id)}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; color: #333; padding: 20px; }
    .receipt-container { max-width: 400px; margin: 0 auto; }
    .header { text-align: center; margin-bottom: 20px; }
    .logo-container { margin-bottom: 10px; }
    .logo-container img { max-width: 120px; max-height: 60px; }
    .company-name { font-size: 18px; font-weight: bold; }
    .company-details { font-size: 11px; color: #666; }
    .document-title { font-size: 20px; font-weight: bold; margin: 15px 0; }
    .receipt-number { font-size: 12px; color: #666; }
    .details { margin-bottom: 20px; }
    .detail-row { display: flex; justify-content: space-between; margin-bottom: 5px; }
    .total { font-size: 18px; font-weight: bold; text-align: right; margin-top: 15px; border-top: 1px solid #333; padding-top: 10px; }
    .footer { text-align: center; margin-top: 30px; font-size: 11px; color: #999; }
    @media print { body { padding: 0; } }
  </style>
</head>
<body>
  <div class="receipt-container">
    <div class="header">
      ${logoUrl ? `<div class="logo-container"><img src="${escapeHtml(logoUrl)}" alt="${escapeHtml(companyName)}" /></div>` : ''}
      <div class="company-name">${escapeHtml(companyName)}</div>
      ${companyAddress ? `<div class="company-details">${escapeHtml(companyAddress).replace(/\n/g, '<br>')}</div>` : ''}
      ${companyPhone ? `<div class="company-details">Tel: ${escapeHtml(companyPhone)}</div>` : ''}
      ${vatNumber ? `<div class="company-details">VAT: ${escapeHtml(vatNumber)}</div>` : ''}
    </div>

    <div class="document-title">RECEIPT</div>
    <div class="receipt-number">${escapeHtml(receipt.receipt_number || `Receipt #${receipt.id}`)}</div>

    <div class="details">
      <div class="detail-row"><span>Date:</span><span>${escapeHtml(receipt.receipt_date || new Date().toLocaleDateString())}</span></div>
      ${receipt.debtor_name ? `<div class="detail-row"><span>Customer:</span><span>${escapeHtml(receipt.debtor_name)}</span></div>` : ''}
      <div class="detail-row"><span>Amount:</span><span>${formatCurrency(receipt.amount || 0)}</span></div>
    </div>

    <div class="total">Total: ${formatCurrency(receipt.amount || 0)}</div>

    <div class="footer">
      <p>Thank you!</p>
      <p>${escapeHtml(companyName)}</p>
    </div>
  </div>
</body>
</html>
  `;
}

/**
 * Open print window with content
 */
export function openPrintWindow(html: string): void {
  const printWindow = window.open('', '_blank', 'width=800,height=600');
  if (printWindow) {
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
  }
}

/**
 * Print an invoice with shop branding
 */
export async function printInvoice(invoice: any): Promise<void> {
  const [shop, tenant] = await Promise.all([
    getShopForPrint(),
    getTenantForPrint(),
  ]);
  
  const html = generateInvoicePrintHTML(invoice, shop, tenant);
  openPrintWindow(html);
}

/**
 * Print a receipt with shop branding
 */
export async function printReceipt(receipt: any): Promise<void> {
  const [shop, tenant] = await Promise.all([
    getShopForPrint(),
    getTenantForPrint(),
  ]);
  
  const html = generateReceiptPrintHTML(receipt, shop, tenant);
  openPrintWindow(html);
}

/**
 * Email an invoice with shop branding
 * @param invoice - The invoice data
 * @param recipientEmail - Email address to send to
 * @returns Promise with success/error status
 */
export async function emailInvoice(invoice: any, recipientEmail: string): Promise<{ success: boolean; message: string }> {
  try {
    const [shop, tenant] = await Promise.all([
      getShopForPrint(),
      getTenantForPrint(),
    ]);
    
    const html = generateInvoicePrintHTML(invoice, shop, tenant);
    
    // Send to backend API for email processing
    const response = await api.post('/api/settings/email-document/', {
      document_type: 'invoice',
      document_id: invoice.id,
      document_number: invoice.invoice_number,
      recipient_email: recipientEmail,
      html_content: html,
      subject: `Invoice ${invoice.invoice_number} from ${shop?.name || tenant?.company_name || 'Company'}`,
    });
    
    return { success: true, message: 'Invoice sent successfully!' };
  } catch (error: any) {
    console.error('Failed to email invoice:', error);
    return { 
      success: false, 
      message: error.response?.data?.detail || error.message || 'Failed to send invoice email' 
    };
  }
}

/**
 * Email a receipt with shop branding
 * @param receipt - The receipt data
 * @param recipientEmail - Email address to send to
 * @returns Promise with success/error status
 */
export async function emailReceipt(receipt: any, recipientEmail: string): Promise<{ success: boolean; message: string }> {
  try {
    const [shop, tenant] = await Promise.all([
      getShopForPrint(),
      getTenantForPrint(),
    ]);
    
    const html = generateReceiptPrintHTML(receipt, shop, tenant);
    
    const response = await api.post('/api/settings/email-document/', {
      document_type: 'receipt',
      document_id: receipt.id,
      document_number: receipt.receipt_number || `Receipt-${receipt.id}`,
      recipient_email: recipientEmail,
      html_content: html,
      subject: `Receipt ${receipt.receipt_number || receipt.id} from ${shop?.name || tenant?.company_name || 'Company'}`,
    });
    
    return { success: true, message: 'Receipt sent successfully!' };
  } catch (error: any) {
    console.error('Failed to email receipt:', error);
    return { 
      success: false, 
      message: error.response?.data?.detail || error.message || 'Failed to send receipt email' 
    };
  }
}
