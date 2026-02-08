"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  FileText,
  DollarSign,
  BarChart,
  Settings,
  CreditCard,
  ShoppingCart,
  Layers,
  ClipboardList,
  Search,
  Users,
  ChevronDown,
  Receipt,
  UserCog,
  Briefcase,
  ArrowDownLeft,
  Wrench,
  Banknote,
  Lock,
} from "lucide-react";

// ================== MENU CONFIG ==================
const menuConfig = [
  { type: "link", name: "Dashboard", href: "/dashboard", icon: Home },

  {
    type: "dropdown",
    name: "Admin",
    base: "/dashboard/admin",
    icon: Briefcase,
    children: [
      {
        type: "nested",
        name: "Debtors",
        base: "/dashboard/admin/debtors",
        icon: Users,
        children: [
          { type: "link", name: "Maintenance", href: "/dashboard/admin/debtors/maintenance", icon: FileText },
          { type: "link", name: "Transactions", href: "/dashboard/admin/debtors/transactions", icon: DollarSign },
          { type: "link", name: "Enquiries", href: "/dashboard/admin/debtors/enquiries", icon: Search },
          { type: "link", name: "Reports", href: "/dashboard/admin/debtors/reports", icon: BarChart },
        ],
      },
      {
        type: "nested",
        name: "Creditors",
        base: "/dashboard/admin/creditors",
        icon: CreditCard,
        children: [
          { type: "link", name: "Maintenance", href: "/dashboard/admin/creditors/maintenance", icon: FileText },
          { type: "link", name: "Transactions", href: "/dashboard/admin/creditors/transactions", icon: DollarSign },
          { type: "link", name: "Enquiries", href: "/dashboard/admin/creditors/enquiries", icon: Search },
          { type: "link", name: "Reports", href: "/dashboard/admin/creditors/reports", icon: BarChart },
        ],
      },
      {
        type: "nested",
        name: "Stock Control",
        base: "/dashboard/admin/stock-control",
        icon: Layers,
        children: [
          { type: "link", name: "Maintenance", href: "/dashboard/admin/stock-control/maintenance", icon: FileText },
          { type: "link", name: "Transactions", href: "/dashboard/admin/stock-control/transactions", icon: DollarSign },
          { type: "link", name: "Enquiries", href: "/dashboard/admin/stock-control/enquiries", icon: Search },
          { type: "link", name: "Reports", href: "/dashboard/admin/stock-control/reports", icon: BarChart },
        ],
      },
      {
        type: "nested",
        name: "Cash Book",
        base: "/dashboard/admin/cash-book",
        icon: Receipt,
        children: [
          { type: "link", name: "Maintenance", href: "/dashboard/admin/cash-book/maintenance", icon: FileText },
          { type: "link", name: "Transactions", href: "/dashboard/admin/cash-book/transactions", icon: DollarSign },
          { type: "link", name: "Enquiries", href: "/dashboard/admin/cash-book/enquiries", icon: Search },
          { type: "link", name: "Reports", href: "/dashboard/admin/cash-book/reports", icon: BarChart },
        ],
      },
      {
        type: "nested",
        name: "Purchase Orders",
        base: "/dashboard/admin/purchase-orders",
        icon: Receipt,
        children: [
          { type: "link", name: "Maintenance", href: "/dashboard/admin/purchase-orders/maintenance", icon: FileText },
          { type: "link", name: "Transactions", href: "/dashboard/admin/purchase-orders/transactions", icon: DollarSign },
          { type: "link", name: "Enquiries", href: "/dashboard/admin/purchase-orders/enquiries", icon: Search },
          { type: "link", name: "Reports", href: "/dashboard/admin/purchase-orders/reports", icon: BarChart },
        ],
      },
      { type: "link", name: "Settings", href: "/dashboard/admin/settings", icon: UserCog },
    ],
  },

  {
    type: "dropdown",
    name: "POS",
    base: "/dashboard/pos",
    icon: ShoppingCart,
    children: [
      { type: "link", name: "Invoices", href: "/dashboard/pos/invoices", icon: FileText },
      { type: "link", name: "Receipts", href: "/dashboard/pos/receipts", icon: Receipt },
      { type: "link", name: "Cash Sales", href: "/dashboard/pos/cash-sales", icon: ShoppingCart },
      { type: "link", name: "Cash Return", href: "/dashboard/pos/cash-return", icon: ArrowDownLeft },
      { type: "link", name: "Credit Note", href: "/dashboard/pos/credit-note", icon: CreditCard },
      { type: "link", name: "Cash Control", href: "/dashboard/pos/cash-control", icon: Lock },
      { type: "link", name: "Payout", href: "/dashboard/pos/payout", icon: DollarSign },
      { type: "link", name: "Job Costing", href: "/dashboard/pos/job-costing", icon: Layers },
      { type: "link", name: "Quotes", href: "/dashboard/pos/quotes", icon: ClipboardList },
      { type: "link", name: "Laybays", href: "/dashboard/pos/laybays", icon: Banknote },
      { type: "link", name: "Repair Controls", href: "/dashboard/pos/repair-controls", icon: Wrench },
      { type: "link", name: "Cheque Cashing", href: "/dashboard/pos/cheque-cashing", icon: CreditCard },
      { type: "link", name: "Transaction Query", href: "/dashboard/pos/transaction-query", icon: Search },
      { type: "link", name: "Reports", href: "/dashboard/pos/reports", icon: BarChart },
      { type: "link", name: "Settings", href: "/dashboard/pos/settings", icon: Settings },
    ],
  },

  { type: "link", name: "Expenses", href: "/dashboard/expenses", icon: DollarSign },
  { type: "link", name: "Reports", href: "/dashboard/reports", icon: BarChart },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [openDropdowns, setOpenDropdowns] = useState<{ [key: string]: boolean }>({});
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true); // Ensure menu only renders on client
  }, []);

  const toggleDropdown = (name: string) => {
    setOpenDropdowns((prev) => ({
      ...prev,
      [name]: !prev[name],
    }));
  };

  const hasAccess = (menu: any) => true; // Replace with your RBAC logic

  // ================== RENDER MENU ==================
  const renderMenu = (menu: any, depth = 0) => {
    if (!hasAccess(menu)) return null;

    const filteredChildren = menu.children?.filter(hasAccess);

    if (menu.type === "link") {
      return (
        <Link
          key={menu.name}
          href={menu.href}
          className={`flex items-center p-3 rounded-lg transition ${
            pathname === menu.href
              ? "bg-gray-200 font-semibold"
              : "hover:bg-gray-100"
          }`}
          style={{ paddingLeft: `${depth * 16 + 12}px` }}
        >
          {menu.icon && <menu.icon className="mr-3 h-5 w-5" />}
          {menu.name}
        </Link>
      );
    }

    if (menu.type === "dropdown" || menu.type === "nested") {
      if (!filteredChildren?.length) return null;

      return (
        <div key={menu.name}>
          <button
            onClick={() => toggleDropdown(menu.name)}
            className={`flex items-center justify-between w-full ${
              menu.type === "dropdown" ? "p-3" : "p-2 text-sm"
            } rounded-lg hover:bg-gray-100 ${
              pathname.startsWith(menu.base) ? "bg-gray-200 font-semibold" : ""
            }`}
            style={{ paddingLeft: `${depth * 16 + 12}px` }}
          >
            <span className="flex items-center gap-3">
              {menu.icon && (
                <menu.icon className={menu.type === "dropdown" ? "h-5 w-5" : "h-4 w-4"} />
              )}
              {menu.name}
            </span>
            <ChevronDown
              className={`h-4 w-4 transform transition-transform ${
                openDropdowns[menu.name] ? "rotate-180" : ""
              }`}
            />
          </button>

          <div
            className={`ml-4 mt-1 flex flex-col gap-1 overflow-hidden transition-all duration-300 ${
              openDropdowns[menu.name]
                ? "max-h-[1000px] opacity-100"
                : "max-h-0 opacity-0"
            }`}
          >
            {filteredChildren.map((child: any) => renderMenu(child, depth + 1))}
          </div>
        </div>
      );
    }
  };

  return (
    <aside className="w-64 bg-white h-screen shadow-md p-4 flex flex-col">
      {/* ========= SITE LOGO ========= */}
      <div className="flex items-center justify-center mb-6">
        <Link href="/" className="flex items-center gap-2">
          {/* Logo placeholder - replace with actual logo.png when available */}
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
            BO
          </div>
          <span className="text-lg font-bold">BlueOlive</span>
        </Link>
      </div>

      {/* ========= MENU ========= */}
      {mounted && (
        <nav className="flex flex-col gap-1">
          {menuConfig.map((menu) => renderMenu(menu))}
        </nav>
      )}
    </aside>
  );
}
