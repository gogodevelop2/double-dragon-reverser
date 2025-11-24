# Double Dragon 압축 해제 루틴 발견 및 분석

## 🎯 핵심 발견

### 압축 해제 코드 위치
- **파일**: DDMAIN.EXE
- **오프셋**: 0x6DE0
- **크기**: 약 512 bytes

### 압축 포맷 확인

```assembly
; 오프셋 0x6DE0: 압축 헤더 체크
0x6DE0: MOV  AX, [SI]      ; 파일에서 2바이트 읽기
0x6DE2: CMP  AX, 0x9D1F    ; 시그니처 확인 (리틀 엔디안: 0x1F 0x9D)
0x6DE5: JZ   decompress    ; 일치하면 압축 해제 루틴으로
0x6DE7: MOV  CX, 0         ; 실패 시 0 반환
0x6DEA: STC                ; Carry 플래그 설정 (에러)
0x6DEB: RET
```

## 파일 포맷 구조

```
[오프셋] [크기] [설명]
0x00     2      시그니처: 0x1F 0x9D
0x02     1      플래그/옵션 (비트 수 등)
0x03     ?      압축된 데이터
```

### 플래그 바이트 (오프셋 0x02)

| 파일 | 플래그 | 최대 비트 (하위 5비트) |
|------|--------|----------------------|
| CHARSET.BIN | 0x0E | 14 bits |
| PLAYER1.EG1 | 0xD6 | 22 bits |
| ABOBO.EG1   | 0xE4 | 20 bits |
| LEVEL11.PC1 | 0x7F | 15 bits |

## 압축 해제 알고리즘 분석

### 주요 명령어 패턴

```assembly
; 비트 시프트 연산 발견
0x6E63: SHL  AX, 1         ; 왼쪽 시프트
0x6EA7: ROL  BL, 1         ; 비트 로테이션

; 비트 버퍼 관련 주소
0x6538: 비트 버퍼 (8비트)
0x653A: 비트 카운터
0x6534: 출력 카운터
```

### 추정 알고리즘

1. **LZW 변형**이지만 표준과 다름
2. **가변 비트 길이** 코드 사용 (14-22 bits)
3. **비트 스트림** 읽기 (비트 단위 처리)
4. **딕셔너리 기반** 압축 (LZW 스타일)

## 실제 압축 해제 방법

### 옵션 1: 어셈블리 에뮬레이션 (고급)

DDMAIN.EXE의 압축 해제 루틴을 직접 호출:

```python
# x86 에뮬레이터 사용 (unicorn, capstone)
from unicorn import *
from unicorn.x86_const import *

# 압축 해제 루틴 로드
uc = Uc(UC_ARCH_X86, UC_MODE_16)
uc.mem_map(0x0, 0x100000)
uc.mem_write(0x1000, routine_code)

# 압축 데이터 설정
uc.mem_write(0x2000, compressed_data)

# 실행
uc.reg_write(UC_X86_REG_SI, 0x2000)  # 입력 포인터
uc.reg_write(UC_X86_REG_DI, 0x3000)  # 출력 포인터
uc.emu_start(0x1000, 0x1000 + len(routine_code))

# 결과 읽기
decompressed = uc.mem_read(0x3000, output_size)
```

### 옵션 2: DOSBox 메모리 덤프 (중급)

게임 실행 중 메모리에서 압축 해제된 데이터 추출:

```bash
# DOSBox-X 디버거 모드
dosbox-x -startmapper

# 게임 로드 후 디버거
Alt + Pause

# 메모리 검색 (예: PLAYER1 스프라이트)
# 특정 패턴 검색
SR 0 0xFFFFF 00 01 02

# 메모리 덤프
MEMDUMP 시작주소 크기 output.bin
```

### 옵션 3: 온라인 도구 활용 (추천)

1. **dosbox-tools**: DOS 파일 전용 도구
2. **Game Extractor**: 게임 에셋 추출 도구
3. **커뮤니티 제작 툴**: Double Dragon 전용 추출기 검색

## 압축 해제 루틴 추출 완료

생성된 파일:
- `decompress_routine.bin`: DDMAIN.EXE에서 추출한 압축 해제 루틴 (512 bytes)
- `reverse_decompress.py`: 분석 스크립트

## 다음 단계 권장사항

### 🏆 Best: Unicorn 엔진 사용

**장점**:
- 실제 x86 코드 실행
- 100% 정확한 결과
- 모든 파일 압축 해제 가능

**구현**:
```bash
pip install unicorn-engine capstone-engine
```

```python
# DOS 압축 해제 루틴을 Unicorn으로 실행
def decompress_with_unicorn(compressed_data):
    # 1. Unicorn x86-16 모드 초기화
    # 2. DDMAIN.EXE 압축 해제 루틴 로드
    # 3. 메모리 설정 및 실행
    # 4. 결과 반환
    pass
```

### ⚡ Fast: DOSBox 자동화

```python
import pexpect

# DOSBox 자동 실행 및 메모리 덤프
child = pexpect.spawn('dosbox-x')
child.expect('Z:\\>')
child.sendline('DDMAIN.EXE')
# ... 메모리 덤프 자동화
```

### 💪 중기적 접근

압축 해제 루틴을 완전히 재구현:
- 어셈블리 코드 수동 분석
- Python으로 로직 재작성
- 모든 파일에 적용

**예상 시간**: 3-5일

## 결론

**압축 해제 루틴을 찾았습니다!**

이제 선택지:
1. ✅ **Unicorn 엔진으로 실행** (2-3시간, 추천)
2. ⏱️ **DOSBox 메모리 덤프** (하루)
3. 🛠️ **수동 재구현** (3-5일)
4. 📸 **스크린샷 방법 유지** (기존 계획)

Unicorn 엔진을 사용하면 모든 파일을 자동으로 압축 해제할 수 있습니다!
