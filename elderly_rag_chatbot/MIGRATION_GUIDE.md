마이그레이션 가이드

모델 변경(예: `ChatSession.user`를 nullable로 변경)을 적용하려면 아래 절차를 따르세요.

1) 가상환경 활성화
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux

2) makemigrations 및 migrate 실행
   python manage.py makemigrations chatbot_web
   python manage.py migrate

3) 변경 예시
   - 변경된 모델이 `chatbot_web/models.py`에 반영되어 있으므로 위 명령으로 migration 파일이 자동 생성됩니다.

4) 수동 마이그레이션 파일 예시
   만약 자동 생성이 문제가 있으면 아래 예시와 같은 수동 migration을 생성할 수 있습니다 (번호 및 의존성은 프로젝트 상황에 따라 조정).

   from django.db import migrations, models

   class Migration(migrations.Migration):
       dependencies = [
           ('chatbot_web', '0001_initial'),
       ]

       operations = [
           migrations.AlterField(
               model_name='chatsession',
               name='user',
               field=models.ForeignKey(null=True, blank=True, on_delete=models.CASCADE, related_name='chat_sessions', to='auth.user'),
           ),
       ]

5) 테스트
   - migrate 후 관리자에서 ChatSession 생성/조회, anonymous 세션 생성/저장 동작을 확인하세요.
