# Double Dragon - Stage 2 게임플레이 메모리 덤프 분석

## 덤프 정보

- **덤프 시점**: 스테이지 2 플레이 중
- **게임 상태**: 활성 플레이 (적 등장, 전투 진행)
- **CPU 사이클**: 756,548,669
- **덤프 시간**: 2025-11-24 00:07

## 생성된 파일

### 1. spice86dumpMemoryDump.bin (1.1MB)
- **전체 메모리 스냅샷**
- 실 모드 주소 공간 (0x00000 ~ 0x10FFEF)
- 스테이지 2 데이터 포함

### 2. spice86dumpExecutionFlow.json (380KB)
- **함수 호출 그래프**
- 실행된 모든 함수의 주소
- CallsFromTo: 함수 간 호출 관계
- JumpsFromTo: 점프 명령어 추적

### 3. spice86dumpGhidraSymbols.txt (27KB)
- **함수 심볼 목록**
- Ghidra 리버스 엔지니어링 도구용
- 200개 이상의 함수 식별

### 4. spice86dumpCpuRegisters.json (1.2KB)
- **CPU 상태**
- 레지스터 값
- 플래그 상태
- 종료 시점의 정확한 CPU 상태

### 5. Breakpoints.json (143B)
- 브레이크포인트 설정 (비어있음)

## CPU 레지스터 상태 (종료 시점)

```
CS:IP = 0xF000:0x7A (BIOS 영역)
DS = 0xAF8 (게임 데이터 세그먼트)
ES = 0xAF8
SS = 0x1061 (스택 세그먼트)
SP = 0x8968

AX = 0x4C00 (DOS 종료 코드)
BX = 0x3FF6
CX = 0x0001
DX = 0x001D
```

## 메모리 분석

### 압축 데이터
- **위치**: 0x76E3
- **시그니처**: 0x1F 0x9D (LZW 압축)
- **상태**: 아직 압축된 상태로 메모리에 존재

### 그래픽 데이터 후보
- **총 1,589개 영역** 발견
- **Top 3 후보**:
  1. 0x7900 - 엔트로피 5.50
  2. 0x6A400 - 엔트로피 5.50 (가장 유망)
  3. 0x3E700 - 엔트로피 5.51

### 비디오 메모리 (0xB8000)
- **상태**: 비어있음
- **이유**: Spice86은 실제 비디오 메모리를 덤프하지 않음
- **대안**: Ghidra로 코드 분석하여 그래픽 렌더링 루틴 추적

## 식별된 주요 함수

```
Entry Point: 0x1700
Interrupt Handlers:
  - INT 08h handler: 0x3383 (타이머)
  - INT 09h handler: 0x34B5 (키보드)

주요 함수들 (예시):
  - unknown_0170_0360: 0x1A60
  - unknown_0170_0B54: 0x2254
  - unknown_0170_16E0: 0x2DE0
  ...
  (200개 이상의 함수 식별됨)
```

## 다음 단계

### Option 1: Ghidra 분석 (권장)
```bash
# 1. Ghidra 설치
brew install --cask ghidra

# 2. DDMAIN.EXE를 Ghidra로 열기

# 3. 심볼 파일 임포트
# spice86dumpGhidraSymbols.txt를 Ghidra에 로드

# 4. 그래픽 렌더링 함수 찾기
# - 비디오 메모리 쓰기 (0xB8000 주소 참조)
# - INT 10h 호출 (BIOS 비디오 서비스)

# 5. 스프라이트 데이터 구조 파악
```

### Option 2: 메모리 후보 영역 추출
```bash
# 유망한 그래픽 데이터 추출
cd "/Users/joejeon/Documents/develop/Double Dragon/analysis"

# 후보 1
python3 analyze_memdump.py spice86dumpMemoryDump.bin 0x7900 0x4000 sprite_1.bin

# 후보 2 (가장 유망)
python3 analyze_memdump.py spice86dumpMemoryDump.bin 0x6A400 0x8000 sprite_2.bin

# 후보 3
python3 analyze_memdump.py spice86dumpMemoryDump.bin 0x3E700 0x4000 sprite_3.bin
```

### Option 3: 압축 데이터 분석
```bash
# 0x76E3에 있는 압축 데이터 추출
python3 analyze_memdump.py spice86dumpMemoryDump.bin 0x76E3 0x2000 compressed.bin

# 압축 해제 시도 (이전에 찾은 루틴 사용)
# 또는 DOS uncompress 시도
uncompress compressed.bin
```

### Option 4: DOSBox-X 디버거
Spice86이 비디오 메모리를 덤프하지 않으므로, DOSBox-X 디버거를 사용하면:
- 실시간으로 비디오 메모리 확인 가능
- 0xB8000 영역을 직접 덤프 가능
- 그래픽이 화면에 렌더링될 때 실제 데이터 캡처

## 발견된 문제점

1. **비디오 메모리 누락**
   - Spice86은 0xB8000 영역을 덤프하지 않음
   - 실제 화면 데이터는 캡처 안 됨

2. **압축된 데이터**
   - 일부 데이터가 아직 압축 상태
   - 압축 해제 루틴을 직접 실행하거나 게임이 해제한 결과를 찾아야 함

3. **함수 이름 없음**
   - 모든 함수가 "unknown"
   - Ghidra로 분석하면서 이름 추론 필요

## 결론

Spice86 덤프는 **코드 리버스 엔지니어링**에는 완벽하지만, **직접 그래픽 추출**에는 부족함.

**추천 경로**:
1. **단기**: DOSBox-X 디버거로 비디오 메모리 덤프
2. **중기**: Ghidra로 그래픽 렌더링 루틴 분석
3. **장기**: 스크린샷 기반 에셋 재생성

웹 복각 프로젝트 목표라면:
- **가장 빠름**: 스크린샷 + Aseprite
- **가장 정확**: DOSBox-X + 메모리 덤프
- **가장 재미있음**: Ghidra + 완전 분석

## 덤프 사용법

### Ghidra에서 사용
```
1. Ghidra 열기
2. DDMAIN.EXE 임포트
3. Window > Script Manager
4. ImportSymbolsScript.py 실행
5. spice86dumpGhidraSymbols.txt 선택
```

### 메모리 덤프 분석
```python
# Python으로 메모리 직접 읽기
with open('spice86dumpMemoryDump.bin', 'rb') as f:
    data = f.read()

# 특정 주소 읽기
offset = 0x6A400
sprite_data = data[offset:offset+0x4000]

# 16진수로 확인
print(' '.join(f'{b:02x}' for b in sprite_data[:64]))
```

---

생성 시간: 2025-11-24 00:09
분석 도구: Spice86 + Python
다음 단계: Ghidra 분석 또는 DOSBox-X 디버거
