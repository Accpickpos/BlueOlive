import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import QuoteDetail from './page';

const mockUseAuth = vi.fn();
const mockGetQuotation = vi.fn();
const mockPush = vi.fn();

vi.mock('@/lib/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock('@/lib/posApi', () => ({
  usePOSAPI: () => ({ getQuotation: mockGetQuotation }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ id: '1' }),
}));

vi.mock('@/components/pos/DebtorPicker', () => ({
  DebtorPicker: () => null,
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

describe('QuoteDetail', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
    mockGetQuotation.mockReset();
    mockPush.mockReset();
    mockUseAuth.mockReturnValue({ user: authenticatedUser, isLoading: false });
  });

  it('renders the loaded quotation', async () => {
    mockGetQuotation.mockResolvedValue({
      id: 1,
      quotation_number: 'QUO-0001',
      status: 'ACTIVE',
      total_amount: 500,
      lines: [],
    });

    render(<QuoteDetail />);

    expect(await screen.findByText('Quotation QUO-0001')).toBeInTheDocument();
    expect(mockGetQuotation).toHaveBeenCalledWith('1');
  });

  it('shows the error state instead of crashing when the fetch fails', async () => {
    mockGetQuotation.mockRejectedValue(new Error('Quotation not found on server'));

    render(<QuoteDetail />);

    expect(await screen.findByText('Quotation not found on server')).toBeInTheDocument();
  });
});
