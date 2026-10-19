import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 text-center">
      <h2 className="mb-2 text-3xl font-bold text-red-600">Page Not Found</h2>
      <p className="mb-6 text-gray-600">Sorry, we could not find the requested resource.</p>
      <Link
        href="/"
        className="rounded bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
      >
        Return Home
      </Link>
    </div>
  );
}
