"""
스토리지 경로 기반 RAG 자동 선택 사용 예시
"""
from .rag_auto_selector import get_rag_auto_selector, process_file_with_auto_rag, search_with_auto_rag


def example_auto_selection():
    """자동 선택 예시"""
    print("=== 스토리지 경로 기반 RAG 자동 선택 ===")
    
    selector = get_rag_auto_selector()
    
    # 현재 경로 매핑 확인
    mappings = selector.get_path_mappings()
    print("\n📁 경로별 RAG 매핑:")
    for path, rag_type in mappings.items():
        print(f"  {path} -> {rag_type.value}")
    
    # 1. 기존 RAG가 처리할 파일들
    legacy_files = [
        "documents/user_upload.pdf",
        "uploads/meeting_notes.txt", 
        "general/research_paper.pdf"
    ]
    
    print("\n🔄 기존 RAG 처리 파일들:")
    for file_path in legacy_files:
        print(f"  📄 {file_path}")
        # results = process_file_with_auto_rag(file_path)
        # print(f"     -> 처리 결과: {len(results)}개 청크")
    
    # 2. TOC 기반 RAG가 처리할 파일들  
    toc_files = [
        "rag-data/pdf변환/parenting_handbook.pdf",
        "handbooks/child_development.pdf",
        "expert-content/family_therapy_guide.pdf"
    ]
    
    print("\n📚 TOC 기반 RAG 처리 파일들:")
    for file_path in toc_files:
        print(f"  📖 {file_path}")
        # results = process_file_with_auto_rag(file_path)
        # print(f"     -> 처리 결과: {len(results)}개 청크")
    
    # 3. 검색 시 컨텍스트 경로 활용
    print("\n🔍 컨텍스트 기반 검색:")
    
    # 일반 문서에서 검색
    print("  일반 문서 검색:")
    # results = search_with_auto_rag("프로젝트 관리", context_path="documents/")
    # print(f"    -> {len(results)}개 결과")
    
    # 전문 핸드북에서 검색  
    print("  전문 핸드북 검색:")
    # results = search_with_auto_rag("육아 조언", context_path="handbooks/")
    # print(f"    -> {len(results)}개 결과")
    
    # 4. 분석 기반 조언 생성
    print("\n💡 분석 기반 조언 생성:")
    # advice = selector.generate_advice_if_supported("analysis_123")
    # print(f"    -> 조언: {advice.get('advice', '생성 실패')[:50]}...")


def example_cloud_function_integration():
    """클라우드 함수 통합 예시"""
    print("\n=== 클라우드 함수 통합 예시 ===")
    
    # GCS 트리거 시뮬레이션
    gcs_events = [
        {
            "name": "documents/new_upload.pdf",
            "bucket": "gaon-cloud-data",
            "eventType": "google.storage.object.finalize"
        },
        {
            "name": "rag-data/pdf변환/new_handbook.pdf", 
            "bucket": "gaon-cloud-data",
            "eventType": "google.storage.object.finalize"
        }
    ]
    
    for event in gcs_events:
        file_path = event["name"]
        print(f"\n📥 GCS 이벤트: {file_path}")
        
        # 자동 RAG 선택 및 처리
        selector = get_rag_auto_selector()
        rag_type = selector._determine_rag_type(file_path)
        
        print(f"🤖 선택된 RAG: {rag_type.value}")
        print(f"📊 처리 방식: {'TOC 기반 의미적 청킹' if rag_type.value == 'toc_based' else '일반 청킹'}")
        
        # 실제 처리는 주석 처리
        # results = process_file_with_auto_rag(f"gs://{event['bucket']}/{file_path}")
        # print(f"✅ 처리 완료: {len(results)}개 청크")


def example_path_customization():
    """경로 커스터마이징 예시"""
    print("\n=== 경로 커스터마이징 ===")
    
    selector = get_rag_auto_selector()
    
    # 새로운 경로 매핑 추가
    selector.add_path_mapping("medical-books/", selector.manager.RAGType.TOC_BASED)
    selector.add_path_mapping("user-docs/", selector.manager.RAGType.LEGACY)
    
    print("새로운 경로 매핑 추가:")
    print("  medical-books/ -> TOC 기반 RAG")
    print("  user-docs/ -> 기존 RAG")
    
    # 업데이트된 매핑 확인
    mappings = selector.get_path_mappings()
    print(f"\n총 {len(mappings)}개 경로 매핑 등록됨")


if __name__ == "__main__":
    example_auto_selection()
    example_cloud_function_integration()
    example_path_customization()
