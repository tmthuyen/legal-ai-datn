import React from 'react';
import { Skeleton } from '@/components/ui/skeleton';

export const DashboardTopStatsSkeleton = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 mt-2">
      {[1, 2, 3].map((i) => (
        <div key={i} className="p-4 bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 flex flex-col items-center justify-center h-[120px]">
          <Skeleton className="h-4 w-24 mb-3" />
          <Skeleton className="h-10 w-16" />
        </div>
      ))}
    </div>
  );
};

export const TableSkeleton = ({ rows = 5 }: { rows?: number }) => {
  return (
    <div className="w-full bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 p-4">
      <div className="flex justify-between items-center mb-6">
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-9 w-32 rounded-lg" />
      </div>
      <div className="space-y-4">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className="flex items-center space-x-4 p-3 rounded-lg border border-gray-100 dark:border-slate-700/50">
            <Skeleton className="h-12 w-12 rounded-lg" />
            <div className="space-y-2 flex-1">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
            <div className="space-y-2 hidden sm:block w-24">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-9 w-9 rounded-lg" />
              <Skeleton className="h-9 w-9 rounded-lg" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const CardListSkeleton = ({ count = 6 }: { count?: number }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(count)].map((_, i) => (
        <div key={i} className="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm flex flex-col h-[200px]">
          <div className="flex justify-between items-start mb-4">
            <Skeleton className="h-10 w-10 rounded-xl" />
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
          <Skeleton className="h-5 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2 mb-auto" />
          <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100 dark:border-slate-700/50">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
};

export const PageSkeleton = () => {
  return (
    <div className="p-6 space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-4 w-1/4" />
      </div>
      <DashboardTopStatsSkeleton />
      <TableSkeleton rows={3} />
    </div>
  );
};
