import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import InvoiceDetail from './page';

const mockUseAuth = vi.fn();
const mockGetInvoice = vi.fn();
const mockPush = vi.fn();

vi.mock('@/lib/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock('@/lib/posApi', () => ({
  usePOSAPI: () => ({ getInvoice: mockGetInvoice }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ id: '1' }),
}));

vi.mock('@/lib/printUtils', () => ({
  printInvoice: vi.fn(),
  emailInvoice: vi.fn(),
}));

const authenticatedUser = {
  id: 1,
  username: 'cashier',
  email: 'cashier@example.com',
  role: 'CASHIER',
  is_superuser: false,
  is_admin: false,
  tenant_id: 1,
  tenant: { id: 1, slug: 'demo', name: 'Demo Tenant' },
};

describe('InvoiceDetail', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
    mockGetInvoice.mockReset();
    mockPush.mockReset();
    mockUseAuth.mockReturnValue({ user: authenticatedUser, isLoading: false });
  });

  it('renders the loaded invoice', async () => {
    mockGetInvoice.mockResolvedValue({
      id: 1,
      invoice_number: 'INV-0001',
      status: 'POSTED',
      total_amount: 1000,
      lines: [],
    });

    render(<InvoiceDetail />);

    expect(await screen.findByText('Invoice INV-0001')).toBeInTheDocument();
    expect(mockGetInvoice).toHaveBeenCalledWith('1');
  });

  it('shows the error state instead of crashing when the fetch fails', async () => {
    mockGetInvoice.mockRejectedValue(new Error('Invoice not found on server'));

    render(<InvoiceDetail />);

    expect(await screen.findByText('Invoice not found on server')).toBeInTheDocument();
  });
});
