# Double Dragon LZW 압축 해제 완전 분석

**날짜**: 2025-11-24
**분석 완료**: 전체 LZW 압축 해제 체인

---

## 함수 호출 체인

```
FUN_1000_5fe0  (매직 넘버 체크: 0x1F 0x9D)
    ↓
FUN_1000_5ff3  (메인 LZW 디코더 루프)
    ↓
    ├─ FUN_1000_604e  (초기화: bits_to_read=9, bits_available=0)
    ├─ FUN_1000_6091  (비트 읽기: MSB-first)
    └─ FUN_1000_605b  (LZW 코드 디코드)
```

---

## 전역 변수 (데이터 세그먼트)

| 주소 | 이름 | 타입 | 용도 |
|------|------|------|------|
| 0x6534 | bits_to_read | int (16bit) | 읽을 비트 수 |
| 0x6536 | remaining_bytes | int (16bit) | 남은 입력 바이트 |
| 0x6538 | bits_available | int (16bit) | 버퍼에 남은 비트 수 |
| 0x653a | bit_buffer | char (8bit) | 비트 읽기 버퍼 |

---

## 함수별 상세 분석

### 1. FUN_1000_5fe0 (매직 넘버 체크)

**목적**: LZW 파일인지 확인

```c
void FUN_1000_5fe0(void) {
  int *unaff_SI;  // 입력 데이터 포인터

  if (*unaff_SI != -0x62e1) {  // 0x9D1F (little-endian 0x1F9D)
    return;  // 매직 넘버 불일치
  }
  FUN_1000_5ff3();  // LZW 디코더 실행
}
```

**매직 넘버**: `0x1F 0x9D` (Unix compress 표준)

---

### 2. FUN_1000_604e (초기화)

**목적**: LZW 디코더 상태 초기화

```c
void FUN_1000_604e(void) {
  *(int *)0x6538 = 0;   // bits_available = 0
  *(int *)0x6534 = 9;   // bits_to_read = 9 (초기 코드 크기)
}
```

**초기 상태**:
- 비트 버퍼 비어있음
- 9비트 코드부터 시작 (표준 LZW)

---

### 3. FUN_1000_5ff3 (메인 LZW 디코더)

**목적**: LZW 압축 해제 메인 루프

```c
void FUN_1000_5ff3(void) {
  int iVar1;
  undefined2 *unaff_SI;  // 딕셔너리 베이스 포인터
  undefined2 unaff_DI;   // 출력 포인터

  // 입력 크기 설정
  *(int *)0x6536 = unaff_SI[1] + 1;  // remaining_bytes

  // 초기화
  FUN_1000_604e();

  while (true) {
    // 딕셔너리 엔트리 저장
    *unaff_SI = unaff_DI;
    unaff_SI = unaff_SI + 1;

    // 0x100 (256) 코드 스킵 (클리어 코드 아님, 단순 스킵)
    while (iVar1 = FUN_1000_6091(), iVar1 == 0x100) {
      *(int *)0x6534 = *(int *)0x6534 + 1;  // bits_to_read++
    }

    // 입력 끝 체크
    if (*(int *)0x6536 == 0) {
      return;
    }

    // LZW 코드 디코드
    FUN_1000_605b();

    // 다시 0x100 스킵
    while (iVar1 = FUN_1000_6091(), iVar1 == 0x100) {
      *(int *)0x6534 = *(int *)0x6534 + 1;
    }

    if (*(int *)0x6536 == 0) break;

    FUN_1000_605b();
  }
}
```

**핵심 로직**:
1. 코드 읽기 (`FUN_1000_6091`)
2. 코드 256이면 스킵하고 비트 크기 증가
3. 코드 디코드 (`FUN_1000_605b`)
4. 딕셔너리에 엔트리 추가 (`*unaff_SI = unaff_DI`)

---

### 4. FUN_1000_6091 (비트 읽기)

**목적**: MSB-first 방식으로 가변 비트 읽기

```c
uint FUN_1000_6091(void) {
  int *piVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  char cVar5;
  char *unaff_SI;  // 입력 데이터 포인터
  bool bVar6;

  uVar2 = 0;  // 결과
  iVar4 = *(int *)0x6538;  // bits_available
  cVar5 = *(char *)0x653a; // bit_buffer
  iVar3 = *(int *)0x6534;  // bits_to_read

  do {
    iVar4 = iVar4 + -1;  // bits_available--

    if (iVar4 < 0) {
      // 버퍼 리필
      cVar5 = *unaff_SI;
      unaff_SI = unaff_SI + 1;
      iVar4 = 7;  // 8비트 로드했으므로 7개 남음

      piVar1 = (int *)0x6536;
      *piVar1 = *piVar1 + -1;  // remaining_bytes--
      if (*piVar1 == 0) break;  // 입력 끝
    }

    bVar6 = cVar5 < '\0';  // MSB 추출 (비트 7)
    cVar5 = cVar5 << 1;    // 왼쪽 시프트
    uVar2 = uVar2 << 1 | (uint)bVar6;  // 결과에 비트 추가

    iVar3 = iVar3 + -1;  // bits_to_read--
  } while (iVar3 != 0);

  *(int *)0x6538 = iVar4;    // bits_available 저장
  *(char *)0x653a = cVar5;   // bit_buffer 저장

  return uVar2;
}
```

**비트 읽기 방식**:
- **MSB-first**: 각 바이트의 비트 7부터 읽음
- `cVar5 < '\0'`: MSB가 1인지 체크
- `cVar5 << 1`: 다음 비트를 MSB 위치로 이동
- `uVar2 << 1 | bit`: 결과에 왼쪽부터 채움

**예시**:
```
바이트: 0x3F = 0011 1111
       비트7(0) → 비트6(0) → ... → 비트0(1)
```

---

### 5. FUN_1000_605b (LZW 코드 디코드)

**목적**: LZW 코드를 실제 데이터로 변환

```c
void FUN_1000_605b(void) {
  undefined2 *puVar1;
  undefined2 *puVar2;
  int in_AX;  // LZW 코드 (파라미터)
  undefined2 *puVar3;
  uint uVar4;
  int unaff_BP;  // 딕셔너리 베이스 포인터
  undefined2 *puVar5;
  undefined2 *unaff_DI;  // 출력 포인터

  if (in_AX < 0x100) {
    // 리터럴 바이트 (0-255)
    *(char *)unaff_DI = (char)in_AX;
  }
  else {
    // 딕셔너리 참조 (256+)
    // 딕셔너리 인덱스 = (in_AX - 0x101) = (code - 257)
    puVar3 = (undefined2 *)((in_AX + -0x101) * 2 + unaff_BP);
    puVar5 = (undefined2 *)*puVar3;        // 시작 포인터
    uVar4 = puVar3[1] - (int)puVar5;       // 길이

    // 바이트 복사 (홀수 길이 처리)
    if ((uVar4 & 1) != 0) {
      puVar1 = puVar5;
      puVar5 = (undefined2 *)((int)puVar5 + 1);
      puVar2 = unaff_DI;
      unaff_DI = (undefined2 *)((int)unaff_DI + 1);
      *(undefined1 *)puVar2 = *(undefined1 *)puVar1;
    }

    // 워드 단위 복사 (최적화)
    for (uVar4 = uVar4 >> 1; uVar4 != 0; uVar4 = uVar4 - 1) {
      puVar2 = unaff_DI;
      unaff_DI = unaff_DI + 1;
      puVar1 = puVar5;
      puVar5 = puVar5 + 1;
      *puVar2 = *puVar1;  // 2바이트 복사
    }
  }
}
```

**딕셔너리 구조**:
```
딕셔너리는 [시작포인터, 끝포인터] 쌍의 배열
BP + (code - 257) * 4:
  [0]: 시작 포인터 (2 bytes)
  [2]: 끝 포인터 (2 bytes)
```

**코드 해석**:
- `code < 256`: 리터럴 바이트 출력
- `code >= 257`: 딕셔너리 인덱스 `code - 257`의 시퀀스 출력
- `code == 256`: **스킵됨** (메인 루프에서 처리)

---

## 핵심 발견

### 1. 코드 256의 특별한 처리

표준 LZW에서 256은 클리어 코드이지만, Double Dragon은:
- **메인 루프에서 스킵**
- 비트 크기만 증가시킴
- 딕셔너리 리셋 안 함

### 2. 딕셔너리 인덱싱

- 코드 257 = 딕셔너리[0]
- 코드 258 = 딕셔너리[1]
- ...

### 3. 비트 크기 증가

코드 256을 만날 때마다 `bits_to_read++`:
- 9 → 10 → 11 → 12 → 13 비트로 증가

### 4. MSB-first 비트 읽기

일반적인 LSB-first가 아닌 **MSB-first** 방식 사용

---

## C 재구현 전략

### 필요한 구성요소:

```c
// 전역 변수
int bits_to_read = 9;
int remaining_bytes = 0;
int bits_available = 0;
unsigned char bit_buffer = 0;

// 입력/출력 포인터
unsigned char *input_ptr;
unsigned char *output_ptr;

// 딕셔너리 (최대 8192 엔트리, 13비트)
struct {
    unsigned char *start;
    unsigned char *end;
} dictionary[8192];

int dict_size = 0;
```

### 메인 함수:

```c
void decompress_lzw(
    unsigned char *input, int input_size,
    unsigned char *output, int *output_size
) {
    // 매직 체크
    if (input[0] != 0x1F || input[1] != 0x9D) return;

    // 초기화
    init_decoder();

    // 메인 루프
    while (remaining_bytes > 0) {
        int code = read_bits();

        if (code == 256) {
            bits_to_read++;
            continue;
        }

        decode_code(code);
        save_dictionary_entry();
    }
}
```

---

**다음 단계**: C 코드 구현 및 컴파일
