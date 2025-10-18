"""
관리자 계정 자동 생성 스크립트
admin / admin 계정을 생성합니다.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.django_settings')
django.setup()

from django.contrib.auth.models import User

def create_admin():
    # 기존 admin 계정 확인
    if User.objects.filter(username='admin').exists():
        print("이미 'admin' 계정이 존재합니다.")
        admin_user = User.objects.get(username='admin')
        admin_user.set_password('admin')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.save()
        print("'admin' 계정의 비밀번호를 'admin'으로 재설정했습니다.")
    else:
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin'
        )
        print("관리자 계정이 생성되었습니다.")
        print("  사용자명: admin")
        print("  비밀번호: admin")

if __name__ == '__main__':
    create_admin()
