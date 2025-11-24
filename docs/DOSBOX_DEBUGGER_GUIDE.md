# DOSBox-X 디버거를 이용한 Double Dragon 분석 가이드

## 🎯 목표

1. 게임 실행 중 메모리에서 압축 해제된 스프라이트 찾기
2. 메모리 덤프로 원본 데이터 추출
3. 레벨 데이터, 캐릭터 스프라이트 분석

## 📋 단계별 계획

### Phase 1: 디버거 시작 및 게임 로드 (5분)

```bash
# 1. DOSBox-X 실행
/opt/homebrew/bin/dosbox-x

# 2. Double Dragon 폴더로 이동
Z:\> mount c "/Users/joejeon/Documents/develop/Double Dragon/reference/dos-original"
Z:\> c:
C:\> dir

# 3. 게임 실행
C:\> DDMAIN.EXE

# 4. 게임이 로딩 화면 보이면 디버거 진입
Alt + Pause  (또는 Cmd + Pause)
```

### Phase 2: 디버거 인터페이스 익히기 (10분)

**주요 명령어**:

```
기본 명령어:
  C         - Continue (실행 계속)
  F5        - Run (브레이크포인트까지 실행)
  F10       - Step Over (다음 명령어)
  F11       - Step Into (함수 안으로)

메모리 관련:
  D <주소>  - 메모리 덤프 보기
  SR        - 메모리 검색
  MEMDUMP   - 메모리를 텍스트로 덤프
  MEMDUMPBIN - 메모리를 바이너리로 덤프

정보 확인:
  R         - 레지스터 보기
  U <주소>  - 디스어셈블리
  BP <주소> - 브레이크포인트 설정

기타:
  HELP      - 도움말
  LOG       - 로그 시작
```

### Phase 3: 스프라이트 데이터 찾기 (30분)

#### 전략 1: 파일 로드 시점 캡처

게임이 파일을 읽는 순간을 잡아서 메모리 주소 찾기:

```
1. 게임 시작 전 디버거 진입
2. 파일 읽기 인터럽트에 브레이크포인트:
   BP INT 21    (DOS 파일 I/O)

3. F5로 실행 → 파일 읽기 시 멈춤
4. 레지스터 확인:
   R
   DS:DX = 파일명 주소
   ES:BX = 데이터 버퍼 주소

5. 버퍼 주소 기록 후 메모리 덤프
```

#### 전략 2: 메모리 패턴 검색

압축 해제된 스프라이트 데이터 특징 찾기:

```
# CGA 그래픽 패턴 검색 (반복되는 픽셀 패턴)
SR 0:0 FFFFF 00 FF 00 FF

# 또는 특정 바이트 시퀀스
SR 0:0 FFFFF AA 55 AA 55

# 검색 결과 주소로 이동
D <찾은주소>
```

#### 전략 3: 코드 세그먼트 추적

DDMAIN.EXE의 압축 해제 루틴 실행 추적:

```
# 압축 해제 루틴 주소에 브레이크포인트
BP CS:6DE0

# 실행
F5

# 멈추면 출력 버퍼 주소 확인
R DI         # 출력 포인터
D ES:DI      # 압축 해제된 데이터 보기
```

### Phase 4: 메모리 덤프 (10분)

#### 방법 1: 특정 주소 덤프

```
# 예: ES:1000에서 64KB 덤프
MEMDUMPBIN ES:1000 10000 player_sprite.bin

# 세그먼트:오프셋 형식
# 크기는 16진수 (10000 = 64KB)
```

#### 방법 2: 전체 메모리 스캔

```
# 640KB 기본 메모리 전체 덤프
MEMDUMPBIN 0:0 A0000 full_memory.bin

# 나중에 Python으로 분석
```

#### 방법 3: 실시간 모니터링

```
# 특정 메모리 주소 워치
LOG ON
D ES:1000
C
# 실행하면서 메모리 변화 관찰
```

### Phase 5: 데이터 분석 (1시간)

Python으로 덤프된 데이터 분석:

```python
# analysis/analyze_memdump.py

import struct
from pathlib import Path

def analyze_memory_dump(dump_path):
    with open(dump_path, 'rb') as f:
        data = f.read()

    print(f"메모리 덤프 크기: {len(data)} bytes")

    # 1F 9D 시그니처 찾기 (압축된 데이터)
    compressed_files = []
    for i in range(len(data) - 2):
        if data[i] == 0x1F and data[i+1] == 0x9D:
            compressed_files.append(i)

    print(f"압축 파일 시그니처 발견: {len(compressed_files)}개")

    # CGA 그래픽 패턴 찾기
    # 320x200, 4색 = 16,000 bytes
    potential_graphics = []
    for i in range(0, len(data) - 16000, 1000):
        chunk = data[i:i+16000]
        # 반복 패턴 체크
        if is_graphic_pattern(chunk):
            potential_graphics.append(i)

    print(f"그래픽 데이터 가능성: {len(potential_graphics)}개")

    return compressed_files, potential_graphics

def is_graphic_pattern(data):
    """그래픽 데이터인지 휴리스틱 체크"""
    # 0xFF가 너무 많으면 빈 공간
    if data.count(0xFF) > len(data) * 0.8:
        return False

    # 0x00이 너무 많으면 빈 공간
    if data.count(0x00) > len(data) * 0.8:
        return False

    # 적당한 엔트로피
    unique_bytes = len(set(data))
    return 10 < unique_bytes < 200
```

## 🎬 실전 워크플로우

### 시나리오 1: 플레이어 스프라이트 추출

```bash
# 1. 게임 시작 화면에서 디버거
Alt + Pause

# 2. 플레이어 그래픽 로드 시점 찾기
BP INT 21
F5

# 3. PLAYER1.EG1 로드되는 순간 멈춤
# 레지스터에서 버퍼 주소 확인
R
# 예: ES = 2000, BX = 0

# 4. 압축 해제 후 메모리 덤프
# (게임 진행 후)
MEMDUMPBIN 2000:0 10000 player_decompressed.bin

# 5. 분석 폴더에 저장
```

### 시나리오 2: 레벨 데이터 추출

```bash
# 1. 레벨 1 시작 전 디버거
Alt + Pause

# 2. LEVEL11.PC1 로드 추적
BP INT 21
F5

# 3. 레벨 데이터 버퍼 덤프
MEMDUMPBIN <세그먼트>:<오프셋> 8000 level1_data.bin
```

### 시나리오 3: 실시간 메모리 캡처

```bash
# 1. 게임 실행
DDMAIN.EXE

# 2. 타이틀 화면에서 디버거
Alt + Pause

# 3. 전체 메모리 덤프 (640KB)
MEMDUMPBIN 0:0 A0000 title_screen.bin

# 4. 게임 플레이 시작
C

# 5. 인게임에서 다시 디버거
Alt + Pause

# 6. 다시 전체 메모리 덤프
MEMDUMPBIN 0:0 A0000 ingame.bin

# 7. 두 덤프 비교 → 차이점이 게임 데이터
```

## 📊 예상 결과

### 찾을 수 있는 데이터:

1. **압축 해제된 스프라이트**
   - PLAYER1.EG1 → 플레이어 애니메이션
   - ABOBO.EG1 → 보스 스프라이트
   - WEAPONS.EG1 → 무기 그래픽

2. **레벨 구조**
   - LEVEL11.PC1 → 배경 타일맵
   - 적 배치 정보
   - 스크롤 데이터

3. **게임 상태**
   - 점수, 체력, 라이프
   - 플레이어 위치
   - 적 AI 상태

## 🛠️ 도구 준비

필요한 Python 스크립트:

```bash
cd "/Users/joejeon/Documents/develop/Double Dragon/analysis"

# 1. 메모리 덤프 분석기
cat > analyze_memdump.py << 'EOF'
#!/usr/bin/env python3
"""메모리 덤프 분석"""

import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_memdump.py <dump_file>")
        return

    dump_file = Path(sys.argv[1])
    # ... 분석 로직

if __name__ == '__main__':
    main()
EOF

chmod +x analyze_memdump.py

# 2. CGA 그래픽 뷰어
# 3. 메모리 diff 도구
```

## ⚠️ 주의사항

1. **메모리 주소는 매번 다를 수 있음**
   - 고정 주소에 의존하지 말 것
   - 패턴 검색으로 찾기

2. **세그먼트:오프셋 이해**
   - 실제 주소 = (세그먼트 × 16) + 오프셋
   - 예: 2000:0100 = 0x20100

3. **크기 단위**
   - MEMDUMPBIN의 크기는 16진수
   - 10000 (hex) = 65536 (dec) = 64KB

## 📝 체크리스트

### 시작 전:
- [ ] DOSBox-X 설치 확인
- [ ] Double Dragon 실행 확인
- [ ] 디버거 단축키 확인 (Alt+Pause)
- [ ] 분석 폴더 준비

### 분석 중:
- [ ] 게임 로딩 화면 캡처
- [ ] 플레이어 스프라이트 메모리 위치 확인
- [ ] 레벨 데이터 메모리 위치 확인
- [ ] 각 데이터 메모리 덤프

### 완료 후:
- [ ] 덤프 파일 백업
- [ ] Python으로 분석
- [ ] 스프라이트 추출 성공 여부 확인
- [ ] 문서화

## 🚀 다음 단계

덤프 성공 시:
1. Python으로 CGA 포맷 파싱
2. PNG로 변환
3. 스프라이트 시트 생성
4. 웹 프로젝트에 통합

## 타임라인

- **첫 시도**: 1-2시간
- **익숙해지면**: 30분 이내
- **전체 게임 분석**: 반나절

지금 바로 시작해보시겠어요?
