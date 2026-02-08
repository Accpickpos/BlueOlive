import React from 'react';

export const metadata = {
  title: 'Cash Book',
  description: 'Cash Book Management System',
};

export default function CashBookLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
