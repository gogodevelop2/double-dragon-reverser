# Ghidra MCP (Model Context Protocol) 완전 가이드

**작성일**: 2025-11-24
**목적**: Claude Code를 통한 완전 자동 리버스 엔지니어링
**대상 프로젝트**: Double Dragon 웹 복각

---

## 📋 목차

1. [MCP란 무엇인가](#1-mcp란-무엇인가)
2. [GhidraMCP 개요](#2-ghidramcp-개요)
3. [구현체 비교](#3-구현체-비교)
4. [pyghidra-mcp 상세 가이드](#4-pyghidra-mcp-상세-가이드)
5. [실전 사용 예제](#5-실전-사용-예제)
6. [Double Dragon 프로젝트 적용](#6-double-dragon-프로젝트-적용)
7. [설치 및 설정](#7-설치-및-설정)
8. [트러블슈팅](#8-트러블슈팅)
9. [참고 자료](#9-참고-자료)

---

## 1. MCP란 무엇인가

### 1.1 Model Context Protocol 정의

**MCP (Model Context Protocol)**는 2024년 12월 Anthropic이 도입한 표준 프로토콜로, AI 어시스턴트와 외부 도구 간의 상호작용을 위한 명세입니다.

**기존 방식**:
```
사용자 → 도구 실행 (수동)
     → 결과 복사
     → AI에게 붙여넣기
     → 분석 받기
```

**MCP 방식**:
```
사용자 → AI에게 질문
     → AI가 자동으로 도구 실행
     → AI가 결과 분석
     → 답변 제공

완전 자동!
```

### 1.2 MCP 아키텍처

```
┌─────────────────────────────────────┐
│ Claude Code (MCP Client)            │
│ - 사용자 질문 이해                  │
│ - 적절한 도구 선택                  │
│ - 결과 통합 및 분석                 │
└──────────────┬──────────────────────┘
               │ MCP Protocol
               │ (stdio/HTTP/SSE)
               ▼
┌─────────────────────────────────────┐
│ MCP Server (예: pyghidra-mcp)       │
│ - Ghidra 제어                       │
│ - 함수 디컴파일                     │
│ - 크로스 레퍼런스 추적              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Ghidra (역공학 도구)                │
│ - 바이너리 분석                     │
│ - 디스어셈블리                      │
│ - 디컴파일                          │
└─────────────────────────────────────┘
```

### 1.3 MCP가 필요한 이유

**문제**: 리버스 엔지니어링은 반복적이고 시간 소모적
- 함수 찾기 → 디컴파일 → 분석 → 다음 함수
- 수백 개 함수를 수동으로 처리

**해결**: MCP로 완전 자동화
- AI가 자동으로 함수 탐색
- AI가 자동으로 연관 함수 추적
- AI가 자동으로 전체 플로우 매핑

**시간 절감**:
- 수동: 200개 함수 = 20시간
- MCP: 200개 함수 = 30분

---

## 2. GhidraMCP 개요

### 2.1 GhidraMCP란?

Ghidra의 강력한 바이너리 분석 기능을 MCP를 통해 LLM에 노출시키는 서버 구현체입니다.

**핵심 기능**:
- ✅ 함수 목록 조회
- ✅ 함수 디컴파일
- ✅ 크로스 레퍼런스 추적
- ✅ 문자열 검색
- ✅ 메모리 분석
- ✅ 함수/변수 자동 이름 변경
- ✅ 주석 자동 추가

### 2.2 발전 역사

```
2024년 12월: Anthropic, MCP 프로토콜 발표
2025년 1월: 초기 GhidraMCP 구현체 등장
2025년 3월: LaurieWired/GhidraMCP 릴리즈
2025년 10월: pyghidra-mcp 릴리즈 (헤드리스)
2025년 11월: 여러 파생 구현체 등장
```

### 2.3 사용 사례

**보안 연구**:
- 악성코드 분석
- 취약점 분석
- 리버스 엔지니어링

**게임 개발**:
- 레트로 게임 복각 (우리 프로젝트!)
- 게임 로직 추출
- 에셋 포맷 분석

**학술 연구**:
- 바이너리 포맷 분석
- 컴파일러 연구
- 아키텍처 연구

---

## 3. 구현체 비교

### 3.1 주요 구현체 3가지

#### Option 1: pyghidra-mcp ⭐⭐⭐⭐⭐

**GitHub**: https://github.com/clearbluejar/pyghidra-mcp
**PyPI**: https://pypi.org/project/pyghidra-mcp/

**특징**:
- ✅ CLI 기반 (GUI 불필요)
- ✅ Headless 모드
- ✅ 다중 바이너리 동시 분석
- ✅ 벡터 임베딩 검색 (ChromaDB)
- ✅ 설치 가장 간단
- ✅ Docker 지원

**장점**:
```
+ 한 줄 설치: uvx pyghidra-mcp
+ GUI 없이 자동 실행
+ 여러 바이너리 프로젝트 단위 분석
+ AI 최적화된 검색 (임베딩)
+ 가장 활발한 개발
```

**단점**:
```
- 비교적 최신 (2025년 10월)
- 문서가 아직 부족
```

**추천 대상**: **우리 프로젝트!** (자동화 극대화)

---

#### Option 2: LaurieWired/GhidraMCP ⭐⭐⭐⭐

**GitHub**: https://github.com/LaurieWired/GhidraMCP

**특징**:
- Ghidra 플러그인 방식
- HTTP 서버 (포트 8080)
- Python bridge 스크립트
- 가장 먼저 나온 구현체

**장점**:
```
+ 안정적 (3월부터 운영)
+ 문서 풍부
+ 커뮤니티 크다
+ Ghidra GUI와 통합
```

**단점**:
```
- Ghidra GUI 필요
- 플러그인 수동 설치
- Java + Python 혼용
```

**추천 대상**: GUI에서 실시간으로 보고 싶은 경우

---

#### Option 3: suidpit/ghidra-mcp ⭐⭐⭐

**GitHub**: https://github.com/suidpit/ghidra-mcp

**특징**:
- SSE (Server-Sent Events) 방식
- 7가지 전문 도구
- mcp-proxy 필요

**제공 도구**:
1. `list_functions` - 함수 목록
2. `decompile_function` - 디컴파일
3. `rename_function` - 함수 이름 변경
4. `rename_variable` - 변수 이름 변경
5. `set_comment` - 주석 추가
6. `find_xrefs` - 크로스 레퍼런스
7. `search_memory` - 메모리 문자열 검색

**장점**:
```
+ 도구 세분화
+ 정확한 제어
```

**단점**:
```
- mcp-proxy 추가 설치 필요
- 설정 복잡
- SSE 프로토콜 제한
```

**추천 대상**: 고급 사용자, 세밀한 제어 필요 시

---

### 3.2 구현체 비교표

| 항목 | pyghidra-mcp | LaurieWired | suidpit |
|------|-------------|------------|---------|
| **설치 난이도** | ⭐ 매우 쉬움 | ⭐⭐ 중간 | ⭐⭐⭐ 어려움 |
| **GUI 필요** | ❌ 불필요 | ✅ 필요 | ✅ 필요 |
| **다중 바이너리** | ✅ 지원 | ❌ 단일 | ❌ 단일 |
| **벡터 검색** | ✅ ChromaDB | ❌ 없음 | ❌ 없음 |
| **프로토콜** | stdio/HTTP | HTTP | SSE |
| **Docker** | ✅ 지원 | ❌ 없음 | ❌ 없음 |
| **개발 활성도** | 🔥 매우 활발 | 🔥 활발 | 💤 보통 |
| **문서** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **추천도** | ✅✅✅✅✅ | ✅✅✅✅ | ✅✅✅ |

---

## 4. pyghidra-mcp 상세 가이드

### 4.1 시스템 요구사항

```
Python: >= 3.10
Ghidra: 11.x (자동 다운로드 가능)
메모리: 최소 4GB (8GB 권장)
디스크: 500MB (Ghidra + 캐시)
```

### 4.2 설치 방법

#### 방법 1: uvx (가장 추천)

```bash
# uv 설치
brew install uv

# 즉시 실행 (자동 설치)
uvx pyghidra-mcp /path/to/binary.exe
```

#### 방법 2: pipx

```bash
# pipx 설치
brew install pipx

# 설치
pipx install pyghidra-mcp

# 실행
pyghidra-mcp /path/to/binary.exe
```

#### 방법 3: pip (가상환경)

```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 설치
pip install pyghidra-mcp

# 실행
pyghidra-mcp /path/to/binary.exe
```

#### 방법 4: Docker

```bash
# stdio 모드
docker run -i --rm ghcr.io/clearbluejar/pyghidra-mcp \
  -t stdio < input.txt

# HTTP 모드
docker run -p 8000:8000 ghcr.io/clearbluejar/pyghidra-mcp
```

### 4.3 전송 모드

pyghidra-mcp는 3가지 전송 프로토콜을 지원:

#### 1. stdio 모드 (기본값)

```bash
pyghidra-mcp /path/to/binary.exe
# 또는
pyghidra-mcp -t stdio /path/to/binary.exe
```

**특징**:
- 표준 입출력 사용
- Claude Desktop 기본 연동
- 화면에 출력 없음 (정상)

**사용 시기**: Claude Desktop MCP 연동

#### 2. Streamable HTTP 모드 (권장)

```bash
pyghidra-mcp -t streamable-http /path/to/binary.exe
```

**특징**:
- HTTP 서버 실행 (기본 포트 8000)
- `/mcp` 엔드포인트
- 브라우저 테스트 가능

**환경변수**:
```bash
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=9000
pyghidra-mcp -t streamable-http /path/to/binary.exe
```

**사용 시기**: 디버깅, 외부 접근

#### 3. SSE 모드

```bash
pyghidra-mcp -t sse /path/to/binary.exe
```

**특징**:
- Server-Sent Events
- `/sse` 엔드포인트
- 레거시 지원

**사용 시기**: 특수한 클라이언트

### 4.4 Ghidra 설치 경로 설정

```bash
# 환경변수로 설정
export GHIDRA_INSTALL_DIR="/opt/homebrew/Caskroom/ghidra/11.2.1-20241105/ghidra_11.2.1_PUBLIC"

# 실행
pyghidra-mcp /path/to/binary.exe
```

**자동 감지 순서**:
1. `GHIDRA_INSTALL_DIR` 환경변수
2. `~/ghidra_*` (홈 디렉토리)
3. `/Applications/ghidra_*` (macOS)
4. `/opt/ghidra` (Linux)

### 4.5 제공하는 도구 (Tools)

pyghidra-mcp가 노출하는 MCP 도구들:

#### 1. `list_binaries`
```
설명: 프로젝트의 모든 바이너리 목록 반환
입력: 없음
출력: 바이너리 이름, 경로, 크기, 포맷
```

#### 2. `list_functions`
```
설명: 특정 바이너리의 모든 함수 나열
입력: binary_name
출력: 함수 이름, 주소, 크기
```

#### 3. `decompile`
```
설명: 함수를 C 코드로 디컴파일
입력: binary_name, function_name 또는 address
출력: 디컴파일된 C 코드
```

#### 4. `find_xrefs`
```
설명: 크로스 레퍼런스 검색
입력: binary_name, address
출력: 참조하는/참조되는 위치 목록
```

#### 5. `list_imports`
```
설명: 바이너리의 import 함수 목록
입력: binary_name
출력: import된 함수 이름, 라이브러리
```

#### 6. `list_exports`
```
설명: 바이너리의 export 함수 목록
입력: binary_name
출력: export된 함수 이름, 주소
```

#### 7. `search_strings`
```
설명: 메모리에서 문자열 검색
입력: binary_name, pattern
출력: 문자열 내용, 주소
```

#### 8. `analyze_function`
```
설명: 함수 상세 분석 (콜 그래프, 변수 등)
입력: binary_name, function_name
출력: 분석 결과 JSON
```

---

## 5. 실전 사용 예제

### 5.1 기본 사용 흐름

**시나리오**: Windows notepad.exe에서 파일 생성 흐름 추적

#### Step 1: 서버 시작

```bash
uvx pyghidra-mcp \
  /bin/notepad.exe \
  /bin/kernel32.dll \
  /bin/kernelbase.dll \
  /bin/ntdll.dll
```

#### Step 2: Claude에게 질문

```
"notepad.exe가 파일을 생성하는 전체 과정을 추적해줘.
사용자 모드에서 커널까지의 호출 체인을 모두 보여줘."
```

#### Step 3: AI 자동 실행 (22개 도구 호출)

```
1. list_binaries
   → notepad.exe, kernel32.dll, kernelbase.dll, ntdll.dll 확인

2. search_strings(notepad.exe, "CreateFile")
   → CreateFileW 함수 참조 발견

3. find_xrefs(notepad.exe, CreateFileW)
   → 0x401234에서 호출 발견

4. decompile(notepad.exe, 0x401234)
   → 파일 생성 로직 확인
   → kernel32.dll!CreateFileW 호출 확인

5. decompile(kernel32.dll, CreateFileW)
   → kernelbase.dll!CreateFileW로 전달

6. decompile(kernelbase.dll, CreateFileW)
   → ntdll.dll!NtCreateFile 호출 확인

7. decompile(ntdll.dll, NtCreateFile)
   → 시스템 콜 0x55 발견

→ 전체 호출 체인 완성!
```

#### Step 4: 결과

```
AI 자동 생성 리포트:

# 파일 생성 호출 체인

1. notepad.exe!SaveFile (0x401234)
   - 사용자 입력 받음
   - CreateFileW 호출 준비

2. kernel32.dll!CreateFileW (0x75E12340)
   - 파라미터 검증
   - kernelbase로 전달

3. kernelbase.dll!CreateFileW (0x76A45678)
   - Unicode 변환
   - NtCreateFile 호출

4. ntdll.dll!NtCreateFile (0x77B89012)
   - 시스템 콜 0x55 실행
   - 커널 모드 진입

→ 총 4단계, 4개 바이너리 자동 추적
```

### 5.2 실제 명령어 예제

#### 예제 1: 함수 찾기

```bash
# 서버 시작
uvx pyghidra-mcp /path/to/game.exe
```

**Claude 질문**:
```
"game.exe에서 압축 관련 함수를 찾아줘"
```

**AI 실행**:
```python
# 1. 모든 함수 검색
tools.list_functions("game.exe")

# 2. 함수 이름에서 "compress" 패턴 찾기
# 3. 발견된 함수 디컴파일
tools.decompile("game.exe", "FUN_00401234")

# 4. 코드 분석 후 답변
"0x401234에 LZW 압축 해제 함수가 있습니다..."
```

#### 예제 2: 문자열 추적

**Claude 질문**:
```
"config.txt 파일을 읽는 함수를 찾아줘"
```

**AI 실행**:
```python
# 1. 문자열 검색
tools.search_strings("game.exe", "config.txt")
# → 0x405678에서 발견

# 2. 크로스 레퍼런스
tools.find_xrefs("game.exe", "0x405678")
# → 0x401ABC에서 참조

# 3. 디컴파일
tools.decompile("game.exe", "0x401ABC")
# → ReadConfig 함수 발견!
```

#### 예제 3: 전체 파이프라인 분석

**Claude 질문**:
```
"game.exe의 그래픽 렌더링 파이프라인을
처음부터 끝까지 추적해서 플로우차트로 만들어줘"
```

**AI 실행** (자동):
```python
# 수십 개 도구 호출...

1. search_strings → "sprite", "render", "draw" 검색
2. find_xrefs → 각 문자열 참조 위치
3. decompile → 각 함수 디컴파일
4. analyze_function → 콜 그래프 분석
5. 전체 통합 → 플로우차트 생성

→ Mermaid 다이어그램 자동 생성!
```

---

## 6. Double Dragon 프로젝트 적용

### 6.1 우리 프로젝트 현황

**완료**:
- ✅ Ghidra로 수동 분석 완료
- ✅ 10개 핵심 함수 디컴파일
- ✅ LZW, RLE, CGA 파이프라인 이해

**한계**:
- ❌ 수동 작업 (시간 소모)
- ❌ 스크린샷 복사/붙여넣기
- ❌ 함수 간 연결 수동 추적

**목표**:
- ✅ 완전 자동 분석
- ✅ 남은 190개 함수 빠르게 분석
- ✅ 전체 게임 로직 매핑

### 6.2 적용 시나리오

#### 시나리오 1: 압축 시스템 완전 분석

**기존 방식** (우리가 한 것):
```
1. Ghidra 열기
2. "1F 9D" 검색
3. FUN_1000_6091 찾기
4. 디컴파일 코드 복사
5. Claude에게 "이게 뭐야?"
6. 분석 받기
7. 다음 함수로...
```

**MCP 방식**:
```
Claude: "DDMAIN.EXE의 압축 시스템을 완전히 분석해줘.
        LZW부터 메모리 쓰기까지 전체 플로우를 추적해."

AI 자동 실행:
  1. search_strings("0x1F9D") → 압축 시그니처 찾기
  2. find_xrefs → 참조하는 함수들
  3. decompile 각 함수
  4. 콜 그래프 분석
  5. 전체 플로우 문서화

결과: 5분 만에 완성!
```

#### 시나리오 2: 파일 I/O 시스템 분석

**질문**:
```
"PLAYER1.EG1 파일이 로드되는 전체 과정을
파일 열기부터 메모리 적재까지 추적해줘.
각 단계마다 어떤 함수가 호출되는지 상세히."
```

**AI 자동 실행**:
```
1. search_strings("PLAYER1.EG1")
2. find_xrefs(0x1988:0x1790)
3. decompile(파일 로드 함수)
4. INT 21h 호출 추적
5. 버퍼 주소 확인
6. 압축 해제 함수로 연결
7. 전체 플로우 다이어그램 생성
```

**결과 문서 (자동 생성)**:
```markdown
# PLAYER1.EG1 로딩 파이프라인

## 1. 파일 열기 (0x1A60)
```c
int open_file(char* filename) {
    AX = 0x3D00;  // DOS Open File
    DX = filename;
    INT 0x21;
    return AX;    // 파일 핸들
}
```

## 2. 파일 읽기 (0x1ACA)
```c
void read_file(int handle, char* buffer, int size) {
    AX = 0x3F00;  // DOS Read File
    BX = handle;
    CX = size;
    DX = buffer;
    INT 0x21;
}
```

## 3. 압축 해제 (0x2DE0)
→ FUN_1000_6091로 전달 (LZW)

## 4. 메모리 적재
→ 0x5000 버퍼에 저장

→ 총 4단계, 완전 자동 추적!
```

#### 시나리오 3: AI 데이터 분석

**질문**:
```
"적 캐릭터 AI 로직을 찾아서
각 적의 행동 패턴을 분석해줘.
어떤 조건에서 어떤 행동을 하는지 표로 만들어줘."
```

**AI 자동 실행**:
```
1. search_strings("ABOBO", "LINDA", "WILLIAMS")
2. 적 데이터 구조 찾기
3. AI 업데이트 함수 디컴파일
4. 상태 머신 분석
5. 조건문 추출
6. 표 자동 생성
```

**결과**:
```markdown
| 적 이름 | 상태 | 조건 | 행동 |
|---------|------|------|------|
| ABOBO | IDLE | 플레이어 거리 < 100px | WALK_TOWARDS |
| ABOBO | WALK | 플레이어 거리 < 50px | ATTACK_PUNCH |
| LINDA | IDLE | 플레이어 체력 < 30% | SPECIAL_ATTACK |
...
```

### 6.3 예상 시간 절감

| 작업 | 수동 방식 | MCP 방식 | 절감 |
|------|----------|---------|------|
| 함수 10개 분석 | 2시간 | 10분 | 92% |
| 파일 I/O 추적 | 1시간 | 5분 | 92% |
| 전체 파이프라인 매핑 | 4시간 | 20분 | 92% |
| AI 로직 분석 | 3시간 | 15분 | 92% |
| 문서화 | 2시간 | 자동 | 100% |
| **총계** | **12시간** | **50분** | **93%** |

---

## 7. 설치 및 설정

### 7.1 Double Dragon 프로젝트 설정

#### Step 1: uv 설치

```bash
# Homebrew로 설치
brew install uv

# 버전 확인
uv --version
```

#### Step 2: Ghidra 경로 확인

```bash
# Ghidra 설치 위치 찾기
ls -la /opt/homebrew/Caskroom/ghidra/

# 예시 출력:
# 11.2.1-20241105/ghidra_11.2.1_PUBLIC

# 환경변수 설정
export GHIDRA_INSTALL_DIR="/opt/homebrew/Caskroom/ghidra/11.2.1-20241105/ghidra_11.2.1_PUBLIC"

# .zshrc에 추가 (영구 설정)
echo 'export GHIDRA_INSTALL_DIR="/opt/homebrew/Caskroom/ghidra/11.2.1-20241105/ghidra_11.2.1_PUBLIC"' >> ~/.zshrc
```

#### Step 3: 테스트 실행

```bash
# DDMAIN.EXE로 테스트
cd "/Users/joejeon/Documents/develop/Double Dragon"

uvx pyghidra-mcp \
  -t streamable-http \
  "reference/dos-original/DDMAIN.EXE"
```

**성공 메시지**:
```
INFO: Starting Ghidra analysis...
INFO: Analyzing DDMAIN.EXE...
INFO: Analysis complete
INFO: MCP server listening on http://127.0.0.1:8000/mcp
```

#### Step 4: Claude Code 설정

**설정 파일 위치**:
```
macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
```

**설정 내용**:
```json
{
  "mcpServers": {
    "ghidra": {
      "command": "uvx",
      "args": [
        "pyghidra-mcp",
        "-t", "stdio",
        "/Users/joejeon/Documents/develop/Double Dragon/reference/dos-original/DDMAIN.EXE"
      ],
      "env": {
        "GHIDRA_INSTALL_DIR": "/opt/homebrew/Caskroom/ghidra/11.2.1-20241105/ghidra_11.2.1_PUBLIC"
      }
    }
  }
}
```

**주의사항**:
- `command`: "uvx" (uv 실행)
- `args`: stdio 모드 사용 (Claude Desktop 기본)
- `env`: Ghidra 경로 **필수**

#### Step 5: Claude Code 재시작

```bash
# Claude Desktop 완전 종료
killall "Claude"

# 재시작
open -a "Claude"
```

#### Step 6: 테스트

Claude Code에서:
```
"DDMAIN.EXE에 몇 개의 함수가 있어?"
```

**성공하면**:
```
DDMAIN.EXE를 분석한 결과, 총 247개의 함수가 있습니다.

주요 함수들:
- FUN_1000_6091: LZW 비트 읽기
- FUN_1000_605b: LZW 디코딩
- FUN_1000_2865: RLE 압축 해제
...
```

### 7.2 고급 설정

#### 다중 파일 분석

```json
{
  "mcpServers": {
    "ghidra": {
      "command": "uvx",
      "args": [
        "pyghidra-mcp",
        "-t", "stdio",
        "/Users/joejeon/Documents/develop/Double Dragon/reference/dos-original/DDMAIN.EXE",
        "/Users/joejeon/Documents/develop/Double Dragon/reference/dos-original/PLAYER1.EG1",
        "/Users/joejeon/Documents/develop/Double Dragon/reference/dos-original/LEVEL11.PC1"
      ],
      "env": {
        "GHIDRA_INSTALL_DIR": "/opt/homebrew/Caskroom/ghidra/11.2.1-20241105/ghidra_11.2.1_PUBLIC"
      }
    }
  }
}
```

**장점**: 파일 간 관계 분석 가능

#### 캐시 설정

```bash
# 캐시 디렉토리 설정
export PYGHIDRA_CACHE_DIR="/Users/joejeon/Documents/develop/Double Dragon/.ghidra-cache"

# 캐시 크기 제한 (GB)
export PYGHIDRA_CACHE_SIZE=5
```

#### 로그 레벨 설정

```bash
# 디버깅용
export PYGHIDRA_LOG_LEVEL=DEBUG

# 프로덕션용
export PYGHIDRA_LOG_LEVEL=INFO
```

---

## 8. 트러블슈팅

### 8.1 일반적인 문제

#### 문제 1: "GHIDRA_INSTALL_DIR not found"

**증상**:
```
ERROR: GHIDRA_INSTALL_DIR not set or invalid
```

**해결**:
```bash
# 1. Ghidra 설치 확인
which ghidraRun

# 2. 경로 찾기
ls -la /opt/homebrew/Caskroom/ghidra/

# 3. 환경변수 설정
export GHIDRA_INSTALL_DIR="/정확한/경로/ghidra_11.2.1_PUBLIC"

# 4. 재실행
uvx pyghidra-mcp ...
```

#### 문제 2: "Connection refused"

**증상**:
```
Claude: ❌ Cannot connect to MCP server
```

**해결**:
```bash
# 1. 서버 프로세스 확인
ps aux | grep pyghidra-mcp

# 2. 포트 확인
lsof -i :8000

# 3. 방화벽 확인
# macOS: 시스템 환경설정 > 보안 > 방화벽

# 4. stdio 모드 사용 (추천)
# claude_desktop_config.json에서 -t stdio 사용
```

#### 문제 3: "Analysis timeout"

**증상**:
```
ERROR: Analysis timeout after 300s
```

**해결**:
```bash
# 타임아웃 늘리기
export PYGHIDRA_TIMEOUT=600  # 10분

# 또는 args에 추가
"args": [
  "pyghidra-mcp",
  "--timeout", "600",
  ...
]
```

#### 문제 4: "Out of memory"

**증상**:
```
java.lang.OutOfMemoryError: Java heap space
```

**해결**:
```bash
# Java 힙 크기 늘리기
export JAVA_OPTS="-Xmx8G"  # 8GB

# Ghidra 전용 설정
export GHIDRA_JAVA_OPTS="-Xmx8G -Xms2G"
```

### 8.2 DOS 바이너리 특수 문제

#### 문제: "Unsupported format: MS-DOS MZ"

**증상**:
```
WARNING: MS-DOS executables have limited support
```

**해결**:
```bash
# 1. Ghidra에서 수동으로 한 번 열기
ghidraRun

# 2. DDMAIN.EXE 임포트
# Format: MS-DOS Executable (MZ)
# Processor: x86 16-bit

# 3. 분석 실행 (한 번만)
# 이후 pyghidra-mcp가 재사용
```

#### 문제: "Segmented addressing"

**증상**:
```
ERROR: Cannot resolve address 1000:6091
```

**해결**:
```
# segment:offset 대신 선형 주소 사용
"0x16091" 대신 "FUN_1000_6091" (함수 이름)

또는 Claude에게:
"0x1000:0x6091에 있는 함수" (AI가 자동 변환)
```

### 8.3 디버깅 팁

#### 로그 확인

```bash
# 상세 로그 켜기
export PYGHIDRA_LOG_LEVEL=DEBUG
export MCP_LOG_LEVEL=DEBUG

# 실행
uvx pyghidra-mcp -t streamable-http DDMAIN.EXE

# 로그 파일 저장
uvx pyghidra-mcp DDMAIN.EXE 2>&1 | tee ghidra-mcp.log
```

#### 수동 테스트

```bash
# HTTP 모드로 서버 시작
uvx pyghidra-mcp -t streamable-http DDMAIN.EXE

# 다른 터미널에서 curl 테스트
curl http://localhost:8000/mcp

# 정상이면 JSON 응답:
{"protocol":"mcp","version":"1.0","capabilities":{...}}
```

---

## 9. 참고 자료

### 9.1 공식 문서

**MCP 프로토콜**:
- https://modelcontextprotocol.io/
- https://github.com/modelcontextprotocol

**pyghidra-mcp**:
- GitHub: https://github.com/clearbluejar/pyghidra-mcp
- PyPI: https://pypi.org/project/pyghidra-mcp/
- 블로그: https://clearbluejar.github.io/posts/pyghidra-mcp-headless-ghidra-mcp-server-for-project-wide-multi-binary-analysis/

**LaurieWired/GhidraMCP**:
- GitHub: https://github.com/LaurieWired/GhidraMCP
- MCP Hub: https://mcphub.tools/detail/LaurieWired/GhidraMCP

**suidpit/ghidra-mcp**:
- GitHub: https://github.com/suidpit/ghidra-mcp

### 9.2 튜토리얼 및 가이드

**Medium 블로그**:
- [Supercharging Ghidra with GhidraMCP](https://medium.com/@clearbluejar/supercharging-ghidra-using-local-llms-with-ghidramcp-via-ollama-and-openweb-ui-794cef02ecf7)
- [GhidraMCP AI-Powered RE](https://medium.com/@metehanuluocak/ghidramcp-ai-powered-reverse-engineering-made-easy-8b012183acd5)
- [GhidraMCP on Claude for RE](https://shadowintel.medium.com/ghidramcp-on-claude-for-re-setup-1c592eb60fa5)

**커뮤니티**:
- DEV Community: https://dev.to/sum3sh1/driving-ghidra-static-analysis-with-local-llms-lm-studio-ghidramcp-setup-ka9

### 9.3 관련 프로젝트

**Ghidra**:
- 공식 사이트: https://ghidra-sre.org/
- GitHub: https://github.com/NationalSecurityAgency/ghidra

**pyghidra**:
- GitHub: https://github.com/dod-cyber-crime-center/pyghidra

**FastMCP**:
- MCP 서버 프레임워크
- https://github.com/jlowin/fastmcp

### 9.4 우리 프로젝트 문서

**Double Dragon 분석 문서**:
- `docs/FILE_ANALYSIS.md` - 초기 파일 분석
- `docs/GHIDRA_ANALYSIS_GUIDE.md` - Ghidra 수동 분석 가이드
- `docs/GHIDRA_FINDINGS.md` - 리버스 엔지니어링 결과
- `docs/PROJECT_STATUS.md` - 프로젝트 전체 현황
- `docs/GHIDRA_MCP_GUIDE.md` - 이 문서

**Ghidra 프로젝트**:
- `ghidra-project/DoubleDragon.gpr` - Ghidra 프로젝트
- `ghidra-project/func copy 01.txt` - 디컴파일 코드 1
- `ghidra-project/func copy 02.txt` - 디컴파일 코드 2

---

## 10. 실전 워크플로우

### 10.1 일반적인 분석 흐름

```
1. 프로젝트 목표 정의
   "무엇을 찾고 싶은가?"

2. Claude에게 고수준 질문
   "게임의 레벨 로드 시스템을 분석해줘"

3. AI 자동 분석
   - 관련 함수 찾기
   - 디컴파일
   - 플로우 추적

4. 결과 검토 및 추가 질문
   "압축 해제 부분을 더 자세히 봐줘"

5. 문서화
   AI가 자동으로 마크다운 생성

6. 구현
   분석 결과로 Python 도구 개발
```

### 10.2 Double Dragon 적용 플랜

#### Week 1: 자동 분석 완료

**Day 1**: MCP 설정 및 테스트
```
- uv 설치
- pyghidra-mcp 설정
- Claude Code 연동
- 기본 테스트
```

**Day 2**: 압축 시스템 완전 분석
```
질문: "DDMAIN.EXE의 모든 압축 관련 함수를 찾아서
      상세히 분석하고 Python 재구현 가이드를 만들어줘"

→ LZW, RLE 완전 이해
→ Python 코드 스켈레톤 자동 생성
```

**Day 3**: 파일 I/O 시스템 분석
```
질문: "모든 .EG1, .PC1 파일 로딩 루틴을 추적해줘.
      각 파일 포맷의 헤더 구조도 파악해줘"

→ 파일 포맷 완전 이해
→ 헤더 구조 문서화
```

**Day 4**: 그래픽 시스템 분석
```
질문: "CGA 그래픽 렌더링 전체 파이프라인을 분석해줘.
      스프라이트부터 화면 출력까지"

→ 렌더링 플로우 완전 매핑
```

**Day 5**: 게임 로직 분석
```
질문: "플레이어 이동, 충돌 감지, 적 AI 시스템을 분석해줘"

→ 게임 로직 완전 이해
```

#### Week 2: 도구 개발

**Day 6-7**: Python 추출 도구 구현
```
AI 분석 결과를 바탕으로:
- LZW 압축 해제기
- RLE 압축 해제기
- CGA 변환기
- 스프라이트 추출기
```

**결과**: 모든 에셋 자동 추출!

---

## 11. 팁과 요령

### 11.1 효과적인 질문법

#### ❌ 나쁜 질문
```
"함수 찾아줘"
→ 너무 모호함
```

#### ✅ 좋은 질문
```
"DDMAIN.EXE에서 '1F 9D' 시그니처를 참조하는
모든 함수를 찾아서 각각 디컴파일해줘.
그리고 LZW 압축 해제 루틴이 맞는지 검증해줘."

→ 구체적, 검증 가능
```

#### ✅ 최고의 질문
```
"PLAYER1.EG1 파일이 디스크에서 읽혀서
화면에 표시될 때까지의 전체 과정을 추적해줘.

다음을 포함해서:
1. 파일 열기/읽기 함수
2. 압축 해제 루틴 (LZW/RLE)
3. 헤더 파싱
4. 메모리 버퍼 위치
5. CGA 변환
6. 비디오 메모리 쓰기

각 단계마다 함수 이름, 주소, 디컴파일 코드를 보여주고,
마지막에 플로우차트로 정리해줘."

→ 매우 구체적, 체계적, 결과물 명확
```

### 11.2 반복 작업 자동화

**시나리오**: 모든 .EG1 파일 분석

```
"reference/dos-original/ 폴더의 모든 .EG1 파일에 대해:

1. 파일명 문자열 검색
2. 로딩 함수 찾기
3. 압축 해제 루틴 확인
4. 헤더 구조 추론
5. 결과를 표로 정리

| 파일명 | 로드 함수 | 압축 방식 | 헤더 크기 | 비고 |
|--------|----------|----------|----------|------|
| ... | ... | ... | ... | ... |
"

→ 36개 파일 자동 분석!
```

### 11.3 점진적 접근

```
1차 질문: "대략적인 구조 파악"
  → 전체 함수 목록, 주요 섹션

2차 질문: "특정 시스템 집중"
  → 압축 시스템만 상세 분석

3차 질문: "세부 구현 확인"
  → 비트 레벨 연산 확인

4차 질문: "검증"
  → "내 분석이 맞는지 확인해줘"
```

---

## 12. 결론

### 12.1 GhidraMCP의 가치

**시간 절감**: 93% 단축
**정확도**: AI가 실수 없이 추적
**완전성**: 모든 함수 체계적 분석
**문서화**: 자동으로 리포트 생성

### 12.2 Double Dragon 프로젝트 전망

**Before MCP**:
- 수동 분석: 2주
- 문서화: 3일
- 도구 개발: 1주
- **총 4주**

**After MCP**:
- 자동 분석: 2일
- 문서화: 자동
- 도구 개발: 3일
- **총 5일**

**8배 빠름!**

### 12.3 다음 단계

1. **즉시**: MCP 설정 (30분)
2. **오늘**: 전체 자동 분석 (2-3시간)
3. **내일**: Python 도구 개발 시작
4. **이번 주**: 모든 에셋 추출 완료
5. **다음 주**: Phaser 3 게임 개발 시작

**목표**: 2주 안에 웹 게임 데모!

---

**문서 버전**: 1.0
**최종 수정**: 2025-11-24
**작성자**: AI Assistant + Joe Jeon
**상태**: 준비 완료, 실행 대기

---

## 부록 A: 빠른 참조

### 명령어 치트시트

```bash
# 설치
brew install uv

# 기본 실행
uvx pyghidra-mcp /path/to/binary.exe

# HTTP 모드
uvx pyghidra-mcp -t streamable-http /path/to/binary.exe

# 다중 파일
uvx pyghidra-mcp file1.exe file2.dll file3.sys

# 환경변수
export GHIDRA_INSTALL_DIR="/path/to/ghidra"
export PYGHIDRA_LOG_LEVEL=DEBUG

# Claude 설정
~/Library/Application Support/Claude/claude_desktop_config.json
```

### 트러블슈팅 체크리스트

- [ ] uv 설치됨
- [ ] GHIDRA_INSTALL_DIR 설정됨
- [ ] claude_desktop_config.json 올바름
- [ ] Claude Desktop 재시작함
- [ ] 방화벽 허용함
- [ ] Java 메모리 충분함
- [ ] 로그 확인함

---

끝.
