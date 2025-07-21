#!/bin/bash

echo "WordPress 서버 설정 스크립트"
echo "===================================="

# 서버 정보 확인
echo "1. 서버 정보 확인"
echo "   OS: $(uname -a)"
echo "   PHP 버전: $(php -v | head -n 1)"
echo "   MySQL 상태: $(systemctl is-active mysql || echo 'MySQL 서비스 확인 필요')"

# WordPress 디렉토리 확인 (경로를 실제 WordPress 설치 경로에 맞게 수정하세요)
WP_DIR="/path/to/wordpress"
if [ -d "$WP_DIR" ]; then
    echo "2. WordPress 설치 확인: ✅"
    echo "   경로: $WP_DIR"
else
    echo "2. WordPress 설치 확인: ❌"
    echo "   WordPress가 설치되지 않았거나 경로가 다릅니다."
    exit 1
fi

# 이미지 업로드 디렉토리 생성 (경로를 실제 WordPress 설치 경로에 맞게 수정하세요)
UPLOAD_DIR="/path/to/wordpress/wp-content/uploads/auto-posts"
echo "3. 이미지 업로드 디렉토리 설정"

if [ ! -d "$UPLOAD_DIR" ]; then
    echo "   디렉토리 생성: $UPLOAD_DIR"
    sudo mkdir -p "$UPLOAD_DIR"
    sudo chown www-data:www-data "$UPLOAD_DIR"  # 또는 bitnami:daemon (서버 환경에 따라)
    sudo chmod 755 "$UPLOAD_DIR"
    echo "   ✅ 디렉토리 생성 완료"
else
    echo "   ✅ 디렉토리가 이미 존재합니다"
fi

# 권한 확인 및 설정
echo "4. 파일 권한 설정"
sudo chown -R www-data:www-data /path/to/wordpress/wp-content/uploads/
sudo chmod -R 755 /path/to/wordpress/wp-content/uploads/
echo "   ✅ 권한 설정 완료"

# WordPress REST API 확인
echo "5. WordPress REST API 확인"
WP_URL="http://localhost"
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$WP_URL/wp-json/wp/v2/")

if [ "$API_RESPONSE" = "200" ]; then
    echo "   ✅ REST API 활성화됨"
else
    echo "   ⚠️  REST API 응답 코드: $API_RESPONSE"
    echo "   WordPress 관리자에서 고유주소 설정을 확인해주세요."
fi

# MySQL 정보 확인
echo "6. MySQL 데이터베이스 정보"
echo "   데이터베이스 이름: your_database_name"
echo "   사용자: your_db_username"
echo "   MySQL 접속 테스트를 위해 다음 명령어를 사용하세요:"
echo "   mysql -u your_db_username -p your_database_name"

# Python 패키지 설치 확인
echo "7. Python 환경 확인"
python3 --version
pip3 --version

echo "   필요한 패키지 설치 중..."
pip3 install requests paramiko mysql-connector-python

# 방화벽 확인 (필요시)
echo "8. 네트워크 설정 확인"
echo "   SFTP 포트 (22): $(netstat -tuln | grep :22 | wc -l)개 리스닝"
echo "   HTTP 포트 (80): $(netstat -tuln | grep :80 | wc -l)개 리스닝"

echo ""
echo "서버 설정 완료!"
echo ""
echo "추가 확인사항:"
echo "- WordPress 관리자 계정 정보 확인"
echo "- 도메인 또는 IP 주소 확인"
echo "- MySQL 비밀번호 확인 (설치 로그 또는 설정 파일 참조)"
echo ""
echo "설정 파일 편집 후 연결 테스트를 실행하세요:"
echo "python3 test_connection.py"