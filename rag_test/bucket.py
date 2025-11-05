import os
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
PREFIX      = "rag-data/pdf변환/"
OUT_DIR     = Path("./pdf변환_downloads")

def download_pdfs():
    cred = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred or not Path(cred).exists():
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS 경로가 없어요. .env 또는 환경변수 확인!")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = storage.Client()  # .env로 올라온 ADC 사용
    blobs  = client.list_blobs(BUCKET_NAME, prefix=PREFIX)

    count = 0
    for blob in blobs:
        if blob.name.endswith("/") or not blob.name.lower().endswith(".pdf"):
            continue
        rel  = Path(blob.name[len(PREFIX):])
        dest = OUT_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"↓ {blob.name} -> {dest}")
        blob.download_to_filename(str(dest))
        count += 1
    print(f"✅ 완료: {count}개 PDF 다운로드")

if __name__ == "__main__":
    download_pdfs()