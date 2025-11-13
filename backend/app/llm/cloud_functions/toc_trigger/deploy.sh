#!/bin/bash

# TOC 기반 RAG Cloud Function 배포

gcloud functions deploy toc-pdf-processor \
  --runtime python311 \
  --trigger-topic gaon-toc-pdfs-topic \
  --entry-point toc_pdf_processor \
  --memory 1GB \
  --timeout 540s \
  --env-vars-file .env.yaml \
  --region asia-northeast3

echo "TOC PDF 처리 함수 배포 완료!"
