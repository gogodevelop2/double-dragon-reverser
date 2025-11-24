# Ghidra를 사용한 Double Dragon 분석 가이드

## 🎯 목표

1. DDMAIN.EXE를 Ghidra로 디컴파일
2. Spice86 심볼 로드
3. 그래픽 렌더링 함수 찾기
4. 스프라이트 데이터 구조 파악

## 📋 준비물

- ✅ Ghidra 11.4.2 설치됨
- ✅ DDMAIN.EXE (105,352 bytes)
- ✅ spice86dumpGhidraSymbols.txt (200+ 함수)
- ✅ spice86dumpMemoryDump.bin (1.1MB)
- ✅ spice86dumpExecutionFlow.json (380KB)

## 🚀 단계별 가이드

### Step 1: Ghidra 실행

```bash
# Ghidra 실행
ghidraRun

# 또는 직접 경로로
/opt/homebrew/bin/ghidraRun
```

처음 실행하면 **Ghidra Project Window**가 열려.

### Step 2: 새 프로젝트 생성

1. **File** → **New Project**
2. **Non-Shared Project** 선택
3. **Next**
4. 프로젝트 위치:
   ```
   /Users/joejeon/Documents/develop/Double Dragon/ghidra-project
   ```
5. 프로젝트 이름: `DoubleDragon`
6. **Finish**

### Step 3: DDMAIN.EXE 임포트

1. **File** → **Import File**
2. 파일 선택:
   ```
   /Users/joejeon/Documents/develop/Double Dragon/reference/dos-original/DDMAIN.EXE
   ```
3. Format: **MS-DOS Executable (MZ)** (자동 인식됨)
4. **OK**

Ghidra가 파일을 분석 시작:
- 파일 타입: DOS MZ executable
- 프로세서: x86 16-bit
- 진행 상황 표시

5. 임포트 완료 후 **OK**

### Step 4: 초기 분석 실행

1. 임포트된 `DDMAIN.EXE` 더블클릭
2. **Analyze** 대화상자 나옴
3. **Yes** 클릭 (자동 분석 시작)
4. Analysis Options:
   - ✅ **Decompiler** (체크)
   - ✅ **Function ID** (체크)
   - ✅ **Stack** (체크)
   - ✅ **x86 Constant Reference Analyzer** (체크)
   - **Analyze** 클릭

**분석 시간**: 1-2분 소요

### Step 5: Spice86 심볼 로드

이제 Spice86이 찾은 함수들을 Ghidra에 임포트하자.

#### 방법 1: Import Symbols Script (추천)

1. **Window** → **Script Manager**
2. 검색창에 "ImportSymbols" 입력
3. **ImportSymbolsScript.py** 더블클릭
4. 파일 선택:
   ```
   /Users/joejeon/Documents/develop/Double Dragon/spice86-dumps/E06625593A0E4A57396DF846E686BC063D03668F1CFB6B8D6B75E14FFCE5D07A/spice86dumpGhidraSymbols.txt
   ```
5. **OK**

**결과**: 200개 이상의 함수 레이블이 자동으로 추가됨

#### 방법 2: 수동 심볼 추가 (대안)

```bash
# Ghidra 심볼 파일을 Ghidra 형식으로 변환
cd "/Users/joejeon/Documents/develop/Double Dragon/spice86-dumps/E06625593A0E4A57396DF846E686BC063D03668F1CFB6B8D6B75E14FFCE5D07A"

# Python 스크립트로 변환
python3 << 'EOF'
with open('spice86dumpGhidraSymbols.txt', 'r') as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 3:
            name = parts[0]
            addr = parts[1]
            print(f"{name} {addr}")
EOF
```

### Step 6: Ghidra 인터페이스 이해

Ghidra 메인 창은 여러 패널로 구성:

1. **Program Trees** (좌측 상단)
   - 파일 구조 트리
   - 세그먼트, 섹션

2. **Listing** (중앙)
   - 디스어셈블리 코드
   - 주소, 바이트, 어셈블리

3. **Decompile** (우측)
   - C 코드로 디컴파일
   - 함수 로직 이해 쉬움

4. **Symbol Tree** (좌측 하단)
   - 모든 함수, 레이블
   - Spice86 심볼 여기 표시됨

### Step 7: 그래픽 함수 찾기

#### 전략 1: INT 10h 호출 찾기

DOS 게임은 BIOS 비디오 서비스 (INT 10h)를 사용:

1. **Search** → **For Instruction Patterns**
2. Pattern: `CD 10` (INT 10h)
3. **Search**

결과:
- 모든 비디오 인터럽트 호출 위치 표시
- 각 위치 클릭하면 주변 코드 확인

#### 전략 2: 비디오 메모리 참조 찾기

CGA 비디오 메모리 주소: `0xB8000`

1. **Search** → **Memory**
2. Value: `B800` (세그먼트)
3. Search in: **All Blocks**
4. **Search**

결과:
- 비디오 메모리에 쓰는 모든 코드 찾기

#### 전략 3: 문자열 검색

파일명이 코드에 있을 수 있음:

1. **Search** → **For Strings**
2. **Search**
3. 결과 창에서:
   - `PLAYER1.EG1`
   - `LEVEL11.PC1`
   - `ABOBO.EG1`
   찾기

이 문자열 참조하는 함수 = 파일 로드 함수!

#### 전략 4: Execution Flow 활용

```bash
# ExecutionFlow.json에서 가장 많이 호출된 함수 찾기
cd "/Users/joejeon/Documents/develop/Double Dragon/spice86-dumps/E06625593A0E4A57396DF846E686BC063D03668F1CFB6B8D6B75E14FFCE5D07A"

python3 << 'EOF'
import json

with open('spice86dumpExecutionFlow.json') as f:
    data = json.load(f)

# 호출 빈도 계산
call_counts = {}
for caller, callees in data.get('CallsFromTo', {}).items():
    for callee in callees:
        addr = callee['Linear']
        call_counts[addr] = call_counts.get(addr, 0) + 1

# Top 20 가장 많이 호출된 함수
top_funcs = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:20]

print("Top 20 가장 많이 호출된 함수:")
for addr, count in top_funcs:
    print(f"  0x{addr:05X}: {count}회")
EOF
```

이 주소들을 Ghidra에서 찾아가면 핵심 함수!

### Step 8: 함수 분석하기

예시: `unknown_0170_0360` 함수 분석

1. **Symbol Tree**에서 함수 이름 더블클릭
2. **Listing** 창에서 어셈블리 코드 보기
3. **Decompile** 창에서 C 코드 보기

**디컴파일 예시**:
```c
void unknown_0170_0360(void) {
    int iVar1;
    ushort uVar2;

    uVar2 = AX;
    if (AX == 0x9d1f) {  // 압축 시그니처!
        // 압축 해제 루틴
        iVar1 = decompress_data();
    }
}
```

### Step 9: 주석 달기

찾은 함수에 주석 달아서 분석 기록:

1. 함수에서 우클릭
2. **Edit Function** → **Set Function Name**
3. 이름 변경:
   - `unknown_0170_0360` → `decompress_lzw`
4. **OK**

코멘트 추가:
- 코드 줄에서 우클릭
- **Set Comment** → **Pre Comment**
- 주석 입력

### Step 10: 데이터 구조 정의

스프라이트 헤더 구조 발견 시:

1. **Window** → **Data Type Manager**
2. **Project Data Types** 우클릭
3. **New** → **Structure**
4. 이름: `SpriteHeader`
5. 필드 추가:
   ```c
   struct SpriteHeader {
       uint16_t width;
       uint16_t height;
       uint16_t num_frames;
       uint32_t data_offset;
   };
   ```

6. 메모리 주소에 적용:
   - Listing에서 주소 선택
   - 우클릭 → **Data** → **Choose Data Type**
   - `SpriteHeader` 선택

## 🎨 그래픽 데이터 찾는 팁

### 패턴 1: 파일 I/O

```assembly
; DOS INT 21h, AH=3Dh (파일 열기)
MOV  AH, 3Dh
MOV  DX, offset filename  ; "PLAYER1.EG1"
INT  21h

; DOS INT 21h, AH=3Fh (파일 읽기)
MOV  AH, 3Fh
MOV  BX, file_handle
MOV  CX, bytes_to_read
MOV  DX, buffer_address   ; 스프라이트 버퍼!
INT  21h
```

### 패턴 2: 압축 해제

```assembly
CMP  AX, 1F9Dh           ; 압축 시그니처 확인
JNE  not_compressed
CALL decompress_routine  ; 압축 해제
```

### 패턴 3: 비디오 메모리 쓰기

```assembly
MOV  AX, 0B800h          ; CGA 비디오 세그먼트
MOV  ES, AX
MOV  DI, offset          ; 화면 오프셋
MOV  SI, sprite_data     ; 스프라이트 데이터
REP  MOVSB               ; 복사
```

## 📊 분석 체크리스트

### 기본 분석
- [ ] DDMAIN.EXE 임포트 완료
- [ ] 자동 분석 완료
- [ ] Spice86 심볼 로드 완료
- [ ] 200개 함수 확인

### 파일 I/O
- [ ] INT 21h 호출 모두 찾기
- [ ] 파일 열기 함수 식별
- [ ] 파일 읽기 버퍼 위치 찾기
- [ ] 파일명 문자열 찾기

### 압축 해제
- [ ] 0x1F9D 시그니처 검색
- [ ] 압축 해제 루틴 찾기
- [ ] 입력/출력 버퍼 파악
- [ ] 압축 해제 알고리즘 이해

### 그래픽 렌더링
- [ ] INT 10h 호출 찾기
- [ ] 0xB800 참조 찾기
- [ ] 스프라이트 렌더링 함수
- [ ] 화면 업데이트 루틴

### 데이터 구조
- [ ] 스프라이트 헤더 구조
- [ ] 레벨 데이터 구조
- [ ] 적 AI 데이터 구조
- [ ] 게임 상태 변수

## 🔍 고급 기법

### 1. Cross References 활용

함수/데이터 우클릭 → **References** → **Show References to**
- 어디서 이 함수를 호출하는지
- 어디서 이 데이터를 읽는지

### 2. Function Graph

**Window** → **Function Graph**
- 함수의 흐름도 보기
- 조건 분기 시각화

### 3. Byte Viewer

**Window** → **Bytes**
- Raw 바이트 데이터 보기
- 그래픽 패턴 찾기

### 4. Memory Map

**Window** → **Memory Map**
- 세그먼트 구조 보기
- 코드/데이터 영역 파악

## 📝 분석 결과 기록

찾은 내용을 문서화:

```markdown
## 발견한 함수들

### 파일 I/O
- `0x1A60`: open_file - 파일 열기
- `0x1ACA`: read_file - 파일 읽기
- `0x1B12`: close_file - 파일 닫기

### 압축
- `0x2DE0`: decompress_lzw - LZW 압축 해제
- `0x2D0A`: check_signature - 0x1F9D 확인

### 그래픽
- `0x3343`: draw_sprite - 스프라이트 그리기
- `0x3526`: update_screen - 화면 업데이트
- `0x37A0`: load_sprite - 스프라이트 로드

### 데이터 구조
- `0x5000`: sprite_buffer - 스프라이트 버퍼
- `0x6000`: level_data - 레벨 데이터
```

## 🎯 다음 단계

Ghidra로 함수들을 찾았으면:

1. **압축 해제 루틴 추출**
   - 디컴파일된 C 코드 복사
   - Python/C로 재구현
   - 모든 .EG1 파일 압축 해제

2. **스프라이트 구조 파악**
   - 헤더 크기
   - 픽셀 포맷
   - 팔레트 정보

3. **스프라이트 추출기 작성**
   ```python
   def extract_sprite(data):
       width = struct.unpack('<H', data[0:2])[0]
       height = struct.unpack('<H', data[2:4])[0]
       pixels = data[8:]
       return width, height, pixels
   ```

4. **PNG 변환기 작성**
   - PIL/Pillow 사용
   - CGA 팔레트 적용
   - PNG로 저장

## 🛠️ 유용한 단축키

```
G - Go to address (주소로 이동)
L - Edit Label (레이블 편집)
; - Add comment (주석 추가)
Ctrl+F - Find (검색)
Ctrl+Shift+E - Set Equate (상수 이름 설정)
F - Create Function (함수 생성)
D - Define Data (데이터 타입 정의)
```

## 💡 팁

1. **자주 저장**: File → Save Project
2. **북마크 사용**: 중요한 위치 북마크
3. **스냅샷**: Edit → Take Snapshot (분석 백업)
4. **스크립트**: Python으로 반복 작업 자동화

## 🚨 주의사항

1. **시간 소요**: 완전 분석은 수일 걸릴 수 있음
2. **인내심**: DOS 어셈블리는 복잡함
3. **점진적 접근**: 한 번에 모든 걸 이해하려 하지 말기
4. **문서화**: 찾은 내용 바로 기록하기

---

지금 시작해보자!

```bash
# Ghidra 실행
ghidraRun
```

화면에 Ghidra 창 뜨면 알려줘!
