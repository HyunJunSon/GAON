"""
RAG 시스템 테스트 모듈
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.llm.rag import RAGSystem
from app.llm.rag.utils import rag_logger as logger


def create_test_pdf(filename: str) -> str:
    """
    테스트용 PDF 파일 생성
    """
    # PyPDF2를 사용하여 간단한 테스트 PDF 생성
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        file_path = os.path.join(tempfile.gettempdir(), filename)
        
        c = canvas.Canvas(file_path, pagesize=letter)
        c.drawString(100, 750, "테스트 문서 제목")
        c.drawString(100, 725, "이 문서는 RAG 시스템 테스트를 위한 PDF 파일입니다.")
        c.drawString(100, 700, "이 문서에는 여러 문장이 포함되어 있습니다.")
        c.drawString(100, 675, "RAG 시스템이 이 텍스트를 처리할 수 있어야 합니다.")
        c.drawString(100, 650, "문서 처리, 청킹, 임베딩 생성, 벡터 DB 저장이 포함됩니다.")
        c.save()
        
        return file_path
    except ImportError:
        # reportlab이 없을 경우 테스트를 건너뜀
        logger.warning("reportlab이 설치되지 않아 테스트 PDF 생성을 건너뜁니다.")
        return None


def create_test_txt(filename: str) -> str:
    """
    테스트용 텍스트 파일 생성
    """
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    content = """
    RAG 시스템 테스트를 위한 텍스트 파일입니다.
    이 파일은 문서 로딩, 추출, 청킹, 임베딩 생성, 벡터 DB 저장 기능을 테스트합니다.
    여러 문장으로 구성되어 있어 청킹 기능도 테스트할 수 있습니다.
    """
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path


def test_rag_system():
    """
    RAG 시스템 전체 기능 테스트
    """
    logger.info("RAG 시스템 전체 기능 테스트 시작")
    
    try:
        # RAG 시스템 초기화 (로컬 스토리지 사용)
        rag_system = RAGSystem(storage_type="local")
        
        # 테스트용 텍스트 파일 생성
        test_txt_file = create_test_txt("test_document.txt")
        if not test_txt_file:
            logger.error("테스트 텍스트 파일 생성 실패")
            return False
        
        logger.info(f"테스트 텍스트 파일 생성됨: {test_txt_file}")
        
        # 1. 문서 처리 테스트
        logger.info("1. 문서 처리 테스트 시작")
        results = rag_system.load_and_process_file(test_txt_file)
        logger.info(f"문서 처리 완료: {len(results)}개 청크 생성됨")
        
        # 2. 유사도 검색 테스트
        logger.info("2. 유사도 검색 테스트 시작")
        search_results = rag_system.search_similar("RAG 시스템 테스트", top_k=3)
        logger.info(f"유사도 검색 완료: {len(search_results)}개 결과 반환")
        
        # 3. 문서 추가 테스트
        logger.info("3. 문서 추가 테스트 시작")
        new_text = "새로운 텍스트 문서를 벡터 DB에 추가합니다."
        new_id = rag_system.add_document(new_text)
        logger.info(f"새 문서 추가 완료: {new_id}")
        
        # 4. 일괄 문서 추가 테스트
        logger.info("4. 일괄 문서 추가 테스트 시작")
        texts_to_add = [
            "일괄 추가 테스트 문서 1",
            "일괄 추가 테스트 문서 2", 
            "일괄 추가 테스트 문서 3"
        ]
        added_ids = rag_system.batch_add_documents(texts_to_add)
        logger.info(f"일괄 문서 추가 완료: {len(added_ids)}개 문서 추가됨")
        
        # 5. 다시 유사도 검색 테스트 (새로 추가한 문서 포함)
        logger.info("5. 새 문서 포함 유사도 검색 테스트 시작")
        search_results_new = rag_system.search_similar("새로운 텍스트", top_k=5)
        logger.info(f"새 문서 포함 유사도 검색 완료: {len(search_results_new)}개 결과 반환")
        
        # 테스트 파일 정리
        if os.path.exists(test_txt_file):
            os.remove(test_txt_file)
            logger.info(f"테스트 파일 정리됨: {test_txt_file}")
        
        logger.info("RAG 시스템 전체 기능 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"RAG 시스템 테스트 실패: {str(e)}")
        return False


def test_error_handling():
    """
    예외 처리 테스트
    """
    logger.info("예외 처리 테스트 시작")
    
    try:
        # 존재하지 않는 파일 처리 시도
        rag_system = RAGSystem(storage_type="local")
        
        try:
            results = rag_system.load_and_process_file("/nonexistent/path/document.pdf")
            logger.error("예외가 발생하지 않음 - 예상치 못한 동작")
            return False
        except Exception as e:
            logger.info(f"존재하지 않는 파일에 대한 예외 처리 성공: {type(e).__name__}")
        
        # 잘못된 쿼리로 유사도 검색 시도
        try:
            search_results = rag_system.search_similar("", top_k=5)
            logger.info(f"빈 쿼리 검색 결과: {len(search_results)}개")
        except Exception as e:
            logger.info(f"빈 쿼리에 대한 예외 처리: {type(e).__name__}")
        
        logger.info("예외 처리 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"예외 처리 테스트 실패: {str(e)}")
        return False


def run_all_tests():
    """
    모든 테스트 실행
    """
    logger.info("=== RAG 시스템 테스트 시작 ===")
    
    tests = [
        ("기본 기능 테스트", test_rag_system),
        ("예외 처리 테스트", test_error_handling)
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{test_name} 실행 중...")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                logger.info(f"{test_name}: 성공")
            else:
                logger.error(f"{test_name}: 실패")
        except Exception as e:
            logger.error(f"{test_name}: 예외 발생 - {str(e)}")
            results[test_name] = False
    
    logger.info("\n=== 테스트 결과 요약 ===")
    for test_name, result in results.items():
        status = "성공" if result else "실패"
        logger.info(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    logger.info(f"\n총 {total_tests}개 테스트 중 {passed_tests}개 성공")
    
    if passed_tests == total_tests:
        logger.info("모든 테스트 성공! RAG 시스템이 정상적으로 작동합니다.")
        return True
    else:
        logger.error(f"일부 테스트 실패. {passed_tests}/{total_tests} 성공")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    if success:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("\n❌ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")