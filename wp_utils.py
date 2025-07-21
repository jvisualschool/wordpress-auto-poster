#!/usr/bin/env python3
"""
WordPress 유틸리티 함수들
데이터베이스 직접 조작 및 관리 기능
"""

import mysql.connector
import json
import os
from datetime import datetime

class WordPressUtils:
    def __init__(self, config_file='wp_config.json'):
        """설정 파일을 로드하여 초기화"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.db_config = self.config['database']
    
    def get_db_connection(self):
        """MySQL 데이터베이스 연결"""
        return mysql.connector.connect(**self.db_config)
    
    def get_all_posts(self, post_type='post', status=None):
        """모든 포스트 조회"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = "SELECT * FROM wp_posts WHERE post_type = %s"
            params = [post_type]
            
            if status:
                query += " AND post_status = %s"
                params.append(status)
            
            query += " ORDER BY post_date DESC"
            
            cursor.execute(query, params)
            posts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return posts
            
        except Exception as e:
            print(f"포스트 조회 실패: {e}")
            return []
    
    def delete_posts_by_title_pattern(self, pattern):
        """제목 패턴으로 포스트 삭제"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 먼저 삭제할 포스트들 조회
            query = "SELECT ID, post_title FROM wp_posts WHERE post_title LIKE %s"
            cursor.execute(query, [f"%{pattern}%"])
            posts_to_delete = cursor.fetchall()
            
            if not posts_to_delete:
                print(f"패턴 '{pattern}'에 해당하는 포스트가 없습니다.")
                return 0
            
            print(f"삭제할 포스트 {len(posts_to_delete)}개:")
            for post_id, title in posts_to_delete:
                print(f"  - ID {post_id}: {title}")
            
            confirm = input("정말 삭제하시겠습니까? (y/N): ")
            if confirm.lower() != 'y':
                print("삭제가 취소되었습니다.")
                return 0
            
            # 포스트 삭제
            delete_query = "DELETE FROM wp_posts WHERE post_title LIKE %s"
            cursor.execute(delete_query, [f"%{pattern}%"])
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            cursor.close()
            conn.close()
            
            print(f"{deleted_count}개 포스트가 삭제되었습니다.")
            return deleted_count
            
        except Exception as e:
            print(f"포스트 삭제 실패: {e}")
            return 0
    
    def update_post_status(self, post_ids, new_status):
        """포스트 상태 변경"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            if isinstance(post_ids, int):
                post_ids = [post_ids]
            
            placeholders = ','.join(['%s'] * len(post_ids))
            query = f"UPDATE wp_posts SET post_status = %s WHERE ID IN ({placeholders})"
            
            params = [new_status] + post_ids
            cursor.execute(query, params)
            
            updated_count = cursor.rowcount
            conn.commit()
            
            cursor.close()
            conn.close()
            
            print(f"{updated_count}개 포스트의 상태가 '{new_status}'로 변경되었습니다.")
            return updated_count
            
        except Exception as e:
            print(f"포스트 상태 변경 실패: {e}")
            return 0
    
    def get_post_statistics(self):
        """포스트 통계 조회"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 상태별 포스트 수
            cursor.execute("""
                SELECT post_status, COUNT(*) as count 
                FROM wp_posts 
                WHERE post_type = 'post' 
                GROUP BY post_status
            """)
            status_stats = cursor.fetchall()
            
            # 최근 포스트
            cursor.execute("""
                SELECT post_title, post_date, post_status 
                FROM wp_posts 
                WHERE post_type = 'post' 
                ORDER BY post_date DESC 
                LIMIT 10
            """)
            recent_posts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            print("=== WordPress 포스트 통계 ===")
            print("상태별 포스트 수:")
            for status, count in status_stats:
                print(f"  {status}: {count}개")
            
            print(f"\n최근 포스트 10개:")
            for title, date, status in recent_posts:
                print(f"  [{status}] {title} ({date})")
            
            return {
                'status_stats': status_stats,
                'recent_posts': recent_posts
            }
            
        except Exception as e:
            print(f"통계 조회 실패: {e}")
            return None
    
    def backup_posts_to_json(self, filename=None):
        """포스트를 JSON 파일로 백업"""
        if not filename:
            filename = f"wp_posts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        posts = self.get_all_posts()
        
        if posts:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(posts, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"포스트 {len(posts)}개가 {filename}에 백업되었습니다.")
            return filename
        else:
            print("백업할 포스트가 없습니다.")
            return None
    
    def clean_auto_posts(self, dry_run=True):
        """자동 생성된 포스트 정리 (제목에 번호가 있는 포스트들)"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 번호로 시작하는 제목의 포스트들 찾기
            query = """
                SELECT ID, post_title, post_status, post_date 
                FROM wp_posts 
                WHERE post_type = 'post' 
                AND post_title REGEXP '^[0-9]+\\.'
                ORDER BY post_date DESC
            """
            
            cursor.execute(query)
            auto_posts = cursor.fetchall()
            
            if not auto_posts:
                print("자동 생성된 포스트가 없습니다.")
                return 0
            
            print(f"자동 생성된 포스트 {len(auto_posts)}개 발견:")
            for post_id, title, status, date in auto_posts:
                print(f"  ID {post_id}: [{status}] {title} ({date})")
            
            if dry_run:
                print(f"\n[DRY RUN] 실제 삭제하려면 dry_run=False로 실행하세요.")
                return 0
            
            confirm = input(f"\n{len(auto_posts)}개 포스트를 정말 삭제하시겠습니까? (y/N): ")
            if confirm.lower() != 'y':
                print("삭제가 취소되었습니다.")
                return 0
            
            # 실제 삭제
            post_ids = [post[0] for post in auto_posts]
            placeholders = ','.join(['%s'] * len(post_ids))
            delete_query = f"DELETE FROM wp_posts WHERE ID IN ({placeholders})"
            
            cursor.execute(delete_query, post_ids)
            deleted_count = cursor.rowcount
            conn.commit()
            
            cursor.close()
            conn.close()
            
            print(f"{deleted_count}개 포스트가 삭제되었습니다.")
            return deleted_count
            
        except Exception as e:
            print(f"포스트 정리 실패: {e}")
            return 0

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WordPress 유틸리티')
    parser.add_argument('--stats', action='store_true', help='포스트 통계 조회')
    parser.add_argument('--backup', action='store_true', help='포스트 백업')
    parser.add_argument('--clean', action='store_true', help='자동 포스트 정리 (dry run)')
    parser.add_argument('--clean-force', action='store_true', help='자동 포스트 정리 (실제 삭제)')
    parser.add_argument('--delete-pattern', help='제목 패턴으로 포스트 삭제')
    parser.add_argument('--publish', nargs='+', type=int, help='포스트 ID들을 발행 상태로 변경')
    parser.add_argument('--draft', nargs='+', type=int, help='포스트 ID들을 초안 상태로 변경')
    
    args = parser.parse_args()
    
    try:
        utils = WordPressUtils()
        
        if args.stats:
            utils.get_post_statistics()
        
        if args.backup:
            utils.backup_posts_to_json()
        
        if args.clean:
            utils.clean_auto_posts(dry_run=True)
        
        if args.clean_force:
            utils.clean_auto_posts(dry_run=False)
        
        if args.delete_pattern:
            utils.delete_posts_by_title_pattern(args.delete_pattern)
        
        if args.publish:
            utils.update_post_status(args.publish, 'publish')
        
        if args.draft:
            utils.update_post_status(args.draft, 'draft')
        
        if not any(vars(args).values()):
            parser.print_help()
            
    except FileNotFoundError:
        print("wp_config.json 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()