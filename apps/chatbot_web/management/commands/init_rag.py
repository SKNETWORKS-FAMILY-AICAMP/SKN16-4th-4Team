"""
RAG 시스템 초기화 관리 명령어
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import logging

from apps.chatbot_web.rag_system.rag_service import get_rag_service
from apps.chatbot_web.rag_system.policy_metadata import PolicyMetadataManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'RAG 시스템 데이터를 초기화합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='벡터스토어를 초기화하고 다시 로드합니다',
        )
        parser.add_argument(
            '--region',
            type=str,
            help='특정 지역만 로드합니다 (예: 경남, 전국)',
        )
        parser.add_argument(
            '--metadata-only',
            action='store_true',
            help='메타데이터만 생성하고 벡터스토어는 업데이트하지 않습니다',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('RAG 시스템 초기화를 시작합니다...')
        )

        try:
            # 메타데이터 매니저 초기화
            metadata_manager = PolicyMetadataManager()
            
            if options['metadata_only']:
                self.stdout.write('메타데이터 자동 생성 중...')
                metadata_manager.auto_generate_metadata()
                metadata_manager.save_metadata()
                self.stdout.write(
                    self.style.SUCCESS('메타데이터 생성이 완료되었습니다.')
                )
                return

            # RAG 서비스 초기화
            rag_service = get_rag_service()
            
            if not rag_service.openai_api_key:
                self.stdout.write(
                    self.style.ERROR('OpenAI API 키가 설정되지 않았습니다.')
                )
                return

            if options['reset']:
                self.stdout.write('벡터스토어를 초기화합니다...')
                rag_service.reset_vectorstore()

            # 데이터 디렉토리 확인
            base_dir = Path("c:/develop1/d/data/복지로")
            if not base_dir.exists():
                self.stdout.write(
                    self.style.ERROR(f'데이터 디렉토리가 존재하지 않습니다: {base_dir}')
                )
                return

            # 지역 목록
            regions = ["경남", "경북", "대구", "부산", "전국", "전남", "전북"]
            
            # 특정 지역만 처리
            if options['region']:
                if options['region'] in regions:
                    regions = [options['region']]
                else:
                    self.stdout.write(
                        self.style.ERROR(f'알 수 없는 지역: {options["region"]}')
                    )
                    return

            # 지역별 PDF 파일 로드
            total_files = 0
            for region in regions:
                pdf_dir = base_dir / region / "pdf"
                if not pdf_dir.exists():
                    self.stdout.write(
                        self.style.WARNING(f'{region} 지역의 PDF 디렉토리가 없습니다: {pdf_dir}')
                    )
                    continue

                pdf_files = list(pdf_dir.glob("*.pdf"))
                if not pdf_files:
                    self.stdout.write(
                        self.style.WARNING(f'{region} 지역에 PDF 파일이 없습니다')
                    )
                    continue

                self.stdout.write(f'{region} 지역 처리 중... ({len(pdf_files)}개 파일)')
                
                try:
                    rag_service.add_documents_from_directory(str(pdf_dir), region)
                    total_files += len(pdf_files)
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ {region} 지역 완료')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ {region} 지역 처리 실패: {e}')
                    )

            # 통계 출력
            stats = rag_service.get_collection_stats()
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n초기화 완료!\n'
                    f'- 처리된 PDF 파일: {total_files}개\n'
                    f'- 벡터스토어 문서 수: {stats["document_count"]}개\n'
                    f'- 컬렉션 이름: {stats["collection_name"]}'
                )
            )

            # 메타데이터도 업데이트
            self.stdout.write('정책 메타데이터 생성 중...')
            metadata_manager.auto_generate_metadata()
            metadata_manager.save_metadata()
            self.stdout.write(
                self.style.SUCCESS('메타데이터 생성 완료')
            )

        except Exception as e:
            logger.error(f"RAG 초기화 실패: {e}", exc_info=True)
            self.stdout.write(
                self.style.ERROR(f'초기화 실패: {e}')
            )