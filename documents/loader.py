import os
import re
from pathlib import Path
from typing import List, Dict
import PyPDF2
import olefile


class DocumentLoader:
    """PDF와 HWP 파일을 로드하는 클래스"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_pdf(self, file_path: str) -> str:
        """PDF 파일을 읽어 텍스트로 반환"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"PDF 로드 오류 ({file_path}): {e}")
            return ""

    def load_hwp(self, file_path: str) -> str:
        """HWP 파일을 읽어 텍스트로 반환 (기본 텍스트 추출)"""
        try:
            # HWP 파일은 OLE 구조를 가짐
            f = olefile.OleFileIO(file_path)
            dirs = f.listdir()

            # HWP 파일 내의 텍스트 스트림 찾기
            text = ""
            for dir_entry in dirs:
                if dir_entry[-1] == 'BodyText':
                    stream = f.openstream(dir_entry)
                    data = stream.read()
                    # 간단한 디코딩 시도
                    try:
                        text += data.decode('utf-16', errors='ignore')
                    except:
                        text += data.decode('utf-8', errors='ignore')

            f.close()
            # 제어 문자 제거
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
            return text
        except Exception as e:
            print(f"HWP 로드 오류 ({file_path}): {e}")
            return ""

    def load_all_documents(self) -> List[Dict[str, str]]:
        """data 폴더 내의 모든 PDF와 HWP 파일을 로드"""
        documents = []

        # 모든 PDF 파일 찾기
        for pdf_file in self.data_dir.rglob("*.pdf"):
            print(f"로딩 중: {pdf_file}")
            content = self.load_pdf(str(pdf_file))
            if content.strip():
                documents.append({
                    "file_path": str(pdf_file),
                    "file_name": pdf_file.name,
                    "content": content,
                    "file_type": "pdf"
                })

        # 모든 HWP/HWPX 파일 찾기
        for hwp_file in list(self.data_dir.rglob("*.hwp")) + list(self.data_dir.rglob("*.hwpx")):
            print(f"로딩 중: {hwp_file}")
            content = self.load_hwp(str(hwp_file))
            if content.strip():
                documents.append({
                    "file_path": str(hwp_file),
                    "file_name": hwp_file.name,
                    "content": content,
                    "file_type": "hwp"
                })

        print(f"\n총 {len(documents)}개의 문서를 로드했습니다.")
        return documents


if __name__ == "__main__":
    # 테스트
    loader = DocumentLoader("data")
    docs = loader.load_all_documents()
    for doc in docs[:3]:  # 처음 3개만 출력
        print(f"\n파일: {doc['file_name']}")
        print(f"내용 길이: {len(doc['content'])} 문자")
        print(f"내용 미리보기: {doc['content'][:200]}...")
