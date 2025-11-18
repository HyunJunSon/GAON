'use client';

import { useState, useEffect } from 'react';
import { getSpeakerMapping, updateSpeakerMapping } from '@/apis/analysis';
import { getFamily, type FamilyMember } from '@/apis/family';
import { useMe } from '@/hooks/useAuth';
import ConversationQuotes from '@/components/ui/ConversationQuotes';

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
      // 최소 1명은 가족 구성원이어야 함 검증
      const familyMemberCount = Object.keys(userMapping).length;
      if (familyMemberCount === 0) {
        setError('최소 1명은 가족 구성원으로 선택해야 합니다.');
        return;
      }

      // 모든 화자가 설정되었는지 확인
      const unsetSpeakers = speakers.filter(speaker => 
        !mapping[speaker.speaker.toString()]
      );
      if (unsetSpeakers.length > 0) {
        setError('모든 화자를 설정해주세요.');
        return;
      }

      setIsLoading(true);
      const response = await updateSpeakerMapping(conversationId, mapping, userMapping);
      
      // 화자 매핑 완료 후 바로 완료 처리 (분석은 백그라운드에서 진행)
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
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto border border-orange-100">
        
        {/* 헤더 */}
        <div className="mb-8 text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-orange-100 to-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">화자 설정</h2>
          <p className="text-gray-600">
            음성에서 인식된 화자들에게 이름을 지정해주세요.
          </p>
          <p className="text-sm text-orange-600 mt-2 bg-orange-50 rounded-lg px-3 py-2">
            ⚠️ 분석을 위해 최소 1명은 가족 구성원으로 선택해야 합니다.
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
            <ConversationQuotes />
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
            <ConversationQuotes />
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
                <ConversationQuotes />
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
                            className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg border transition-all duration-200 ${
                              speakerTypes[speaker.speaker.toString()] === 'family'
                                ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white border-orange-500 shadow-md' 
                                : 'bg-white border-gray-300 text-gray-700 hover:bg-orange-50 hover:border-orange-200'
                            }`}
                          >
                            👨‍👩‍👧‍👦 가족 구성원
                          </button>
                          <button
                            type="button"
                            onClick={() => handleSpeakerTypeChange(speaker.speaker.toString(), 'guest')}
                            className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg border transition-all duration-200 ${
                              speakerTypes[speaker.speaker.toString()] === 'guest'
                                ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white border-orange-500 shadow-md' 
                                : 'bg-white border-gray-300 text-gray-700 hover:bg-orange-50 hover:border-orange-200'
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
                              {familyMembers.map(member => {
                                // 이미 다른 화자가 선택한 가족 구성원은 비활성화
                                const isAlreadySelected = Object.values(userMapping).includes(parseInt(member.id)) && 
                                                         userMapping[speaker.speaker.toString()] !== parseInt(member.id);
                                
                                return (
                                  <option 
                                    key={member.id} 
                                    value={member.id}
                                    disabled={isAlreadySelected}
                                  >
                                    {member.name} {isAlreadySelected ? '(이미 선택됨)' : ''}
                                  </option>
                                );
                              })}
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
                    className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200"
                  >
                    취소
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={
                      Object.keys(mapping).length === 0 || 
                      Object.keys(userMapping).length === 0 || 
                      isLoading
                    }
                    className="flex-1 rounded-lg bg-gradient-to-r from-orange-500 to-red-500 px-4 py-2 text-sm font-medium text-white hover:from-orange-600 hover:to-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
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
