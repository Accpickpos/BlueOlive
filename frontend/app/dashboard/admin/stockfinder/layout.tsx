import React from 'react';
import AddonGate from '@/components/AddonGate';

export const metadata = {
  title: 'Stockfinder',
  description: 'Stockfinder Integration',
};

export default function StockfinderLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AddonGate addon="stockfinder">{children}</AddonGate>;
}
