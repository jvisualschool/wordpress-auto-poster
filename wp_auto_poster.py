#!/usr/bin/env python3
"""
WordPress 자동 포스팅 스크립트
TXT 파일과 이미지를 이용해 WordPress 블로그에 자동으로 포스팅합니다.
"""

import os
import re
import json
import requests
import paramiko
from datetime import datetime, timedelta
import mysql.connector
from urllib.parse import urljoin
import base64
import mimetypes

class WordPressAutoPoster:
    def __init__(self, config_file='wp_config.json'):
        """설정 파일을 로드하여 초기화"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.wp_url = self.config['wordpress']['url']
        self.wp_user = self.config['wordpress']['username']
        self.wp_password = self.config['wordpress']['password']
        
        # Application Password가 있으면 사용
        if 'application_password' in self.config['wordpress']:
            self.wp_application_password = self.config['wordpress']['application_password']
        
        # SFTP 설정
        self.sftp_host = self.config['sftp']['host']
        self.sftp_user = self.config['sftp']['username']
        self.sftp_password = self.config['sftp'].get('password')
        self.sftp_private_key = self.config['sftp'].get('privateKey')
        self.sftp_port = self.config['sftp'].get('port', 22)
        self.remote_image_path = self.config['sftp']['remote_image_path']
        self.image_url_base = self.config['sftp']['image_url_base']
        
        # MySQL 설정
        self.db_config = self.config['database']
        
    def parse_posts_from_txt(self, txt_file):
        """TXT 파일에서 포스트들을 파싱"""
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 포스트를 구분하는 패턴 (-----로 구분)
        posts = re.split(r'-----\n', content)
        parsed_posts = []
        
        for post in posts:
            post = post.strip()
            if not post:
                continue
                
            # 첫 번째 줄에서 번호와 제목 추출
            lines = post.split('\n')
            if not lines:
                continue
                
            first_line = lines[0].strip()
            # "1. 제목" 형식에서 번호와 제목 추출
            match = re.match(r'^(\d+)\.\s*(.+)', first_line)
            if match:
                post_number = int(match.group(1))
                title = match.group(2)
                content_lines = lines[1:] if len(lines) > 1 else []
                content = '\n'.join(content_lines).strip()
                
                parsed_posts.append({
                    'number': post_number,
                    'title': title,
                    'content': content
                })
        
        return parsed_posts
    
    def get_post_images(self, post_number, img_folder='img'):
        """특정 포스트 번호에 해당하는 이미지 파일들을 찾기"""
        images = []
        if not os.path.exists(img_folder):
            return images
            
        for filename in os.listdir(img_folder):
            # 파일명 패턴: [번호]-[순서].jpg 또는 [번호]-[순서].png
            pattern = rf'^{post_number}-\d+\.(jpg|jpeg|png|gif)$'
            if re.match(pattern, filename, re.IGNORECASE):
                images.append(os.path.join(img_folder, filename))
        
        # 순서대로 정렬
        images.sort(key=lambda x: int(re.search(rf'{post_number}-(\d+)', os.path.basename(x)).group(1)))
        return images
    
    def upload_image_via_sftp(self, local_image_path, post_number):
        """SFTP를 통해 이미지 업로드"""
        try:
            # SSH 클라이언트 생성
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # SSH 키 또는 비밀번호로 연결
            if self.sftp_private_key:
                # SSH 키 파일 경로 처리 (~/ 확장)
                key_path = os.path.expanduser(self.sftp_private_key)
                ssh.connect(
                    self.sftp_host, 
                    port=self.sftp_port,
                    username=self.sftp_user, 
                    key_filename=key_path
                )
            elif self.sftp_password:
                # 비밀번호로 연결
                ssh.connect(
                    self.sftp_host, 
                    port=self.sftp_port,
                    username=self.sftp_user, 
                    password=self.sftp_password
                )
            else:
                raise Exception("SSH 키 파일 또는 비밀번호가 필요합니다")
            
            # SFTP 클라이언트 생성
            sftp = ssh.open_sftp()
            
            # 원격 디렉토리 생성 (존재하지 않는 경우)
            remote_dir = f"{self.remote_image_path}/post_{post_number}"
            try:
                sftp.mkdir(remote_dir)
            except:
                pass  # 이미 존재하는 경우 무시
            
            # 파일명 생성
            filename = os.path.basename(local_image_path)
            remote_file_path = f"{remote_dir}/{filename}"
            
            # 파일 업로드
            sftp.put(local_image_path, remote_file_path)
            
            # 웹 URL 생성
            image_url = f"{self.image_url_base}/post_{post_number}/{filename}"
            
            sftp.close()
            ssh.close()
            
            return image_url
            
        except Exception as e:
            print(f"이미지 업로드 실패: {local_image_path}, 오류: {e}")
            return None
    
    def create_wp_post(self, title, content, post_number, images=None, status='draft'):
        """WordPress REST API를 통해 포스트 생성"""
        
        # 이미지가 있는 경우 컨텐츠에 추가
        if images:
            image_html = ""
            for img_url in images:
                image_html += f'<img src="{img_url}" alt="{title}" style="max-width: 100%; height: auto; margin: 10px 0;" />\n'
            content = image_html + "\n" + content
        
        # 포스트 날짜 계산 (1번이 최신, 번호가 클수록 과거)
        # 1번 = 오늘, 2번 = 어제, 3번 = 그저께...
        days_ago = post_number - 1
        post_date = datetime.now() - timedelta(days=days_ago)
        post_date_str = post_date.strftime('%Y-%m-%dT%H:%M:%S')
        
        # WordPress REST API 엔드포인트
        api_url = f"{self.wp_url}/wp-json/wp/v2/posts"
        
        # 인증 헤더 (Application Password 사용)
        if hasattr(self, 'wp_application_password'):
            print("Application Password 사용")
            credentials = base64.b64encode(f"{self.wp_user}:{self.wp_application_password}".encode()).decode()
        else:
            print("일반 비밀번호 사용")
            credentials = base64.b64encode(f"{self.wp_user}:{self.wp_password}".encode()).decode()
            
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        # 포스트 데이터
        post_data = {
            'title': title,
            'content': content,
            'status': status,
            'format': 'standard',
            'date': post_date_str  # 포스트 날짜 설정
        }
        
        try:
            print(f"API URL: {api_url}")
            response = requests.post(api_url, headers=headers, json=post_data)
            
            if response.status_code >= 400:
                print(f"오류 응답: {response.status_code}")
                print(f"응답 내용: {response.text[:200]}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"포스트 생성 실패: {e}")
            return None
    
    def process_posts(self, txt_file, start_post=None, end_post=None, status='draft'):
        """포스트들을 처리하여 WordPress에 업로드"""
        posts = self.parse_posts_from_txt(txt_file)
        
        # 범위 필터링
        if start_post is not None:
            posts = [p for p in posts if p['number'] >= start_post]
        if end_post is not None:
            posts = [p for p in posts if p['number'] <= end_post]
        
        results = []
        
        for post in posts:
            print(f"처리 중: 포스트 {post['number']} - {post['title']}")
            
            # 이미지 찾기
            local_images = self.get_post_images(post['number'])
            uploaded_images = []
            
            # 이미지 업로드
            for img_path in local_images:
                print(f"  이미지 업로드 중: {img_path}")
                img_url = self.upload_image_via_sftp(img_path, post['number'])
                if img_url:
                    uploaded_images.append(img_url)
            
            # WordPress 포스트 생성
            wp_result = self.create_wp_post(
                title=post['title'],
                content=post['content'],
                post_number=post['number'],
                images=uploaded_images,
                status=status
            )
            
            if wp_result:
                print(f"  성공: 포스트 ID {wp_result.get('id')}")
                results.append({
                    'post_number': post['number'],
                    'wp_id': wp_result.get('id'),
                    'title': post['title'],
                    'status': 'success',
                    'images_count': len(uploaded_images)
                })
            else:
                print(f"  실패: 포스트 생성 오류")
                results.append({
                    'post_number': post['number'],
                    'title': post['title'],
                    'status': 'failed',
                    'images_count': len(uploaded_images)
                })
        
        return results
    
    def get_db_connection(self):
        """MySQL 데이터베이스 연결"""
        return mysql.connector.connect(**self.db_config)
    
    def check_existing_posts(self):
        """기존 포스트 확인 (중복 방지용)"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = "SELECT post_title, post_status FROM wp_posts WHERE post_type = 'post'"
            cursor.execute(query)
            
            existing_posts = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return existing_posts
            
        except Exception as e:
            print(f"데이터베이스 조회 실패: {e}")
            return []

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WordPress 자동 포스팅 스크립트')
    parser.add_argument('--txt-file', default='post.txt', help='포스트 텍스트 파일')
    parser.add_argument('--start', type=int, help='시작 포스트 번호')
    parser.add_argument('--end', type=int, help='끝 포스트 번호')
    parser.add_argument('--status', default='draft', choices=['draft', 'publish'], 
                       help='포스트 상태 (draft 또는 publish)')
    parser.add_argument('--config', default='wp_config.json', help='설정 파일')
    
    args = parser.parse_args()
    
    try:
        poster = WordPressAutoPoster(args.config)
        results = poster.process_posts(
            txt_file=args.txt_file,
            start_post=args.start,
            end_post=args.end,
            status=args.status
        )
        
        # 결과 요약
        success_count = len([r for r in results if r['status'] == 'success'])
        total_count = len(results)
        
        print(f"\n=== 처리 완료 ===")
        print(f"성공: {success_count}/{total_count}")
        
        # 결과를 JSON 파일로 저장
        with open(f'posting_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
    except FileNotFoundError:
        print(f"설정 파일을 찾을 수 없습니다: {args.config}")
        print("wp_config.json 파일을 생성해주세요.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()