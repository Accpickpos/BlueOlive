import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import LaybyeDetail from './page';

const mockUseAuth = vi.fn();
const mockGetLaybye = vi.fn();
const mockPush = vi.fn();

vi.mock('@/lib/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock('@/lib/posApi', () => ({
  usePOSAPI: () => ({ getLaybye: mockGetLaybye }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ id: '1' }),
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

describe('LaybyeDetail', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
    mockGetLaybye.mockReset();
    mockPush.mockReset();
    mockUseAuth.mockReturnValue({ user: authenticatedUser, isLoading: false });
  });

  it('renders the loaded laybye', async () => {
    mockGetLaybye.mockResolvedValue({
      id: 1,
      laybye_number: 'LAY-0001',
      status: 'ACTIVE',
      balance_due: 100,
      lines: [],
      payments: [],
    });

    render(<LaybyeDetail />);

    expect(await screen.findByText('Laybye LAY-0001')).toBeInTheDocument();
    expect(mockGetLaybye).toHaveBeenCalledWith('1');
  });

  it('shows the error state instead of crashing when the fetch fails', async () => {
    mockGetLaybye.mockRejectedValue(new Error('Laybye not found on server'));

    render(<LaybyeDetail />);

    expect(await screen.findByText('Laybye not found on server')).toBeInTheDocument();
  });
});
