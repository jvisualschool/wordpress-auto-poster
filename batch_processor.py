#!/usr/bin/env python3
"""
배치 처리 스크립트
대량의 포스트를 안전하게 처리하기 위한 배치 프로세서
"""

import time
import json
from datetime import datetime
from wp_auto_poster import WordPressAutoPoster

class BatchProcessor:
    def __init__(self, config_file='wp_config.json'):
        self.poster = WordPressAutoPoster(config_file)
        self.batch_size = 5  # 한 번에 처리할 포스트 수
        self.delay_between_batches = 30  # 배치 간 대기 시간 (초)
        self.delay_between_posts = 5  # 포스트 간 대기 시간 (초)
    
    def process_in_batches(self, txt_file, start_post=1, end_post=None, status='draft'):
        """배치 단위로 포스트 처리"""
        
        # 전체 포스트 파싱
        posts = self.poster.parse_posts_from_txt(txt_file)
        
        # 범위 필터링
        if end_post is None:
            end_post = max(p['number'] for p in posts)
        
        posts = [p for p in posts if start_post <= p['number'] <= end_post]
        
        if not posts:
            print("처리할 포스트가 없습니다.")
            return []
        
        print(f"총 {len(posts)}개 포스트를 배치 크기 {self.batch_size}로 처리합니다.")
        print(f"예상 소요 시간: {self._estimate_time(len(posts))} 분")
        
        all_results = []
        
        # 배치 단위로 처리
        for i in range(0, len(posts), self.batch_size):
            batch_posts = posts[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(posts) + self.batch_size - 1) // self.batch_size
            
            print(f"\n=== 배치 {batch_num}/{total_batches} 처리 중 ===")
            print(f"포스트 범위: {batch_posts[0]['number']} ~ {batch_posts[-1]['number']}")
            
            batch_results = self._process_batch(batch_posts, status)
            all_results.extend(batch_results)
            
            # 마지막 배치가 아니면 대기
            if i + self.batch_size < len(posts):
                print(f"다음 배치까지 {self.delay_between_batches}초 대기...")
                time.sleep(self.delay_between_batches)
        
        # 최종 결과 저장
        self._save_results(all_results)
        self._print_summary(all_results)
        
        return all_results
    
    def _process_batch(self, batch_posts, status):
        """단일 배치 처리"""
        batch_results = []
        
        for i, post in enumerate(batch_posts):
            print(f"  [{i+1}/{len(batch_posts)}] 처리 중: {post['number']}. {post['title']}")
            
            try:
                # 이미지 찾기 및 업로드
                local_images = self.poster.get_post_images(post['number'])
                uploaded_images = []
                
                for img_path in local_images:
                    print(f"    이미지 업로드: {img_path}")
                    img_url = self.poster.upload_image_via_sftp(img_path, post['number'])
                    if img_url:
                        uploaded_images.append(img_url)
                
                # WordPress 포스트 생성
                wp_result = self.poster.create_wp_post(
                    title=post['title'],
                    content=post['content'],
                    post_number=post['number'],
                    images=uploaded_images,
                    status=status
                )
                
                if wp_result:
                    print(f"    ✅ 성공: 포스트 ID {wp_result.get('id')}")
                    batch_results.append({
                        'post_number': post['number'],
                        'wp_id': wp_result.get('id'),
                        'title': post['title'],
                        'status': 'success',
                        'images_count': len(uploaded_images),
                        'processed_at': datetime.now().isoformat()
                    })
                else:
                    print(f"    ❌ 실패: 포스트 생성 오류")
                    batch_results.append({
                        'post_number': post['number'],
                        'title': post['title'],
                        'status': 'failed',
                        'images_count': len(uploaded_images),
                        'processed_at': datetime.now().isoformat()
                    })
                
                # 포스트 간 대기
                if i < len(batch_posts) - 1:
                    time.sleep(self.delay_between_posts)
                    
            except Exception as e:
                print(f"    ❌ 오류: {e}")
                batch_results.append({
                    'post_number': post['number'],
                    'title': post['title'],
                    'status': 'error',
                    'error': str(e),
                    'processed_at': datetime.now().isoformat()
                })
        
        return batch_results
    
    def _estimate_time(self, total_posts):
        """예상 소요 시간 계산 (분)"""
        batches = (total_posts + self.batch_size - 1) // self.batch_size
        
        # 포스트 처리 시간 (포스트당 평균 30초 가정)
        post_time = total_posts * 30
        
        # 포스트 간 대기 시간
        post_delays = (total_posts - 1) * self.delay_between_posts
        
        # 배치 간 대기 시간
        batch_delays = (batches - 1) * self.delay_between_batches
        
        total_seconds = post_time + post_delays + batch_delays
        return round(total_seconds / 60, 1)
    
    def _save_results(self, results):
        """결과를 JSON 파일로 저장"""
        filename = f'batch_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n결과가 {filename}에 저장되었습니다.")
    
    def _print_summary(self, results):
        """처리 결과 요약 출력"""
        total = len(results)
        success = len([r for r in results if r['status'] == 'success'])
        failed = len([r for r in results if r['status'] == 'failed'])
        error = len([r for r in results if r['status'] == 'error'])
        
        print(f"\n=== 배치 처리 완료 ===")
        print(f"총 처리: {total}개")
        print(f"성공: {success}개")
        print(f"실패: {failed}개")
        print(f"오류: {error}개")
        print(f"성공률: {(success/total*100):.1f}%")
        
        if failed > 0 or error > 0:
            print(f"\n실패한 포스트:")
            for result in results:
                if result['status'] in ['failed', 'error']:
                    print(f"  - {result['post_number']}. {result['title']}")

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WordPress 배치 포스팅 스크립트')
    parser.add_argument('--txt-file', default='post.txt', help='포스트 텍스트 파일')
    parser.add_argument('--start', type=int, default=1, help='시작 포스트 번호')
    parser.add_argument('--end', type=int, help='끝 포스트 번호')
    parser.add_argument('--status', default='draft', choices=['draft', 'publish'], 
                       help='포스트 상태')
    parser.add_argument('--batch-size', type=int, default=5, help='배치 크기')
    parser.add_argument('--batch-delay', type=int, default=30, help='배치 간 대기 시간(초)')
    parser.add_argument('--post-delay', type=int, default=5, help='포스트 간 대기 시간(초)')
    
    args = parser.parse_args()
    
    try:
        processor = BatchProcessor()
        processor.batch_size = args.batch_size
        processor.delay_between_batches = args.batch_delay
        processor.delay_between_posts = args.post_delay
        
        processor.process_in_batches(
            txt_file=args.txt_file,
            start_post=args.start,
            end_post=args.end,
            status=args.status
        )
        
    except FileNotFoundError:
        print("설정 파일을 찾을 수 없습니다: wp_config.json")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()