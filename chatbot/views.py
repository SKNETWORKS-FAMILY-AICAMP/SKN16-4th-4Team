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
from documents.vectorstore import VectorStore, RAGSystem
from documents.embedder import DocumentEmbedder

# RAG 시스템 초기화 (전역)
try:
    embedder = DocumentEmbedder()
    vectorstore = VectorStore()
    rag_system = RAGSystem(vectorstore, embedder)
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

        # RAG 시스템으로 관련 문서 검색
        if rag_system:
            relevant_docs = rag_system.retrieve_relevant_docs(question, n_results=3, user_profile=user_profile)

            # 간단한 답변 생성 (실제로는 LLM 사용)
            context = "\n\n".join([doc['content'][:500] for doc in relevant_docs])

            # 여기서는 간단한 답변을 생성합니다. 실제 프로덕션에서는 OpenAI API 등을 사용해야 합니다.
            answer = f"질문에 대한 관련 정보를 찾았습니다:\n\n"
            for i, doc in enumerate(relevant_docs, 1):
                answer += f"{i}. {doc['file_name']}\n"
                answer += f"   {doc['content'][:200]}...\n\n"

            answer += "\n더 자세한 정보는 복지로 웹사이트를 참고해주세요."
        else:
            answer = "죄송합니다. 현재 시스템이 초기화되지 않았습니다. 관리자에게 문의해주세요."

        # 대화 이력 저장
        ChatHistory.objects.create(
            user=request.user,
            question=question,
            answer=answer
        )

        return JsonResponse({
            'answer': answer,
            'sources': [doc['file_name'] for doc in relevant_docs] if rag_system else []
        })

    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)
