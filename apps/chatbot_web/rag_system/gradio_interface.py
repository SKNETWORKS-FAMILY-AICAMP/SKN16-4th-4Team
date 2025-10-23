"""
Gradio 인터페이스 모듈

웹 UI 및 사용자 상호작용 관리
"""

import gradio as gr
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from config.settings import GRADIO_SERVER_PORT, PROJECT_ROOT

logger = logging.getLogger(__name__)

class GradioInterfaceManager:
    """Gradio 인터페이스 관리자"""
    
    def __init__(self, welfare_bot, feedback_evaluator, ab_evaluator, monitor):
        self.welfare_bot = welfare_bot
        self.feedback_evaluator = feedback_evaluator
        self.ab_evaluator = ab_evaluator
        self.monitor = monitor
        
        # 세션 관리
        self.sessions = {}
        
    def _get_session_id(self) -> str:
        """세션 ID 생성"""
        return str(uuid.uuid4())[:8]
    
    def _process_question(self, question: str, session_id: str = None) -> Tuple[str, Dict]:
        """질문 처리 및 응답 생성"""
        if not session_id:
            session_id = self._get_session_id()
        
        start_time = time.time()
        
        try:
            # A/B 테스트 변형 적용
            variant = self.ab_evaluator.get_variant_for_session(session_id)
            
            # RAG 체인을 통한 응답 생성
            result = self.welfare_bot.get_response(question)
            
            # 응답 시간 기록
            response_time = time.time() - start_time
            self.monitor.record_query(success=True, response_time=response_time)
            
            # 응답 포맷팅
            formatted_response = self._format_response(result)
            
            # 세션 정보 저장
            self.sessions[session_id] = {
                'last_question': question,
                'last_response': result,
                'variant': variant,
                'timestamp': datetime.now()
            }
            
            return formatted_response, {"session_id": session_id, "result": result}
            
        except Exception as e:
            logger.error(f"질문 처리 실패: {e}")
            self.monitor.record_query(success=False, error=str(e))
            
            error_response = "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            return error_response, {"session_id": session_id, "error": str(e)}
    
    def _format_response(self, result: Dict[str, Any]) -> str:
        """응답 포맷팅"""
        answer = result.get("answer", "응답을 생성할 수 없습니다.")
        sources = result.get("sources", [])
        intent = result.get("intent", "unknown")
        confidence = result.get("confidence", "medium")
        
        # 기본 답변
        formatted = answer
        
        # 소스 정보 추가
        if sources:
            formatted += "\n\n📚 **참고자료:**\n"
            for i, source in enumerate(sources[:3]):
                region = source.get('region', '지역미상')
                filename = source.get('filename', '문서명 없음')
                formatted += f"{i+1}. {filename} ({region})\n"
        
        # 신뢰도 표시 (낮은 신뢰도인 경우)
        if confidence == "low":
            formatted += "\n\n⚠️ *정확한 정보는 관련 기관에 문의하시기 바랍니다.*"
        
        return formatted
    
    def _submit_feedback(self, rating: int, usefulness: int, comment: str, session_data: Dict) -> str:
        """피드백 제출"""
        try:
            session_id = session_data.get("session_id")
            result = session_data.get("result", {})
            
            if not session_id or session_id not in self.sessions:
                return "❌ 세션 정보를 찾을 수 없습니다."
            
            session_info = self.sessions[session_id]
            
            feedback_data = {
                'question': session_info['last_question'],
                'answer': result.get('answer', ''),
                'rating': rating,
                'usefulness': usefulness,
                'comment': comment,
                'intent': result.get('intent', ''),
                'confidence': result.get('confidence', ''),
                'sources_count': len(result.get('sources', [])),
                'session_id': session_id
            }
            
            success = self.feedback_evaluator.submit_feedback(feedback_data)
            
            if success:
                return "✅ 소중한 피드백을 주셔서 감사합니다!"
            else:
                return "❌ 피드백 저장에 실패했습니다."
                
        except Exception as e:
            logger.error(f"피드백 제출 실패: {e}")
            return "❌ 피드백 처리 중 오류가 발생했습니다."
    
    def _get_system_stats(self) -> str:
        """시스템 통계 조회"""
        try:
            # 실시간 모니터링 통계
            monitor_stats = self.monitor.get_current_stats()
            
            # 피드백 통계
            feedback_stats = self.feedback_evaluator.get_feedback_stats(days=7)
            
            stats_text = f"""
## 📊 시스템 현황

### 🔄 실시간 모니터링
- **가동 시간**: {monitor_stats.get('uptime_formatted', '0:00:00')}
- **총 질의수**: {monitor_stats.get('total_queries', 0)}개
- **성공률**: {monitor_stats.get('success_rate', 0)}%
- **평균 응답시간**: {monitor_stats.get('avg_response_time', 0)}초
- **분당 질의수**: {monitor_stats.get('queries_per_minute', 0)}개

### 📝 사용자 피드백 (최근 7일)
- **총 피드백**: {feedback_stats.get('total_feedback', 0)}건
- **평균 만족도**: {feedback_stats.get('avg_rating', 0)}/5.0
- **평균 유용성**: {feedback_stats.get('avg_usefulness', 0)}/5.0
- **긍정 평가율**: {feedback_stats.get('positive_rating_rate', 0)}%

### 💾 데이터베이스
- **벡터 문서수**: {getattr(self.welfare_bot.rag_chain.vector_store, 'get_document_count', lambda: 0)()}개
            """
            
            return stats_text.strip()
            
        except Exception as e:
            logger.error(f"시스템 통계 조회 실패: {e}")
            return "❌ 시스템 통계를 불러올 수 없습니다."
    
    def _get_recent_feedback(self) -> str:
        """최근 피드백 조회"""
        try:
            feedback_list = self.feedback_evaluator.get_recent_feedback(limit=10)
            
            if not feedback_list:
                return "📝 아직 피드백이 없습니다."
            
            feedback_text = "## 📝 최근 피드백\n\n"
            
            for fb in feedback_list:
                timestamp = fb['timestamp'][:19]  # 초 단위까지만
                question = fb['question']
                rating = "⭐" * fb['rating']
                usefulness = "👍" * fb['usefulness']
                comment = fb.get('comment', '')
                
                feedback_text += f"**{timestamp}**\n"
                feedback_text += f"Q: {question}\n"
                feedback_text += f"만족도: {rating} | 유용성: {usefulness}\n"
                if comment:
                    feedback_text += f"💬 {comment}\n"
                feedback_text += "---\n\n"
            
            return feedback_text
            
        except Exception as e:
            logger.error(f"최근 피드백 조회 실패: {e}")
            return "❌ 피드백을 불러올 수 없습니다."
    
    def create_interface(self) -> gr.Blocks:
        """Gradio 인터페이스 생성"""
        
        with gr.Blocks(
            title="🏥 노인복지 RAG 시스템",
            theme=gr.themes.Soft(),
            css="""
                .main-container { max-width: 1200px; margin: 0 auto; }
                .chat-container { height: 500px; }
                .feedback-container { border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
            """
        ) as interface:
            
            # 상태 변수들
            session_data = gr.State({})
            
            gr.Markdown("""
            # 🏥 노인복지 RAG 시스템
            
            **AI 기반 노인복지 정책 상담 서비스**
            
            궁금한 노인복지 정책에 대해 질문해보세요. 전국 및 지역별 복지 정책 정보를 바탕으로 친절하게 답변드립니다.
            """)
            
            with gr.Tabs():
                # 메인 채팅 탭
                with gr.Tab("💬 상담하기"):
                    with gr.Row():
                        with gr.Column(scale=2):
                            chatbot = gr.Chatbot(
                                label="노인복지 상담",
                                height=500,
                                show_label=True,
                                elem_classes=["chat-container"]
                            )
                            
                            with gr.Row():
                                question_input = gr.Textbox(
                                    placeholder="노인복지 정책에 대해 질문해주세요... (예: 기초연금 신청 방법이 궁금합니다)",
                                    label="질문 입력",
                                    lines=2,
                                    scale=4
                                )
                                submit_btn = gr.Button("📤 질문하기", scale=1, variant="primary")
                            
                            gr.Examples(
                                examples=[
                                    "기초연금 수급 조건이 어떻게 되나요?",
                                    "노인 의료비 지원 제도는 무엇이 있나요?",
                                    "독거노인 돌봄 서비스 신청 방법을 알려주세요",
                                    "경로당 지원 정책이 궁금합니다",
                                    "어르신 틀니 지원 사업은 어떻게 신청하나요?"
                                ],
                                inputs=question_input
                            )
                        
                        # 피드백 섹션
                        with gr.Column(scale=1):
                            with gr.Group():
                                gr.Markdown("### 📋 답변 평가")
                                gr.Markdown("*마지막 답변에 대한 평가를 해주세요*")
                                
                                rating_slider = gr.Slider(
                                    minimum=1, maximum=5, value=3, step=1,
                                    label="만족도 (1=매우 불만족, 5=매우 만족)"
                                )
                                
                                usefulness_slider = gr.Slider(
                                    minimum=1, maximum=5, value=3, step=1,
                                    label="유용성 (1=전혀 도움안됨, 5=매우 도움됨)"
                                )
                                
                                feedback_comment = gr.Textbox(
                                    label="추가 의견 (선택사항)",
                                    lines=3,
                                    placeholder="개선사항이나 추가 의견을 남겨주세요..."
                                )
                                
                                feedback_btn = gr.Button("📝 피드백 제출", variant="secondary")
                                feedback_result = gr.Markdown("")
                
                # 시스템 모니터링 탭
                with gr.Tab("📊 시스템 현황"):
                    with gr.Row():
                        with gr.Column():
                            stats_display = gr.Markdown("시스템 통계를 불러오는 중...")
                            refresh_stats_btn = gr.Button("🔄 새로고침")
                        
                        with gr.Column():
                            feedback_display = gr.Markdown("피드백을 불러오는 중...")
                            refresh_feedback_btn = gr.Button("🔄 피드백 새로고침")
            
            # 이벤트 핸들러
            def handle_submit(question, history, session_data):
                if not question.strip():
                    return history, "", session_data
                
                # 사용자 질문 추가
                history = history or []
                history.append([question, "답변을 생성하는 중..."])
                
                # 응답 생성
                response, new_session_data = self._process_question(question, session_data.get("session_id"))
                
                # 답변 업데이트
                history[-1][1] = response
                
                return history, "", new_session_data
            
            def handle_feedback(rating, usefulness, comment, session_data):
                return self._submit_feedback(rating, usefulness, comment, session_data)
            
            # 이벤트 바인딩
            submit_btn.click(
                fn=handle_submit,
                inputs=[question_input, chatbot, session_data],
                outputs=[chatbot, question_input, session_data]
            )
            
            question_input.submit(
                fn=handle_submit,
                inputs=[question_input, chatbot, session_data],
                outputs=[chatbot, question_input, session_data]
            )
            
            feedback_btn.click(
                fn=handle_feedback,
                inputs=[rating_slider, usefulness_slider, feedback_comment, session_data],
                outputs=[feedback_result]
            )
            
            refresh_stats_btn.click(
                fn=self._get_system_stats,
                outputs=[stats_display]
            )
            
            refresh_feedback_btn.click(
                fn=self._get_recent_feedback,
                outputs=[feedback_display]
            )
            
            # 초기 로드
            interface.load(
                fn=self._get_system_stats,
                outputs=[stats_display]
            )
            
            interface.load(
                fn=self._get_recent_feedback,
                outputs=[feedback_display]
            )
        
        return interface
    
    def launch(self, server_port: int = None, share: bool = False, debug: bool = False):
        """인터페이스 실행"""
        port = server_port or GRADIO_SERVER_PORT
        
        interface = self.create_interface()
        
        logger.info(f"Gradio 인터페이스 시작 - 포트: {port}")
        
        interface.launch(
            server_port=port,
            share=share,
            debug=debug,
            server_name="0.0.0.0",
            show_error=True,
            quiet=False
        )