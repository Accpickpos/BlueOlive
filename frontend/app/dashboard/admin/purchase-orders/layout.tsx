import type { ReactNode } from 'react';

export const metadata = {
  title: 'Purchase Orders Management - Admin',
  description: 'Manage purchase orders, goods receipts, and inquiries',
};

export default function PurchaseOrdersLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <>{children}</>;
}
