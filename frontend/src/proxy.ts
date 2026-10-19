import { NextResponse, NextRequest } from 'next/server';

export function proxy(request: NextRequest) {


  return NextResponse.next({
    request: {
      headers: request.headers,
    },
  });
}

export const config = {
  matcher: [
    '/api/:path*',
    '/auth/:path*',
    '/profile/:path*',
    '/setting/:path*',
    '/dashboard/:path*',
    '/admin/:path*',
  ],
};
