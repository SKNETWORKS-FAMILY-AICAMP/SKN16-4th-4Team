"""
RAG 데이터베이스 구축 명령
"""
from django.core.management.base import BaseCommand
from chatbot_web.rag_system.rag_service import get_main_rag_service, get_validation_rag_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'RAG 시스템 데이터베이스 구축 (청킹/임베딩)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--validation',
            action='store_true',
            help='검증용 데이터베이스 구축 (복지로 - 복사본)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 데이터베이스 강제 재구축',
        )

    def handle(self, *args, **options):
        is_validation = options['validation']
        force_rebuild = options['force']

        if is_validation:
            self.stdout.write(self.style.WARNING("\n=== 검증용 RAG 데이터베이스 구축 ==="))
            self.stdout.write(f"데이터: 복지로 - 복사본")
            rag_service = get_validation_rag_service()
            db_path = rag_service.chroma_db_dir
        else:
            self.stdout.write(self.style.SUCCESS("\n=== 메인 RAG 데이터베이스 구축 ==="))
            self.stdout.write(f"데이터: 복지로 (전체)")
            rag_service = get_main_rag_service()
            db_path = rag_service.chroma_db_dir

        # 기존 DB 확인
        if db_path.exists() and not force_rebuild:
            # DB 파일 개수 확인
            db_files = list(db_path.rglob('*'))
            if db_files:
                self.stdout.write(self.style.WARNING(f"\n[WARNING] 기존 데이터베이스 발견: {db_path}"))
                self.stdout.write(f"   파일 수: {len(db_files)}개")

                # 사용자에게 선택 물어보기
                while True:
                    choice = input("\n선택하세요:\n  [1] 기존 DB 사용 (건너뛰기)\n  [2] 기존 DB 삭제 후 재구축\n  [3] 취소\n\n입력 (1/2/3): ").strip()

                    if choice == '1':
                        self.stdout.write(self.style.SUCCESS("\n[OK] 기존 데이터베이스 사용"))
                        self.stdout.write(f"위치: {db_path}")
                        return
                    elif choice == '2':
                        force_rebuild = True
                        self.stdout.write(self.style.WARNING("\n[DELETE] 기존 데이터베이스 삭제 후 재구축"))
                        break
                    elif choice == '3':
                        self.stdout.write(self.style.ERROR("\n[CANCEL] 취소됨"))
                        return
                    else:
                        self.stdout.write(self.style.ERROR("잘못된 입력입니다. 1, 2, 또는 3을 입력하세요."))

        if force_rebuild:
            self.stdout.write(self.style.WARNING("[DELETE] 강제 재구축 모드: 기존 데이터 삭제"))

        try:
            self.stdout.write("\n데이터 처리 시작...")
            self.stdout.write("이 작업은 시간이 오래 걸릴 수 있습니다 (수 분 ~ 수십 분)")

            result = rag_service.build_database(force_rebuild=force_rebuild)

            self.stdout.write(self.style.SUCCESS("\n[OK] 데이터베이스 구축 완료!"))
            self.stdout.write(f"결과: {result}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n[ERROR] 오류 발생: {e}"))
            logger.error(f"Database build error: {e}", exc_info=True)
            raise
