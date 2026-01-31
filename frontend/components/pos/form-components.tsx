/**
 * POS Form Components Library
 * Reusable components for POS transaction forms
 */
"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  AlertCircle,
  CheckCircle2,
  Info,
  Loader2,
  Plus,
  Trash2,
} from "lucide-react";

// Form Section Header
export function FormSectionHeader({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="border-b pb-4 mb-4">
      <h3 className="font-semibold text-lg">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mt-1">{description}</p>
      )}
    </div>
  );
}

// Status Badge
export function StatusBadge({
  status,
  variant = "default",
}: {
  status: string;
  variant?: "default" | "draft" | "posted" | "success";
}) {
  const styles = {
    default: "bg-gray-100 text-gray-800",
    draft: "bg-yellow-100 text-yellow-800",
    posted: "bg-green-100 text-green-800",
    success: "bg-blue-100 text-blue-800",
  };

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${styles[variant]}`}
    >
      {status}
    </span>
  );
}

// Form Field with Label
export function FormField({
  label,
  error,
  required,
  children,
  hint,
}: {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

// Account Info Display
export function AccountInfoCard({
  accountName,
  accountNumber,
  balance,
  creditLimit,
  loading,
  error,
}: {
  accountName?: string;
  accountNumber?: string;
  balance?: number;
  creditLimit?: number;
  loading?: boolean;
  error?: string;
}) {
  if (loading) {
    return (
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-blue-600">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Loading account information...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <p className="text-red-700 text-sm">{error}</p>
      </div>
    );
  }

  if (!accountName) {
    return null;
  }

  const availableCredit = creditLimit ? creditLimit - (balance || 0) : 0;
  const creditWarning = availableCredit < 0;

  return (
    <Card className={creditWarning ? "border-orange-300 bg-orange-50" : ""}>
      <CardContent className="pt-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Account Name</p>
            <p className="font-semibold">{accountName}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Account Number</p>
            <p className="font-semibold">{accountNumber}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Current Balance</p>
            <p className={`font-semibold ${balance && balance > 0 ? "text-red-600" : ""}`}>
              R{balance?.toFixed(2) || "0.00"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Available Credit</p>
            <p
              className={`font-semibold ${
                creditWarning ? "text-red-600" : "text-green-600"
              }`}
            >
              R{availableCredit.toFixed(2)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Totals Summary
export function TotalsSummary({
  subtotal,
  discount,
  tax,
  total,
}: {
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
}) {
  return (
    <Card className="bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
      <CardContent className="pt-6">
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Subtotal:</span>
            <span className="font-medium">R{subtotal.toFixed(2)}</span>
          </div>
          {discount > 0 && (
            <div className="flex justify-between text-sm text-orange-600">
              <span>Discount:</span>
              <span className="font-medium">-R{discount.toFixed(2)}</span>
            </div>
          )}
          {tax > 0 && (
            <div className="flex justify-between text-sm text-blue-600">
              <span>Tax:</span>
              <span className="font-medium">R{tax.toFixed(2)}</span>
            </div>
          )}
          <div className="border-t pt-3 flex justify-between">
            <span className="font-bold text-lg">Total:</span>
            <span className="font-bold text-lg text-green-600">
              R{total.toFixed(2)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Loading Overlay
export function LoadingOverlay({ message = "Processing..." }: { message?: string }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-80">
        <CardContent className="pt-6 flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-center font-medium">{message}</p>
        </CardContent>
      </Card>
    </div>
  );
}

// Success Alert
export function SuccessAlert({ message }: { message: string }) {
  return (
    <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
      <CheckCircle2 className="h-4 w-4 text-green-600" />
      <p className="text-green-800 text-sm">{message}</p>
    </div>
  );
}

// Info Alert
export function InfoAlert({ message }: { message: string }) {
  return (
    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-3">
      <Info className="h-4 w-4 text-blue-600" />
      <p className="text-blue-800 text-sm">{message}</p>
    </div>
  );
}

// Error Alert
export function ErrorAlert({ message }: { message: string }) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
      <AlertCircle className="h-4 w-4 text-red-600" />
      <p className="text-red-800 text-sm">{message}</p>
    </div>
  );
}

// Action Buttons Footer
export function FormActions({
  onCancel,
  onSaveDraft,
  onSubmit,
  loading,
  submitLabel = "Submit",
  showDraft = true,
}: {
  onCancel: () => void;
  onSaveDraft?: () => void;
  onSubmit: () => void;
  loading: boolean;
  submitLabel?: string;
  showDraft?: boolean;
}) {
  return (
    <div className="flex gap-3 justify-end border-t pt-6">
      <Button
        variant="outline"
        onClick={onCancel}
        disabled={loading}
      >
        Cancel
      </Button>
      {showDraft && onSaveDraft && (
        <Button
          variant="outline"
          onClick={onSaveDraft}
          disabled={loading}
        >
          Save Draft
        </Button>
      )}
      <Button
        onClick={onSubmit}
        disabled={loading}
        className="gap-2"
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {submitLabel}
      </Button>
    </div>
  );
}

// Line Item Row Component
export function LineItemRow({
  item,
  onUpdate,
  onRemove,
  index,
}: {
  item: any;
  onUpdate: (field: string, value: any) => void;
  onRemove: () => void;
  index: number;
}) {
  return (
    <div className="flex gap-2 items-end p-4 bg-slate-50 rounded-lg border">
      <div className="flex-1">
        <label className="text-xs font-medium text-muted-foreground">
          Item/Description
        </label>
        <Input
          placeholder="Item description"
          value={item.description || ""}
          onChange={(e) => onUpdate("description", e.target.value)}
          className="mt-1"
        />
      </div>
      <div className="w-24">
        <label className="text-xs font-medium text-muted-foreground">
          Quantity
        </label>
        <Input
          type="number"
          min="1"
          value={item.quantity || 1}
          onChange={(e) => onUpdate("quantity", parseFloat(e.target.value))}
          className="mt-1"
        />
      </div>
      <div className="w-24">
        <label className="text-xs font-medium text-muted-foreground">
          Amount
        </label>
        <Input
          type="number"
          min="0"
          step="0.01"
          value={item.amount || 0}
          onChange={(e) => onUpdate("amount", parseFloat(e.target.value))}
          className="mt-1"
        />
      </div>
      <Button
        size="icon"
        variant="ghost"
        onClick={onRemove}
        className="text-red-600 hover:text-red-700 hover:bg-red-50"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}

// Tender Row Component
export function TenderRow({
  tender,
  onUpdate,
  onRemove,
  index,
}: {
  tender: any;
  onUpdate: (field: string, value: any) => void;
  onRemove: () => void;
  index: number;
}) {
  const isCheque = tender.tender_type === "CHEQUE";

  return (
    <div className="space-y-3 p-4 bg-slate-50 rounded-lg border">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-muted-foreground">
            Payment Method
          </label>
          <select
            value={tender.tender_type}
            onChange={(e) => onUpdate("tender_type", e.target.value)}
            className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="CASH">Cash</option>
            <option value="CHEQUE">Cheque</option>
            <option value="CREDIT_CARD">Credit Card</option>
            <option value="EFT">EFT</option>
            <option value="SPEEDPOINT">Speedpoint</option>
            <option value="VOUCHER">Voucher</option>
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">
            Amount (R)
          </label>
          <Input
            type="number"
            min="0"
            step="0.01"
            value={tender.amount || 0}
            onChange={(e) => onUpdate("amount", parseFloat(e.target.value))}
            className="mt-1"
            placeholder="0.00"
          />
        </div>
      </div>

      {isCheque && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Cheque Number
              </label>
              <Input
                value={tender.cheque_number || ""}
                onChange={(e) => onUpdate("cheque_number", e.target.value)}
                className="mt-1"
                placeholder="Cheque #"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Drawer Name
              </label>
              <Input
                value={tender.drawer || ""}
                onChange={(e) => onUpdate("drawer", e.target.value)}
                className="mt-1"
                placeholder="Drawer name"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Bank
              </label>
              <Input
                value={tender.bank || ""}
                onChange={(e) => onUpdate("bank", e.target.value)}
                className="mt-1"
                placeholder="Bank name"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Account
              </label>
              <Input
                value={tender.account || ""}
                onChange={(e) => onUpdate("account", e.target.value)}
                className="mt-1"
                placeholder="Account #"
              />
            </div>
          </div>
        </>
      )}

      <div className="flex justify-end">
        <Button
          size="sm"
          variant="ghost"
          onClick={onRemove}
          className="text-red-600 hover:text-red-700 hover:bg-red-50"
        >
          <Trash2 className="h-4 w-4 mr-1" />
          Remove
        </Button>
      </div>
    </div>
  );
}
