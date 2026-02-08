"use client";

import { useState } from "react";

interface FormErrors {
  [key: string]: string;
}

interface FormData {
  account_number: string;
  name: string;
  search_name: string;
  contact_person: string;
  telephone1: string;
  telephone2: string;
  fax: string;
  email: string;
  postal_address_line1: string;
  postal_address_line2: string;
  postal_address_line3: string;
  postal_code: string;
  delivery_address_line1: string;
  delivery_address_line2: string;
  delivery_address_line3: string;
  delivery_code: string;
  vat_number: string;
  additional_info: string;
  trade_discount: number;
  credit_limit: number;
  terms: number;
  prompt_discount_percentage: number;
  price_level: number;
  charge_interest: boolean;
  print_discount_on_invoice: boolean;
  print_balance_on_documents: boolean;
  is_blocked: boolean;
  block_reason: string;
  account_category: string;
}

interface DebtorAccountFormProps {
  open: boolean;
  onClose: () => void;
  onDelete?: () => void;
  onSave?: (data: FormData) => void;
}

export default function DebtorAccountForm({
  open,
  onClose,
  onDelete,
  onSave,
}: DebtorAccountFormProps) {
  const [formData, setFormData] = useState<FormData>({
    account_number: "",
    name: "",
    search_name: "",
    contact_person: "",
    telephone1: "",
    telephone2: "",
    fax: "",
    email: "",
    postal_address_line1: "",
    postal_address_line2: "",
    postal_address_line3: "",
    postal_code: "",
    delivery_address_line1: "",
    delivery_address_line2: "",
    delivery_address_line3: "",
    delivery_code: "",
    vat_number: "",
    additional_info: "",
    trade_discount: 0,
    credit_limit: 0,
    terms: 30,
    prompt_discount_percentage: 0,
    price_level: 1,
    charge_interest: false,
    print_discount_on_invoice: false,
    print_balance_on_documents: true,
    is_blocked: false,
    block_reason: "",
    account_category: "",
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<{ [key: string]: boolean }>({});

  // Required fields
  const requiredFields = [
    "account_number",
    "name",
    "contact_person",
    "telephone1",
    "email",
  ];

  // Field validation rules
  const validateField = (fieldName: string, value: any): string | null => {
    switch (fieldName) {
      case "account_number":
        if (!value || !value.trim()) return "Account number is required";
        if (value.length > 20) return "Account number cannot exceed 20 characters";
        return null;

      case "name":
        if (!value || !value.trim()) return "Debtor name is required";
        if (value.length < 3) return "Name must be at least 3 characters";
        if (value.length > 200) return "Name cannot exceed 200 characters";
        return null;

      case "search_name":
        if (value && value.length > 50) return "Search name cannot exceed 50 characters";
        return null;

      case "contact_person":
        if (!value || !value.trim()) return "Contact person is required";
        if (value.length > 100) return "Contact person cannot exceed 100 characters";
        return null;

      case "telephone1":
        if (!value || !value.trim()) return "Primary telephone is required";
        if (!/^[\d\s\-\+\(\)]{5,}$/.test(value)) 
          return "Please enter a valid phone number (minimum 5 digits)";
        if (value.length > 50) return "Telephone cannot exceed 50 characters";
        return null;

      case "telephone2":
        if (value && value.length > 50) return "Telephone cannot exceed 50 characters";
        if (value && !/^[\d\s\-\+\(\)]{5,}$/.test(value) && value.trim())
          return "Please enter a valid phone number";
        return null;

      case "email":
        if (!value || !value.trim()) return "Email is required";
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))
          return "Please enter a valid email address";
        if (value.length > 254) return "Email cannot exceed 254 characters";
        return null;

      case "fax":
        if (value && value.length > 50) return "Fax cannot exceed 50 characters";
        return null;

      case "vat_number":
        if (value && value.length > 50) return "VAT number cannot exceed 50 characters";
        return null;

      case "postal_code":
        if (formData.postal_address_line1 && !value)
          return "Postal code is required if providing postal address";
        if (value && value.length > 20) return "Postal code cannot exceed 20 characters";
        return null;

      case "trade_discount":
        if (value < 0) return "Trade discount cannot be negative";
        if (value > 100) return "Trade discount cannot exceed 100%";
        return null;

      case "credit_limit":
        if (value < 0) return "Credit limit cannot be negative";
        if (value > 999999.99) return "Credit limit exceeds maximum allowed value";
        return null;

      case "prompt_discount_percentage":
        if (value < 0) return "Prompt discount cannot be negative";
        if (value > 100) return "Prompt discount cannot exceed 100%";
        return null;

      case "price_level":
        if (value < 1 || value > 3) return "Price level must be between 1 and 3";
        return null;

      case "terms":
        const allowedTerms = [0, 30, 60, 90, 120, 150, 180];
        if (!allowedTerms.includes(value)) 
          return "Payment terms must be 0, 30, 60, 90, 120, 150, or 180 days";
        return null;

      case "block_reason":
        if (formData.is_blocked && !value)
          return "Block reason is required when blocking account";
        return null;

      default:
        return null;
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const newValue =
      type === "checkbox" ? (e.target as HTMLInputElement).checked : value;

    setFormData((prev) => ({
      ...prev,
      [name]: newValue,
    }));

    // Auto-update search_name from name
    if (name === "name") {
      setFormData((prev) => ({
        ...prev,
        search_name: (value || "").substring(0, 50).toUpperCase(),
      }));
    }

    // Clear error when field is corrected
    if (touched[name]) {
      const error = validateField(name, newValue);
      setErrors((prev) => {
        const newErrors = { ...prev };
        if (error) {
          newErrors[name] = error;
        } else {
          delete newErrors[name];
        }
        return newErrors;
      });
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));

    const error = validateField(name, value);
    setErrors((prev) => {
      const newErrors = { ...prev };
      if (error) {
        newErrors[name] = error;
      } else {
        delete newErrors[name];
      }
      return newErrors;
    });
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Check required fields
    requiredFields.forEach((field) => {
      const error = validateField(
        field,
        formData[field as keyof FormData]
      );
      if (error) {
        newErrors[field] = error;
      }
    });

    // Check optional fields that have values
    const optionalFields = Object.keys(formData).filter(
      (key) => !requiredFields.includes(key)
    );

    optionalFields.forEach((field) => {
      const value = formData[field as keyof FormData];
      if (value !== undefined && value !== null && value !== false && value !== 0 && value !== "") {
        const error = validateField(field, value);
        if (error) {
          newErrors[field] = error;
        }
      }
    });

    // Custom validation: at least one contact method
    const hasContact =
      formData.telephone1 || formData.email || formData.contact_person;
    if (!hasContact) {
      newErrors.contact_person =
        "Please provide at least one contact method (name, phone, or email)";
    }

    // Cash customers cannot have payment terms
    if (formData.account_category === "C" && formData.terms > 0) {
      newErrors.terms = "Cash customers cannot have payment terms";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (validateForm()) {
      if (onSave) {
        onSave(formData);
      }
      setErrors({});
      setTouched({});
    }
  };

  const renderField = (
    label: string,
    name: keyof FormData,
    type: string = "text",
    required: boolean = false,
    options?: { value: any; label: string }[]
  ) => {
    const value = formData[name];
    const error = errors[name];
    const isTouched = touched[name];
    const isRequired = required || requiredFields.includes(name);

    return (
      <div
        key={name}
        className={`${
          type === "textarea" ? "col-span-2" : "col-span-1"
        } flex flex-col`}
      >
        <label className="text-sm font-medium mb-1">
          {label}
          {isRequired && <span className="text-red-500">*</span>}
        </label>
        {type === "textarea" ? (
          <textarea
            name={name}
            value={String(value || "")}
            onChange={handleChange}
            onBlur={handleBlur}
            rows={2}
            className={`border p-2 rounded text-sm ${
              error && isTouched
                ? "border-red-500 bg-red-50"
                : "border-gray-300"
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
          />
        ) : type === "select" ? (
          <select
            name={name}
            value={String(value || "")}
            onChange={handleChange}
            onBlur={handleBlur}
            className={`border p-2 rounded text-sm ${
              error && isTouched
                ? "border-red-500 bg-red-50"
                : "border-gray-300"
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
          >
            <option value="">-- Select --</option>
            {options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : type === "checkbox" ? (
          <input
            type="checkbox"
            name={name}
            checked={value as boolean}
            onChange={handleChange}
            className="w-4 h-4 rounded"
          />
        ) : (
          <input
            type={type}
            name={name}
            value={String(value || "")}
            onChange={handleChange}
            onBlur={handleBlur}
            className={`border p-2 rounded text-sm ${
              error && isTouched
                ? "border-red-500 bg-red-50"
                : "border-gray-300"
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
          />
        )}
        {error && isTouched && (
          <p className="text-red-500 text-xs mt-1">{error}</p>
        )}
      </div>
    );
  };

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
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-2 gap-4 text-sm">
          {/* Basic Information */}
          <div className="col-span-2 mb-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              Basic Information
            </h3>
          </div>

          {renderField("Account Number", "account_number", "text", true)}
          {renderField("Name", "name", "text", true)}
          {renderField("Search Name", "search_name")}
          {renderField("Contact Person", "contact_person", "text", true)}
          {renderField("Account Category", "account_category", "select", false, [
            { value: "", label: "Balance Forward" },
            { value: "O", label: "Open Item" },
            { value: "C", label: "Cash Customer" },
          ])}

          {/* Contact Information */}
          <div className="col-span-2 mb-4 mt-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              Contact Information
            </h3>
          </div>

          {renderField("Primary Telephone", "telephone1", "tel", true)}
          {renderField("Secondary Telephone", "telephone2", "tel")}
          {renderField("Email", "email", "email", true)}
          {renderField("Fax", "fax", "tel")}
          {renderField("VAT/Tax Number", "vat_number")}

          {/* Address Information */}
          <div className="col-span-2 mb-4 mt-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              Address Information
            </h3>
          </div>

          {renderField("Postal Address Line 1", "postal_address_line1", "text")}
          {renderField("Postal Address Line 2", "postal_address_line2", "text")}
          {renderField("Postal Address Line 3", "postal_address_line3", "text")}
          {renderField("Postal Code", "postal_code")}
          {renderField("Delivery Address Line 1", "delivery_address_line1", "text")}
          {renderField("Delivery Address Line 2", "delivery_address_line2", "text")}
          {renderField("Delivery Address Line 3", "delivery_address_line3", "text")}
          {renderField("Delivery Code", "delivery_code")}

          {/* Credit Terms */}
          <div className="col-span-2 mb-4 mt-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              Credit Terms
            </h3>
          </div>

          {renderField("Credit Limit", "credit_limit", "number")}
          {renderField("Payment Terms (Days)", "terms", "select", false, [
            { value: 0, label: "Immediate (0)" },
            { value: 30, label: "30 Days" },
            { value: 60, label: "60 Days" },
            { value: 90, label: "90 Days" },
            { value: 120, label: "120 Days" },
            { value: 150, label: "150 Days" },
            { value: 180, label: "180 Days" },
          ])}
          {renderField("Trade Discount (%)", "trade_discount", "number")}
          {renderField("Prompt Discount (%)", "prompt_discount_percentage", "number")}
          {renderField("Price Level", "price_level", "select", false, [
            { value: 1, label: "Level 1" },
            { value: 2, label: "Level 2" },
            { value: 3, label: "Level 3" },
          ])}

          {/* Additional Settings */}
          <div className="col-span-2 mb-4 mt-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              Settings
            </h3>
          </div>

          <div className="flex items-center gap-2">
            {renderField("Charge Interest", "charge_interest", "checkbox")}
          </div>
          <div className="flex items-center gap-2">
            {renderField("Print Discount on Invoice", "print_discount_on_invoice", "checkbox")}
          </div>
          <div className="flex items-center gap-2">
            {renderField("Print Balance on Documents", "print_balance_on_documents", "checkbox")}
          </div>
          <div className="flex items-center gap-2">
            {renderField("Block Account", "is_blocked", "checkbox")}
          </div>

          {formData.is_blocked && renderField("Block Reason", "block_reason", "textarea")}

          {/* Additional Information */}
          <div className="col-span-2 mb-4 mt-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              Notes
            </h3>
          </div>

          {renderField("Additional Information", "additional_info", "textarea")}

          {/* Error Summary */}
          {Object.keys(errors).length > 0 && (
            <div className="col-span-2 p-4 bg-red-50 border border-red-200 rounded">
              <p className="text-red-700 font-semibold mb-2">
                Please fix the following errors:
              </p>
              <ul className="text-red-600 text-sm list-disc list-inside">
                {Object.values(errors).map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </form>

      {/* Footer */}
      <div className="flex justify-between items-center gap-2 p-4 border-t bg-gray-50">
        {/* Delete button (left aligned) */}
        {onDelete && (
          <button
            onClick={onDelete}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
          >
            Delete
          </button>
        )}

        {/* Action buttons (right aligned) */}
        <div className="flex gap-2 ml-auto">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded hover:bg-gray-100 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition disabled:bg-gray-400"
            disabled={Object.keys(errors).length > 0 && Object.keys(touched).length > 0}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
