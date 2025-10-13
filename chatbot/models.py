from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """사용자 프로필 모델 - 맞춤형 정책 추천을 위한 정보"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # 개인 정보
    age = models.IntegerField(null=True, blank=True, verbose_name="나이")
    gender = models.CharField(
        max_length=10,
        choices=[('남성', '남성'), ('여성', '여성'), ('기타', '기타')],
        null=True,
        blank=True,
        verbose_name="성별"
    )
    region = models.CharField(max_length=100, null=True, blank=True, verbose_name="거주지역")

    # 추가 정보
    disability = models.BooleanField(default=False, verbose_name="장애 여부")
    veteran = models.BooleanField(default=False, verbose_name="보훈 대상 여부")
    low_income = models.BooleanField(default=False, verbose_name="저소득층 여부")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필"

    def __str__(self):
        return f"{self.user.username}의 프로필"


class ChatHistory(models.Model):
    """챗봇 대화 이력 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_history')
    question = models.TextField(verbose_name="질문")
    answer = models.TextField(verbose_name="답변")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    # 평가 필드 추가
    relevance_score = models.FloatField(null=True, blank=True, verbose_name="관련성 점수")
    accuracy_score = models.FloatField(null=True, blank=True, verbose_name="정확성 점수")
    completeness_score = models.FloatField(null=True, blank=True, verbose_name="완전성 점수")
    overall_score = models.FloatField(null=True, blank=True, verbose_name="종합 점수")

    class Meta:
        verbose_name = "채팅 이력"
        verbose_name_plural = "채팅 이력"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def calculate_overall_score(self):
        """종합 점수 계산"""
        scores = [s for s in [self.relevance_score, self.accuracy_score, self.completeness_score] if s is not None]
        if scores:
            self.overall_score = sum(scores) / len(scores)
            return self.overall_score
        return None


class Policy(models.Model):
    """정책 정보 모델"""
    title = models.CharField(max_length=500, verbose_name="정책명")
    category = models.CharField(max_length=100, verbose_name="카테고리")
    description = models.TextField(verbose_name="설명")
    target = models.CharField(max_length=200, verbose_name="대상")
    url = models.URLField(blank=True, verbose_name="관련 링크")
    file_name = models.CharField(max_length=500, blank=True, verbose_name="원본 파일명")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "정책"
        verbose_name_plural = "정책"
        ordering = ['category', 'title']

    def __str__(self):
        return self.title


class Document(models.Model):
    """업로드된 문서 관리 모델"""
    title = models.CharField(max_length=500, verbose_name="문서 제목")
    file = models.FileField(upload_to='documents/%Y/%m/', verbose_name="파일")
    file_type = models.CharField(max_length=10, verbose_name="파일 형식")  # pdf, hwp, hwpx
    category = models.CharField(max_length=100, verbose_name="카테고리")
    description = models.TextField(blank=True, verbose_name="설명")

    # 추출된 텍스트 내용 (캐시)
    extracted_text = models.TextField(blank=True, verbose_name="추출된 텍스트")

    # ChromaDB 동기화 상태
    is_synced = models.BooleanField(default=False, verbose_name="ChromaDB 동기화 여부")
    chunk_count = models.IntegerField(default=0, verbose_name="청크 수")

    # 메타데이터
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="업로드한 사용자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "문서"
        verbose_name_plural = "문서"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_file_extension(self):
        """파일 확장자 반환"""
        return self.file.name.split('.')[-1].lower()

    def delete(self, *args, **kwargs):
        """문서 삭제 시 파일도 함께 삭제"""
        if self.file:
            self.file.delete()
        super().delete(*args, **kwargs)
