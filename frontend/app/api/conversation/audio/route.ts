import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // FormData를 그대로 전달
    const formData = await request.formData();
    
    console.log('Proxying audio upload to:', `${backendUrl}/api/conversation/audio`);
    console.log('Auth header:', authHeader);
    
    const response = await fetch(`${backendUrl}/api/conversation/audio`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader || '',
      },
      body: formData,
    });

    const data = await response.json();
    console.log('Backend response:', response.status, data);
    
    return Response.json(data, { 
      status: response.status
    });
  } catch (error) {
    console.error('Audio upload proxy error:', error);
    return Response.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : String(error) }, 
      { status: 500 }
    );
  }
}
