#!/bin/bash

# 서버에서 실행하는 스크립트
# 이미지 업로드 디렉토리 생성

echo "이미지 업로드 디렉토리 생성 스크립트"
echo "===================================="

# 업로드 디렉토리 생성 (경로를 실제 WordPress 설치 경로에 맞게 수정하세요)
UPLOAD_DIR="/path/to/wordpress/wp-content/uploads/auto-posts"

echo "디렉토리 생성: $UPLOAD_DIR"
sudo mkdir -p $UPLOAD_DIR

echo "권한 설정"
sudo chown -R www-data:www-data $UPLOAD_DIR  # 또는 bitnami:daemon (서버 환경에 따라)
sudo chmod -R 755 $UPLOAD_DIR

echo "디렉토리 확인"
ls -la $UPLOAD_DIR

echo "완료!"
echo "이제 맥북에서 다시 테스트를 실행하세요:"
echo "python3 test_connection.py"