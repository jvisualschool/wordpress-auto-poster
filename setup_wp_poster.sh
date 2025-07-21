#!/bin/bash

echo "WordPress 자동 포스팅 스크립트 설정"
echo "===================================="

# Python 패키지 설치
echo "1. Python 패키지 설치 중..."
pip3 install requests paramiko mysql-connector-python

# 설정 파일 생성
if [ ! -f "wp_config.json" ]; then
    echo "2. 설정 파일 생성 중..."
    cp wp_config.json.example wp_config.json
    echo "   wp_config.json 파일이 생성되었습니다."
    echo "   이 파일을 편집하여 실제 설정값을 입력해주세요."
else
    echo "2. wp_config.json 파일이 이미 존재합니다."
fi

# 실행 권한 부여
echo "3. 실행 권한 설정 중..."
chmod +x wp_auto_poster.py
chmod +x test_connection.py

# 이미지 폴더 확인
if [ ! -d "img" ]; then
    echo "4. img 폴더가 없습니다. 생성합니다..."
    mkdir img
    echo "   이미지 파일들을 img/ 폴더에 넣어주세요."
else
    echo "4. img 폴더가 존재합니다."
    echo "   이미지 파일 수: $(ls img/ | wc -l)개"
fi

# post.txt 파일 확인
if [ ! -f "post.txt" ]; then
    echo "5. post.txt 파일이 없습니다."
    echo "   포스트 내용이 담긴 텍스트 파일을 post.txt로 저장해주세요."
else
    echo "5. post.txt 파일이 존재합니다."
    echo "   포스트 수: $(grep -c '^[0-9]\+\.' post.txt)개"
fi

echo ""
echo "설정 완료!"
echo ""
echo "다음 단계:"
echo "1. wp_config.json 파일을 편집하여 실제 설정값 입력"
echo "2. python3 test_connection.py 실행하여 연결 테스트"
echo "3. python3 wp_auto_poster.py --help 로 사용법 확인"
echo ""