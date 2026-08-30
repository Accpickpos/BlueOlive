/**
 * General Ledger — Integration Settings + Integration Transfer API Client
 * Base URL: /api/v1/general-ledger/integration-settings/, /integration/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import {
  GLIntegrationSettings,
  IntegrationTransferRequest,
  IntegrationTransferResponse,
  IntegrationOutstandingResponse,
} from '../types/generalLedger';

export const glIntegrationApi = {
  getSettings: async () => {
    const { data } = await api.get<GLIntegrationSettings>(
      ENDPOINTS.GENERAL_LEDGER.INTEGRATION_SETTINGS_CURRENT
    );
    return data;
  },

  updateSettings: async (body: Partial<GLIntegrationSettings>) => {
    const { data } = await api.patch<GLIntegrationSettings>(
      ENDPOINTS.GENERAL_LEDGER.INTEGRATION_SETTINGS_CURRENT, body
    );
    return data;
  },

  transfer: async (body: IntegrationTransferRequest) => {
    const { data } = await api.post<IntegrationTransferResponse>(
      ENDPOINTS.GENERAL_LEDGER.INTEGRATION_TRANSFER, body
    );
    return data;
  },

  outstanding: async () => {
    const { data } = await api.get<IntegrationOutstandingResponse>(
      ENDPOINTS.GENERAL_LEDGER.INTEGRATION_OUTSTANDING
    );
    return data;
  },
};
