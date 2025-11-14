import { NextResponse } from 'next/server';
import { store } from '../_store';

export async function GET() {
  return NextResponse.json({ participants: store.participants() }, { status: 200 });
}