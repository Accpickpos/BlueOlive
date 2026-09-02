import React from 'react';
import AddonGate from '@/components/AddonGate';

export const metadata = {
  title: 'General Ledger',
  description: 'General Ledger Management System',
};

export default function GeneralLedgerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AddonGate addon="general_ledger">{children}</AddonGate>;
}
