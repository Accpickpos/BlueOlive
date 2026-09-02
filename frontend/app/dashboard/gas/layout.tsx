import React from 'react';
import AddonGate from '@/components/AddonGate';

export const metadata = {
  title: 'Gas',
  description: 'LPG Cylinder Rental Management',
};

export default function GasLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AddonGate addon="gas">{children}</AddonGate>;
}
