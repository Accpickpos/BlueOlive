'use client';

import { Pagination } from '@/components/ui/pagination';

interface CreditorsPaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export default function CreditorsPagination({
  page,
  pageSize,
  total,
  onPageChange,
}: CreditorsPaginationProps) {
  const totalPages = Math.ceil(total / pageSize);

  if (total <= 0) {
    return null;
  }

  return (
    <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
      <p className="text-sm text-gray-600">
        Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total}
      </p>
      <Pagination
        currentPage={page}
        totalPages={totalPages}
        onPageChange={onPageChange}
      />
    </div>
  );
}
