# Generated manually for Phase 3-1: Feedback Analysis Enhancement

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot_web', '0003_kakaouser_sessionrating'),
    ]

    operations = [
        migrations.AddField(
            model_name='userfeedback',
            name='category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('feature_request', '기능 요청'),
                    ('bug', '버그'),
                    ('usability', '사용성 문제'),
                    ('praise', '칭찬'),
                    ('other', '기타')
                ],
                max_length=20,
                null=True,
                verbose_name='카테고리'
            ),
        ),
        migrations.AddField(
            model_name='userfeedback',
            name='sentiment',
            field=models.CharField(
                blank=True,
                choices=[
                    ('positive', '긍정'),
                    ('neutral', '중립'),
                    ('negative', '부정')
                ],
                max_length=10,
                null=True,
                verbose_name='감정'
            ),
        ),
    ]
