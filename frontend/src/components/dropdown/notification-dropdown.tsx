import React from 'react';
import { Skeleton } from '../ui/skeleton';

function NotificationDropdown() {
  return (
    <div className="absolute top-full right-0 mt-2 h-64 w-48 rounded-lg bg-white p-4 shadow-lg">
      <Skeleton className="mb-2 h-1/4 w-full" />
      <Skeleton className="mb-2 h-1/4 w-full" />
      <Skeleton className="h-1/4 w-full" />
    </div>
  );
}

export default NotificationDropdown;
