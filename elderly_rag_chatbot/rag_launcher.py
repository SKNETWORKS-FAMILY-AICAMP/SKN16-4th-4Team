"""
🚀 RAG 시스템 통합 런처
======================

모든 RAG 비교평가 및 자동화 시스템을 하나의 인터페이스로 제공하는 런처
"""

import os
import sys
from typing import Dict, List, Any
from pathlib import Path

def show_main_menu():
    """메인 메뉴 표시"""
    print("\n" + "="*70)
    print("🚀 RAG 파이프라인 통합 제어 시스템")
    print("="*70)
    print("┌─ 🎮 리모컨 시스템 ─────────────────────────────────────────────┐")
    print("│ 1. 📱 궁극의 리모컨        │  원클릭 모든 기능 제어              │")
    print("│ 2. 🎯 마스터 리모컨        │  기본 비교평가 시스템               │")
    print("│ 3. 🤖 AutoRAG 시스템       │  완전 자동화 최적화                 │")
    print("├─ 📊 비교평가 시스템 ──────────────────────────────────────────┤")
    print("│ 4. 📄 텍스트 추출 비교     │  PDF/HWP 추출기 성능 비교           │")
    print("│ 5. ✂️ 청킹 전략 비교       │  다양한 청킹 방법 비교              │")  
    print("│ 6. 🔢 임베딩 모델 비교     │  임베딩 모델 성능 비교              │")
    print("│ 7. 🔍 검색 전략 비교       │  검색 알고리즘 성능 비교            │")
    print("├─ 🛠️ 통합 도구 ────────────────────────────────────────────────┤")
    print("│ 8. 🎯 통합 비교평가        │  전체 구성요소 종합 비교            │")
    print("│ 9. 📋 메뉴 시스템          │  사용자 친화적 메뉴 인터페이스       │")
    print("│10. ⚡ 빠른 테스트          │  개별 파일 빠른 테스트              │")
    print("├─ 📈 결과 및 리포팅 ───────────────────────────────────────────┤")
    print("│11. 📊 결과 조회            │  이전 실행 결과 확인                │")
    print("│12. 📄 리포트 생성          │  HTML/PDF 리포트 생성               │")
    print("│13. 💾 데이터 관리          │  결과 저장/로드/내보내기            │")
    print("├─ ⚙️ 고급 기능 ────────────────────────────────────────────────┤")
    print("│14. 🎛️ 커스텀 파이프라인    │  사용자 정의 RAG 구성               │")
    print("│15. 🔄 배치 처리            │  대량 파일 자동 처리                │")
    print("│16. 📊 데모 실행            │  전체 시스템 데모                   │")
    print("├─ 📚 도움말 및 정보 ───────────────────────────────────────────┤")
    print("│17. ❓ 도움말               │  사용법 및 명령어 안내              │")
    print("│18. 📊 시스템 상태          │  현재 시스템 상태 확인              │")
    print("│19. ⚙️ 설정 관리            │  시스템 설정 변경                   │")
    print("└────────────────────────────────────────────────────────────┘")
    print("│ 0. 🚪 종료                │  프로그램 종료                      │")
    print("└────────────────────────────────────────────────────────────┘")

def run_ultimate_remote():
    """궁극의 리모컨 실행"""
    print("\n🎮 궁극의 리모컨을 시작합니다...")
    try:
        os.system("python ultimate_rag_remote.py")
    except Exception as e:
        print(f"❌ 실행 실패: {e}")

def run_master_remote():
    """마스터 리모컨 실행"""
    print("\n🎯 마스터 리모컨을 시작합니다...")
    try:
        os.system("python rag_remote_control.py")
    except Exception as e:
        print(f"❌ 실행 실패: {e}")

def run_autorag_system():
    """AutoRAG 시스템 실행"""
    print("\n🤖 AutoRAG 시스템을 시작합니다...")
    try:
        os.system("python autorag_system.py")
    except Exception as e:
        print(f"❌ 실행 실패: {e}")

def run_text_extraction_comparison():
    """텍스트 추출 비교 실행"""
    print("\n📄 텍스트 추출 비교를 시작합니다...")
    
    # 파일 선택
    data_files = list(Path("data").glob("**/*.pdf")) + list(Path("data").glob("**/*.hwp"))
    
    if not data_files:
        print("❌ 테스트할 파일이 없습니다. data/ 폴더에 PDF 또는 HWP 파일을 추가해주세요.")
        return
    
    print("📁 사용 가능한 파일:")
    for i, file_path in enumerate(data_files[:5], 1):
        print(f"   {i}. {file_path.name}")
    
    try:
        choice = input("\n파일 번호를 선택하세요 (엔터=전체): ").strip()
        
        if choice:
            idx = int(choice) - 1
            if 0 <= idx < len(data_files):
                selected_file = data_files[idx]
                os.system(f'python quick_extraction_test.py "{selected_file}"')
            else:
                print("❌ 잘못된 번호입니다.")
        else:
            # 전체 파일 테스트
            from src.text_extraction_comparison import TextExtractionComparison
            extractor = TextExtractionComparison()
            
            print(f"\n🔄 {len(data_files)} 파일 비교 실행 중...")
            for file_path in data_files[:3]:  # 처음 3개만
                print(f"\n📄 {file_path.name}")
                try:
                    results = extractor.compare_extractors(str(file_path))
                    for extractor_name, result in results.items():
                        success = "✅" if result.get('success', False) else "❌"
                        chars = len(result.get('content', ''))
                        time_taken = result.get('processing_time', 0)
                        print(f"   {success} {extractor_name}: {chars:,}자 ({time_taken:.3f}초)")
                except Exception as e:
                    print(f"   ❌ 오류: {e}")
                    
    except ValueError:
        print("❌ 잘못된 입력입니다.")
    except Exception as e:
        print(f"❌ 실행 실패: {e}")

def run_integrated_comparison():
    """통합 비교평가 실행"""
    print("\n🎯 통합 비교평가를 시작합니다...")
    try:
        os.system("python integrated_comparison.py")
    except Exception as e:
        print(f"❌ 실행 실패: {e}")

def run_menu_system():
    """메뉴 시스템 실행"""
    print("\n📋 메뉴 시스템을 시작합니다...")
    try:
        os.system("python comparison_menu.py")
    except Exception as e:
        print(f"❌ 실행 실패: {e}")

def run_quick_test():
    """빠른 테스트 실행"""
    print("\n⚡ 빠른 테스트를 시작합니다...")
    try:
        os.system("python quick_extraction_test.py")
    except Exception as e:
        print(f"❌ 실행 실패: {e}")

def run_demo():
    """데모 실행"""
    print("\n📊 시스템 데모를 시작합니다...")
    try:
        os.system("python demo_comparison.py")
    except Exception as e:
        print(f"❌ 실행 실패: {e}")

def show_help():
    """도움말 표시"""
    print("\n❓ RAG 시스템 사용 도움말")
    print("="*50)
    
    print("\n🎮 리모컨 시스템:")
    print("   • 궁극의 리모컨: 모든 기능을 하나의 명령어로 제어")
    print("   • 마스터 리모컨: 기본적인 비교평가 및 벤치마크")
    print("   • AutoRAG 시스템: 완전 자동화된 최적화")
    
    print("\n📊 비교평가 시스템:")
    print("   • 각 구성요소별 성능을 개별적으로 비교")
    print("   • 다양한 라이브러리와 전략의 성능 측정")
    print("   • 상세한 분석 결과와 추천사항 제공")
    
    print("\n🛠️ 주요 명령어:")
    print("   python ultimate_rag_remote.py    # 궁극의 리모컨")
    print("   python rag_remote_control.py     # 마스터 리모컨") 
    print("   python autorag_system.py         # AutoRAG 시스템")
    print("   python integrated_comparison.py  # 통합 비교평가")
    print("   python comparison_menu.py        # 메뉴 시스템")
    print("   python quick_extraction_test.py  # 빠른 테스트")
    
    print("\n📁 파일 구조:")
    print("   config/          # 설정 파일들")
    print("   src/             # 핵심 모듈들")
    print("   data/            # 테스트 데이터")
    print("   results/         # 결과 저장소")
    
    print("\n💡 시작하기:")
    print("   1. 먼저 '시스템 상태'를 확인하세요")
    print("   2. '데모 실행'으로 전체 기능을 체험하세요")
    print("   3. 필요한 기능을 개별적으로 실행하세요")

def show_system_status():
    """시스템 상태 표시"""
    print("\n📊 시스템 상태 확인")
    print("="*30)
    
    try:
        # 모듈 import 테스트
        modules_status = {}
        
        try:
            from rag_remote_control import RAGMasterRemote
            modules_status['마스터 리모컨'] = "✅ 사용 가능"
        except Exception as e:
            modules_status['마스터 리모컨'] = f"❌ 오류: {str(e)[:50]}..."
        
        try:
            from autorag_system import AutoRAGOptimizer
            modules_status['AutoRAG 시스템'] = "✅ 사용 가능"
        except Exception as e:
            modules_status['AutoRAG 시스템'] = f"❌ 오류: {str(e)[:50]}..."
        
        try:
            from ultimate_rag_remote import UltimateRAGRemote
            modules_status['궁극의 리모컨'] = "✅ 사용 가능"
        except Exception as e:
            modules_status['궁극의 리모컨'] = f"❌ 오류: {str(e)[:50]}..."
        
        try:
            from src.text_extraction_comparison import TextExtractionComparison
            modules_status['텍스트 추출'] = "✅ 사용 가능"
        except Exception as e:
            modules_status['텍스트 추출'] = f"❌ 오류: {str(e)[:50]}..."
        
        # 결과 출력
        print("📦 모듈 상태:")
        for module, status in modules_status.items():
            print(f"   {module}: {status}")
        
        # 파일 시스템 확인
        print("\n📁 파일 시스템:")
        
        directories = ['config', 'src', 'data', 'results']
        for dir_name in directories:
            if Path(dir_name).exists():
                file_count = len(list(Path(dir_name).glob("**/*")))
                print(f"   {dir_name}/: ✅ 존재 ({file_count}개 파일)")
            else:
                print(f"   {dir_name}/: ❌ 없음")
        
        # 테스트 데이터 확인
        data_files = list(Path("data").glob("**/*.pdf")) + list(Path("data").glob("**/*.hwp"))
        print(f"\n📄 테스트 데이터: {len(data_files)}개 파일")
        
        for file_path in data_files[:5]:
            size = file_path.stat().st_size / 1024  # KB
            print(f"   📄 {file_path.name} ({size:.1f}KB)")
        
        if len(data_files) > 5:
            print(f"   ... 및 {len(data_files) - 5}개 더")
        
        # 전체 상태 요약
        available_modules = sum(1 for status in modules_status.values() if "✅" in status)
        total_modules = len(modules_status)
        
        print(f"\n📊 전체 상태: {available_modules}/{total_modules} 모듈 사용 가능")
        
        if available_modules == total_modules:
            print("🎉 모든 시스템이 정상 작동합니다!")
        elif available_modules >= total_modules * 0.7:
            print("⚠️ 대부분의 시스템이 작동합니다.")
        else:
            print("❌ 일부 시스템에 문제가 있습니다.")
        
    except Exception as e:
        print(f"❌ 상태 확인 실패: {e}")

def show_settings():
    """설정 관리"""
    print("\n⚙️ 설정 관리")
    print("="*20)
    
    config_files = [
        "config/comparison_config.json",
        "config/remote_config.json", 
        "config/autorag_config.json"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            size = Path(config_file).stat().st_size
            print(f"   ✅ {config_file} ({size} bytes)")
        else:
            print(f"   ❌ {config_file} (없음)")
    
    print("\n💡 설정 파일 편집:")
    print("   텍스트 에디터로 JSON 파일을 직접 편집하거나")
    print("   메뉴 시스템(옵션 9)의 설정 관리를 사용하세요.")

def main():
    """메인 런처"""
    while True:
        try:
            show_main_menu()
            
            choice = input("\n선택하세요 (0-19): ").strip()
            
            if choice == "0":
                print("\n👋 RAG 시스템을 종료합니다. 좋은 하루 되세요!")
                break
            elif choice == "1":
                run_ultimate_remote()
            elif choice == "2":
                run_master_remote()
            elif choice == "3":
                run_autorag_system()
            elif choice == "4":
                run_text_extraction_comparison()
            elif choice == "5":
                print("\n✂️ 청킹 전략 비교는 통합 시스템(옵션 8)을 사용해주세요.")
            elif choice == "6":
                print("\n🔢 임베딩 모델 비교는 통합 시스템(옵션 8)을 사용해주세요.")
            elif choice == "7":
                print("\n🔍 검색 전략 비교는 통합 시스템(옵션 8)을 사용해주세요.")
            elif choice == "8":
                run_integrated_comparison()
            elif choice == "9":
                run_menu_system()
            elif choice == "10":
                run_quick_test()
            elif choice == "11":
                print("\n📊 results/ 폴더의 파일들을 확인해주세요.")
                os.system("dir results" if os.name == "nt" else "ls -la results")
            elif choice == "12":
                print("\n📄 리포트 생성은 궁극의 리모컨(옵션 1)을 사용해주세요.")
            elif choice == "13":
                print("\n💾 데이터 관리는 궁극의 리모컨(옵션 1)을 사용해주세요.")
            elif choice == "14":
                print("\n🎛️ 커스텀 파이프라인은 궁극의 리모컨(옵션 1)을 사용해주세요.")
            elif choice == "15":
                print("\n🔄 배치 처리는 궁극의 리모컨(옵션 1)을 사용해주세요.")
            elif choice == "16":
                run_demo()
            elif choice == "17":
                show_help()
            elif choice == "18":
                show_system_status()
            elif choice == "19":
                show_settings()
            else:
                print("❌ 잘못된 선택입니다. 0-19 사이의 숫자를 입력해주세요.")
            
            if choice != "0":
                input("\n엔터키를 눌러 메인 메뉴로 돌아가기...")
                
        except KeyboardInterrupt:
            print("\n\n👋 프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            input("엔터키를 눌러 계속...")

if __name__ == "__main__":
    print("🚀 RAG 파이프라인 통합 제어 시스템을 시작합니다...")
    main()