export default function Spining({ isLocalLoading }: { isLocalLoading?: boolean }) {
  // You can render any UI here, including a skeleton component
  return (
    <div className={`flex items-center justify-center ${isLocalLoading ? 'h-full' : 'h-screen'}`}>
      <div className="border-accent h-24 w-24 animate-spin rounded-full border-t-5 border-b-5"></div>
      <p className="ml-3 text-lg font-semibold text-gray-700">Đang tải...</p>
    </div>
  );
}
