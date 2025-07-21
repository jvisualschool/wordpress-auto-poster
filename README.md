# WordPress Auto Poster

WordPress 블로그에 텍스트 파일과 이미지를 자동으로 포스팅하는 Python 스크립트입니다.

## ✨ 주요 기능

- 📝 TXT 파일에서 포스트 내용 자동 파싱
- 🖼️ 포스트별 이미지 자동 매칭 및 업로드 (SFTP)
- 🚀 WordPress REST API를 통한 자동 포스팅
- 🗄️ MySQL 데이터베이스 직접 접근
- ⚡ 배치 처리 및 범위 지정 포스팅
- 📅 포스트 날짜 자동 설정

## 🛠️ 시스템 요구사항

- Python 3.6+
- WordPress with REST API enabled
- SFTP 접근 권한
- MySQL 접근 권한 (선택사항)

## 📦 설치

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/wordpress-auto-poster.git
cd wordpress-auto-poster
```

### 2. 가상환경 생성 및 활성화

```bash
python3 -m venv wp_venv
source wp_venv/bin/activate  # Linux/Mac
# 또는
wp_venv\Scripts\activate     # Windows
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 설정 파일 생성

```bash
cp wp_config.json.example wp_config.json
```

`wp_config.json` 파일을 편집하여 실제 설정 정보를 입력하세요:

```json
{
  "wordpress": {
    "url": "https://your-domain.com/blog",
    "username": "your_wp_username",
    "password": "your_wp_password",
    "application_password": "your_application_password"
  },
  "sftp": {
    "host": "your_server_ip",
    "username": "your_sftp_username",
    "privateKey": "~/.ssh/your_private_key.pem",
    "port": 22,
    "remote_image_path": "/path/to/wordpress/wp-content/uploads/auto-posts",
    "image_url_base": "https://your-domain.com/blog/wp-content/uploads/auto-posts"
  },
  "database": {
    "host": "localhost",
    "user": "your_db_username",
    "password": "your_db_password",
    "database": "your_database_name",
    "port": 3306
  }
}
```

## 📁 파일 구조

```
wordpress-auto-poster/
├── wp_auto_poster.py      # 메인 스크립트
├── batch_processor.py     # 배치 처리 스크립트
├── wp_utils.py           # WordPress 관리 유틸리티
├── test_connection.py    # 연결 테스트 스크립트
├── post.txt              # 포스트 내용 파일
├── img/                  # 이미지 폴더
│   ├── 1-1.jpg          # 1번 포스트 첫 번째 이미지
│   ├── 1-2.png          # 1번 포스트 두 번째 이미지
│   ├── 2-1.jpg          # 2번 포스트 첫 번째 이미지
│   └── ...
├── wp_config.json        # 설정 파일 (생성 필요)
└── requirements.txt      # Python 의존성
```

## 📝 포스트 파일 형식

`post.txt` 파일은 다음과 같은 형식으로 작성하세요:

```
1. 첫 번째 포스트 제목

첫 번째 포스트의 내용입니다.
여러 줄로 작성할 수 있습니다.

-----
2. 두 번째 포스트 제목

두 번째 포스트의 내용입니다.

-----
3. 세 번째 포스트 제목

세 번째 포스트의 내용입니다.
```

## 🖼️ 이미지 파일 명명 규칙

이미지 파일은 `img/` 폴더에 다음 규칙으로 저장하세요:

- 형식: `[포스트번호]-[순서].[확장자]`
- 예시: `1-1.jpg`, `1-2.png`, `2-1.jpg`
- 지원 확장자: jpg, jpeg, png, gif

## 🚀 사용법

### 기본 사용법

```bash
# 연결 테스트
python3 test_connection.py

# 모든 포스트를 초안으로 업로드
python3 wp_auto_poster.py --status draft

# 특정 범위의 포스트만 업로드
python3 wp_auto_poster.py --start 1 --end 10 --status draft

# 포스트를 바로 발행
python3 wp_auto_poster.py --start 1 --end 5 --status publish
```

### 배치 처리 (대량 포스팅 권장)

```bash
# 5개씩 배치로 처리, 30초 간격
python3 batch_processor.py --start 1 --end 50 --batch-size 5 --batch-delay 30

# 포스트 간 대기시간 조정
python3 batch_processor.py --post-delay 10
```

### WordPress 관리 유틸리티

```bash
# 포스트 통계 확인
python3 wp_utils.py --stats

# 포스트 백업
python3 wp_utils.py --backup

# 자동 포스트 정리 (미리보기)
python3 wp_utils.py --clean

# 포스트 상태 변경
python3 wp_utils.py --publish 123 124 125
python3 wp_utils.py --draft 126 127
```

## 🔧 WordPress 설정

### 1. REST API 활성화

WordPress 관리자 페이지에서:
1. 설정 → 고유주소 → 기본값이 아닌 다른 옵션 선택
2. 변경사항 저장

### 2. Application Password 생성 (권장)

1. 사용자 → 프로필에서 Application Passwords 섹션 찾기
2. 새 Application Password 생성
3. 생성된 비밀번호를 `wp_config.json`의 `application_password`에 입력

### 3. 사용자 권한 확인

포스트를 생성할 사용자가 '편집자(Editor)' 이상의 권한을 가져야 합니다.

## 📅 날짜 자동 설정

포스트 날짜는 번호에 따라 자동으로 설정됩니다:
- 1번 포스트: 오늘 (최신)
- 2번 포스트: 어제
- 3번 포스트: 그저께
- ...

WordPress에서 날짜순 정렬 시 1번이 맨 위에 표시됩니다.

## 🔒 보안 주의사항

- `wp_config.json` 파일은 절대 공개 저장소에 업로드하지 마세요
- SSH 키 파일 권한을 적절히 설정하세요: `chmod 600 ~/.ssh/your_key.pem`
- Application Password 사용을 권장합니다
- 정기적으로 백업을 생성하세요

## 🐛 문제 해결

### WordPress REST API 오류
```bash
# 고유주소 설정 확인
# WordPress 관리자 → 설정 → 고유주소
```

### SFTP 권한 오류
```bash
# 서버에서 디렉토리 권한 설정
sudo mkdir -p /path/to/wordpress/wp-content/uploads/auto-posts
sudo chown www-data:www-data /path/to/wordpress/wp-content/uploads/auto-posts
sudo chmod 755 /path/to/wordpress/wp-content/uploads/auto-posts
```

### SSH 키 권한 오류
```bash
chmod 600 ~/.ssh/your_private_key.pem
```

## 📊 결과 확인

스크립트 실행 후 다음 파일들에서 결과를 확인할 수 있습니다:
- `posting_results_YYYYMMDD_HHMMSS.json`: 단일 실행 결과
- `batch_results_YYYYMMDD_HHMMSS.json`: 배치 처리 결과

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## ⚠️ 면책 조항

이 도구를 사용하기 전에 반드시 테스트 환경에서 먼저 실행해보세요. 대량 포스팅 전에는 백업을 생성하는 것을 강력히 권장합니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면 [Issues](https://github.com/your-username/wordpress-auto-poster/issues)에 등록해주세요.
