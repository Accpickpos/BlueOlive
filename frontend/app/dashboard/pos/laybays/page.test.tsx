import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import LaybaysPage from './page';

const mockUseAuth = vi.fn();
const mockListLaybyes = vi.fn();

vi.mock('@/lib/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock('@/lib/posApi', () => ({
  usePOSAPI: () => ({ listLaybyes: mockListLaybyes }),
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

describe('LaybaysPage', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
    mockListLaybyes.mockReset();
  });

  it('renders laybays returned by the API once loaded', async () => {
    mockUseAuth.mockReturnValue({ user: authenticatedUser, isLoading: false });
    mockListLaybyes.mockResolvedValue({
      results: [
        {
          id: 1,
          laybye_number: 'LAY-0001',
          customer_name: 'Jane Doe',
          total_amount: 500,
          balance_due: 200,
          status: 'ACTIVE',
        },
      ],
    });

    render(<LaybaysPage />);

    expect(await screen.findByText('LAY-0001')).toBeInTheDocument();
    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(mockListLaybyes).toHaveBeenCalledTimes(1);
  });

  it('shows the empty state when the API call fails instead of crashing', async () => {
    mockUseAuth.mockReturnValue({ user: authenticatedUser, isLoading: false });
    mockListLaybyes.mockRejectedValue(new Error('network error'));

    render(<LaybaysPage />);

    await waitFor(() => {
      expect(screen.getByText('No laybays found')).toBeInTheDocument();
    });
  });

  it('does not call the API while auth is still loading', () => {
    mockUseAuth.mockReturnValue({ user: null, isLoading: true });

    render(<LaybaysPage />);

    expect(mockListLaybyes).not.toHaveBeenCalled();
  });
});
