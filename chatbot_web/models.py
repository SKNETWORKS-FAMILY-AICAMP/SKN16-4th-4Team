"""
RAG 챗봇 시스템 모델
- 사용자 관리
- RAG 구성 관리
- 대화 기록 관리
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """사용자 프로필 확장"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.IntegerField(null=True, blank=True, verbose_name="나이")
    region = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('서울특별시', '서울특별시'),
            ('부산광역시', '부산광역시'),
            ('대구광역시', '대구광역시'),
            ('인천광역시', '인천광역시'),
            ('광주광역시', '광주광역시'),
            ('대전광역시', '대전광역시'),
            ('울산광역시', '울산광역시'),
            ('세종특별자치시', '세종특별자치시'),
            ('경기도', '경기도'),
            ('강원특별자치도', '강원특별자치도'),
            ('충청북도', '충청북도'),
            ('충청남도', '충청남도'),
            ('전북특별자치도', '전북특별자치도'),
            ('전라남도', '전라남도'),
            ('경상북도', '경상북도'),
            ('경상남도', '경상남도'),
            ('제주특별자치도', '제주특별자치도'),
        ],
        verbose_name="사는 지역"
    )

    class Meta:
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필들"

    def __str__(self):
        return f"{self.user.username}의 프로필"


# User 생성 시 자동으로 Profile 생성
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class RAGConfiguration(models.Model):
    """RAG 파이프라인 구성 설정"""

    name = models.CharField(max_length=200, verbose_name="구성 이름")
    description = models.TextField(blank=True, verbose_name="설명")

    # PDF 텍스트 추출 설정
    pdf_extractor = models.CharField(
        max_length=50,
        choices=[
            ('PyPDF2', 'PyPDF2'),
            ('pdfplumber', 'PDF Plumber'),
            ('PyMuPDF', 'PyMuPDF (Fitz)'),
            ('pdfminer', 'PDFMiner'),
            ('unstructured', 'Unstructured'),
        ],
        default='pdfplumber',
        verbose_name="PDF 추출기"
    )

    # HWP 텍스트 추출 설정
    hwp_extractor = models.CharField(
        max_length=50,
        choices=[
            ('olefile', 'OleFile (HWP 3.0-5.0)'),
            ('hwpx', 'HWPX (HWP 2014+)'),
            ('advanced_hwp', 'Advanced HWP (권장)'),
        ],
        default='advanced_hwp',
        verbose_name="HWP 추출기"
    )

    # OCR 사용 여부
    use_ocr = models.BooleanField(default=True, verbose_name="OCR 사용 (PDF 실패 시)")

    # 청킹 전략
    chunking_strategy = models.CharField(
        max_length=50,
        choices=[
            ('fixed_size', 'Fixed Size'),
            ('sentence', 'Sentence-based'),
            ('paragraph', 'Paragraph-based'),
            ('semantic', 'Semantic'),
            ('recursive', 'Recursive Character'),
        ],
        default='recursive',
        verbose_name="청킹 전략"
    )
    chunk_size = models.IntegerField(default=1000, verbose_name="청크 크기")
    chunk_overlap = models.IntegerField(default=200, verbose_name="청크 오버랩")

    # 임베딩 모델
    embedding_model = models.CharField(
        max_length=100,
        choices=[
            ('openai', 'OpenAI text-embedding-ada-002'),
            ('sentence-transformers/all-MiniLM-L6-v2', 'MiniLM-L6-v2 (영어)'),
            ('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'Multilingual MiniLM'),
            ('jhgan/ko-sroberta-multitask', 'KoSRoBERTa'),
            ('BM-K/KoSimCSE-roberta', 'KoSimCSE'),
        ],
        default='jhgan/ko-sroberta-multitask',
        verbose_name="임베딩 모델"
    )

    # 검색 전략
    retrieval_strategy = models.CharField(
        max_length=50,
        choices=[
            ('similarity', 'Similarity Search'),
            ('mmr', 'MMR (Maximal Marginal Relevance)'),
            ('bm25', 'BM25'),
            ('ensemble', 'Ensemble (Hybrid)'),
        ],
        default='similarity',
        verbose_name="검색 전략"
    )
    top_k = models.IntegerField(default=5, verbose_name="검색 결과 개수")

    # ChromaDB 설정
    collection_name = models.CharField(max_length=100, unique=True, verbose_name="컬렉션 이름")

    # 메타 정보
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rag_configs')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    is_active = models.BooleanField(default=True, verbose_name="활성화")
    is_validation = models.BooleanField(default=False, verbose_name="검증용 구성")

    # 통계
    document_count = models.IntegerField(default=0, verbose_name="문서 수")
    chunk_count = models.IntegerField(default=0, verbose_name="청크 수")
    build_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '대기 중'),
            ('building', '구축 중'),
            ('completed', '완료'),
            ('failed', '실패'),
        ],
        default='pending',
        verbose_name="구축 상태"
    )
    build_started_at = models.DateTimeField(null=True, blank=True, verbose_name="구축 시작 시간")
    build_completed_at = models.DateTimeField(null=True, blank=True, verbose_name="구축 완료 시간")
    error_message = models.TextField(blank=True, verbose_name="오류 메시지")

    # 통계 추가
    total_documents = models.IntegerField(default=0, verbose_name="총 문서 수")
    total_chunks = models.IntegerField(default=0, verbose_name="총 청크 수")

    class Meta:
        verbose_name = "RAG 구성"
        verbose_name_plural = "RAG 구성들"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.collection_name})"


class ChatSession(models.Model):
    """사용자 채팅 세션"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    rag_config = models.ForeignKey(RAGConfiguration, on_delete=models.SET_NULL, null=True)

    session_id = models.CharField(max_length=100, unique=True, verbose_name="세션 ID")
    title = models.CharField(max_length=200, default="새 대화", verbose_name="대화 제목")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "채팅 세션"
        verbose_name_plural = "채팅 세션들"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    """채팅 메시지"""

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')

    role = models.CharField(
        max_length=20,
        choices=[
            ('user', '사용자'),
            ('assistant', '챗봇'),
            ('system', '시스템'),
        ],
        verbose_name="역할"
    )
    content = models.TextField(verbose_name="내용")

    # 검색 결과 (assistant 메시지인 경우)
    retrieved_docs = models.JSONField(null=True, blank=True, verbose_name="검색된 문서")

    # 성능 메트릭
    response_time = models.FloatField(null=True, blank=True, verbose_name="응답 시간(초)")
    tokens_used = models.IntegerField(null=True, blank=True, verbose_name="사용된 토큰")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        verbose_name = "채팅 메시지"
        verbose_name_plural = "채팅 메시지들"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.session.session_id} - {self.role}: {self.content[:50]}"


class UserFeedback(models.Model):
    """사용자 피드백"""

    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    rating = models.IntegerField(
        choices=[(1, '매우 나쁨'), (2, '나쁨'), (3, '보통'), (4, '좋음'), (5, '매우 좋음')],
        verbose_name="평점"
    )
    comment = models.TextField(blank=True, verbose_name="코멘트")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        verbose_name = "사용자 피드백"
        verbose_name_plural = "사용자 피드백들"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.rating}점"


class ElderlyPolicy(models.Model):
    """노년 복지 정책"""

    title = models.CharField(max_length=300, verbose_name="정책명")
    provider = models.CharField(max_length=100, verbose_name="제공기관")
    region = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('전국', '전국'),
            ('서울특별시', '서울특별시'),
            ('부산광역시', '부산광역시'),
            ('대구광역시', '대구광역시'),
            ('인천광역시', '인천광역시'),
            ('광주광역시', '광주광역시'),
            ('대전광역시', '대전광역시'),
            ('울산광역시', '울산광역시'),
            ('세종특별자치시', '세종특별자치시'),
            ('경기도', '경기도'),
            ('강원특별자치도', '강원특별자치도'),
            ('충청북도', '충청북도'),
            ('충청남도', '충청남도'),
            ('전북특별자치도', '전북특별자치도'),
            ('전라남도', '전라남도'),
            ('경상북도', '경상북도'),
            ('경상남도', '경상남도'),
            ('제주특별자치도', '제주특별자치도'),
        ],
        default='전국',
        verbose_name="지역"
    )
    policy_url = models.URLField(blank=True, verbose_name="정책 링크")
    description = models.TextField(blank=True, verbose_name="정책 설명")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록일")

    class Meta:
        verbose_name = "노년 복지 정책"
        verbose_name_plural = "노년 복지 정책들"
        ordering = ['region', 'title']

    def __str__(self):
        return f"[{self.region}] {self.title}"
