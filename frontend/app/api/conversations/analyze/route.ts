import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const contentType = req.headers.get('content-type') || '';
  if (!contentType.includes('multipart/form-data')) {
    return NextResponse.json({ message: 'multipart/form-data 필요'}, { status: 400 })
  }
  // (검증 단순화) FormData 파싱만 시도
  try {
    const formData = await req.formData();
    const file = formData.get('file');
    if (!(file instanceof File)) {
      return NextResponse.json({ message: '`file` 필드가 필요합니다.' }, { status: 400 });
    }
  } catch {
    return NextResponse.json({ message: 'FormData 파싱 실패' }, { status: 400 });
  }

  // 임의 conversationId 생성
  const conversationId = 'conv_' + Math.random().toString(36).slice(2, 8);

  // 실서비스: 업로드 저장 + 큐 등록 + 상태 저장(DB)
  // 여기선 클라이언트가 /api/analysis/[id]를 폴링하면
  // 몇 번 후 ready를 내려주는 방식으로 흉내냄
  return NextResponse.json(
    { conversationId, status: 'queued' },
    { status: 202 }
  );
}