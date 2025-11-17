/**
 * 화자 맵핑 모달 컴포넌트 테스트
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SpeakerMappingModal from '@/components/upload/SpeakerMappingModal';

// API 모킹
jest.mock('@/apis/analysis', () => ({
  getSpeakerMapping: jest.fn(),
  updateSpeakerMapping: jest.fn(),
}));

const mockProps = {
  conversationId: 'test-conversation-id',
  isOpen: true,
  onClose: jest.fn(),
  onComplete: jest.fn(),
  status: 'ready' as const,
};

const mockSpeakerData = {
  conversation_id: 'test-conversation-id',
  file_id: 1,
  speaker_mapping: {},
  speaker_count: 2,
  mapped_segments: [
    {
      speaker: 1,
      start: 0,
      end: 5,
      text: '안녕하세요. 오늘 날씨가 정말 좋네요.',
    },
    {
      speaker: 2,
      start: 5,
      end: 10,
      text: '네, 맞아요. 산책하기 좋은 날씨입니다.',
    },
  ],
};

describe('SpeakerMappingModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('모달이 열리지 않으면 렌더링되지 않음', () => {
    render(<SpeakerMappingModal {...mockProps} isOpen={false} />);
    expect(screen.queryByText('화자 설정')).not.toBeInTheDocument();
  });

  test('업로드 중 상태 표시', () => {
    render(<SpeakerMappingModal {...mockProps} status="uploading" />);
    
    expect(screen.getByText('화자 설정')).toBeInTheDocument();
    expect(screen.getByText('업로드 중입니다...')).toBeInTheDocument();
    expect(screen.getByText('📤')).toBeInTheDocument();
  });

  test('STT 처리 중 상태 표시', () => {
    render(<SpeakerMappingModal {...mockProps} status="processing" />);
    
    expect(screen.getByText('음성을 텍스트로 변환 중입니다...')).toBeInTheDocument();
    expect(screen.getByText('🎙️→📝')).toBeInTheDocument();
  });

  test('화자 선택 상태에서 화자 목록 표시', async () => {
    const { getSpeakerMapping } = require('@/apis/analysis');
    getSpeakerMapping.mockResolvedValue(mockSpeakerData);

    render(<SpeakerMappingModal {...mockProps} status="ready" />);

    await waitFor(() => {
      expect(screen.getByText('화자 1')).toBeInTheDocument();
      expect(screen.getByText('화자 2')).toBeInTheDocument();
    });

    // 발화 내용 확인
    expect(screen.getByText('"안녕하세요. 오늘 날씨가 정말 좋네요."')).toBeInTheDocument();
    expect(screen.getByText('"네, 맞아요. 산책하기 좋은 날씨입니다."')).toBeInTheDocument();

    // 시간 정보 확인
    expect(screen.getByText('0초 - 5초')).toBeInTheDocument();
    expect(screen.getByText('5초 - 10초')).toBeInTheDocument();
  });

  test('화자 이름 입력 기능', async () => {
    const { getSpeakerMapping } = require('@/apis/analysis');
    getSpeakerMapping.mockResolvedValue(mockSpeakerData);

    render(<SpeakerMappingModal {...mockProps} status="ready" />);

    await waitFor(() => {
      expect(screen.getByText('화자 1')).toBeInTheDocument();
    });

    // 첫 번째 화자 이름 입력
    const nameInputs = screen.getAllByPlaceholderText('예: 엄마, 아빠, 아이 등');
    fireEvent.change(nameInputs[0], { target: { value: '엄마' } });
    fireEvent.change(nameInputs[1], { target: { value: '아이' } });

    expect(nameInputs[0]).toHaveValue('엄마');
    expect(nameInputs[1]).toHaveValue('아이');
  });

  test('확인 버튼 클릭 시 화자 맵핑 저장', async () => {
    const { getSpeakerMapping, updateSpeakerMapping } = require('@/apis/analysis');
    getSpeakerMapping.mockResolvedValue(mockSpeakerData);
    updateSpeakerMapping.mockResolvedValue({});

    render(<SpeakerMappingModal {...mockProps} status="ready" />);

    await waitFor(() => {
      expect(screen.getByText('화자 1')).toBeInTheDocument();
    });

    // 화자 이름 입력
    const nameInputs = screen.getAllByPlaceholderText('예: 엄마, 아빠, 아이 등');
    fireEvent.change(nameInputs[0], { target: { value: '엄마' } });

    // 확인 버튼 클릭
    const confirmButton = screen.getByText('확인');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(updateSpeakerMapping).toHaveBeenCalledWith('test-conversation-id', {
        '1': '엄마',
      });
      expect(mockProps.onComplete).toHaveBeenCalledWith({
        '1': '엄마',
      });
    });
  });

  test('취소 버튼 클릭 시 모달 닫기', () => {
    render(<SpeakerMappingModal {...mockProps} status="ready" />);

    const cancelButton = screen.getByText('취소');
    fireEvent.click(cancelButton);

    expect(mockProps.onClose).toHaveBeenCalled();
  });

  test('에러 상태 표시', async () => {
    const { getSpeakerMapping } = require('@/apis/analysis');
    getSpeakerMapping.mockRejectedValue(new Error('API 오류'));

    render(<SpeakerMappingModal {...mockProps} status="ready" />);

    await waitFor(() => {
      expect(screen.getByText('화자 정보를 불러오는데 실패했습니다.')).toBeInTheDocument();
    });
  });
});
