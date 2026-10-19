import { Skeleton } from '@/components/ui/skeleton';

export default function AdminSkeletonLayout() {
  return (
    <div className="flex min-h-screen w-full flex-col">
      {/* Header */}
      <div className="border-b p-4">
        <Skeleton className="h-16 w-full shrink-0 rounded-none" />
      </div>
      <div className="flex flex-1">
        {/* Sidebar - desktop/tablet */}
        <aside className="hidden w-64 shrink-0 border-r p-4 md:block">
          <div className="space-y-3">
            {Array.from({ length: 10 }).map((_, index) => (
              <Skeleton key={index} className="h-8 w-full" />
            ))}
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-hidden p-4">
          {/* Page title / toolbar */}
          <Skeleton className="mb-8 h-12 w-48" />

          {/* Cards */}
          <div className="mb-8 grid gap-4 md:grid-cols-2">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>

          {/* Table */}
          <Skeleton className="h-64 w-full" />
        </main>
      </div>
    </div>
  );
}
