import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    const backendUrl = 'http://127.0.0.1:8000'; // 127.0.0.1 사용
    
    console.log('Proxying logout to:', `${backendUrl}/api/auth/logout`);
    console.log('Auth header:', authHeader);
    
    const response = await fetch(`${backendUrl}/api/auth/logout`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader || '',
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    console.log('Backend response:', response.status, data);
    
    return Response.json(data, { 
      status: response.status
    });
  } catch (error) {
    console.error('Logout proxy error:', error);
    return Response.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : String(error) }, 
      { status: 500 }
    );
  }
}
