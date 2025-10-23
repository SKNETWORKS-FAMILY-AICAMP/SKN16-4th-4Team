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
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
import uuid
import json
import logging
import requests
from datetime import timedelta

from .models import ChatSession, ChatMessage, UserProfile, ElderlyPolicy, KakaoUser
from .rag_system.rag_service import get_rag_service

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

    # 카카오 로그인 여부 확인
    is_kakao = request.session.get('is_kakao_user', False)

    context = {
        'recent_sessions': recent_sessions,
        'is_kakao_user': is_kakao,
        'kakao_nickname': request.session.get('kakao_nickname', ''),
    }
    return render(request, 'chatbot_web/home.html', context)


# ==================== 인증 ====================
def register(request):
    """회원가입"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password1')  # 템플릿과 일치
        password_confirm = request.POST.get('password2')  # 템플릿과 일치
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


# ==================== 카카오 로그인 ====================
KAKAO_REST_API_KEY = '54d356a020d597f5e8b9540f3e82703d'
KAKAO_CLIENT_SECRET = 'nXDLTIFaISpYDmKpHmCXQzvfFE8laGPP'


def kakao_login(request):
    """카카오 로그인 시작 (인가 코드 요청)"""
    # 도메인 기반 redirect_uri 생성
    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    redirect_uri = f"{scheme}://{host}/kakao/callback/"

    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
    )

    return redirect(kakao_auth_url)


def kakao_callback(request):
    """카카오 로그인 콜백 (토큰 및 사용자 정보 받기)"""
    code = request.GET.get('code')

    if not code:
        messages.error(request, '카카오 로그인에 실패했습니다.')
        return redirect('chatbot_web:login')

    # 도메인 기반 redirect_uri 생성
    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    redirect_uri = f"{scheme}://{host}/kakao/callback/"

    # 1. 토큰 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': KAKAO_REST_API_KEY,
        'client_secret': KAKAO_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'code': code,
    }

    try:
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()

        if 'error' in token_json:
            messages.error(request, f'토큰 요청 실패: {token_json.get("error_description")}')
            return redirect('chatbot_web:login')

        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')
        expires_in = token_json.get('expires_in', 21600)  # 기본 6시간

        # 2. 사용자 정보 요청
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }

        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()

        if 'id' not in user_info:
            messages.error(request, '사용자 정보를 가져올 수 없습니다.')
            return redirect('chatbot_web:login')

        # 3. 카카오 사용자 정보 파싱
        kakao_id = user_info['id']
        kakao_account = user_info.get('kakao_account', {})
        profile = kakao_account.get('profile', {})

        nickname = profile.get('nickname')
        email = kakao_account.get('email')
        profile_image = profile.get('profile_image_url')
        thumbnail_image = profile.get('thumbnail_image_url')

        # 4. KakaoUser DB에 저장 또는 업데이트
        kakao_user, created = KakaoUser.objects.get_or_create(
            kakao_id=kakao_id,
            defaults={
                'nickname': nickname,
                'email': email,
                'profile_image': profile_image,
                'thumbnail_image': thumbnail_image,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expires_at': timezone.now() + timedelta(seconds=expires_in),
            }
        )

        if not created:
            # 기존 사용자 정보 업데이트
            kakao_user.nickname = nickname
            kakao_user.email = email
            kakao_user.profile_image = profile_image
            kakao_user.thumbnail_image = thumbnail_image
            kakao_user.access_token = access_token
            kakao_user.refresh_token = refresh_token
            kakao_user.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            kakao_user.last_login = timezone.now()
            kakao_user.save()

        # 5. Django User 자동 생성 또는 로그인 (채팅/프로필/북마크 사용 가능하도록)
        username = f'kakao_{kakao_id}'  # 카카오 ID로 고유한 username 생성

        try:
            # 기존 Django User 확인
            django_user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Django User 생성 (임의의 복잡한 비밀번호 설정 - 카카오 로그인만 사용)
            import secrets
            random_password = secrets.token_urlsafe(32)
            django_user = User.objects.create_user(
                username=username,
                email=email if email else f'kakao_{kakao_id}@kakao.user',
                password=random_password  # 임의의 비밀번호 (아무도 모름)
            )

            # UserProfile 생성 (자동으로 생성되지만 확실하게)
            UserProfile.objects.get_or_create(user=django_user)

        # Django 인증 시스템으로 로그인
        auth_login(request, django_user, backend='django.contrib.auth.backends.ModelBackend')

        # 세션에 카카오 정보 추가 저장
        request.session['kakao_user_id'] = kakao_user.id
        request.session['kakao_nickname'] = kakao_user.nickname
        request.session['is_kakao_user'] = True

        messages.success(request, f'{nickname}님, 카카오 로그인에 성공했습니다!')
        return redirect('chatbot_web:home')

    except requests.exceptions.RequestException as e:
        logger.error(f"카카오 API 요청 오류: {e}")
        messages.error(request, '카카오 로그인 중 오류가 발생했습니다.')
        return redirect('chatbot_web:login')
    except Exception as e:
        logger.error(f"카카오 로그인 오류: {e}")
        messages.error(request, f'로그인 처리 중 오류가 발생했습니다: {str(e)}')
        return redirect('chatbot_web:login')


def kakao_logout(request):
    """카카오 로그아웃"""
    from django.contrib.auth import logout as auth_logout

    kakao_user_id = request.session.get('kakao_user_id')

    if kakao_user_id:
        try:
            kakao_user = KakaoUser.objects.get(id=kakao_user_id)
            access_token = kakao_user.access_token

            # 카카오 로그아웃 API 호출
            logout_url = "https://kapi.kakao.com/v1/user/logout"
            headers = {'Authorization': f'Bearer {access_token}'}
            requests.post(logout_url, headers=headers)
        except Exception as e:
            logger.error(f"카카오 로그아웃 오류: {e}")

    # Django 로그아웃
    auth_logout(request)

    # 세션 정리
    request.session.pop('kakao_user_id', None)
    request.session.pop('kakao_nickname', None)
    request.session.pop('is_kakao_user', None)

    messages.success(request, '로그아웃되었습니다.')
    return redirect('chatbot_web:login')


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
    chat_messages = ChatMessage.objects.filter(session=session).order_by('created_at')

    context = {
        'session': session,
        'chat_messages': chat_messages,
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

        # 간소화된 RAG 서비스 사용
        from .simple_rag_service import get_rag_service
        rag_service = get_rag_service()

        try:
            # 질문 처리 (새로운 RAG 서비스)
            result = rag_service.generate_answer(user_message, user_region=user_region)

            ai_response = result.get('answer', '죄송합니다. 응답을 생성할 수 없습니다.')
            sources = result.get('sources', [])
            retrieved_count = result.get('retrieved_count', 0)

            # AI 응답 저장
            ai_message = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=ai_response,
                retrieved_docs=sources
            )

            return JsonResponse({
                'response': ai_response,
                'sources': sources,
                'retrieved_count': retrieved_count,
                'message_id': ai_message.id
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
    """검증용 채팅 - RAG 구성 선택으로 리다이렉트"""
    return redirect('chatbot_web:validation_config_select')


@login_required
@user_passes_test(is_admin)
def validation_config_select(request):
    """RAG 구성 선택 페이지"""
    if request.method == 'POST':
        # 선택된 구성 정보를 세션에 저장
        request.session['validation_config'] = {
            'embedding_model': request.POST.get('embedding_model', 'text-embedding-3-small'),
            'chunking_strategy': request.POST.get('chunking_strategy', 'recursive'),
            'chunk_size': int(request.POST.get('chunk_size', 1000)),
            'chunk_overlap': int(request.POST.get('chunk_overlap', 200)),
            'retrieval_strategy': request.POST.get('retrieval_strategy', 'similarity'),
            'hybrid_weight': float(request.POST.get('hybrid_weight', 0.7)),
            'top_k': int(request.POST.get('top_k', 5)),
        }
        messages.success(request, 'RAG 구성이 설정되었습니다. 검증용 챗봇을 시작합니다.')
        return redirect('chatbot_web:validation_chat_new_session')

    return render(request, 'chatbot_web/validation/config_select.html')


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

    chat_messages = ChatMessage.objects.filter(session=session).order_by('created_at')

    context = {
        'session': session,
        'chat_messages': chat_messages,
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

        # 검증용 RAG 처리 (동일한 RAG 서비스 사용)
        from .simple_rag_service import get_rag_service
        rag_service = get_rag_service()

        try:
            result = rag_service.generate_answer(user_message, user_region=user_region)
            ai_response = result.get('answer', '죄송합니다. 응답을 생성할 수 없습니다.')
            sources = result.get('sources', [])
            retrieved_count = result.get('retrieved_count', 0)

            # 로그 추가
            logger.info(f"[검증용] 질문: {user_message[:50]}... | 응답 길이: {len(ai_response)}자 | 소스 수: {len(sources)}개 | GPT 사용: {result.get('used_gpt', False)}")

            ai_message = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=ai_response,
                retrieved_docs=sources
            )

            return JsonResponse({
                'response': ai_response,
                'sources': sources,
                'retrieved_count': retrieved_count,
                'used_gpt': result.get('used_gpt', False),
                'message_id': ai_message.id
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

    # 카카오 사용자 체크
    is_kakao_user = request.session.get('is_kakao_user', False) or request.user.username.startswith('kakao_')

    context = {
        'region_choices': UserProfile._meta.get_field('region').choices,
        'is_kakao_user': is_kakao_user,
    }
    return render(request, 'chatbot_web/profile.html', context)


@login_required
def profile_edit(request):
    """프로필 수정 (비밀번호 변경 제외)"""
    if request.method == 'POST':
        age = request.POST.get('age')
        region = request.POST.get('region')
        gender = request.POST.get('gender')

        # 프로필 정보 업데이트
        from .models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        if age:
            try:
                profile.age = int(age)
            except ValueError:
                messages.error(request, '나이는 숫자로 입력해주세요.')
                return redirect('chatbot_web:profile')
        else:
            profile.age = None

        profile.region = region if region else ''
        profile.gender = gender if gender else ''
        profile.save()

        messages.success(request, '프로필이 업데이트되었습니다.')
        return redirect('chatbot_web:profile')

    return redirect('chatbot_web:profile')


@login_required
def password_change(request):
    """비밀번호 변경 (일반 로그인 사용자만)"""
    # 카카오 사용자는 비밀번호 변경 불가
    is_kakao_user = request.session.get('is_kakao_user', False) or request.user.username.startswith('kakao_')

    if is_kakao_user:
        messages.warning(request, '카카오 로그인 사용자는 비밀번호를 변경할 수 없습니다.')
        return redirect('chatbot_web:profile')

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')

        if not old_password or not new_password or not new_password_confirm:
            messages.error(request, '모든 필드를 입력해주세요.')
            return render(request, 'chatbot_web/password_change.html')

        # 현재 비밀번호 확인
        if not request.user.check_password(old_password):
            messages.error(request, '현재 비밀번호가 일치하지 않습니다.')
            return render(request, 'chatbot_web/password_change.html')

        # 새 비밀번호 확인
        if new_password != new_password_confirm:
            messages.error(request, '새 비밀번호가 일치하지 않습니다.')
            return render(request, 'chatbot_web/password_change.html')

        # 비밀번호 길이 확인
        if len(new_password) < 8:
            messages.error(request, '비밀번호는 최소 8자 이상이어야 합니다.')
            return render(request, 'chatbot_web/password_change.html')

        # 비밀번호 변경
        request.user.set_password(new_password)
        request.user.save()

        messages.success(request, '비밀번호가 변경되었습니다. 다시 로그인해주세요.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('chatbot_web:login')

    return render(request, 'chatbot_web/password_change.html')


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


@login_required
@user_passes_test(is_admin)
def monitoring_view(request):
    """시스템 모니터링 (PostgreSQL 데이터 확인)"""
    from .models import UserFeedback
    from django.db.models import Avg

    # 통계 수집
    stats = {
        'total_feedbacks': UserFeedback.objects.count(),
        'avg_rating': UserFeedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0,
        'validation_sessions': ChatSession.objects.filter(title__startswith='[검증]').count(),
        'regular_sessions': ChatSession.objects.exclude(title__startswith='[검증]').count(),
    }

    # 최근 피드백 (최근 50개)
    feedbacks = UserFeedback.objects.select_related('user', 'message').order_by('-created_at')[:50]

    # 검증용 세션 (최근 20개)
    validation_sessions = ChatSession.objects.filter(
        title__startswith='[검증]'
    ).prefetch_related('messages').order_by('-created_at')[:20]

    # 성능 데이터 (응답 시간 및 토큰 사용량 있는 메시지, 최근 50개)
    performance_data = ChatMessage.objects.filter(
        role='assistant'
    ).select_related('session').order_by('-created_at')[:50]

    context = {
        'stats': stats,
        'feedbacks': feedbacks,
        'validation_sessions': validation_sessions,
        'performance_data': performance_data,
    }
    return render(request, 'chatbot_web/monitoring.html', context)


# ============ 새로운 페이지 뷰들 ============

@login_required
def quick_start(request):
    """맞춤형 복지 정책 추천 페이지 (회원 전용)"""
    # 프로필 정보 확인
    try:
        profile = UserProfile.objects.get(user=request.user)
        has_profile = bool(profile.age and profile.region)
    except UserProfile.DoesNotExist:
        has_profile = False
        profile = None

    # 프로필이 있으면 간소화된 페이지로
    if has_profile:
        context = {
            'profile': profile,
            'has_profile': True
        }
        return render(request, 'chatbot_web/quick_start_simple.html', context)

    return render(request, 'chatbot_web/quick_start.html')


@login_required
@require_http_methods(["POST"])
def quick_start_recommend(request):
    """맞춤형 정책 추천 API"""
    try:
        data = json.loads(request.body)
        age = data.get('age')
        region = data.get('region')
        interests = data.get('interests', [])
        disability = data.get('disability', False)
        low_income = data.get('low_income', False)

        # RAG 서비스로 맞춤형 추천 쿼리 생성
        query_parts = []

        if age:
            query_parts.append(f"{age}세")

        if region:
            query_parts.append(f"{region} 지역")

        if interests:
            query_parts.append(f"{', '.join(interests)} 관련")

        if disability:
            query_parts.append("장애인 대상")

        if low_income:
            query_parts.append("저소득층 대상")

        query_parts.append("복지 정책 및 지원 프로그램")

        query = " ".join(query_parts)

        # RAG 서비스로 검색
        from .simple_rag_service import get_rag_service
        rag_service = get_rag_service()

        result = rag_service.generate_answer(query, user_region=region)

        if result.get('is_off_topic') or result.get('no_documents'):
            return JsonResponse({
                'error': '조건에 맞는 정책을 찾을 수 없습니다. 조건을 변경해 보세요.'
            }, status=404)

        # GPT로 추가 분석 (추천 포맷으로 변환)
        recommendations = []

        def clean_title(source_str):
            """파일 경로와 확장자를 제거하고 깔끔한 제목만 반환"""
            import os
            # 파일명만 추출
            filename = os.path.basename(source_str)
            # .pdf, .hwp 등 확장자 제거
            title = os.path.splitext(filename)[0]
            # 지역명 제거 (전국 - 전국\pdf\ 같은 패턴)
            for region in ['전국', '경남', '경북', '대구', '부산', '서울', '인천', '경기', '강원', '충북', '충남', '세종', '전남', '전북', '광주', '제주']:
                if title.startswith(region):
                    title = title.replace(region, '').strip()
                    break
            return title.strip()

        # 검색된 문서에서 정책 정보 추출
        for source in result.get('sources', [])[:5]:
            clean_source_title = clean_title(source.get('source', '복지 정책'))
            recommendations.append({
                'title': clean_source_title,
                'region': source.get('region', '전국'),
                'description': source.get('content', ''),
                'how_to_apply': '',
                'required_docs': ''
            })

        summary = f"{region} 지역 {age}세 분께 추천하는 복지 정책입니다."
        if interests:
            summary += f" ({', '.join(interests)} 관련)"

        return JsonResponse({
            'summary': summary,
            'recommendations': recommendations,
            'answer': result.get('answer', '')
        })

    except Exception as e:
        logger.error(f"Quick start recommendation error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def faq(request):
    """자주 묻는 질문 페이지"""
    return render(request, 'chatbot_web/faq.html')


@login_required
def bookmark_list(request):
    """북마크 목록"""
    from .models import Bookmark
    bookmarks = Bookmark.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'bookmarks': bookmarks,
    }
    return render(request, 'chatbot_web/bookmarks.html', context)


@login_required
def bookmark_save(request):
    """북마크 저장 (AJAX)"""
    from .models import Bookmark
    import json

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            answer = data.get('answer', '')
            chatbot_type = data.get('chatbot_type', 'regular')

            if not question or not answer:
                return JsonResponse({'success': False, 'error': '질문과 답변이 필요합니다.'}, status=400)

            # 북마크 생성
            bookmark = Bookmark.objects.create(
                user=request.user,
                question=question,
                answer=answer,
                chatbot_type=chatbot_type
            )

            return JsonResponse({
                'success': True,
                'bookmark_id': bookmark.id,
                'message': '북마크가 저장되었습니다.'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)


@login_required
def bookmark_delete(request, bookmark_id):
    """북마크 삭제"""
    from .models import Bookmark

    if request.method == 'POST':
        try:
            bookmark = Bookmark.objects.get(id=bookmark_id, user=request.user)
            bookmark.delete()
            messages.success(request, '북마크가 삭제되었습니다.')
        except Bookmark.DoesNotExist:
            messages.error(request, '북마크를 찾을 수 없습니다.')
        except Exception as e:
            messages.error(request, f'삭제 중 오류가 발생했습니다: {str(e)}')

    return redirect('chatbot_web:bookmark_list')


# ==================== 챗봇 최적화 (AutoRAG) ====================
@login_required
@user_passes_test(is_admin)
def chatbot_optimization(request):
    """챗봇 최적화 메인 대시보드"""
    context = {}
    return render(request, 'chatbot_web/optimization/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def optimization_text_extraction(request):
    """텍스트 추출 최적화"""
    context = {}
    return render(request, 'chatbot_web/optimization/text_extraction.html', context)


@login_required
@user_passes_test(is_admin)
def optimization_chunking(request):
    """청킹 전략 최적화"""
    context = {}
    return render(request, 'chatbot_web/optimization/chunking.html', context)


@login_required
@user_passes_test(is_admin)
def optimization_embedding(request):
    """임베딩 모델 최적화"""
    context = {}
    return render(request, 'chatbot_web/optimization/embedding.html', context)


@login_required
@user_passes_test(is_admin)
def optimization_retriever(request):
    """검색기 최적화"""
    context = {}
    return render(request, 'chatbot_web/optimization/retriever.html', context)


@login_required
@user_passes_test(is_admin)
def optimization_rag_system(request):
    """RAG 시스템 최적화"""
    context = {}
    return render(request, 'chatbot_web/optimization/rag_system.html', context)


@login_required
@user_passes_test(is_admin)
def optimization_full_pipeline(request):
    """전체 파이프라인 최적화"""
    context = {}
    return render(request, 'chatbot_web/optimization/full_pipeline.html', context)


# ==================== AutoRAG API 엔드포인트 ====================
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def api_run_text_extraction(request):
    """텍스트 추출 최적화 실행 API"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        from src.autorag_optimizer import AutoRAGOptimizer, AutoRAGConfig
        from django.conf import settings

        # 데이터 디렉토리 설정
        data_directory = getattr(settings, 'DATA_DIRECTORY', os.path.join(settings.BASE_DIR, 'data'))

        # 설정 생성
        config = AutoRAGConfig(
            evaluation_queries=["기초연금이란 무엇인가요?", "노인장기요양보험 신청 방법은?"],
            evaluation_documents=[],
            optimization_target="balanced",
            automation_level="full",
            results_directory=os.path.join(settings.BASE_DIR, 'autorag_results')
        )

        optimizer = AutoRAGOptimizer(config, data_directory=data_directory)

        # 텍스트 추출 최적화 실행
        import asyncio
        result = asyncio.run(optimizer._optimize_text_extraction())

        return JsonResponse({
            'success': True,
            'result': {
                'component_name': result.component_name,
                'selected_option': result.selected_option,
                'score': result.score,
                'reason': result.reason,
                'metrics': result.metrics
            }
        })

    except Exception as e:
        logger.error(f"Text extraction optimization error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def api_run_chunking(request):
    """청킹 전략 최적화 실행 API"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        from src.autorag_optimizer import AutoRAGOptimizer, AutoRAGConfig, ComponentSelection
        from django.conf import settings

        # 데이터 디렉토리 설정
        data_directory = getattr(settings, 'DATA_DIRECTORY', os.path.join(settings.BASE_DIR, 'data'))

        config = AutoRAGConfig(
            evaluation_queries=["기초연금이란 무엇인가요?", "노인장기요양보험 신청 방법은?"],
            evaluation_documents=[],
            optimization_target="balanced",
            automation_level="full",
            results_directory=os.path.join(settings.BASE_DIR, 'autorag_results')
        )

        optimizer = AutoRAGOptimizer(config, data_directory=data_directory)

        # 더미 추출 결과
        extraction_result = ComponentSelection(
            component_name="text_extraction",
            selected_option="pdfplumber",
            score=0.8,
            reason="PDF 추출 성능 우수",
            metrics={}
        )

        import asyncio
        result = asyncio.run(optimizer._optimize_chunking_strategy(extraction_result))

        return JsonResponse({
            'success': True,
            'result': {
                'component_name': result.component_name,
                'selected_option': result.selected_option,
                'score': result.score,
                'reason': result.reason,
                'metrics': result.metrics
            }
        })

    except Exception as e:
        logger.error(f"Chunking optimization error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def api_run_embedding(request):
    """임베딩 모델 최적화 실행 API"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        from src.autorag_optimizer import AutoRAGOptimizer, AutoRAGConfig, ComponentSelection
        from django.conf import settings

        # 데이터 디렉토리 설정
        data_directory = getattr(settings, 'DATA_DIRECTORY', os.path.join(settings.BASE_DIR, 'data'))

        config = AutoRAGConfig(
            evaluation_queries=["기초연금이란 무엇인가요?", "노인장기요양보험 신청 방법은?"],
            evaluation_documents=[],
            optimization_target="balanced",
            automation_level="full",
            results_directory=os.path.join(settings.BASE_DIR, 'autorag_results')
        )

        optimizer = AutoRAGOptimizer(config, data_directory=data_directory)

        # 더미 청킹 결과
        chunking_result = ComponentSelection(
            component_name="chunking_strategy",
            selected_option="recursive",
            score=0.8,
            reason="재귀적 분할 전략",
            metrics={}
        )

        import asyncio
        result = asyncio.run(optimizer._optimize_embedding_model(chunking_result))

        return JsonResponse({
            'success': True,
            'result': {
                'component_name': result.component_name,
                'selected_option': result.selected_option,
                'score': result.score,
                'reason': result.reason,
                'metrics': result.metrics
            }
        })

    except Exception as e:
        logger.error(f"Embedding optimization error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def api_run_full_optimization(request):
    """전체 파이프라인 최적화 실행 API"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        from src.autorag_optimizer import AutoRAGOptimizer, AutoRAGConfig

        data = json.loads(request.body)

        # 평가 쿼리 가져오기
        evaluation_queries = data.get('evaluation_queries', [
            "기초연금이란 무엇인가요?",
            "노인장기요양보험 신청 방법은?",
            "65세 이상 의료비 지원 제도는?"
        ])

        optimization_target = data.get('optimization_target', 'balanced')

        # 데이터 디렉토리 설정
        from django.conf import settings
        data_directory = getattr(settings, 'DATA_DIRECTORY', os.path.join(settings.BASE_DIR, 'data'))

        config = AutoRAGConfig(
            evaluation_queries=evaluation_queries,
            evaluation_documents=[],
            optimization_target=optimization_target,
            automation_level="full",
            results_directory=os.path.join(settings.BASE_DIR, 'autorag_results')
        )

        optimizer = AutoRAGOptimizer(config, data_directory=data_directory)

        import asyncio
        result = asyncio.run(optimizer.optimize_pipeline())

        # 결과를 JSON 직렬화 가능한 형태로 변환
        serializable_result = {
            'optimization_complete': result['optimization_complete'],
            'overall_score': result['overall_score'],
            'pipeline_components': result['pipeline_components'],
            'final_evaluation': result['final_evaluation'],
            'recommended_config': result['recommended_config'],
            'optimization_summary': result['optimization_summary']
        }

        return JsonResponse({
            'success': True,
            'result': serializable_result
        })

    except Exception as e:
        logger.error(f"Full optimization error: {e}")
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
