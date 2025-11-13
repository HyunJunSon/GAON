'use client';
import { useAnalysis } from "@/hooks/useAnalysis";
import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import { getSpeakerMapping, updateSpeakerMapping, type SpeakerMapping, type SpeakerSegment } from "@/apis/analysis";

export default function ResultsDialogPage() {
  const { conversationId } = useParams();
  const id = Array.isArray(conversationId) ? conversationId[0] : conversationId as string;
  const { data, isLoading, isError, error } = useAnalysis(id);
  
  const [speakerData, setSpeakerData] = useState<{
    mapping: SpeakerMapping;
    segments: SpeakerSegment[];
    speakerCount: number;
  } | null>(null);
  const [isLoadingSpeaker, setIsLoadingSpeaker] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editMapping, setEditMapping] = useState<SpeakerMapping>({});
  const [saveError, setSaveError] = useState<string | null>(null);

  // 화자 매핑 데이터 로드
  useEffect(() => {
    if (!id) return;
    
    const loadSpeakerMapping = async () => {
      setIsLoadingSpeaker(true);
      try {
        const result = await getSpeakerMapping(id);
        setSpeakerData({
          mapping: result.speaker_mapping || {},
          segments: result.mapped_segments || [],
          speakerCount: result.speaker_count || 0
        });
        setEditMapping(result.speaker_mapping || {});
      } catch (err) {
        console.error('화자 매핑 로드 실패:', err);
      } finally {
        setIsLoadingSpeaker(false);
      }
    };

    loadSpeakerMapping();
  }, [id]);

  const handleSaveMapping = async () => {
    setSaveError(null);
    try {
      await updateSpeakerMapping(id, editMapping);
      setSpeakerData(prev => prev ? { ...prev, mapping: editMapping } : null);
      setIsEditing(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : '저장 중 오류가 발생했습니다.');
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) return <div>로딩…</div>;
  if (isError || !data) return <div>{(error as Error)?.message ?? '불러오기 실패'}</div>;
  if (data.status !== 'ready') return <div>현재 상태: {data.status}</div>;

  return (
    <main className="mx-auto max-w-3xl p-6 space-y-6">
      {/* 화자 매핑 설정 섹션 */}
      {speakerData && speakerData.speakerCount > 0 && (
        <section className="rounded-lg border bg-white p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium">화자 설정</h2>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                편집
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={handleSaveMapping}
                  className="px-3 py-1 text-sm bg-blue-500 text-white hover:bg-blue-600 rounded"
                >
                  저장
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setEditMapping(speakerData.mapping);
                    setSaveError(null);
                  }}
                  className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                >
                  취소
                </button>
              </div>
            )}
          </div>

          {saveError && (
            <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
              {saveError}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            {Array.from({ length: speakerData.speakerCount }, (_, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-sm text-gray-600">화자{i}:</span>
                {isEditing ? (
                  <input
                    type="text"
                    value={editMapping[i.toString()] || ''}
                    onChange={(e) => setEditMapping(prev => ({ ...prev, [i.toString()]: e.target.value }))}
                    placeholder={`화자${i} 이름`}
                    className="flex-1 px-2 py-1 text-sm border rounded"
                  />
                ) : (
                  <span className="text-sm font-medium">
                    {speakerData.mapping[i.toString()] || `화자${i}`}
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 대화록 섹션 */}
      <section className="rounded-lg border bg-white p-4">
        <h2 className="text-lg font-medium mb-4">대화록</h2>
        
        {isLoadingSpeaker ? (
          <div className="text-sm text-gray-600">화자 정보 로딩 중…</div>
        ) : speakerData && speakerData.segments.length > 0 ? (
          <div className="space-y-3">
            {speakerData.segments.map((segment, index) => {
              const speakerName = speakerData.mapping[segment.speaker.toString()] || `화자${segment.speaker}`;
              return (
                <div key={index} className="flex gap-3 p-3 bg-gray-50 rounded">
                  <div className="flex-shrink-0 text-xs text-gray-500 w-16">
                    {formatTime(segment.start)}
                  </div>
                  <div className="flex-shrink-0 font-medium text-sm w-20">
                    {speakerName}
                  </div>
                  <div className="flex-1 text-sm">
                    {segment.text}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <pre className="rounded bg-gray-50 p-3 text-sm whitespace-pre-wrap">
            {data.dialog?.raw}
          </pre>
        )}
      </section>
    </main>
  );
}