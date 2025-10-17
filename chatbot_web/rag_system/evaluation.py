"""
평가 시스템 모듈

사용자 피드백 수집, A/B 테스트, 실시간 모니터링
"""

import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics

from config.settings import PROJECT_ROOT, FEEDBACK_DB_PATH

logger = logging.getLogger(__name__)

class UserFeedbackEvaluator:
    """사용자 피드백 평가자"""
    
    def __init__(self):
        self.db_path = FEEDBACK_DB_PATH
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 피드백 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    usefulness INTEGER NOT NULL CHECK (usefulness >= 1 AND usefulness <= 5),
                    comment TEXT,
                    intent TEXT,
                    confidence TEXT,
                    sources_count INTEGER,
                    session_id TEXT
                )
            ''')
            
            # 시스템 메트릭 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_queries INTEGER,
                    successful_queries INTEGER,
                    error_count INTEGER,
                    avg_response_time REAL,
                    avg_rating REAL,
                    avg_usefulness REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
    
    def submit_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """피드백 제출"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO feedback 
                (question, answer, rating, usefulness, comment, intent, confidence, sources_count, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feedback_data.get('question', ''),
                feedback_data.get('answer', ''),
                feedback_data.get('rating', 3),
                feedback_data.get('usefulness', 3),
                feedback_data.get('comment', ''),
                feedback_data.get('intent', ''),
                feedback_data.get('confidence', ''),
                feedback_data.get('sources_count', 0),
                feedback_data.get('session_id', '')
            ))
            
            conn.commit()
            conn.close()
            
            logger.info("사용자 피드백 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"피드백 저장 실패: {e}")
            return False
    
    def get_feedback_stats(self, days: int = 7) -> Dict[str, Any]:
        """피드백 통계 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 날짜 범위 설정
            start_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_feedback,
                    AVG(rating) as avg_rating,
                    AVG(usefulness) as avg_usefulness,
                    COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_rating,
                    COUNT(CASE WHEN usefulness >= 4 THEN 1 END) as positive_usefulness
                FROM feedback 
                WHERE timestamp >= ?
            ''', (start_date.isoformat(),))
            
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                stats = {
                    'total_feedback': result[0],
                    'avg_rating': round(result[1], 2) if result[1] else 0,
                    'avg_usefulness': round(result[2], 2) if result[2] else 0,
                    'positive_rating_rate': round(result[3] / result[0] * 100, 1) if result[3] else 0,
                    'positive_usefulness_rate': round(result[4] / result[0] * 100, 1) if result[4] else 0,
                    'period_days': days
                }
            else:
                stats = {
                    'total_feedback': 0,
                    'avg_rating': 0,
                    'avg_usefulness': 0,
                    'positive_rating_rate': 0,
                    'positive_usefulness_rate': 0,
                    'period_days': days
                }
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"피드백 통계 조회 실패: {e}")
            return {}
    
    def get_recent_feedback(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 피드백 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, question, rating, usefulness, comment
                FROM feedback 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            
            feedback_list = []
            for row in results:
                feedback_list.append({
                    'timestamp': row[0],
                    'question': row[1][:100] + '...' if len(row[1]) > 100 else row[1],
                    'rating': row[2],
                    'usefulness': row[3],
                    'comment': row[4][:200] + '...' if row[4] and len(row[4]) > 200 else row[4]
                })
            
            conn.close()
            return feedback_list
            
        except Exception as e:
            logger.error(f"최근 피드백 조회 실패: {e}")
            return []

class ABTestEvaluator:
    """A/B 테스트 평가자"""
    
    def __init__(self):
        self.test_configs = {
            'default': {
                'temperature': 0.1,
                'top_k': 5,
                'chunk_size': 1000
            },
            'variant_a': {
                'temperature': 0.3,
                'top_k': 3,
                'chunk_size': 800
            },
            'variant_b': {
                'temperature': 0.05,
                'top_k': 7,
                'chunk_size': 1200
            }
        }
        
        self.current_variant = 'default'
    
    def get_variant_for_session(self, session_id: str) -> str:
        """세션별 변형 할당"""
        # 간단한 해시 기반 할당
        hash_val = hash(session_id) % 100
        
        if hash_val < 70:
            return 'default'
        elif hash_val < 85:
            return 'variant_a'
        else:
            return 'variant_b'
    
    def get_config(self, variant: str) -> Dict[str, Any]:
        """변형별 설정 반환"""
        return self.test_configs.get(variant, self.test_configs['default'])
    
    def record_test_result(self, variant: str, question: str, response_quality: float):
        """테스트 결과 기록"""
        # 실제 구현에서는 별도 DB 테이블에 저장
        logger.info(f"A/B 테스트 결과: {variant} - 품질: {response_quality}")

class RealTimeMonitor:
    """실시간 모니터링"""
    
    def __init__(self):
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'error_count': 0,
            'response_times': [],
            'start_time': datetime.now()
        }
    
    def record_query(self, success: bool, response_time: float = 0.0, error: str = None):
        """쿼리 기록"""
        self.metrics['total_queries'] += 1
        
        if success:
            self.metrics['successful_queries'] += 1
        else:
            self.metrics['error_count'] += 1
            if error:
                logger.error(f"쿼리 오류: {error}")
        
        if response_time > 0:
            self.metrics['response_times'].append(response_time)
            
            # 최근 100개 응답시간만 유지
            if len(self.metrics['response_times']) > 100:
                self.metrics['response_times'] = self.metrics['response_times'][-100:]
    
    def get_current_stats(self) -> Dict[str, Any]:
        """현재 통계 반환"""
        uptime = datetime.now() - self.metrics['start_time']
        
        avg_response_time = 0
        if self.metrics['response_times']:
            avg_response_time = statistics.mean(self.metrics['response_times'])
        
        success_rate = 0
        if self.metrics['total_queries'] > 0:
            success_rate = (self.metrics['successful_queries'] / self.metrics['total_queries']) * 100
        
        return {
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_formatted': str(uptime).split('.')[0],
            'total_queries': self.metrics['total_queries'],
            'successful_queries': self.metrics['successful_queries'],
            'error_count': self.metrics['error_count'],
            'success_rate': round(success_rate, 1),
            'avg_response_time': round(avg_response_time, 3),
            'queries_per_minute': round(self.metrics['total_queries'] / max(uptime.total_seconds() / 60, 1), 2)
        }
    
    def reset_stats(self):
        """통계 초기화"""
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'error_count': 0,
            'response_times': [],
            'start_time': datetime.now()
        }
        logger.info("시스템 통계 초기화됨")

class QualityAssessment:
    """품질 평가"""
    
    @staticmethod
    def assess_response_quality(question: str, answer: str, sources: List[Dict]) -> Dict[str, Any]:
        """응답 품질 평가"""
        score = 0
        details = []
        
        # 답변 길이 평가
        if len(answer) < 50:
            details.append("답변이 너무 짧음")
        elif len(answer) > 2000:
            details.append("답변이 너무 길음")
        else:
            score += 20
            details.append("적절한 답변 길이")
        
        # 소스 활용 평가
        if sources and len(sources) > 0:
            score += 30
            details.append(f"{len(sources)}개 참고자료 활용")
        else:
            details.append("참고자료 없음")
        
        # 질문 관련성 평가 (간단한 키워드 매칭)
        welfare_keywords = ['복지', '노인', '어르신', '연금', '의료', '돌봄']
        question_keywords = [kw for kw in welfare_keywords if kw in question]
        answer_keywords = [kw for kw in welfare_keywords if kw in answer]
        
        if question_keywords and answer_keywords:
            score += 30
            details.append("질문-답변 키워드 일치")
        
        # 구체성 평가
        specific_indicators = ['신청', '방법', '조건', '대상', '금액', '지원']
        if any(indicator in answer for indicator in specific_indicators):
            score += 20
            details.append("구체적인 정보 포함")
        
        # 최종 등급
        if score >= 80:
            grade = "우수"
        elif score >= 60:
            grade = "양호"
        elif score >= 40:
            grade = "보통"
        else:
            grade = "개선필요"
        
        return {
            'score': score,
            'grade': grade,
            'details': details,
            'max_score': 100
        }