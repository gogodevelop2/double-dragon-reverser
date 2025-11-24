# Analysis Scripts

이 디렉토리는 Double Dragon 리버스 엔지니어링 과정에서 사용된 임시 분석 스크립트들을 포함합니다.

## 스크립트 카테고리

### 호출 그래프 분석
- `analyze_call_graph.py` - Spice86 ExecutionFlow.json 분석
- `batch_decompile_missing.py` - 누락 함수 일괄 디컴파일
- `batch_decompile_18c6_missing.py` - 0x18c6 점프 테이블 복구

### 점프 테이블 분석
- `dump_jump_table_18c6.py` - 0x18c6 렌더링 점프 테이블 덤프
- `dump_dispatch_table.py` - 디스패처 테이블 덤프
- `explore_dispatch_16ef.py` - 0x16ef AI 디스패처 탐색

### 함수 디컴파일
- `decompile_new_function.py` - 개별 함수 디컴파일
- `disassemble_address.py` - 특정 주소 디스어셈블
- `disassemble_12c0.py` - FUN_1000_12c0 디스어셈블

### 기타 분석
- `check_addresses.py` - 메모리 주소 확인
- `check_function_labels.py` - 함수 레이블 확인
- `extract_all_assets.py` - 에셋 추출
- `analysis_summary.txt` - 분석 요약

## 사용법

대부분의 스크립트는 pyghidra를 사용합니다:

```bash
source venv/bin/activate
export GHIDRA_INSTALL_DIR="/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
export JAVA_HOME="/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

python scripts/analysis/script_name.py
```

## 주의사항

이 스크립트들은 임시 분석 도구로, 프로덕션 코드가 아닙니다.
