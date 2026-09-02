'use client';

import OwnerRoute from '@/components/OwnerRoute';
import { ReactNode } from 'react';

export default function ApiKeysLayout({ children }: { children: ReactNode }) {
  return <OwnerRoute>{children}</OwnerRoute>;
}
