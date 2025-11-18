import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const backendUrl = 'http://127.0.0.1:8000';
    
    console.log('Proxying signup to:', `${backendUrl}/api/auth/signup`);
    console.log('Signup data:', body);
    
    const response = await fetch(`${backendUrl}/api/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    console.log('Backend signup response:', response.status, data);
    
    return Response.json(data, { 
      status: response.status
    });
  } catch (error) {
    console.error('Signup proxy error:', error);
    return Response.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : String(error) }, 
      { status: 500 }
    );
  }
}
