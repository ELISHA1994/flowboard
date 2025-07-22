import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  // Only handle /api routes
  if (request.nextUrl.pathname.startsWith('/api')) {
    // Build the backend URL
    const backendUrl = new URL(
      request.nextUrl.pathname.replace('/api', ''),
      'http://localhost:8000'
    );

    // Copy all search params
    backendUrl.search = request.nextUrl.search;

    // Create headers object with all original headers
    const headers = new Headers();
    request.headers.forEach((value, key) => {
      // Skip host header to avoid conflicts
      if (key.toLowerCase() !== 'host') {
        headers.set(key, value);
      }
    });

    // Get the body for POST/PUT/PATCH requests
    let body: any = undefined;
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      try {
        const contentType = request.headers.get('content-type');
        if (contentType?.includes('application/json')) {
          body = await request.json();
          body = JSON.stringify(body);
        } else {
          body = await request.text();
        }
      } catch (e) {
        // If body parsing fails, continue without body
      }
    }

    // Forward the request to the backend
    const backendResponse = await fetch(backendUrl.toString(), {
      method: request.method,
      headers: headers,
      body: body,
    });

    // Create response with backend data
    const response = new NextResponse(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: new Headers(backendResponse.headers),
    });

    // Forward cookies from backend
    const setCookieHeader = backendResponse.headers.get('set-cookie');
    if (setCookieHeader) {
      response.headers.set('set-cookie', setCookieHeader);
    }

    return response;
  }
}

export const config = {
  matcher: '/api/:path*',
};
