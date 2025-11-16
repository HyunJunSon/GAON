'use client';

import { useState, useEffect } from 'react';
import { getSpeakerMapping, updateSpeakerMapping } from '@/apis/analysis';
import { getFamily, type FamilyMember } from '@/apis/family';
import { useMe } from '@/hooks/useAuth';

type SpeakerMappingModalProps = {
  conversationId: string;
  isOpen: boolean;
  onClose: () => void;
  onComplete: (mapping: Record<string, string>) => void;
  status: 'uploading' | 'processing' | 'ready';
};

type SpeakerSegment = {
  speaker: number;
  speaker_name?: string;
  start: number;
  end: number;
  text: string;
};

export default function SpeakerMappingModal({
  conversationId,
  isOpen,
  onClose,
  onComplete,
  status
}: SpeakerMappingModalProps) {
  const [speakers, setSpeakers] = useState<SpeakerSegment[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [userMapping, setUserMapping] = useState<Record<string, number>>({});
  const [speakerTypes, setSpeakerTypes] = useState<Record<string, 'family' | 'guest'>>({});
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { data: user } = useMe(); // 현재 사용자 정보 가져오기

  // 화자 정보 및 가족 구성원 로드
  useEffect(() => {
    if (isOpen && status === 'ready' && conversationId) {
      loadSpeakerData();
      loadFamilyMembers();
    }
  }, [isOpen, status, conversationId]);

  const loadSpeakerData = async () => {
    try {
      setIsLoading(true);
      const data = await getSpeakerMapping(conversationId);
      
      // 고유한 화자 목록 추출
      const uniqueSpeakers = data.mapped_segments.reduce((acc: SpeakerSegment[], segment) => {
        if (!acc.find(s => s.speaker === segment.speaker)) {
          acc.push(segment);
        }
        return acc;
      }, []);
      
      setSpeakers(uniqueSpeakers);
      setMapping(data.speaker_mapping || {});
    } catch (err) {
      setError('화자 정보를 불러오는데 실패했습니다.');
      console.error('화자 정보 로드 실패:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadFamilyMembers = async () => {
    try {
      const familyData = await getFamily();
      let members = familyData.members || [];
      
      // 현재 사용자를 가족 구성원 목록 맨 앞에 추가
      if (user) {
        members = [
          { id: user.id.toString(), name: `${user.name} (나)`, email: user.email },
          ...members.filter(member => member.id !== user.id.toString())
        ];
      }
      
      setFamilyMembers(members);
    } catch (err) {
      console.error('가족 구성원 로드 실패:', err);
      // 가족 정보 로드 실패해도 현재 사용자는 추가
      if (user) {
        setFamilyMembers([
          { id: user.id.toString(), name: `${user.name} (나)`, email: user.email }
        ]);
      }
    }
  };

  const handleNameChange = (speakerId: string, name: string) => {
    setMapping(prev => ({
      ...prev,
      [speakerId]: name
    }));
  };

  // 화자 유형 설정 (가족 구성원 vs 게스트)
  const handleSpeakerTypeChange = (speakerId: string, type: 'family' | 'guest') => {
    setSpeakerTypes(prev => ({
      ...prev,
      [speakerId]: type
    }));
    
    // 게스트로 변경 시 user_mapping에서 제거
    if (type === 'guest') {
      setUserMapping(prev => {
        const newMapping = { ...prev };
        delete newMapping[speakerId];
        return newMapping;
      });
    }
  };

  // 가족 구성원 선택
  const handleFamilyMemberSelect = (speakerId: string, memberId: string) => {
    const member = familyMembers.find(m => m.id === memberId);
    if (member) {
      setMapping(prev => ({
        ...prev,
        [speakerId]: member.name
      }));
      setUserMapping(prev => ({
        ...prev,
        [speakerId]: parseInt(member.id)
      }));
    }
  };

  const handleSubmit = async () => {
    try {
      setIsLoading(true);
      await updateSpeakerMapping(conversationId, mapping, userMapping);
      onComplete(mapping);
      onClose();
    } catch (err) {
      setError('화자 맵핑 저장에 실패했습니다.');
      console.error('화자 맵핑 저장 실패:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        
        {/* 헤더 */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2">화자 설정</h2>
          <p className="text-sm text-gray-600">
            음성에서 인식된 화자들에게 이름을 지정해주세요.
          </p>
        </div>
        
        {/* 업로드 중 상태 */}
        {status === 'uploading' && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📤</div>
            <div className="space-y-2">
              <div className="w-8 h-8 border-2 border-gray-300 border-t-black rounded-full animate-spin mx-auto"></div>
              <p className="text-sm text-gray-600">업로드 중입니다...</p>
            </div>
          </div>
        )}

        {/* STT 처리 중 상태 */}
        {status === 'processing' && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🎙️→📝</div>
            <div className="space-y-2">
              <div className="w-8 h-8 border-2 border-gray-300 border-t-black rounded-full animate-spin mx-auto"></div>
              <p className="text-sm text-gray-600">음성을 텍스트로 변환 중입니다...</p>
            </div>
          </div>
        )}

        {/* 화자 선택 상태 */}
        {status === 'ready' && (
          <>
            {/* 에러 메시지 */}
            {error && (
              <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* 로딩 중 */}
            {isLoading ? (
              <div className="text-center py-12">
                <div className="w-8 h-8 border-2 border-gray-300 border-t-black rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-sm text-gray-600">처리 중...</p>
              </div>
            ) : (
              <>
                {/* 화자 목록 */}
                <div className="space-y-4 mb-6">
                  {speakers.map((speaker, index) => (
                    <div key={speaker.speaker} className="rounded-lg border border-gray-300 bg-white p-4">
                      
                      {/* 화자 헤더 */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium">
                            {index + 1}
                          </div>
                          <span className="text-sm font-medium text-gray-700">화자 {speaker.speaker}</span>
                        </div>
                        <span className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded">
                          {Math.floor(speaker.start)}초 - {Math.floor(speaker.end)}초
                        </span>
                      </div>
                      
                      {/* 발화 내용 미리보기 */}
                      <div className="mb-3 rounded bg-gray-50 p-3">
                        <p className="text-sm text-gray-700">
                          "{speaker.text.substring(0, 120)}{speaker.text.length > 120 ? '...' : ''}"
                        </p>
                      </div>

                      {/* 화자 설정 */}
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-2">
                          화자 설정
                        </label>
                        
                        {/* 화자 유형 선택 */}
                        <div className="flex space-x-2 mb-3">
                          <button
                            type="button"
                            onClick={() => handleSpeakerTypeChange(speaker.speaker.toString(), 'family')}
                            className={`flex-1 px-3 py-2 text-xs font-medium rounded border transition-colors ${
                              speakerTypes[speaker.speaker.toString()] === 'family'
                                ? 'bg-black text-white border-black' 
                                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                            }`}
                          >
                            👨‍👩‍👧‍👦 가족 구성원
                          </button>
                          <button
                            type="button"
                            onClick={() => handleSpeakerTypeChange(speaker.speaker.toString(), 'guest')}
                            className={`flex-1 px-3 py-2 text-xs font-medium rounded border transition-colors ${
                              speakerTypes[speaker.speaker.toString()] === 'guest'
                                ? 'bg-black text-white border-black' 
                                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                            }`}
                          >
                            👥 게스트/친구
                          </button>
                        </div>

                        {/* 가족 구성원 선택 */}
                        {speakerTypes[speaker.speaker.toString()] === 'family' && (
                          <div>
                            <select
                              value={userMapping[speaker.speaker.toString()] || ''}
                              onChange={(e) => handleFamilyMemberSelect(speaker.speaker.toString(), e.target.value)}
                              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
                            >
                              <option value="">가족 구성원 선택</option>
                              {familyMembers.map(member => (
                                <option key={member.id} value={member.id}>
                                  {member.name}
                                </option>
                              ))}
                            </select>
                          </div>
                        )}

                        {/* 게스트 이름 입력 */}
                        {speakerTypes[speaker.speaker.toString()] === 'guest' && (
                          <div>
                            <input
                              type="text"
                              placeholder="게스트 이름 (예: 친구, 선생님, 이웃 등)"
                              value={mapping[speaker.speaker.toString()] || ''}
                              onChange={(e) => handleNameChange(speaker.speaker.toString(), e.target.value)}
                              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
                            />
                          </div>
                        )}
                        
                        {/* 상태 표시 */}
                        <div className="mt-2 text-xs text-gray-500">
                          {userMapping[speaker.speaker.toString()] ? (
                            <span>✓ 시스템 사용자 - 개인 분석 가능</span>
                          ) : mapping[speaker.speaker.toString()] ? (
                            <span>✓ 게스트 - 대화 맥락 참고용</span>
                          ) : (
                            <span>화자를 설정해주세요</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* 버튼 영역 */}
                <div className="flex space-x-3">
                  <button
                    onClick={onClose}
                    className="flex-1 rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    취소
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={Object.keys(mapping).length === 0 || isLoading}
                    className="flex-1 rounded bg-black px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                  >
                    {isLoading ? '저장 중...' : '확인'}
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
