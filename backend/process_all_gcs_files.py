"""
GCP Cloud Storage의 모든 파일을 벡터 DB에 저장하는 스크립트
"""
import os
from dotenv import load_dotenv
from app.llm.rag import RAGSystem

# 환경 변수 로드
load_dotenv()

def main():
    print("RAG 시스템을 시작합니다...")
    
    # 환경 변수 확인
    bucket_name = os.getenv("GCP_BUCKET_NAME", "gaon-cloud-data")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    print(f"버킷 이름: {bucket_name}")
    print(f"서비스 계정 키 경로: {credentials_path}")
    
    # 서비스 계정 키 파일 존재 여부 확인
    abs_credentials_path = os.path.abspath(credentials_path) if credentials_path else None
    if not abs_credentials_path or not os.path.exists(abs_credentials_path):
        print(f"서비스 계정 키 파일이 존재하지 않습니다: {abs_credentials_path}")
        return
    
    # RAG 시스템 초기화 (GCP 스토리지 사용)
    try:
        rag_system = RAGSystem(
            storage_type="gcp",
            bucket_name=bucket_name,
            credentials_path=abs_credentials_path
        )
    except Exception as e:
        print(f"RAG 시스템 초기화 실패: {str(e)}")
        return
    
    print(f"GCP 버킷 {bucket_name}에서 모든 파일을 가져옵니다...")
    
    # GCP CLI를 사용하여 모든 파일 목록 가져오기
    import subprocess
    try:
        # 버킷 내 모든 파일 목록 조회
        result = subprocess.run([
            'gsutil', 'ls', f'gs://{bucket_name}/rag-data/'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"파일 목록 조회 실패: {result.stderr}")
            return
        
        # 출력에서 실제 파일 경로만 추출
        all_files = [line.strip() for line in result.stdout.strip().split('\n') if line.strip().endswith(('.pdf', '.epub', '.txt', '.docx', '.md'))]
        
        # 폴더 경로는 제외하고 실제 파일만 남기기
        actual_files = []
        for file_path in all_files:
            if file_path != f"gs://{bucket_name}/rag-data/" and not file_path.endswith('/'):
                # gs:// 접두어 제거하고 경로만 추출
                actual_path = file_path.replace(f"gs://{bucket_name}/", "")
                actual_files.append(actual_path)
        
        print(f"총 {len(actual_files)}개의 파일을 찾았습니다:")
        for i, file_path in enumerate(actual_files, 1):
            print(f"{i}. {file_path}")
        
        # 각 파일을 처리
        for i, gcp_document_path in enumerate(actual_files, 1):
            print(f"\n[{i}/{len(actual_files)}] 파일 처리 시작: {gcp_document_path}")
            
            try:
                results = rag_system.load_and_process_from_storage(gcp_document_path)
                print(f"파일 처리 완료: {gcp_document_path}, {len(results)}개 청크 생성")
            except Exception as e:
                print(f"파일 처리 실패: {gcp_document_path}, 오류: {str(e)}")
                continue
    
        # 처리 완료 후 간단한 유사도 검색 테스트
        print("\n유사도 검색 테스트:")
        query = "대화법"
        search_results = rag_system.search_similar(query, top_k=3)
        
        print(f"'{query}'에 대한 유사도 검색 결과 ({len(search_results)}개):")
        for i, (content, similarity, id) in enumerate(search_results, 1):
            print(f"{i}. 유사도: {similarity:.3f}, ID: {id}")
            print(f"   내용 미리보기: {content[:100]}...")
            print()
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()