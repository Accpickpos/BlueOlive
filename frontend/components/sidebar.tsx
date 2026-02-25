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
  MessageSquare,
  Package,
  ArrowRight,
  Upload,
  PanelLeftClose,
  PanelLeftOpen,
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
      { type: "link", name: "Import Data", href: "/dashboard/admin/import", icon: Upload },
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

  { type: "link", name: "Messaging", href: "/dashboard/messaging", icon: MessageSquare },
  { type: "link", name: "Inter-Branch Transfers", href: "/dashboard/ibt", icon: ArrowRight },
  { type: "link", name: "Inter-Branch Items", href: "/dashboard/ibi", icon: Package },
  { type: "link", name: "Stock Consolidation", href: "/dashboard/stock-consolidation", icon: Layers },
  { type: "link", name: "Expenses", href: "/dashboard/expenses", icon: DollarSign },
  { type: "link", name: "Reports", href: "/dashboard/reports", icon: BarChart },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [openDropdowns, setOpenDropdowns] = useState<{ [key: string]: boolean }>({});
  const [mounted, setMounted] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleDropdown = (name: string) => {
    if (collapsed) {
      setCollapsed(false);
      setOpenDropdowns((prev) => ({ ...prev, [name]: true }));
      return;
    }
    setOpenDropdowns((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const hasAccess = (menu: any) => true;

  // ================== RENDER MENU ==================
  const renderMenu = (menu: any, depth = 0) => {
    if (!hasAccess(menu)) return null;
    const filteredChildren = menu.children?.filter(hasAccess);

    if (menu.type === "link") {
      return (
        <Link
          key={menu.name}
          href={menu.href}
          title={collapsed && depth === 0 ? menu.name : undefined}
          className={`group flex items-center gap-3 rounded-lg transition-all duration-150 relative
            ${collapsed && depth === 0 ? "justify-center px-0 py-3" : "px-3 py-2.5"}
            ${pathname === menu.href
              ? "bg-blue-50 text-blue-700 font-semibold"
              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            }`}
          style={!collapsed ? { paddingLeft: `${depth * 14 + 12}px` } : undefined}
        >
          {menu.icon && (
            <menu.icon
              className={`shrink-0 transition-colors
                ${pathname === menu.href ? "text-blue-600" : "text-gray-400 group-hover:text-gray-600"}
                ${depth === 0 ? "h-5 w-5" : "h-4 w-4"}`}
            />
          )}
          {(!collapsed || depth > 0) && (
            <span className={`truncate leading-tight ${depth === 0 ? "text-sm" : "text-xs"}`}>
              {menu.name}
            </span>
          )}
          {/* Active indicator bar */}
          {pathname === menu.href && (
            <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-blue-500 rounded-r-full" />
          )}
        </Link>
      );
    }

    if (menu.type === "dropdown" || menu.type === "nested") {
      if (!filteredChildren?.length) return null;
      const isActive = pathname.startsWith(menu.base);
      const isOpen = openDropdowns[menu.name];

      return (
        <div key={menu.name}>
          <button
            onClick={() => toggleDropdown(menu.name)}
            title={collapsed && depth === 0 ? menu.name : undefined}
            className={`group flex items-center w-full rounded-lg transition-all duration-150 relative
              ${collapsed && depth === 0 ? "justify-center px-0 py-3" : "px-3 gap-3"}
              ${menu.type === "dropdown" ? "py-2.5" : "py-2"}
              ${isActive ? "bg-blue-50 text-blue-700 font-semibold" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"}`}
            style={!collapsed ? { paddingLeft: `${depth * 14 + 12}px` } : undefined}
          >
            {/* Active indicator */}
            {isActive && (
              <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-blue-500 rounded-r-full" />
            )}
            {menu.icon && (
              <menu.icon
                className={`shrink-0 transition-colors
                  ${isActive ? "text-blue-600" : "text-gray-400 group-hover:text-gray-600"}
                  ${depth === 0 ? "h-5 w-5" : "h-4 w-4"}`}
              />
            )}
            {(!collapsed || depth > 0) && (
              <>
                <span className={`flex-1 text-left truncate leading-tight ${depth === 0 ? "text-sm" : "text-xs"}`}>
                  {menu.name}
                </span>
                <ChevronDown
                  className={`h-3.5 w-3.5 shrink-0 text-gray-400 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
                />
              </>
            )}
          </button>

          {(!collapsed || depth > 0) && (
            <div
              className={`flex flex-col gap-0.5 overflow-hidden transition-all duration-200 ease-in-out ${
                isOpen ? "max-h-[1000px] opacity-100 mt-0.5" : "max-h-0 opacity-0"
              }`}
            >
              {/* Subtle left border for nested groups */}
              <div className="ml-5 pl-3 border-l border-gray-100 flex flex-col gap-0.5">
                {filteredChildren.map((child: any) => renderMenu(child, depth + 1))}
              </div>
            </div>
          )}
        </div>
      );
    }
  };

  return (
    <>
      {/* Sidebar */}
      <aside
        className={`relative flex flex-col h-screen bg-white border-r border-gray-100 shadow-sm transition-all duration-300 ease-in-out shrink-0
          ${collapsed ? "w-16" : "w-64"}`}
      >
        {/* Toggle button — sits on the right edge */}
        <button
          onClick={() => setCollapsed((v) => !v)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="absolute -right-3 top-6 z-20 flex items-center justify-center w-6 h-6 rounded-full bg-white border border-gray-200 shadow-sm text-gray-500 hover:text-blue-600 hover:border-blue-300 hover:shadow-md transition-all duration-150"
        >
          {collapsed
            ? <PanelLeftOpen className="h-3 w-3" />
            : <PanelLeftClose className="h-3 w-3" />
          }
        </button>

        {/* Logo */}
        <div className={`flex items-center h-16 border-b border-gray-100 shrink-0 transition-all duration-300 ${collapsed ? "justify-center px-0" : "px-5 gap-3"}`}>
          <Link href="/" className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center text-white font-bold text-sm shrink-0 shadow-sm">
              BO
            </div>
            {!collapsed && (
              <span className="text-base font-bold text-gray-900 tracking-tight truncate">BlueOlive</span>
            )}
          </Link>
        </div>

        {/* Scrollable nav */}
        {mounted && (
          <nav className="flex-1 overflow-y-auto overflow-x-hidden py-3 px-2 flex flex-col gap-0.5 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent">
            {menuConfig.map((menu) => renderMenu(menu))}
          </nav>
        )}

        {/* Bottom user hint when collapsed */}
        {collapsed && (
          <div className="shrink-0 h-12 border-t border-gray-100 flex items-center justify-center">
            <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
              <UserCog className="h-4 w-4" />
            </div>
          </div>
        )}
      </aside>
    </>
  );
}