"""
중복 활성화된 구성 수정 Django 관리 명령
"""
from django.core.management.base import BaseCommand
from chatbot_web.models import RAGConfiguration


class Command(BaseCommand):
    help = '각 타입별로 하나의 구성만 활성화되도록 수정'

    def handle(self, *args, **options):
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("RAG 구성 활성화 상태 수정"))
        self.stdout.write("=" * 50)

        # 일반 구성 확인
        self.stdout.write("\n[일반 구성]")
        normal_configs = RAGConfiguration.objects.filter(is_validation=False)
        active_normal = normal_configs.filter(is_active=True)

        self.stdout.write(f"총 구성 수: {normal_configs.count()}")
        self.stdout.write(f"활성화된 구성 수: {active_normal.count()}")

        if active_normal.count() > 1:
            self.stdout.write(self.style.WARNING("\n[WARNING] 여러 개의 일반 구성이 활성화되어 있습니다!"))
            for config in active_normal:
                self.stdout.write(f"  - {config.name} (ID: {config.pk})")

            # 가장 최근에 생성된 것만 남기고 나머지 비활성화
            latest_active = active_normal.order_by('-created_at').first()
            normal_configs.update(is_active=False)
            latest_active.is_active = True
            latest_active.save()

            self.stdout.write(self.style.SUCCESS(f"\n[OK] '{latest_active.name}'만 활성화하고 나머지는 비활성화했습니다."))
        elif active_normal.count() == 1:
            self.stdout.write(self.style.SUCCESS(f"[OK] 올바르게 1개만 활성화되어 있습니다: {active_normal.first().name}"))
        else:
            self.stdout.write(self.style.WARNING("[WARNING] 활성화된 구성이 없습니다."))

        # 검증용 구성 확인
        self.stdout.write("\n[검증용 구성]")
        validation_configs = RAGConfiguration.objects.filter(is_validation=True)
        active_validation = validation_configs.filter(is_active=True)

        self.stdout.write(f"총 구성 수: {validation_configs.count()}")
        self.stdout.write(f"활성화된 구성 수: {active_validation.count()}")

        if active_validation.count() > 1:
            self.stdout.write(self.style.WARNING("\n[WARNING] 여러 개의 검증용 구성이 활성화되어 있습니다!"))
            for config in active_validation:
                self.stdout.write(f"  - {config.name} (ID: {config.pk})")

            # 가장 최근에 생성된 것만 남기고 나머지 비활성화
            latest_active = active_validation.order_by('-created_at').first()
            validation_configs.update(is_active=False)
            latest_active.is_active = True
            latest_active.save()

            self.stdout.write(self.style.SUCCESS(f"\n[OK] '{latest_active.name}'만 활성화하고 나머지는 비활성화했습니다."))
        elif active_validation.count() == 1:
            self.stdout.write(self.style.SUCCESS(f"[OK] 올바르게 1개만 활성화되어 있습니다: {active_validation.first().name}"))
        else:
            self.stdout.write(self.style.WARNING("[WARNING] 활성화된 구성이 없습니다."))

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("수정 완료!"))
        self.stdout.write("=" * 50)
