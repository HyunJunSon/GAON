import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const backendUrl = 'http://127.0.0.1:8000';
    
    console.log('Proxying login to:', `${backendUrl}/api/auth/login`);
    console.log('Form data:', Object.fromEntries(formData));
    
    const response = await fetch(`${backendUrl}/api/auth/login`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    console.log('Backend login response:', response.status, data);
    
    return Response.json(data, { 
      status: response.status
    });
  } catch (error) {
    console.error('Login proxy error:', error);
    return Response.json(
      { error: 'Internal server error', details: error.message }, 
      { status: 500 }
    );
  }
}
