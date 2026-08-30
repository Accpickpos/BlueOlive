import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import QuotesPage from './page';

const mockUseAuth = vi.fn();
const mockListQuotations = vi.fn();

vi.mock('@/lib/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock('@/lib/posApi', () => ({
  usePOSAPI: () => ({ listQuotations: mockListQuotations }),
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

describe('QuotesPage', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
    mockListQuotations.mockReset();
  });

  it('renders quotes returned by the API once loaded', async () => {
    mockUseAuth.mockReturnValue({ user: authenticatedUser, isLoading: false });
    mockListQuotations.mockResolvedValue({
      results: [
        {
          id: 1,
          quotation_number: 'QUO-0001',
          customer_name: 'Jane Doe',
          total_amount: 750,
          expiry_date: '2026-09-01',
          status: 'ACTIVE',
        },
      ],
    });

    render(<QuotesPage />);

    expect(await screen.findByText('QUO-0001')).toBeInTheDocument();
    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(mockListQuotations).toHaveBeenCalledTimes(1);
  });

  it('shows the empty state when the API call fails instead of crashing', async () => {
    mockUseAuth.mockReturnValue({ user: authenticatedUser, isLoading: false });
    mockListQuotations.mockRejectedValue(new Error('network error'));

    render(<QuotesPage />);

    await waitFor(() => {
      expect(screen.getByText('No quotes found')).toBeInTheDocument();
    });
  });
});
