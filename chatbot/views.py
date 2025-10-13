from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import sys

from .models import UserProfile, ChatHistory, Policy
from documents.vectorstore import VectorStore
from documents.embedder import DocumentEmbedder
from documents.langgraph_rag import LangGraphRAG

# LangGraph RAG 시스템 초기화 (전역)
try:
    embedder = DocumentEmbedder()
    vectorstore = VectorStore()
    rag_system = LangGraphRAG(vectorstore, embedder)
    print("✓ LangGraph RAG 시스템이 초기화되었습니다.")
except Exception as e:
    print(f"RAG 시스템 초기화 오류: {e}")
    rag_system = None


def index(request):
    """메인 페이지"""
    return render(request, 'index.html')


def register_view(request):
    """회원가입"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 사용자 프로필 자동 생성
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, '회원가입이 완료되었습니다!')
            return redirect('profile')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """로그인"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'{username}님, 환영합니다!')
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """로그아웃"""
    logout(request)
    messages.info(request, '로그아웃되었습니다.')
    return redirect('index')


@login_required
def profile_view(request):
    """사용자 프로필 페이지"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # 프로필 업데이트
        profile.age = request.POST.get('age') or None
        profile.gender = request.POST.get('gender') or None
        profile.region = request.POST.get('region') or None
        profile.disability = request.POST.get('disability') == 'on'
        profile.veteran = request.POST.get('veteran') == 'on'
        profile.low_income = request.POST.get('low_income') == 'on'
        profile.save()
        messages.success(request, '프로필이 업데이트되었습니다!')
        return redirect('profile')

    return render(request, 'profile.html', {'profile': profile})


def policies_view(request):
    """정책 목록 페이지"""
    # 카테고리별 정책 그룹화
    categories = {}

    # 실제 정책 데이터 (간단한 예시)
    sample_policies = [
        {
            'category': '건강/의료',
            'title': '기초연금',
            'description': '만 65세 이상 소득 하위 70% 노인에게 지급되는 연금',
            'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000062'
        },
        {
            'category': '건강/의료',
            'title': '노인맞춤돌봄서비스',
            'description': '일상생활 영위가 어려운 취약 노인에게 적절한 돌봄서비스 제공',
            'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00001954'
        },
        {
            'category': '일자리',
            'title': '노인일자리 및 사회활동 지원사업',
            'description': '노인에게 맞춤형 일자리·사회활동 지원하여 소득창출 및 사회참여 기회 제공',
            'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000150'
        },
        {
            'category': '주거/생활',
            'title': '에너지바우처',
            'description': '저소득층의 에너지 이용 보장을 위한 에너지 구입비용 지원',
            'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00003872'
        },
        {
            'category': '생활지원',
            'title': '국민기초생활보장',
            'description': '생활이 어려운 사람에게 필요한 급여를 실시하여 최저생활 보장',
            'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000014'
        },
        {
            'category': '건강/의료',
            'title': '의료급여',
            'description': '생활이 어려운 사람에게 의료급여를 실시하여 국민보건 향상 및 사회복지 증진',
            'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000013'
        },
    ]

    for policy in sample_policies:
        cat = policy['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(policy)

    return render(request, 'policies.html', {'categories': categories})


@login_required
def chatbot_view(request):
    """챗봇 페이지"""
    # 사용자의 최근 대화 이력 가져오기
    chat_history = ChatHistory.objects.filter(user=request.user)[:10]
    return render(request, 'chatbot.html', {'chat_history': chat_history})


@login_required
@csrf_exempt
def chatbot_api(request):
    """챗봇 API - 질문에 대한 답변 반환"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()

        if not question:
            return JsonResponse({'error': '질문을 입력해주세요.'}, status=400)

        # 사용자 프로필 가져오기
        profile = UserProfile.objects.filter(user=request.user).first()
        user_profile = None
        if profile:
            user_profile = {
                'age': profile.age,
                'gender': profile.gender,
                'region': profile.region,
                'disability': profile.disability,
                'veteran': profile.veteran,
                'low_income': profile.low_income
            }

        # LangGraph RAG 시스템으로 답변 생성
        if rag_system:
            result = rag_system.run(question, user_profile=user_profile)
            answer = result['answer']
            sources = result['sources']
            quality_score = result['quality_score']
        else:
            answer = "죄송합니다. 현재 시스템이 초기화되지 않았습니다. 관리자에게 문의해주세요."
            sources = []
            quality_score = 0

        # 대화 이력 저장 (품질 점수 포함)
        chat = ChatHistory.objects.create(
            user=request.user,
            question=question,
            answer=answer
        )

        # 자동 품질 평가 저장
        if quality_score > 0:
            chat.relevance_score = quality_score
            chat.accuracy_score = quality_score * 0.9  # 약간 낮게 설정
            chat.completeness_score = quality_score * 0.95
            chat.calculate_overall_score()
            chat.save()

        return JsonResponse({
            'answer': answer,
            'sources': sources,
            'quality_score': round(quality_score, 2)
        })

    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


# ============ 관리자 전용 기능 ============

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator


@staff_member_required
def admin_dashboard(request):
    """관리자 대시보드"""
    # 통계 데이터
    total_users = User.objects.count()
    total_chats = ChatHistory.objects.count()
    avg_score = ChatHistory.objects.filter(overall_score__isnull=False).aggregate(Avg('overall_score'))['overall_score__avg']

    # 최근 대화 (평가 필요)
    recent_chats = ChatHistory.objects.filter(overall_score__isnull=True)[:10]

    # 사용자별 활동 통계
    user_stats = User.objects.annotate(
        chat_count=Count('chat_history')
    ).order_by('-chat_count')[:10]

    context = {
        'total_users': total_users,
        'total_chats': total_chats,
        'avg_score': round(avg_score, 2) if avg_score else 0,
        'recent_chats': recent_chats,
        'user_stats': user_stats,
    }

    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def admin_user_management(request):
    """사용자 관리 페이지"""
    users = User.objects.all().select_related('profile').annotate(
        chat_count=Count('chat_history')
    )

    # 검색
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # 페이지네이션
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/user_management.html', {'page_obj': page_obj, 'search_query': search_query})


@staff_member_required
def admin_toggle_staff(request, user_id):
    """사용자 관리자 권한 토글"""
    if request.method == 'POST':
        user = User.objects.get(id=user_id)
        user.is_staff = not user.is_staff
        user.save()
        messages.success(request, f'{user.username}의 관리자 권한이 {"부여" if user.is_staff else "제거"}되었습니다.')

    return redirect('admin_user_management')


@staff_member_required
def admin_chat_logs(request):
    """사용자별 질의응답 로그"""
    user_id = request.GET.get('user_id')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    chats = ChatHistory.objects.all().select_related('user')

    # 필터링
    if user_id:
        chats = chats.filter(user_id=user_id)
    if date_from:
        chats = chats.filter(created_at__gte=date_from)
    if date_to:
        chats = chats.filter(created_at__lte=date_to)

    # 페이지네이션
    paginator = Paginator(chats, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 사용자 목록
    users = User.objects.all().order_by('username')

    context = {
        'page_obj': page_obj,
        'users': users,
        'selected_user_id': user_id,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'admin/chat_logs.html', context)


@staff_member_required
@csrf_exempt
def admin_evaluate_response(request, chat_id):
    """챗봇 응답 평가"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            chat = ChatHistory.objects.get(id=chat_id)

            chat.relevance_score = float(data.get('relevance_score', 0))
            chat.accuracy_score = float(data.get('accuracy_score', 0))
            chat.completeness_score = float(data.get('completeness_score', 0))
            chat.calculate_overall_score()
            chat.save()

            return JsonResponse({
                'success': True,
                'overall_score': chat.overall_score
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
