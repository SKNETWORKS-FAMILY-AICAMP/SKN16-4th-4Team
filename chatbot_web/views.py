"""
새로운 간소화된 Views
elderly_welfare_rag 통합 버전
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import uuid
import json
import logging

from .models import ChatSession, ChatMessage, UserProfile, ElderlyPolicy
from .rag_system.rag_service import get_main_rag_service, get_validation_rag_service

logger = logging.getLogger(__name__)


def is_admin(user):
    """관리자 권한 확인"""
    return user.is_staff


# ==================== 홈 ====================
@login_required
def home(request):
    """홈 화면"""
    # 최근 세션 5개
    recent_sessions = ChatSession.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    context = {
        'recent_sessions': recent_sessions,
    }
    return render(request, 'chatbot_web/home.html', context)


# ==================== 인증 ====================
def register(request):
    """회원가입"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        email = request.POST.get('email', '')

        # 유효성 검사
        if not username or not password:
            messages.error(request, '아이디와 비밀번호를 입력해주세요.')
            return render(request, 'chatbot_web/register.html')

        if password != password_confirm:
            messages.error(request, '비밀번호가 일치하지 않습니다.')
            return render(request, 'chatbot_web/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, '이미 존재하는 아이디입니다.')
            return render(request, 'chatbot_web/register.html')

        if email and User.objects.filter(email=email).exists():
            messages.error(request, '이미 등록된 이메일입니다.')
            return render(request, 'chatbot_web/register.html')

        # 사용자 생성
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        messages.success(request, '회원가입이 완료되었습니다. 로그인해주세요.')
        return redirect('chatbot_web:login')

    return render(request, 'chatbot_web/register.html')


# ==================== 채팅 ====================
@login_required
def chat_view(request):
    """채팅 메인"""
    return redirect('chatbot_web:chat_new_session')


@login_required
def chat_new_session(request):
    """새 채팅 세션 생성"""
    # 새 세션 생성
    session_id = str(uuid.uuid4())
    session = ChatSession.objects.create(
        user=request.user,
        session_id=session_id,
        title="새로운 대화"
    )

    return redirect('chatbot_web:chat_session', session_id=session_id)


@login_required
def chat_session(request, session_id):
    """채팅 세션"""
    session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)

    # 메시지 로드
    messages_list = ChatMessage.objects.filter(session=session).order_by('created_at')

    context = {
        'session': session,
        'messages': messages_list,
    }
    return render(request, 'chatbot_web/chat.html', context)


@login_required
@require_http_methods(["POST"])
def chat_api_message(request):
    """채팅 메시지 API"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()

        if not session_id or not user_message:
            return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)

        # 세션 확인
        session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)

        # 사용자 메시지 저장
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=user_message
        )

        # 세션 제목 업데이트 (첫 메시지인 경우)
        if session.title == "새로운 대화":
            session.title = user_message[:50]
            session.save()

        # 사용자 지역 정보 가져오기
        user_region = None
        try:
            profile = UserProfile.objects.get(user=request.user)
            user_region = profile.region
        except UserProfile.DoesNotExist:
            pass

        # RAG 처리
        rag_service = get_main_rag_service()

        try:
            # 대화 기록 가져오기
            history = []
            prev_messages = ChatMessage.objects.filter(session=session).order_by('created_at')
            for msg in prev_messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # 질문 처리
            result = rag_service.process_question(user_message, history, user_region=user_region)

            ai_response = result.get('answer', '죄송합니다. 응답을 생성할 수 없습니다.')
            sources = result.get('sources', [])

            # AI 응답 저장
            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=ai_response,
                retrieved_docs=sources
            )

            return JsonResponse({
                'response': ai_response,
                'sources': sources
            })

        except Exception as e:
            logger.error(f"RAG processing error: {e}")
            error_message = "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=error_message
            )

            return JsonResponse({
                'response': error_message,
                'sources': []
            })

    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return JsonResponse({'error': '서버 오류가 발생했습니다.'}, status=500)


@login_required
@require_http_methods(["POST"])
def chat_session_delete(request, session_id):
    """채팅 세션 삭제"""
    session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)
    session.delete()
    messages.success(request, '대화 기록이 삭제되었습니다.')
    return redirect('chatbot_web:home')


# ==================== 검증용 채팅 (관리자 전용) ====================
@login_required
@user_passes_test(is_admin)
def validation_chat_view(request):
    """검증용 채팅"""
    return redirect('chatbot_web:validation_chat_new_session')


@login_required
@user_passes_test(is_admin)
def validation_chat_new_session(request):
    """검증용 새 세션"""
    session_id = str(uuid.uuid4())
    session = ChatSession.objects.create(
        user=request.user,
        session_id=session_id,
        title="[검증] 새로운 대화"
    )

    return redirect('chatbot_web:validation_chat_session', session_id=session_id)


@login_required
@user_passes_test(is_admin)
def validation_chat_session(request, session_id):
    """검증용 채팅 세션"""
    session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)

    messages_list = ChatMessage.objects.filter(session=session).order_by('created_at')

    context = {
        'session': session,
        'messages': messages_list,
        'is_validation': True,
    }
    return render(request, 'chatbot_web/validation/chat.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def validation_chat_api_message(request):
    """검증용 채팅 메시지 API"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()

        if not session_id or not user_message:
            return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)

        session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)

        # 사용자 메시지 저장
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=user_message
        )

        if session.title == "[검증] 새로운 대화":
            session.title = f"[검증] {user_message[:50]}"
            session.save()

        # 사용자 지역 정보 가져오기
        user_region = None
        try:
            profile = UserProfile.objects.get(user=request.user)
            user_region = profile.region
        except UserProfile.DoesNotExist:
            pass

        # 검증용 RAG 처리
        rag_service = get_validation_rag_service()

        try:
            result = rag_service.process_question(user_message, user_region=user_region)
            ai_response = result.get('answer', '죄송합니다. 응답을 생성할 수 없습니다.')
            sources = result.get('sources', [])

            # 로그 추가
            logger.info(f"[검증용] 질문: {user_message[:50]}... | 응답 길이: {len(ai_response)}자 | 소스 수: {len(sources)}개")

            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=ai_response,
                retrieved_docs=sources
            )

            return JsonResponse({
                'response': ai_response,
                'sources': sources
            })

        except Exception as e:
            logger.error(f"[검증용] RAG 처리 오류: {e}", exc_info=True)
            error_message = f"죄송합니다. 오류가 발생했습니다.\n\n상세 오류: {str(e)}"

            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=error_message
            )

            return JsonResponse({
                'response': error_message,
                'sources': []
            })

    except Exception as e:
        logger.error(f"Validation chat API error: {e}")
        return JsonResponse({'error': '서버 오류가 발생했습니다.'}, status=500)


# ==================== 프로필 ====================
@login_required
def profile_view(request):
    """프로필 조회"""
    from .models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'region_choices': UserProfile._meta.get_field('region').choices,
    }
    return render(request, 'chatbot_web/profile.html', context)


@login_required
def profile_edit(request):
    """프로필 수정"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        age = request.POST.get('age')
        region = request.POST.get('region')

        if not old_password:
            messages.error(request, '현재 비밀번호를 입력해주세요.')
            return redirect('chatbot_web:profile')

        if not request.user.check_password(old_password):
            messages.error(request, '현재 비밀번호가 일치하지 않습니다.')
            return redirect('chatbot_web:profile')

        if new_password:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, '비밀번호가 변경되었습니다. 다시 로그인해주세요.')
            return redirect('chatbot_web:login')

        from .models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        if age:
            try:
                profile.age = int(age)
            except ValueError:
                messages.error(request, '나이는 숫자로 입력해주세요.')
                return redirect('chatbot_web:profile')
        else:
            profile.age = None

        profile.region = region if region else ''
        profile.save()

        messages.success(request, '프로필이 업데이트되었습니다.')
        return redirect('chatbot_web:profile')

    return redirect('chatbot_web:profile')


# ==================== 정책 목록 ====================
@login_required
def policy_list(request):
    """노년 복지 정책 목록 - PDF 파일 기반 (시도별-주제별 정리)"""
    from .rag_system.policy_metadata import scan_policy_pdfs

    # PDF 파일들을 스캔하여 시도별-카테고리별로 정리
    policies_by_region = scan_policy_pdfs()

    # 총 정책 개수 계산
    total_count = 0
    for region_data in policies_by_region.values():
        for category_policies in region_data.values():
            total_count += len(category_policies)

    # 템플릿에서 사용하기 쉽게 리스트로 변환
    regions_data = []
    for region in sorted(policies_by_region.keys()):
        categories_list = []
        for category in sorted(policies_by_region[region].keys()):
            categories_list.append({
                'name': category,
                'policies': policies_by_region[region][category]
            })
        regions_data.append({
            'name': region,
            'categories': categories_list
        })

    context = {
        'regions_data': regions_data,
        'total_count': total_count,
    }
    return render(request, 'chatbot_web/policy_list.html', context)


# ==================== 관리자 대시보드 ====================
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """관리자 대시보드"""
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta

    # 통계
    total_users = User.objects.count()
    total_sessions = ChatSession.objects.count()
    total_messages = ChatMessage.objects.count()

    # 최근 7일 활동
    week_ago = timezone.now() - timedelta(days=7)
    recent_sessions = ChatSession.objects.filter(created_at__gte=week_ago).count()

    context = {
        'total_users': total_users,
        'total_sessions': total_sessions,
        'total_messages': total_messages,
        'recent_sessions': recent_sessions,
    }
    return render(request, 'chatbot_web/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def chat_logs(request):
    """채팅 로그"""
    sessions = ChatSession.objects.all().order_by('-created_at')[:50]

    context = {
        'sessions': sessions,
    }
    return render(request, 'chatbot_web/chat_logs.html', context)


@login_required
@user_passes_test(is_admin)
def user_management(request):
    """사용자 관리"""
    users = User.objects.all().order_by('-date_joined')

    context = {
        'users': users,
    }
    return render(request, 'chatbot_web/user_management.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def user_toggle_admin(request, user_id):
    """사용자 관리자 권한 토글"""
    user = get_object_or_404(User, pk=user_id)

    if user == request.user:
        messages.error(request, '자기 자신의 권한은 변경할 수 없습니다.')
        return redirect('chatbot_web:user_management')

    user.is_staff = not user.is_staff
    user.save()

    status = "관리자" if user.is_staff else "일반 사용자"
    messages.success(request, f'{user.username}님의 권한이 {status}로 변경되었습니다.')
    return redirect('chatbot_web:user_management')


@login_required
@user_passes_test(is_admin)
def validation_chat_logs(request):
    """검증용 채팅 로그"""
    sessions = ChatSession.objects.filter(
        title__startswith='[검증]'
    ).order_by('-created_at')[:50]

    context = {
        'sessions': sessions,
        'is_validation': True,
    }
    return render(request, 'chatbot_web/validation/chat_logs.html', context)
