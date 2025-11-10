#!/bin/bash

# RAG Cloud Function 배포 스크립트

FUNCTION_NAME="rag-processor"
REGION="asia-northeast3"

echo "RAG Cloud Function 배포 시작..."

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=rag_file_processor \
  --trigger-topic=gcs-rag-notifications \
  --env-vars-file=.env.yaml \
  --memory=1Gi \
  --timeout=540s

echo "배포 완료!"
