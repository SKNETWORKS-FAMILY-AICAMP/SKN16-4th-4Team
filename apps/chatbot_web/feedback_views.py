"""
피드백 시스템 Views
사용자 피드백 수집 및 분석
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count
from datetime import timedelta
from django.utils import timezone
import json
import logging

from .models import ChatMessage, UserFeedback, SessionRating, ChatSession

logger = logging.getLogger(__name__)


def is_admin(user):
    """관리자 권한 확인"""
    return user.is_staff


def analyze_feedback_with_ai(comment, rating, message=None):
    """
    OpenAI API를 사용하여 피드백 분석
    Returns: (category, sentiment)

    Args:
        comment: 사용자가 작성한 피드백 텍스트
        rating: 평점 (1-5)
        message: ChatMessage 객체 (옵션, 컨텍스트 분석용)
    """
    # 분석할 텍스트 준비
    feedback_text = comment if comment and comment.strip() else ''

    # 코멘트가 없고 메시지 컨텍스트도 없으면 평점으로만 분류
    if not feedback_text and not message:
        if rating >= 4:
            return 'praise', 'positive'
        elif rating == 3:
            return 'other', 'neutral'
        else:
            return 'usability', 'negative'

    try:
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # 프롬프트 구성
        if feedback_text:
            # 명시적인 피드백 텍스트가 있는 경우
            context_info = f"""피드백 내용: {feedback_text}
평점: {rating}/5"""
        elif message:
            # 피드백 텍스트가 없지만 메시지 컨텍스트가 있는 경우
            # 사용자 질문과 챗봇 답변을 컨텍스트로 활용
            try:
                # 메시지의 세션에서 가장 최근 사용자 질문 찾기
                user_question = message.session.messages.filter(
                    role='user',
                    created_at__lte=message.created_at
                ).order_by('-created_at').first()

                question_text = user_question.content if user_question else "질문 없음"
                answer_text = message.content[:200] + "..." if len(message.content) > 200 else message.content

                context_info = f"""사용자 질문: {question_text}
챗봇 답변: {answer_text}
평점: {rating}/5
(사용자가 별도 피드백 텍스트 없이 평점만 제공)"""
            except Exception as e:
                logger.warning(f"메시지 컨텍스트 추출 실패: {e}")
                context_info = f"평점: {rating}/5"
        else:
            context_info = f"평점: {rating}/5"

        prompt = f"""다음 사용자 피드백을 분석하세요.

{context_info}

1. 카테고리를 다음 중 하나로 분류하세요:
- feature_request: 새로운 기능 요청
- bug: 버그나 오류 보고
- usability: 사용성 문제
- praise: 칭찬이나 긍정적 피드백
- other: 기타

2. 감정을 다음 중 하나로 분류하세요:
- positive: 긍정적
- neutral: 중립적
- negative: 부정적

다음 JSON 형식으로만 답변하세요:
{{"category": "카테고리", "sentiment": "감정"}}
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes user feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        category = result.get('category', 'other')
        sentiment = result.get('sentiment', 'neutral')

        # 검증
        valid_categories = ['feature_request', 'bug', 'usability', 'praise', 'other']
        valid_sentiments = ['positive', 'neutral', 'negative']

        if category not in valid_categories:
            category = 'other'
        if sentiment not in valid_sentiments:
            sentiment = 'neutral'

        return category, sentiment

    except Exception as e:
        logger.warning(f"AI 피드백 분석 실패: {e}, 기본 분류 사용")
        # AI 분석 실패 시 평점 기반으로 기본 분류 (개선된 버전)
        if rating >= 4:
            return 'praise', 'positive'
        elif rating == 3:
            return 'other', 'neutral'
        else:
            return 'usability', 'negative'


@login_required
@require_http_methods(["POST"])
def feedback_submit(request):
    """피드백 제출 API"""
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        rating = data.get('rating')
        comment = data.get('comment', '')

        if not message_id or not rating:
            return JsonResponse({'success': False, 'error': '메시지 ID와 평점이 필요합니다.'}, status=400)

        # 메시지 확인
        try:
            message = ChatMessage.objects.get(id=message_id, session__user=request.user)
        except ChatMessage.DoesNotExist:
            return JsonResponse({'success': False, 'error': '메시지를 찾을 수 없습니다.'}, status=404)

        # AI를 사용한 피드백 자동 분석 (메시지 컨텍스트 포함)
        category, sentiment = analyze_feedback_with_ai(comment, rating, message)

        # 피드백 저장 (기존 피드백 업데이트 또는 새로 생성)
        feedback, created = UserFeedback.objects.update_or_create(
            message=message,
            user=request.user,
            defaults={
                'rating': rating,
                'comment': comment,
                'category': category,
                'sentiment': sentiment
            }
        )

        logger.info(f"피드백 {'생성' if created else '업데이트'}: 사용자={request.user.username}, 메시지ID={message_id}, 평점={rating}, 카테고리={category}, 감정={sentiment}")

        return JsonResponse({
            'success': True,
            'feedback_id': feedback.id,
            'message': '피드백이 저장되었습니다.'
        })

    except Exception as e:
        logger.error(f"피드백 제출 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
def feedback_analytics(request):
    """피드백 분석 페이지 (관리자 전용)"""
    # 전체 피드백 통계
    total_feedbacks = UserFeedback.objects.count()
    avg_rating = UserFeedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0

    # 평점별 분포
    rating_distribution = UserFeedback.objects.values('rating').annotate(count=Count('rating')).order_by('rating')

    # 카테고리별 분포
    category_distribution = UserFeedback.objects.exclude(
        category__isnull=True
    ).values('category').annotate(count=Count('category')).order_by('-count')

    # 감정별 분포
    sentiment_distribution = UserFeedback.objects.exclude(
        sentiment__isnull=True
    ).values('sentiment').annotate(count=Count('sentiment')).order_by('-count')

    # 최근 7일 피드백
    week_ago = timezone.now() - timedelta(days=7)
    recent_feedbacks = UserFeedback.objects.filter(created_at__gte=week_ago).order_by('-created_at')[:50]

    # 낮은 평점 피드백 (개선 필요)
    low_rating_feedbacks = UserFeedback.objects.filter(rating__lte=2).order_by('-created_at')[:20]

    # 카테고리별 평균 평점
    category_avg_rating = UserFeedback.objects.exclude(
        category__isnull=True
    ).values('category').annotate(avg_rating=Avg('rating')).order_by('-avg_rating')

    # 세션 평가 통계 추가
    total_session_ratings = SessionRating.objects.count()
    avg_session_rating = SessionRating.objects.aggregate(Avg('rating'))['rating__avg'] or 0

    # 카테고리/감정 레이블 매핑
    category_labels = dict(UserFeedback.CATEGORY_CHOICES)
    sentiment_labels = dict(UserFeedback.SENTIMENT_CHOICES)

    # 템플릿에서 사용하기 쉽도록 레이블 추가
    category_dist_with_labels = []
    for item in category_distribution:
        category_dist_with_labels.append({
            'category': item['category'],
            'label': category_labels.get(item['category'], item['category']),
            'count': item['count']
        })

    sentiment_dist_with_labels = []
    for item in sentiment_distribution:
        sentiment_dist_with_labels.append({
            'sentiment': item['sentiment'],
            'label': sentiment_labels.get(item['sentiment'], item['sentiment']),
            'count': item['count']
        })

    category_rating_with_labels = []
    for item in category_avg_rating:
        category_rating_with_labels.append({
            'category': item['category'],
            'label': category_labels.get(item['category'], item['category']),
            'avg_rating': round(item['avg_rating'], 2)
        })

    context = {
        'total_feedbacks': total_feedbacks,
        'avg_rating': round(avg_rating, 2),
        'rating_distribution': list(rating_distribution),
        'category_distribution': category_dist_with_labels,
        'sentiment_distribution': sentiment_dist_with_labels,
        'category_avg_rating': category_rating_with_labels,
        'recent_feedbacks': recent_feedbacks,
        'low_rating_feedbacks': low_rating_feedbacks,
        'total_session_ratings': total_session_ratings,
        'avg_session_rating': round(avg_session_rating, 2),
    }
    return render(request, 'chatbot_web/feedback_analytics.html', context)


@login_required
@require_http_methods(["POST"])
def session_rating_submit(request):
    """세션 평가 제출 API"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        rating = float(data.get('rating'))
        comment = data.get('comment', '')

        if not session_id or rating is None:
            return JsonResponse({'success': False, 'error': '세션 ID와 평점이 필요합니다.'}, status=400)

        # 평점 범위 검증 (0.5 ~ 5.0)
        if rating < 0.5 or rating > 5.0 or (rating * 2) % 1 != 0:
            return JsonResponse({'success': False, 'error': '평점은 0.5 ~ 5.0 사이의 0.5 단위여야 합니다.'}, status=400)

        # 세션 확인
        try:
            session = ChatSession.objects.get(session_id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': '세션을 찾을 수 없습니다.'}, status=404)

        # 세션 평가 저장 (기존 평가 업데이트 또는 새로 생성)
        session_rating, created = SessionRating.objects.update_or_create(
            session=session,
            user=request.user,
            defaults={
                'rating': rating,
                'comment': comment
            }
        )

        logger.info(f"세션 평가 {'생성' if created else '업데이트'}: 사용자={request.user.username}, 세션ID={session_id}, 평점={rating}")

        return JsonResponse({
            'success': True,
            'rating_id': session_rating.id,
            'message': '세션 평가가 저장되었습니다.'
        })

    except Exception as e:
        logger.error(f"세션 평가 제출 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
