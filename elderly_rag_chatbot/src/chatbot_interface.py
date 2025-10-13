# =========================================
# 💬 챗봇 인터페이스 모듈
# =========================================

import os
import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime
import pandas as pd

# Gradio 임포트
try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False

# Streamlit 임포트 (대안)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

logger = logging.getLogger(__name__)


class ElderlyWelfareChatbot:
    """노인복지 정책 챗봇 인터페이스"""
    
    def __init__(self, rag_system=None, workflow_system=None):
        """
        Args:
            rag_system: RAG 시스템 인스턴스
            workflow_system: LangGraph 워크플로우 시스템
        """
        self.rag_system = rag_system
        self.workflow_system = workflow_system
        
        # 대화 기록
        self.conversation_history = []
        
        # 평가 데이터
        self.evaluation_data = []
        
        # 설정
        self.config = {
            "max_history_length": 20,
            "enable_feedback": True,
            "show_sources": True,
            "show_confidence": True
        }
        
        logger.info("노인복지 챗봇 인터페이스 초기화 완료")
    
    def process_message(self, 
                       user_message: str, 
                       use_workflow: bool = False) -> Dict[str, Any]:
        """사용자 메시지 처리"""
        
        if not user_message.strip():
            return {
                "answer": "질문을 입력해주세요.",
                "sources": [],
                "confidence": 0.0,
                "success": False
            }
        
        try:
            if use_workflow and self.workflow_system:
                # LangGraph 워크플로우 사용
                result = self.workflow_system.process_query(user_message)
                
                response = {
                    "answer": result.get("answer", "답변을 생성할 수 없습니다."),
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence_score", 0.0),
                    "follow_up_questions": result.get("follow_up_questions", []),
                    "user_intent": result.get("user_intent", ""),
                    "success": result.get("success", False)
                }
                
            elif self.rag_system:
                # 기본 RAG 시스템 사용
                result = self.rag_system.ask(user_message)
                
                response = {
                    "answer": result.get("answer", "답변을 생성할 수 없습니다."),
                    "sources": result.get("sources", []),
                    "confidence": 0.8,  # 기본값
                    "success": result.get("success", False)
                }
                
            else:
                # 시스템이 없을 때 기본 응답
                response = self._get_default_response(user_message)
            
            # 대화 기록에 추가
            self._add_to_history(user_message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")
            return {
                "answer": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }
    
    def _get_default_response(self, message: str) -> Dict[str, Any]:
        """기본 응답 생성 (시스템이 없을 때)"""
        
        message_lower = message.lower()
        
        # 키워드 기반 간단 응답
        if any(word in message_lower for word in ['의료비', '진료비']):
            answer = """노인 의료비 지원 제도 안내:

1. **노인의료비 지원사업**
   - 대상: 만 65세 이상 기초생활수급자 및 차상위계층
   - 지원내용: 본인부담금 지원
   
2. **기초연금 의료비 지원**
   - 대상: 기초연금 수급자
   - 지원범위: 외래, 입원 본인부담금

자세한 내용은 관할 주민센터나 보건소에 문의하세요."""

        elif any(word in message_lower for word in ['돌봄', '요양', '간병']):
            answer = """노인 돌봄 서비스 안내:

1. **노인장기요양보험**
   - 대상: 만 65세 이상 또는 노인성 질병자
   - 서비스: 재가급여, 시설급여, 특별현금급여
   
2. **노인돌봄서비스**
   - 대상: 독거노인, 노인부부가구 등
   - 내용: 안전확인, 생활교육, 서비스연계

신청: 국민건강보험공단 또는 주민센터"""

        elif any(word in message_lower for word in ['생활비', '수당', '연금']):
            answer = """노인 생활비 지원 제도:

1. **기초연금**
   - 대상: 만 65세 이상 소득하위 70%
   - 금액: 월 최대 334,810원 (2024년 기준)
   
2. **기초생활보장급여**
   - 생계급여, 의료급여, 주거급여, 교육급여
   
3. **노인일자리 사업**
   - 공익활동, 시장형사업단, 취업알선형

신청: 거주지 주민센터"""

        else:
            answer = """안녕하세요! 노인복지 정책 상담 챗봇입니다.

다음과 같은 분야에 대해 문의하실 수 있습니다:

🏥 **의료 지원**: 의료비, 건강검진, 치료비 지원
👥 **돌봄 서비스**: 요양, 간병, 방문돌봄
💰 **생활 지원**: 기초연금, 생활비, 수당
🏠 **주거 지원**: 임대주택, 주거급여
🚌 **교통 지원**: 교통비 할인, 이동서비스

구체적인 질문을 해주시면 더 자세한 안내를 드리겠습니다."""

        return {
            "answer": answer,
            "sources": [{"index": 1, "content": "기본 안내 정보", "source": "시스템 기본값"}],
            "confidence": 0.7,
            "success": True
        }
    
    def _add_to_history(self, user_message: str, response: Dict[str, Any]):
        """대화 기록에 추가"""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": response["answer"],
            "sources_count": len(response["sources"]),
            "confidence": response["confidence"],
            "success": response["success"]
        }
        
        self.conversation_history.append(entry)
        
        # 최대 기록 수 제한
        if len(self.conversation_history) > self.config["max_history_length"]:
            self.conversation_history.pop(0)
    
    def add_feedback(self, 
                    message_index: int, 
                    rating: int, 
                    comment: str = "") -> bool:
        """사용자 피드백 추가"""
        
        try:
            if 0 <= message_index < len(self.conversation_history):
                feedback = {
                    "timestamp": datetime.now().isoformat(),
                    "message_index": message_index,
                    "rating": rating,  # 1-5 점수
                    "comment": comment,
                    "conversation_entry": self.conversation_history[message_index]
                }
                
                self.evaluation_data.append(feedback)
                logger.info(f"피드백 추가됨: 평점 {rating}/5")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"피드백 추가 실패: {e}")
            return False
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """대화 요약 통계"""
        
        if not self.conversation_history:
            return {
                "total_conversations": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
                "common_topics": []
            }
        
        successful = sum(1 for entry in self.conversation_history if entry["success"])
        total = len(self.conversation_history)
        
        # 평균 신뢰도
        confidences = [entry["confidence"] for entry in self.conversation_history if entry["success"]]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # 공통 주제 분석 (간단한 키워드 기반)
        all_messages = " ".join([entry["user_message"] for entry in self.conversation_history])
        
        topic_keywords = {
            "의료 지원": ["의료", "치료", "병원", "약", "진료"],
            "돌봄 서비스": ["돌봄", "요양", "간병", "케어"],
            "생활 지원": ["생활비", "수당", "연금", "급여"],
            "신청 방법": ["신청", "방법", "절차", "서류"]
        }
        
        common_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_messages for keyword in keywords):
                common_topics.append(topic)
        
        return {
            "total_conversations": total,
            "successful_conversations": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_confidence": avg_confidence,
            "common_topics": common_topics,
            "feedback_count": len(self.evaluation_data)
        }
    
    def export_conversation_data(self, file_path: str = None) -> str:
        """대화 데이터 내보내기"""
        
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"chatbot_conversations_{timestamp}.json"
        
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "total_conversations": len(self.conversation_history),
                "total_feedback": len(self.evaluation_data)
            },
            "conversations": self.conversation_history,
            "feedback": self.evaluation_data,
            "summary": self.get_conversation_summary()
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"대화 데이터 내보내기 완료: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"대화 데이터 내보내기 실패: {e}")
            raise


class GradioInterface:
    """Gradio 기반 웹 인터페이스"""
    
    def __init__(self, chatbot: ElderlyWelfareChatbot):
        if not GRADIO_AVAILABLE:
            raise ImportError("Gradio가 설치되지 않았습니다. pip install gradio")
        
        self.chatbot = chatbot
        self.interface = None
    
    def create_interface(self) -> gr.Blocks:
        """Gradio 인터페이스 생성"""
        
        with gr.Blocks(
            title="노인복지 정책 상담 챗봇",
            theme=gr.themes.Soft(),
            css=""".message { padding: 10px; margin: 5px; border-radius: 10px; }"""
        ) as interface:
            
            # 헤더
            gr.Markdown("""
            # 🏥 노인복지 정책 상담 챗봇
            
            노인복지 관련 정책과 서비스에 대해 궁금한 것을 물어보세요.
            의료비 지원, 돌봄 서비스, 생활 지원 등 다양한 정보를 제공합니다.
            """)
            
            with gr.Tab("💬 챗봇 대화"):
                with gr.Row():
                    with gr.Column(scale=3):
                        # 채팅 인터페이스
                        chatbot_ui = gr.Chatbot(
                            label="대화",
                            height=400,
                            show_label=False,
                            container=True
                        )
                        
                        with gr.Row():
                            msg_input = gr.Textbox(
                                label="메시지 입력",
                                placeholder="노인복지 정책에 대해 궁금한 것을 물어보세요...",
                                container=False,
                                scale=4
                            )
                            submit_btn = gr.Button("전송", scale=1, variant="primary")
                        
                        # 고급 옵션
                        with gr.Accordion("고급 옵션", open=False):
                            use_workflow = gr.Checkbox(
                                label="워크플로우 모드 사용",
                                value=False,
                                info="더 정확하지만 느린 처리"
                            )
                            show_sources = gr.Checkbox(
                                label="출처 정보 표시",
                                value=True
                            )
                    
                    with gr.Column(scale=1):
                        # 사이드바
                        gr.Markdown("### 📊 대화 통계")
                        stats_display = gr.JSON(label="통계", container=True)
                        
                        refresh_stats_btn = gr.Button("통계 새로고침", size="sm")
                        
                        gr.Markdown("### 💡 추천 질문")
                        suggested_questions = gr.Radio(
                            choices=[
                                "65세 이상 의료비 지원 제도는?",
                                "노인 돌봄 서비스 신청 방법은?",
                                "기초연금 수급 조건은?",
                                "독거노인 지원 서비스는?",
                                "노인장기요양보험이란?"
                            ],
                            label="추천 질문 선택",
                            interactive=True
                        )
            
            with gr.Tab("📈 평가 및 피드백"):
                gr.Markdown("### 시스템 성능 평가")
                
                with gr.Row():
                    eval_method = gr.Radio(
                        choices=["키워드 기반", "의미 기반", "하이브리드"],
                        label="평가 방법",
                        value="하이브리드"
                    )
                    eval_btn = gr.Button("성능 평가 실행", variant="primary")
                
                eval_results = gr.JSON(label="평가 결과")
                
                gr.Markdown("### 사용자 피드백")
                with gr.Row():
                    feedback_rating = gr.Slider(
                        minimum=1, maximum=5, step=1, value=5,
                        label="만족도 (1-5)"
                    )
                    feedback_comment = gr.TextArea(
                        label="의견",
                        placeholder="챗봇 답변에 대한 의견을 남겨주세요..."
                    )
                    feedback_btn = gr.Button("피드백 제출")
                
                feedback_status = gr.Textbox(label="피드백 상태", interactive=False)
            
            with gr.Tab("📊 데이터 관리"):
                gr.Markdown("### 대화 기록 관리")
                
                with gr.Row():
                    export_btn = gr.Button("대화 기록 내보내기", variant="primary")
                    clear_btn = gr.Button("대화 기록 초기화", variant="stop")
                
                export_status = gr.Textbox(label="내보내기 상태", interactive=False)
                
                gr.Markdown("### 시스템 정보")
                system_info = gr.JSON(label="시스템 상태")
            
            # 이벤트 핸들러
            def respond(message, history, use_wf, show_src):
                if message.strip():
                    response = self.chatbot.process_message(message, use_workflow=use_wf)
                    
                    # 답변 포맷팅
                    bot_message = response["answer"]
                    
                    if show_src and response["sources"]:
                        bot_message += "\n\n📚 **참고 자료:**\n"
                        for source in response["sources"][:3]:
                            bot_message += f"• {source.get('content', 'N/A')[:100]}...\n"
                    
                    if response.get("confidence", 0) > 0:
                        confidence_emoji = "🟢" if response["confidence"] > 0.7 else "🟡" if response["confidence"] > 0.4 else "🔴"
                        bot_message += f"\n\n{confidence_emoji} 신뢰도: {response['confidence']:.1%}"
                    
                    history.append([message, bot_message])
                    return "", history
                
                return message, history
            
            def get_stats():
                return self.chatbot.get_conversation_summary()
            
            def run_evaluation(method):
                # 간단한 평가 시뮬레이션
                return {
                    "method": method,
                    "accuracy": 0.85,
                    "response_time": "1.2초",
                    "user_satisfaction": 4.2,
                    "total_queries": len(self.chatbot.conversation_history)
                }
            
            def submit_feedback(rating, comment):
                if self.chatbot.conversation_history:
                    last_index = len(self.chatbot.conversation_history) - 1
                    success = self.chatbot.add_feedback(last_index, rating, comment)
                    if success:
                        return "피드백이 성공적으로 제출되었습니다. 감사합니다!"
                    else:
                        return "피드백 제출에 실패했습니다."
                return "피드백을 제출할 대화가 없습니다."
            
            def export_data():
                try:
                    file_path = self.chatbot.export_conversation_data()
                    return f"대화 기록이 성공적으로 내보내졌습니다: {file_path}"
                except Exception as e:
                    return f"내보내기 실패: {str(e)}"
            
            def clear_history():
                self.chatbot.conversation_history.clear()
                return "대화 기록이 초기화되었습니다."
            
            def use_suggested_question(question):
                if question:
                    return question
                return ""
            
            # 이벤트 연결
            submit_btn.click(
                respond,
                [msg_input, chatbot_ui, use_workflow, show_sources],
                [msg_input, chatbot_ui]
            )
            
            msg_input.submit(
                respond,
                [msg_input, chatbot_ui, use_workflow, show_sources],
                [msg_input, chatbot_ui]
            )
            
            suggested_questions.change(
                use_suggested_question,
                suggested_questions,
                msg_input
            )
            
            refresh_stats_btn.click(get_stats, outputs=stats_display)
            
            eval_btn.click(run_evaluation, eval_method, eval_results)
            
            feedback_btn.click(
                submit_feedback,
                [feedback_rating, feedback_comment],
                feedback_status
            )
            
            export_btn.click(export_data, outputs=export_status)
            
            clear_btn.click(clear_history, outputs=export_status)
        
        self.interface = interface
        return interface
    
    def launch(self, **kwargs):
        """인터페이스 실행"""
        if self.interface is None:
            self.create_interface()
        
        default_kwargs = {
            "server_name": "0.0.0.0",
            "server_port": 7860,
            "share": False,
            "debug": False
        }
        default_kwargs.update(kwargs)
        
        return self.interface.launch(**default_kwargs)


class StreamlitInterface:
    """Streamlit 기반 인터페이스 (대안)"""
    
    def __init__(self, chatbot: ElderlyWelfareChatbot):
        if not STREAMLIT_AVAILABLE:
            raise ImportError("Streamlit이 설치되지 않았습니다. pip install streamlit")
        
        self.chatbot = chatbot
    
    def run_interface(self):
        """Streamlit 인터페이스 실행"""
        
        st.set_page_config(
            page_title="노인복지 정책 상담 챗봇",
            page_icon="🏥",
            layout="wide"
        )
        
        st.title("🏥 노인복지 정책 상담 챗봇")
        st.markdown("노인복지 관련 정책과 서비스에 대해 궁금한 것을 물어보세요.")
        
        # 사이드바
        with st.sidebar:
            st.header("📊 대화 통계")
            stats = self.chatbot.get_conversation_summary()
            st.json(stats)
            
            st.header("⚙️ 설정")
            use_workflow = st.checkbox("워크플로우 모드", value=False)
            show_sources = st.checkbox("출처 표시", value=True)
        
        # 메인 채팅 영역
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # 대화 기록 표시
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # 사용자 입력
        if prompt := st.chat_input("메시지를 입력하세요..."):
            # 사용자 메시지 표시
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # 챗봇 응답
            with st.chat_message("assistant"):
                with st.spinner("답변 생성 중..."):
                    response = self.chatbot.process_message(prompt, use_workflow=use_workflow)
                
                answer = response["answer"]
                
                if show_sources and response["sources"]:
                    answer += "\n\n**참고 자료:**\n"
                    for source in response["sources"][:3]:
                        answer += f"• {source.get('content', '')[:100]}...\n"
                
                st.markdown(answer)
                
                # 신뢰도 표시
                if response.get("confidence", 0) > 0:
                    st.progress(response["confidence"], f"신뢰도: {response['confidence']:.1%}")
            
            st.session_state.messages.append({"role": "assistant", "content": answer})


def main():
    """챗봇 인터페이스 테스트"""
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    print("💬 챗봇 인터페이스 테스트")
    print("=" * 50)
    
    try:
        # 챗봇 생성
        chatbot = ElderlyWelfareChatbot()
        
        # 테스트 메시지
        test_message = "65세 이상 노인 의료비 지원에 대해 알려주세요"
        response = chatbot.process_message(test_message)
        
        print(f"테스트 질문: {test_message}")
        print(f"챗봇 답변: {response['answer'][:200]}...")
        print(f"성공 여부: {response['success']}")
        
        # 대화 요약
        summary = chatbot.get_conversation_summary()
        print(f"\n대화 요약: {summary}")
        
        # Gradio 인터페이스 테스트 (설치된 경우에만)
        if GRADIO_AVAILABLE:
            print(f"\n🌐 Gradio 인터페이스 생성 테스트...")
            gradio_interface = GradioInterface(chatbot)
            interface = gradio_interface.create_interface()
            print("Gradio 인터페이스 생성 완료")
            
            # 실제 실행은 주석 처리 (테스트 환경에서)
            # interface.launch(share=False, debug=True)
        
        print(f"\n✅ 챗봇 인터페이스 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()