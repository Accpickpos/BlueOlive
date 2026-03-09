/**
 * Creditors Documents API Client
 * Handles all document-related endpoints for creditors.
 *
 * Base URL: /api/v1/creditors/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';
import {
  TransactionFilters,
  PaginatedResponse,
  GoodsReceivedNote,
  GoodsReceivedNoteCreateData,
  GRNLineItem,
  CreditorInvoice,
  CreditorInvoiceCreateData,
  InvoiceLineItem,
  CreditorCreditNote,
  CreditorCreditNoteCreateData,
  CreditNoteLineItem,
  RFC,
  RFCCreateData,
  RFCStatus,
  RFCLineItem,
} from '../types/creditors';

// ============================================================================
// Documents API client
// ============================================================================
export const creditorsDocumentsApi = {

  // ── GOODS RECEIVED NOTES ──────────────────────────────────────────────────
  grns: {
    list: async (filters?: TransactionFilters) => {
      const { data } = await api.get<PaginatedResponse<GoodsReceivedNote>>(
        ENDPOINTS.CREDITORS.GRNS, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<GoodsReceivedNote>(
        `${ENDPOINTS.CREDITORS.GRNS}${id}/`
      );
      return data;
    },

    create: async (body: GoodsReceivedNoteCreateData) => {
      const { data } = await api.post<GoodsReceivedNote>(
        ENDPOINTS.CREDITORS.GRNS, body
      );
      return data;
    },

    update: async (id: string | number, body: Partial<GoodsReceivedNoteCreateData>) => {
      const { data } = await api.patch<GoodsReceivedNote>(
        `${ENDPOINTS.CREDITORS.GRNS}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.GRNS}${id}/`);
    },

    post: async (id: string | number) => {
      const { data } = await api.post<GoodsReceivedNote>(
        ENDPOINTS.CREDITORS.POST_GRN(id)
      );
      return data;
    },

    byCreditor: async (creditorId: string | number, filters?: TransactionFilters) => {
      const { data } = await api.get<GoodsReceivedNote[]>(
        ENDPOINTS.CREDITORS.GRNS_BY_CREDITOR,
        { params: { creditor: creditorId, ...filters } }
      );
      return data;
    },

    lines: {
      list: async (grnId: string | number) => {
        const { data } = await api.get<GRNLineItem[]>(
          ENDPOINTS.CREDITORS.GRN_LINES(grnId)
        );
        return data;
      },
      create: async (grnId: string | number, body: GRNLineItem) => {
        const { data } = await api.post<GRNLineItem>(
          ENDPOINTS.CREDITORS.GRN_LINES(grnId), body
        );
        return data;
      },
      update: async (grnId: string | number, lineId: string | number, body: Partial<GRNLineItem>) => {
        const { data } = await api.patch<GRNLineItem>(
          `${ENDPOINTS.CREDITORS.GRN_LINES(grnId)}${lineId}/`, body
        );
        return data;
      },
      delete: async (grnId: string | number, lineId: string | number) => {
        await api.delete(`${ENDPOINTS.CREDITORS.GRN_LINES(grnId)}${lineId}/`);
      },
    },
  },

  // ── CREDITOR INVOICES (expense) ───────────────────────────────────────────
  invoices: {
    list: async (filters?: TransactionFilters) => {
      const { data } = await api.get<PaginatedResponse<CreditorInvoice>>(
        ENDPOINTS.CREDITORS.INVOICES, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<CreditorInvoice>(
        `${ENDPOINTS.CREDITORS.INVOICES}${id}/`
      );
      return data;
    },

    create: async (body: CreditorInvoiceCreateData) => {
      const { data } = await api.post<CreditorInvoice>(
        ENDPOINTS.CREDITORS.INVOICES, body
      );
      return data;
    },

    update: async (id: string | number, body: Partial<CreditorInvoiceCreateData>) => {
      const { data } = await api.patch<CreditorInvoice>(
        `${ENDPOINTS.CREDITORS.INVOICES}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.INVOICES}${id}/`);
    },

    post: async (id: string | number) => {
      const { data } = await api.post<CreditorInvoice>(
        ENDPOINTS.CREDITORS.POST_INVOICE(id)
      );
      return data;
    },

    lines: {
      list: async (invoiceId: string | number) => {
        const { data } = await api.get<InvoiceLineItem[]>(
          ENDPOINTS.CREDITORS.INVOICE_LINES(invoiceId)
        );
        return data;
      },
      create: async (invoiceId: string | number, body: InvoiceLineItem) => {
        const { data } = await api.post<InvoiceLineItem>(
          ENDPOINTS.CREDITORS.INVOICE_LINES(invoiceId), body
        );
        return data;
      },
      update: async (invoiceId: string | number, lineId: string | number, body: Partial<InvoiceLineItem>) => {
        const { data } = await api.patch<InvoiceLineItem>(
          `${ENDPOINTS.CREDITORS.INVOICE_LINES(invoiceId)}${lineId}/`, body
        );
        return data;
      },
      delete: async (invoiceId: string | number, lineId: string | number) => {
        await api.delete(`${ENDPOINTS.CREDITORS.INVOICE_LINES(invoiceId)}${lineId}/`);
      },
    },
  },

  // ── CREDIT NOTES ──────────────────────────────────────────────────────────
  creditNotes: {
    list: async (filters?: TransactionFilters) => {
      const { data } = await api.get<PaginatedResponse<CreditorCreditNote>>(
        ENDPOINTS.CREDITORS.CREDIT_NOTES, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<CreditorCreditNote>(
        `${ENDPOINTS.CREDITORS.CREDIT_NOTES}${id}/`
      );
      return data;
    },

    create: async (body: CreditorCreditNoteCreateData) => {
      const { data } = await api.post<CreditorCreditNote>(
        ENDPOINTS.CREDITORS.CREDIT_NOTES, body
      );
      return data;
    },

    update: async (id: string | number, body: Partial<CreditorCreditNoteCreateData>) => {
      const { data } = await api.patch<CreditorCreditNote>(
        `${ENDPOINTS.CREDITORS.CREDIT_NOTES}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.CREDIT_NOTES}${id}/`);
    },

    post: async (id: string | number) => {
      const { data } = await api.post<CreditorCreditNote>(
        ENDPOINTS.CREDITORS.POST_CREDIT_NOTE(id)
      );
      return data;
    },

    lines: {
      list: async (cnId: string | number) => {
        const { data } = await api.get<CreditNoteLineItem[]>(
          ENDPOINTS.CREDITORS.CREDIT_NOTE_LINES(cnId)
        );
        return data;
      },
      create: async (cnId: string | number, body: CreditNoteLineItem) => {
        const { data } = await api.post<CreditNoteLineItem>(
          ENDPOINTS.CREDITORS.CREDIT_NOTE_LINES(cnId), body
        );
        return data;
      },
      update: async (cnId: string | number, lineId: string | number, body: Partial<CreditNoteLineItem>) => {
        const { data } = await api.patch<CreditNoteLineItem>(
          `${ENDPOINTS.CREDITORS.CREDIT_NOTE_LINES(cnId)}${lineId}/`, body
        );
        return data;
      },
      delete: async (cnId: string | number, lineId: string | number) => {
        await api.delete(`${ENDPOINTS.CREDITORS.CREDIT_NOTE_LINES(cnId)}${lineId}/`);
      },
    },
  },

  // ── RFC (RETURN FOR CREDIT) ───────────────────────────────────────────────
  rfc: {
    list: async (filters?: { creditor?: number; status?: RFCStatus; page?: number }) => {
      const { data } = await api.get<PaginatedResponse<RFC>>(
        ENDPOINTS.CREDITORS.RFC, { params: filters }
      );
      return data;
    },

    get: async (id: string | number) => {
      const { data } = await api.get<RFC>(`${ENDPOINTS.CREDITORS.RFC}${id}/`);
      return data;
    },

    create: async (body: RFCCreateData) => {
      const { data } = await api.post<RFC>(ENDPOINTS.CREDITORS.RFC, body);
      return data;
    },

    update: async (id: string | number, body: Partial<RFCCreateData>) => {
      const { data } = await api.patch<RFC>(
        `${ENDPOINTS.CREDITORS.RFC}${id}/`, body
      );
      return data;
    },

    delete: async (id: string | number) => {
      await api.delete(`${ENDPOINTS.CREDITORS.RFC}${id}/`);
    },

    byStatus: async (status: RFCStatus) => {
      const { data } = await api.get<RFC[]>(
        ENDPOINTS.CREDITORS.RFC_BY_STATUS, { params: { status } }
      );
      return data;
    },

    updateStatus: async (id: string | number, status: RFCStatus) => {
      const { data } = await api.patch<RFC>(
        ENDPOINTS.CREDITORS.RFC_UPDATE_STATUS(id), { status }
      );
      return data;
    },

    lines: {
      list: async (rfcId: string | number) => {
        const { data } = await api.get<RFCLineItem[]>(
          ENDPOINTS.CREDITORS.RFC_LINES(rfcId)
        );
        return data;
      },
      create: async (rfcId: string | number, body: RFCLineItem) => {
        const { data } = await api.post<RFCLineItem>(
          ENDPOINTS.CREDITORS.RFC_LINES(rfcId), body
        );
        return data;
      },
      update: async (rfcId: string | number, lineId: string | number, body: Partial<RFCLineItem>) => {
        const { data } = await api.patch<RFCLineItem>(
          `${ENDPOINTS.CREDITORS.RFC_LINES(rfcId)}${lineId}/`, body
        );
        return data;
      },
      delete: async (rfcId: string | number, lineId: string | number) => {
        await api.delete(`${ENDPOINTS.CREDITORS.RFC_LINES(rfcId)}${lineId}/`);
      },
    },
  },

};
