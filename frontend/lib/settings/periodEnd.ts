/**
 * Settings — Day End / Month End / Year End (manual §8.6/§8.7)
 * Base URL: /api/v1/settings/system-config/
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';

export interface PeriodEndStatus {
  last_day_end_date: string | null;
  last_month_end_date: string | null;
  last_year_end_date: string | null;
  scheduling: {
    day_end: { enabled: boolean; time: string | null; days_of_week: string | null };
    month_end: { enabled: boolean; day: number | null; time: string | null };
    year_end: { enabled: boolean; month: number | null; day: number | null; time: string | null };
  };
  current_period: { period: number; year: number };
}

export interface PeriodEndResult {
  success: boolean;
  message: string;
  details: Record<string, unknown>;
  errors: string[];
}

export interface AsyncTaskResult {
  message: string;
  task_id: string;
}

export interface DayEndReport {
  id: number;
  process_date: string;
  shop_id: number | null;
  success: boolean;
  message: string;
  details: Record<string, unknown>;
  errors: string[];
  created_at: string;
}

export const periodEndApi = {
  status: async () => {
    const { data } = await api.get<PeriodEndStatus>(ENDPOINTS.SETTINGS.PERIOD_END_STATUS);
    return data;
  },

  runDayEnd: async (params?: { process_date?: string; shop_id?: number; async?: boolean }) => {
    const { data } = await api.post<PeriodEndResult | AsyncTaskResult>(
      ENDPOINTS.SETTINGS.RUN_DAY_END,
      { async: false, ...params }
    );
    return data;
  },

  runMonthEnd: async (params?: { process_date?: string; advance_period?: boolean; async?: boolean }) => {
    const { data } = await api.post<PeriodEndResult | AsyncTaskResult>(
      ENDPOINTS.SETTINGS.RUN_MONTH_END,
      { async: false, ...params }
    );
    return data;
  },

  runYearEnd: async (params?: { process_year?: number; advance_year?: boolean; async?: boolean }) => {
    const { data } = await api.post<PeriodEndResult | AsyncTaskResult>(
      ENDPOINTS.SETTINGS.RUN_YEAR_END,
      { async: false, ...params }
    );
    return data;
  },

  listDayEndReports: async (filters?: { process_date?: string; shop_id?: number; success?: boolean }) => {
    const { data } = await api.get<{ results: DayEndReport[] } | DayEndReport[]>(
      ENDPOINTS.SETTINGS.DAY_END_REPORTS,
      { params: filters }
    );
    return Array.isArray(data) ? data : data.results;
  },

  getDayEndReport: async (id: number) => {
    const { data } = await api.get<DayEndReport>(ENDPOINTS.SETTINGS.DAY_END_REPORT_DETAIL(id));
    return data;
  },
};

export function isAsyncTaskResult(result: PeriodEndResult | AsyncTaskResult): result is AsyncTaskResult {
  return 'task_id' in result;
}
