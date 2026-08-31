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
 * Shared "COPY" watermark — manual §1 "6. Transaction Query" requires a
 * reprint to visibly show the word COPY, distinguishing it from the
 * original. Applied whenever a document is printed/emailed via the
 * Transaction Query search rather than at the time it was first created.
 */
const COPY_WATERMARK_CSS = `
    .copy-watermark {
      position: fixed;
      top: 45%;
      left: 50%;
      transform: translate(-50%, -50%) rotate(-30deg);
      font-size: 110px;
      font-weight: bold;
      letter-spacing: 10px;
      color: rgba(200, 0, 0, 0.28);
      z-index: 1000;
      pointer-events: none;
      white-space: nowrap;
    }
`;
function watermarkHtml(isCopy?: boolean): string {
  return isCopy ? '<div class="copy-watermark">COPY</div>' : '';
}

/**
 * Generate print-friendly HTML for an invoice
 */
export function generateInvoicePrintHTML(invoice: any, shop: any, tenant: any, isCopy?: boolean): string {
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
${COPY_WATERMARK_CSS}
  </style>
</head>
<body>
  ${watermarkHtml(isCopy)}
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
export function generateReceiptPrintHTML(receipt: any, shop: any, tenant: any, isCopy?: boolean): string {
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
${COPY_WATERMARK_CSS}
  </style>
</head>
<body>
  ${watermarkHtml(isCopy)}
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
 * A single line item on a generic document (cash sale, credit note, job
 * card, etc). Mirrors the shared field naming used by InvoiceLine,
 * CashSaleLine, CreditNoteLine, JobCardLine, QuotationLine and LaybyeLine.
 */
interface GenericDocumentLine {
  description: string;
  quantity?: number | string;
  unit_price?: number;
  discount_percentage?: number;
  line_total: number;
}

/**
 * Config for generateGenericDocumentHTML — one shared template covering
 * every POS document type that doesn't already have a bespoke generator
 * (Invoice and Receipt-on-Account keep their own above). Documents without
 * line items (Payout, Repair, Receipt) just omit `lines` and rely on
 * `detailRows` + `total`.
 */
export interface GenericDocumentConfig {
  title: string; // e.g. "CASH SALE", "CREDIT NOTE", "JOB CARD"
  number: string;
  date: string;
  customerName?: string;
  customerExtra?: string[]; // address lines, phone, account number, etc.
  detailRows?: { label: string; value: string }[]; // status, reference, tender type, etc.
  lines?: GenericDocumentLine[];
  subtotal?: number;
  vat?: number;
  total: number;
  notes?: string;
  isCopy?: boolean; // true when reprinted via Transaction Query, per manual §1 "6. Transaction Query"
}

/**
 * Generate print-friendly HTML for any document type via GenericDocumentConfig.
 * Visual structure mirrors generateInvoicePrintHTML so all printed documents
 * look consistent, without duplicating that template per document type.
 */
export function generateGenericDocumentHTML(
  config: GenericDocumentConfig,
  shop: any,
  tenant: any
): string {
  const companyName = shop?.name || tenant?.company_name || 'Company Name';
  const companyAddress = shop?.address || tenant?.company_address || '';
  const companyPhone = shop?.phone || tenant?.phone || '';
  const vatNumber = tenant?.vat_number || '';
  const regNumber = tenant?.registration_number || '';
  const logoUrl = isSafeImageUrl(shop?.logo) ? shop.logo : null;

  const lines = config.lines || [];
  const hasLines = lines.length > 0;

  const itemsHtml = lines.map((line) => {
    const qty = line.quantity ?? '';
    const unitPrice = line.unit_price ?? 0;
    const discount = line.discount_percentage ?? 0;
    return `
        <tr>
          <td>${escapeHtml(line.description || 'Item')}</td>
          <td class="text-center">${escapeHtml(qty)}</td>
          <td class="text-right">${formatCurrency(unitPrice)}</td>
          <td class="text-right">${escapeHtml(discount)}%</td>
          <td class="text-right">${formatCurrency(line.line_total)}</td>
        </tr>
    `;
  }).join('');

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${escapeHtml(config.title)} ${escapeHtml(config.number)}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; color: #333; }
    .doc-container { max-width: 800px; margin: 0 auto; padding: 20px; }
    .header { display: flex; justify-content: space-between; margin-bottom: 30px; }
    .company-info { flex: 1; }
    .company-name { font-size: 24px; font-weight: bold; color: #1a1a1a; margin-bottom: 5px; }
    .company-details { font-size: 12px; color: #666; }
    .logo-container { width: 150px; height: 80px; display: flex; align-items: center; justify-content: flex-end; }
    .logo-container img { max-width: 100%; max-height: 100%; object-fit: contain; }
    .document-title { font-size: 28px; font-weight: bold; color: #333; text-align: right; margin-bottom: 5px; }
    .doc-number { font-size: 14px; color: #666; text-align: right; }
    .details-section { display: flex; justify-content: space-between; margin-bottom: 30px; }
    .bill-to { flex: 1; }
    .doc-details { text-align: right; }
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
    @media print {
      body { -webkit-print-color-adjust: exact; }
      .doc-container { padding: 0; }
    }
${COPY_WATERMARK_CSS}
  </style>
</head>
<body>
  ${watermarkHtml(config.isCopy)}
  <div class="doc-container">
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
        <div class="document-title">${escapeHtml(config.title)}</div>
        <div class="doc-number">${escapeHtml(config.number)}</div>
      </div>
    </div>

    <div class="details-section">
      <div class="bill-to">
        ${config.customerName ? `
          <div class="label">Customer:</div>
          <div style="font-weight: bold;">${escapeHtml(config.customerName)}</div>
          ${(config.customerExtra || []).map((line) => `<div>${escapeHtml(line)}</div>`).join('')}
        ` : ''}
      </div>
      <div class="doc-details">
        <div class="value"><span class="label">Date:</span> ${escapeHtml(config.date)}</div>
        ${(config.detailRows || []).map((row) => `
          <div class="value"><span class="label">${escapeHtml(row.label)}:</span> ${escapeHtml(row.value)}</div>
        `).join('')}
      </div>
    </div>

    ${hasLines ? `
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
        ${config.subtotal !== undefined ? `
          <div class="total-row">
            <span>Subtotal</span>
            <span>${formatCurrency(config.subtotal)}</span>
          </div>
        ` : ''}
        ${config.vat !== undefined ? `
          <div class="total-row">
            <span>VAT</span>
            <span>${formatCurrency(config.vat)}</span>
          </div>
        ` : ''}
        <div class="total-row grand-total">
          <span>Total</span>
          <span>${formatCurrency(config.total)}</span>
        </div>
      </div>
    ` : `
      <div class="totals">
        <div class="total-row grand-total">
          <span>Total</span>
          <span>${formatCurrency(config.total)}</span>
        </div>
      </div>
    `}

    ${config.notes ? `
      <div style="margin-top: 30px;">
        <div class="label">Notes:</div>
        <div>${escapeHtml(config.notes)}</div>
      </div>
    ` : ''}

    <div class="footer">
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
export async function printInvoice(invoice: any, isReprint: boolean = false): Promise<void> {
  const [shop, tenant] = await Promise.all([
    getShopForPrint(),
    getTenantForPrint(),
  ]);

  const html = generateInvoicePrintHTML(invoice, shop, tenant, isReprint);
  openPrintWindow(html);
}

/**
 * Print a receipt with shop branding
 */
export async function printReceipt(receipt: any, isReprint: boolean = false): Promise<void> {
  const [shop, tenant] = await Promise.all([
    getShopForPrint(),
    getTenantForPrint(),
  ]);

  const html = generateReceiptPrintHTML(receipt, shop, tenant, isReprint);
  openPrintWindow(html);
}

/**
 * Email an invoice with shop branding
 * @param invoice - The invoice data
 * @param recipientEmail - Email address to send to
 * @param isReprint - Marks the attached document as a COPY (manual §1 "6. Transaction Query")
 * @returns Promise with success/error status
 */
export async function emailInvoice(invoice: any, recipientEmail: string, isReprint: boolean = false): Promise<{ success: boolean; message: string }> {
  try {
    const [shop, tenant] = await Promise.all([
      getShopForPrint(),
      getTenantForPrint(),
    ]);

    const html = generateInvoicePrintHTML(invoice, shop, tenant, isReprint);

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
 * @param isReprint - Marks the attached document as a COPY (manual §1 "6. Transaction Query")
 * @returns Promise with success/error status
 */
export async function emailReceipt(receipt: any, recipientEmail: string, isReprint: boolean = false): Promise<{ success: boolean; message: string }> {
  try {
    const [shop, tenant] = await Promise.all([
      getShopForPrint(),
      getTenantForPrint(),
    ]);

    const html = generateReceiptPrintHTML(receipt, shop, tenant, isReprint);

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

// ============================================================
// GENERIC DOCUMENT PRINT/EMAIL — cash sales, credit notes, laybyes,
// quotations, job cards, repairs and payouts, none of which had a print
// or email path before. Each type below is a normalizer (raw API object
// -> GenericDocumentConfig) plus print/email wrappers built on the same
// generateGenericDocumentHTML template and /api/settings/email-document/
// endpoint the invoice/receipt paths already use.
// ============================================================

async function printGenericDocument(config: GenericDocumentConfig): Promise<void> {
  const [shop, tenant] = await Promise.all([getShopForPrint(), getTenantForPrint()]);
  const html = generateGenericDocumentHTML(config, shop, tenant);
  openPrintWindow(html);
}

async function emailGenericDocument(
  documentType: string,
  documentId: string | number,
  config: GenericDocumentConfig,
  recipientEmail: string
): Promise<{ success: boolean; message: string }> {
  try {
    const [shop, tenant] = await Promise.all([getShopForPrint(), getTenantForPrint()]);
    const html = generateGenericDocumentHTML(config, shop, tenant);

    await api.post('/api/settings/email-document/', {
      document_type: documentType,
      document_id: documentId,
      document_number: config.number,
      recipient_email: recipientEmail,
      html_content: html,
      subject: `${config.title} ${config.number} from ${shop?.name || tenant?.company_name || 'Company'}`,
    });

    return { success: true, message: `${config.title} sent successfully!` };
  } catch (error: any) {
    console.error(`Failed to email ${documentType}:`, error);
    return {
      success: false,
      message: error.response?.data?.detail || error.message || `Failed to send ${config.title.toLowerCase()} email`,
    };
  }
}

function lineItemsFrom(lines: any[]): GenericDocumentLine[] {
  return (lines || []).map((l) => ({
    description: l.description || l.stock_code || 'Item',
    quantity: l.quantity,
    unit_price: Number(l.unit_price || 0),
    discount_percentage: Number(l.discount_percentage || 0),
    line_total: Number(l.line_total || 0),
  }));
}

// ----- Cash Sale -----

function cashSaleConfig(cashSale: any): GenericDocumentConfig {
  return {
    title: 'CASH SALE',
    number: cashSale.sale_number || `CS-${cashSale.id}`,
    date: cashSale.sale_date || '',
    customerName: cashSale.customer_name || undefined,
    customerExtra: [cashSale.delivery_address, cashSale.telephone ? `Tel: ${cashSale.telephone}` : ''].filter(Boolean),
    lines: lineItemsFrom(cashSale.lines),
    subtotal: Number(cashSale.subtotal || 0),
    vat: Number(cashSale.vat_amount || 0),
    total: Number(cashSale.total_amount || 0),
  };
}

export async function printCashSale(cashSale: any, isReprint: boolean = false): Promise<void> {
  return printGenericDocument({ ...cashSaleConfig(cashSale), isCopy: isReprint });
}

export async function emailCashSale(cashSale: any, recipientEmail: string, isReprint: boolean = false) {
  return emailGenericDocument('cash_sale', cashSale.id, { ...cashSaleConfig(cashSale), isCopy: isReprint }, recipientEmail);
}

// ----- Credit Note -----

function creditNoteConfig(creditNote: any): GenericDocumentConfig {
  return {
    title: 'CREDIT NOTE',
    number: creditNote.credit_number || `CN-${creditNote.id}`,
    date: creditNote.credit_date || '',
    customerName: creditNote.customer_name || undefined,
    detailRows: [
      ...(creditNote.debtor_account ? [{ label: 'Account', value: String(creditNote.debtor_account) }] : []),
      ...(creditNote.refund_type_display || creditNote.refund_type
        ? [{ label: 'Refund Method', value: creditNote.refund_type_display || creditNote.refund_type }]
        : []),
    ],
    lines: lineItemsFrom(creditNote.lines),
    subtotal: Number(creditNote.subtotal || 0),
    vat: Number(creditNote.vat_amount || 0),
    total: Number(creditNote.total_amount || 0),
    notes: creditNote.reason || undefined,
  };
}

export async function printCreditNote(creditNote: any, isReprint: boolean = false): Promise<void> {
  return printGenericDocument({ ...creditNoteConfig(creditNote), isCopy: isReprint });
}

export async function emailCreditNote(creditNote: any, recipientEmail: string, isReprint: boolean = false) {
  return emailGenericDocument('credit_note', creditNote.id, { ...creditNoteConfig(creditNote), isCopy: isReprint }, recipientEmail);
}

// ----- Laybye -----

function laybyeConfig(laybye: any): GenericDocumentConfig {
  return {
    title: 'LAYBYE',
    number: laybye.laybye_number || `LAY-${laybye.id}`,
    date: laybye.laybye_date || '',
    customerName: laybye.customer_name || undefined,
    customerExtra: [laybye.telephone ? `Tel: ${laybye.telephone}` : ''].filter(Boolean),
    detailRows: [
      { label: 'Status', value: laybye.status_display || laybye.status || '' },
      { label: 'Expiry Date', value: laybye.expiry_date || '' },
      { label: 'Deposit', value: formatCurrency(Number(laybye.deposit_amount || 0)) },
      { label: 'Paid', value: formatCurrency(Number(laybye.amount_paid || 0)) },
      { label: 'Balance Due', value: formatCurrency(Number(laybye.balance_due || 0)) },
    ],
    lines: lineItemsFrom((laybye.lines || []).filter((l: any) => l.transaction_type === 'SP')),
    total: Number(laybye.total_amount || 0),
  };
}

export async function printLaybye(laybye: any, isReprint: boolean = false): Promise<void> {
  return printGenericDocument({ ...laybyeConfig(laybye), isCopy: isReprint });
}

export async function emailLaybye(laybye: any, recipientEmail: string, isReprint: boolean = false) {
  return emailGenericDocument('laybye', laybye.id, { ...laybyeConfig(laybye), isCopy: isReprint }, recipientEmail);
}

// ----- Quotation -----

function quotationConfig(quotation: any): GenericDocumentConfig {
  return {
    title: 'QUOTATION',
    number: quotation.quotation_number || `QT-${quotation.id}`,
    date: quotation.quotation_date || '',
    customerName: quotation.debtor_account_name || quotation.customer_name || undefined,
    customerExtra: [
      quotation.address_line1, quotation.address_line2, quotation.address_line3,
      quotation.telephone ? `Tel: ${quotation.telephone}` : '',
    ].filter(Boolean),
    detailRows: [{ label: 'Expiry Date', value: quotation.expiry_date || '' }],
    lines: lineItemsFrom(quotation.lines),
    subtotal: Number(quotation.subtotal || 0),
    vat: Number(quotation.vat_amount || 0),
    total: Number(quotation.total_amount || 0),
  };
}

export async function printQuotation(quotation: any, isReprint: boolean = false): Promise<void> {
  return printGenericDocument({ ...quotationConfig(quotation), isCopy: isReprint });
}

export async function emailQuotation(quotation: any, recipientEmail: string, isReprint: boolean = false) {
  return emailGenericDocument('quotation', quotation.id, { ...quotationConfig(quotation), isCopy: isReprint }, recipientEmail);
}

// ----- Job Card -----

function jobCardConfig(jobCard: any): GenericDocumentConfig {
  return {
    title: 'JOB CARD',
    number: jobCard.job_number || `JB-${jobCard.id}`,
    date: jobCard.job_date || '',
    customerName: jobCard.customer_name || undefined,
    customerExtra: [
      jobCard.address, jobCard.telephone ? `Tel: ${jobCard.telephone}` : '',
      jobCard.registration_number ? `Reg: ${jobCard.registration_number}` : '',
    ].filter(Boolean),
    detailRows: [{ label: 'Status', value: jobCard.status_display || jobCard.status || '' }],
    lines: lineItemsFrom(jobCard.lines),
    subtotal: Number(jobCard.subtotal || 0),
    vat: Number(jobCard.vat_amount || 0),
    total: Number(jobCard.total_amount || 0),
    notes: jobCard.job_description || undefined,
  };
}

export async function printJobCard(jobCard: any, isReprint: boolean = false): Promise<void> {
  return printGenericDocument({ ...jobCardConfig(jobCard), isCopy: isReprint });
}

export async function emailJobCard(jobCard: any, recipientEmail: string, isReprint: boolean = false) {
  return emailGenericDocument('job_card', jobCard.id, { ...jobCardConfig(jobCard), isCopy: isReprint }, recipientEmail);
}

// ----- Repair -----

function repairConfig(repair: any): GenericDocumentConfig {
  return {
    title: 'REPAIR VOUCHER',
    number: repair.repair_number || `REP-${repair.id}`,
    date: repair.date_received || repair.created_at || '',
    customerName: repair.customer_name || undefined,
    customerExtra: [
      repair.address_line1, repair.address_line2,
      repair.telephone ? `Tel: ${repair.telephone}` : '',
    ].filter(Boolean),
    detailRows: [
      { label: 'Status', value: repair.status_display || repair.status || '' },
      ...(repair.date_required ? [{ label: 'Date Required', value: repair.date_required }] : []),
    ],
    total: Number(repair.selling_price ?? repair.quoted_value ?? repair.repair_cost ?? 0),
    notes: repair.repair_details || undefined,
  };
}

export async function printRepair(repair: any, isReprint: boolean = false): Promise<void> {
  return printGenericDocument({ ...repairConfig(repair), isCopy: isReprint });
}

export async function emailRepair(repair: any, recipientEmail: string, isReprint: boolean = false) {
  return emailGenericDocument('repair', repair.id, { ...repairConfig(repair), isCopy: isReprint }, recipientEmail);
}

// ----- Payout -----

function payoutConfig(payout: any): GenericDocumentConfig {
  return {
    title: 'PAYOUT VOUCHER',
    number: `PO-${payout.id}`,
    date: payout.payout_date || '',
    customerName: payout.payee || undefined,
    detailRows: payout.reference ? [{ label: 'Reference', value: payout.reference }] : [],
    total: Number(payout.amount || 0),
    notes: payout.description || undefined,
  };
}

export async function printPayout(payout: any, isReprint: boolean = false): Promise<void> {
  return printGenericDocument({ ...payoutConfig(payout), isCopy: isReprint });
}

export async function emailPayout(payout: any, recipientEmail: string, isReprint: boolean = false) {
  return emailGenericDocument('payout', payout.id, { ...payoutConfig(payout), isCopy: isReprint }, recipientEmail);
}
