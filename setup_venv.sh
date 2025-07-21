#!/bin/bash

echo "WordPress 자동 포스팅 스크립트 가상환경 설정"
echo "=========================================="

# 가상환경 생성
echo "1. 가상환경 생성 중..."
python3 -m venv wp_venv

# 가상환경 활성화
echo "2. 가상환경 활성화..."
source wp_venv/bin/activate

# 패키지 설치
echo "3. 필요한 패키지 설치 중..."
pip install requests paramiko mysql-connector-python

# 실행 권한 설정
echo "4. 실행 권한 설정 중..."
chmod +x wp_auto_poster.py
chmod +x test_connection.py
chmod +x batch_processor.py
chmod +x wp_utils.py

echo ""
echo "설정 완료!"
echo ""
echo "가상환경을 활성화하려면 다음 명령어를 실행하세요:"
echo "source wp_venv/bin/activate"
echo ""
echo "연결 테스트:"
echo "python test_connection.py"
echo ""
echo "포스팅 시작:"
echo "python wp_auto_poster.py --start 1 --end 1 --status draft"