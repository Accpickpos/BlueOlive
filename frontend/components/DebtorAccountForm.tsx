"use client";

interface DebtorAccountFormProps {
  open: boolean;
  onClose: () => void;
  onDelete?: () => void; // optional delete callback
}

export default function DebtorAccountForm({
  open,
  onClose,
  onDelete,
}: DebtorAccountFormProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 flex flex-col bg-white z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b shadow">
        <h2 className="text-2xl font-bold">Debtor Account Details</h2>
        <button
          onClick={onClose}
          className="px-4 py-2 border rounded hover:bg-gray-100"
        >
          Close
        </button>
      </div>

      {/* Scrollable form */}
      <div className="flex-1 overflow-y-auto p-6">
        <form className="grid grid-cols-2 gap-4 text-sm">
          <label>
            Account Number
            <input
              type="text"
              className="w-full border p-2 rounded"
              defaultValue="10000"
            />
          </label>
          <label>
            Name
            <input type="text" className="w-full border p-2 rounded" />
          </label>

          <label className="col-span-2">
            Address (Postal)
            <textarea className="w-full border p-2 rounded" rows={2}></textarea>
          </label>
          <label className="col-span-2">
            Address (Delivery)
            <textarea className="w-full border p-2 rounded" rows={2}></textarea>
          </label>

          <label>Postal Code <input className="w-full border p-2 rounded" /></label>
          <label>Contact <input className="w-full border p-2 rounded" /></label>
          <label>Tel1 <input className="w-full border p-2 rounded" /></label>
          <label>Tel2 <input className="w-full border p-2 rounded" /></label>
          <label>Fax <input className="w-full border p-2 rounded" /></label>
          <label>Email <input type="email" className="w-full border p-2 rounded" /></label>

          <label>Area/Sman <input className="w-full border p-2 rounded" /></label>
          <label>Additional Info <input className="w-full border p-2 rounded" /></label>
          <label>Trade Disc % <input type="number" step="0.01" className="w-full border p-2 rounded" /></label>
          <label>Credit Limit <input type="number" step="0.01" className="w-full border p-2 rounded" /></label>
          <label>Terms Days <input type="number" className="w-full border p-2 rounded" /></label>
          <label>Prompt Disc % <input type="number" step="0.01" className="w-full border p-2 rounded" /></label>

          <label>Price Code <input className="w-full border p-2 rounded" /></label>
          <label>Charge Interest (Y/N) <input className="w-full border p-2 rounded" /></label>
          <label>Print on Invoices (Y/N) <input className="w-full border p-2 rounded" /></label>
          <label>Balance on POS Docs (Y/N) <input className="w-full border p-2 rounded" /></label>
          <label>Change Block Status (Y/N) <input className="w-full border p-2 rounded" /></label>

          <label className="col-span-1">Search Name <input className="w-full border p-2 rounded" /></label>
          <label className="col-span-1">Account Category <input className="w-full border p-2 rounded" /></label>
          <label className="col-span-2">VAT/Tax Ref No <input className="w-full border p-2 rounded" /></label>
        </form>
      </div>

      {/* Footer */}
      <div className="flex justify-between items-center gap-2 p-4 border-t">
        {/* Delete button (left aligned) */}
        {onDelete && (
          <button
            onClick={onDelete}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Delete
          </button>
        )}

        {/* Action buttons (right aligned) */}
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-green-600 text-white rounded"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
