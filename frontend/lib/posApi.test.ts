import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockApi = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
}));

vi.mock('./api', () => ({
  api: mockApi,
}));

import { POSTransactionAPI } from './posApi';
import { ENDPOINTS } from './api-config';

describe('POSTransactionAPI', () => {
  let posAPI: POSTransactionAPI;

  beforeEach(() => {
    mockApi.get.mockReset();
    mockApi.post.mockReset();
    mockApi.put.mockReset();
    mockApi.patch.mockReset();
    mockApi.delete.mockReset();
    posAPI = new POSTransactionAPI();
  });

  it('listLaybyes issues a GET against the laybyes endpoint and returns response.data', async () => {
    mockApi.get.mockResolvedValue({ status: 200, data: { results: [], count: 0 } });

    const result = await posAPI.listLaybyes();

    expect(mockApi.get).toHaveBeenCalledWith(ENDPOINTS.POS.LAYBYES);
    expect(result).toEqual({ results: [], count: 0 });
  });

  it('listLaybyes appends only truthy filters as query params', async () => {
    mockApi.get.mockResolvedValue({ status: 200, data: { results: [], count: 0 } });

    await posAPI.listLaybyes({ status: 'ACTIVE', page: 2, debtor_account_number: '' });

    const calledEndpoint = mockApi.get.mock.calls[0][0] as string;
    expect(calledEndpoint).toContain(`${ENDPOINTS.POS.LAYBYES}?`);
    expect(calledEndpoint).toContain('status=ACTIVE');
    expect(calledEndpoint).toContain('page=2');
    expect(calledEndpoint).not.toContain('debtor_account_number');
  });

  it('createLaybye issues a POST with the given payload', async () => {
    mockApi.post.mockResolvedValue({ status: 201, data: { id: 1 } });

    const payload = {
      customer_name: 'Jane Doe',
      expiry_date: '2026-12-31',
      deposit_amount: 100,
      lines: [],
    };
    const result = await posAPI.createLaybye(payload as any);

    expect(mockApi.post).toHaveBeenCalledWith(ENDPOINTS.POS.LAYBYES, payload);
    expect(result).toEqual({ id: 1 });
  });

  it('surfaces a server-provided "detail" message as the thrown error', async () => {
    mockApi.get.mockRejectedValue({
      response: { status: 404, data: { detail: 'Laybye not found.' } },
      message: 'Request failed with status code 404',
    });

    await expect(posAPI.getLaybye(999)).rejects.toThrow('Laybye not found.');
  });

  it('joins DRF field-validation errors into a single readable message', async () => {
    mockApi.post.mockRejectedValue({
      response: {
        status: 400,
        data: { deposit_amount: ['This field is required.'], expiry_date: ['This field is required.'] },
      },
      message: 'Request failed with status code 400',
    });

    await expect(posAPI.createLaybye({} as any)).rejects.toThrow(
      /deposit_amount: This field is required\..*expiry_date: This field is required\./
    );
  });

  it('re-throws the original error when the response has no usable data', async () => {
    const originalError = new Error('Network Error');
    mockApi.get.mockRejectedValue(originalError);

    await expect(posAPI.getLaybye(1)).rejects.toBe(originalError);
  });
});
