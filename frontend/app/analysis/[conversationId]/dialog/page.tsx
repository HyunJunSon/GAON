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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">대화록을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-red-600">{(error as Error)?.message ?? '대화록을 불러올 수 없습니다'}</p>
        </div>
      </div>
    );
  }

  if (data.status !== 'ready' && data.status !== 'completed') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">현재 상태: {data.status}</p>
        </div>
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="space-y-8">
        {/* 헤더 */}
        <header className="text-center">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-800">대화록</h1>
          </div>
          <p className="text-gray-600 text-lg">대화 내용을 시간순으로 확인할 수 있습니다</p>
        </header>

        {/* 화자 매핑 설정 섹션 */}
        {speakerData && speakerData.speakerCount > 0 && (
          <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-800">화자 설정</h2>
              </div>
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 text-sm bg-gradient-to-r from-orange-500 to-red-500 text-white hover:from-orange-600 hover:to-red-600 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  편집
                </button>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveMapping}
                    className="px-4 py-2 text-sm bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
                  >
                    저장
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setEditMapping(speakerData.mapping);
                      setSaveError(null);
                    }}
                    className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-all duration-200"
                  >
                    취소
                  </button>
                </div>
              )}
            </div>

            {saveError && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 flex items-center gap-2">
                <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {saveError}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: speakerData.speakerCount }, (_, i) => (
                <div key={i} className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center">
                    <span className="text-sm font-semibold text-blue-600">{i}</span>
                  </div>
                  <span className="text-sm text-gray-600 min-w-[60px]">화자 {i}:</span>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editMapping[i.toString()] || ''}
                      onChange={(e) => setEditMapping(prev => ({ ...prev, [i.toString()]: e.target.value }))}
                      placeholder={`화자${i} 이름`}
                      className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    />
                  ) : (
                    <span className="text-sm font-medium text-gray-800">
                      {speakerData.mapping[i.toString()] || `화자${i}`}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 대화록 섹션 */}
        <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-green-100 to-emerald-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800">대화 내용</h2>
          </div>
          
          {isLoadingSpeaker ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="w-8 h-8 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-3"></div>
                <p className="text-gray-600">화자 정보 로딩 중...</p>
              </div>
            </div>
          ) : speakerData && speakerData.segments.length > 0 ? (
            <div className="space-y-4">
              {speakerData.segments.map((segment, index) => {
                const speakerName = speakerData.mapping[segment.speaker.toString()] || `화자${segment.speaker}`;
                const speakerColors = [
                  'from-blue-100 to-indigo-100 border-blue-200',
                  'from-green-100 to-emerald-100 border-green-200',
                  'from-purple-100 to-pink-100 border-purple-200',
                  'from-orange-100 to-red-100 border-orange-200',
                  'from-yellow-100 to-amber-100 border-yellow-200',
                ];
                const colorClass = speakerColors[segment.speaker % speakerColors.length];
                
                return (
                  <div key={index} className={`flex gap-4 p-4 bg-gradient-to-r ${colorClass} rounded-xl border transition-all duration-200 hover:shadow-md`}>
                    <div className="flex-shrink-0 text-xs text-gray-500 bg-white px-2 py-1 rounded-lg font-mono min-w-[50px] text-center">
                      {formatTime(segment.start)}
                    </div>
                    <div className="flex-shrink-0 font-semibold text-sm bg-white px-3 py-1 rounded-lg min-w-[80px] text-center">
                      {speakerName}
                    </div>
                    <div className="flex-1 text-sm leading-relaxed bg-white/50 px-3 py-2 rounded-lg">
                      {segment.text}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-gray-50 rounded-xl p-6">
              <pre className="text-sm whitespace-pre-wrap text-gray-700 leading-relaxed">
                {data.dialog?.raw || '대화 내용이 없습니다.'}
              </pre>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}