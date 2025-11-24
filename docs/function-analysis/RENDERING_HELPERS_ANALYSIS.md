# 렌더링 헬퍼 함수 분석 (0x18c6 테이블)

**작성일**: 2025-11-24
**Phase**: 4.6 완료 후속
**분석 함수**: 5개 (FUN_1000_48e4, _8139, _810f, _5864, _591d)

---

## 🎯 개요

Phase 4.6에서 복구한 나머지 5개 렌더링 헬퍼 함수의 완전한 분석입니다. 이 함수들은 0x18c6 렌더링 점프 테이블에서 파라미터 변환, 화면 버퍼 관리, 타일맵 처리를 담당합니다.

---

## 📊 0x18c6 점프 테이블 전체 구조

| 인덱스 | 주소 | 함수 | 카테고리 | 용도 |
|--------|------|------|----------|------|
| **[0]** | 0x48e4 | FUN_1000_48e4 | 파라미터 | 렌더링 파라미터 변환 |
| [1] | 0x81c6 | FUN_1000_81c6 | 스크롤 | ⬇️ DOWN |
| [2] | 0x822e | FUN_1000_822e | 스크롤 | ⬆️ UP |
| [3] | 0x827b | FUN_1000_827b | 스크롤 | ➡️ RIGHT |
| [4] | 0x82f8 | FUN_1000_82f8 | 스크롤 | ⬅️ LEFT |
| **[5]** | 0x8139 | FUN_1000_8139 | 화면 버퍼 | 조건부 복사 |
| **[6]** | 0x810f | FUN_1000_810f | 화면 버퍼 | 전체 업데이트 (반복) |
| **[7]** | 0x5864 | FUN_1000_5864 | 타일맵 | 타일맵 변환 |
| **[8]** | 0x591d | FUN_1000_591d | 그리기 | 패턴 fill |
| [9-29] | ... | (21개 미분석) | 렌더링 | 추가 헬퍼들 |

---

## 🔍 상세 분석

### 1. FUN_1000_48e4 - 렌더링 파라미터 변환

**주소**: 1000:48e4
**크기**: 90 bytes
**인덱스**: 0x18c6[0]
**역할**: 렌더링 전 파라미터 전처리

#### 코드
```c
void FUN_1000_48e4(
    undefined2 param_1,
    undefined2 param_2,
    undefined2 param_3,
    undefined2 *param_4   // 출력 버퍼
) {
    undefined2 *unaff_SI;  // 입력 파라미터 포인터

    // 1. 입력 파라미터 복사 (0x4640 ~ 0x464c, 7 words = 14 bytes)
    *(undefined2 *)0x4640 = *unaff_SI;
    *(undefined2 *)0x4642 = unaff_SI[1];
    *(undefined2 *)0x4644 = unaff_SI[2];
    *(undefined2 *)0x4646 = unaff_SI[3];
    *(undefined2 *)0x4648 = unaff_SI[4];
    *(undefined2 *)0x464a = unaff_SI[5];
    *(undefined2 *)0x464c = unaff_SI[6];

    // 2. 변환 함수 호출
    func_0x00014a0d(unaff_SI + 7);  // 추가 파라미터 처리
    func_0x0001496e();              // 변환 1
    func_0x0001493e();              // 변환 2
    func_0x0001493e();              // 변환 3 (반복)

    // 3. 조건부 업데이트
    if (*(int *)0x4656 != 0 || *(int *)0x4658 != 0) {
        *(int *)0x4662 = *(int *)0x4662 + *(int *)0x4660;
    }

    // 4. 추가 변환
    func_0x0001496e();

    // 5. 출력 파라미터 쓰기 (0x464e ~ 0x465e, 9 words = 18 bytes)
    *param_4 = *(undefined2 *)0x464e;
    param_4[1] = *(undefined2 *)0x4650;
    param_4[2] = *(undefined2 *)0x4652;
    param_4[3] = *(undefined2 *)0x4654;
    param_4[4] = *(undefined2 *)0x4656;
    param_4[5] = *(undefined2 *)0x4658;
    param_4[6] = *(undefined2 *)0x465a;
    param_4[7] = *(undefined2 *)0x465c;
    param_4[8] = *(undefined2 *)0x465e;
}
```

#### 메모리 레이아웃

**입력 버퍼** (0x4640 ~ 0x464c, 14 bytes):
```
0x4640: param[0]
0x4642: param[1]
0x4644: param[2]
0x4646: param[3]
0x4648: param[4]
0x464a: param[5]
0x464c: param[6]
```

**중간 버퍼** (0x464e ~ 0x465e, 18 bytes):
```
0x464e: result[0]
0x4650: result[1]
0x4652: result[2]
0x4654: result[3]
0x4656: result[4]  ← 조건 체크
0x4658: result[5]  ← 조건 체크
0x465a: result[6]
0x465c: result[7]
0x465e: result[8]
```

**작업 변수**:
```
0x4660: delta 값
0x4662: 누적 값 (조건부 업데이트)
```

#### 처리 파이프라인
```
Input (SI register, 7+ words)
    ↓
[Copy to 0x4640]
    ↓
[func_0x00014a0d] ← 추가 파라미터
    ↓
[func_0x0001496e] ← 변환 1
    ↓
[func_0x0001493e] ← 변환 2
    ↓
[func_0x0001493e] ← 변환 3
    ↓
[Conditional add]  ← if (4656 || 4658) { 4662 += 4660 }
    ↓
[func_0x0001496e] ← 추가 변환
    ↓
[Copy from 0x464e]
    ↓
Output (param_4, 9 words)
```

#### 추정 용도
- **좌표 변환**: 월드 좌표 → 화면 좌표
- **스크롤 보정**: X/Y 스크롤 오프셋 적용
- **클리핑**: 화면 경계 체크
- **스프라이트 메타데이터**: 크기, 플립, 팔레트 정보

---

### 2. FUN_1000_8139 - 화면 버퍼 조건부 복사

**주소**: 1000:8139
**크기**: 84 bytes
**인덱스**: 0x18c6[5]
**역할**: VRAM → 화면 버퍼 복사 (CGA 인터레이스)

#### 코드
```c
void FUN_1000_8139(void) {
    undefined2 *puVar4;  // VRAM 소스
    undefined2 *puVar5;  // 화면 버퍼 대상
    int iVar3;

    // 1. VRAM 소스 포인터
    puVar4 = (undefined2 *)*(undefined2 *)0xf38c;
    puVar5 = (undefined2 *)0x32a;  // 기본: 짝수 라인 버퍼

    // 2. 상단 경계 체크
    if (0x9fU - *(int *)0xf38e >> 1 != 0) {
        func_0x0001818e();  // 상단 영역 처리
    }

    // 3. 홀수/짝수 라인 분기
    if ((*(uint *)0xf38e & 1) == 0) {
        // 짝수 라인: 0x32a → EVEN scanlines
        for (iVar3 = 0x1e; iVar3 != 0; iVar3 = iVar3 + -1) {
            puVar2 = puVar5;
            puVar5 = puVar5 + 1;
            puVar1 = puVar4;
            puVar4 = puVar4 + 1;
            *puVar2 = *puVar1;  // 60 bytes 복사
        }
        func_0x000181a4();
    } else {
        // 홀수 라인: 0x22ee → ODD scanlines
        func_0x000181a4();
        puVar5 = (undefined2 *)0x22ee;
        for (iVar3 = 0x1e; iVar3 != 0; iVar3 = iVar3 + -1) {
            puVar2 = puVar5;
            puVar5 = puVar5 + 1;
            puVar1 = puVar4;
            puVar4 = puVar4 + 1;
            *puVar2 = *puVar1;  // 60 bytes 복사
        }
    }

    // 4. 하단 경계 체크
    if (*(uint *)0xf38e >> 1 != 0) {
        func_0x0001818e();  // 하단 영역 처리
    }
}
```

#### CGA 인터레이스 구조
```
CGA 320×200 메모리:
  Bank 0 (0xB8000): 짝수 scanlines (0, 2, 4, ... 198)
  Bank 1 (0xBA000): 홀수 scanlines (1, 3, 5, ... 199)

화면 버퍼:
  0x022ee (8,942):  홀수 라인 버퍼
  0x0032a (810):    짝수 라인 버퍼
```

#### 메모리 업데이트
```
if (scanline & 1 == 0):  # 짝수
    VRAM → 0x32a (60 bytes)
else:                     # 홀수
    VRAM → 0x22ee (60 bytes)
```

#### 동작 원리
1. **Scanline 오프셋 체크**: 0xf38e (현재 scanline)
2. **홀짝 판정**: scanline & 1
3. **버퍼 선택**:
   - 짝수 → 0x32a
   - 홀수 → 0x22ee
4. **60 bytes 복사**: 30 words (0x1e 반복)
5. **경계 처리**: 상단/하단 영역 별도 처리

---

### 3. FUN_1000_810f - 화면 전체 업데이트 (반복)

**주소**: 1000:810f
**크기**: 38 bytes
**인덱스**: 0x18c6[6]
**역할**: 전체 VRAM 범위 순회 업데이트

#### 코드
```c
void FUN_1000_810f(void) {
    int iVar1;
    uint uVar2;
    bool bVar3;
    uint in_stack_00000000;  // 스택 변수 (루프 카운터)

    iVar1 = *(int *)0xf394;  // 평면 오프셋
    uVar2 = 0xb0d0;          // 시작 주소

    do {
        // 1. 수직 스크롤 업데이트
        func_0x00018351(uVar2);

        // 2. 평면 오프셋 조정
        if (0x3f < iVar1) {  // > 63
            iVar1 = iVar1 + -0x40;  // -64
        }

        // 3. 수직 스크롤 완료
        func_0x00018391();

        // 4. 다음 반복
        bVar3 = in_stack_00000000 < 0xd650;
        uVar2 = in_stack_00000000;
        in_stack_00000000 = 0x812e;

    } while (bVar3);  // 0xb0d0 ~ 0xd650
}
```

#### VRAM 범위
```
시작: 0xb0d0 (45,264)
끝:   0xd650 (54,864)
범위: 9,600 bytes

CGA 전체 VRAM:
  0xB8000 ~ 0xBBFFF (16,384 bytes)

처리 범위 (세그먼트 오프셋):
  0xb0d0 ~ 0xd650 (9,600 bytes) ≈ 60% VRAM
```

#### 동작 원리
1. **VRAM 범위 순회**: 0xb0d0 → 0xd650
2. **각 위치마다**:
   - func_0x00018351(주소) 호출
   - 평면 오프셋 조정
   - func_0x00018391() 호출
3. **전체 화면 갱신**: 스크롤 후 전체 다시 그리기

#### 추정 사용 시점
- 스테이지 전환
- 대량 스크롤 후
- 화면 전체 리프레시 필요 시

---

### 4. FUN_1000_5864 - 타일맵 변환

**주소**: 1000:5864
**크기**: 165 bytes
**인덱스**: 0x18c6[7]
**역할**: 타일맵 데이터를 화면 버퍼로 변환

#### 코드
```c
void FUN_1000_5864(void) {
    int in_AX;       // 모드 (1 or 2)
    int unaff_DI;    // 오프셋 인덱스
    undefined1 *puVar6;  // 출력 버퍼
    uint *puVar4;        // 입력 소스
    int iVar2;

    // 1. 출력 버퍼 포인터
    puVar6 = (undefined1 *)(unaff_DI * 2 + 0x1c70);
    iVar2 = 8;  // 8 iterations

    // 2. 스택 포인터 저장
    *(undefined1 **)0x5634 = &stack0xfffa;
    *(undefined2 *)0x5632 = unaff_SS;

    // 3. 모드별 분기
    if (in_AX == 2) {
        // === 모드 2 ===
        puVar4 = (uint *)*(undefined2 *)0x1dc5;  // 소스 포인터

        do {
            // 6 + 6 words 복사 (12 words per iteration)
            *puVar6 = *(undefined1 *)((*puVar4 & 0xff) - 0x9f8);
            puVar6[1] = *(undefined1 *)((puVar4[1] & 0xff) - 0x9f8);
            puVar6[2] = *(undefined1 *)((puVar4[2] & 0xff) - 0x9f8);
            puVar6[3] = *(undefined1 *)((puVar4[3] & 0xff) - 0x9f8);
            puVar6[4] = *(undefined1 *)((puVar4[4] & 0xff) - 0x9f8);
            puVar6[5] = *(undefined1 *)((puVar4[5] & 0xff) - 0x9f8);

            // 다른 평면 (offset +0x2000)
            puVar6[0x2000] = *(undefined1 *)((puVar4[6] & 0xff) - 0x9f8);
            puVar6[0x2001] = *(undefined1 *)((puVar4[7] & 0xff) - 0x9f8);
            puVar6[0x2002] = *(undefined1 *)((puVar4[8] & 0xff) - 0x9f8);
            puVar6[0x2003] = *(undefined1 *)((puVar4[9] & 0xff) - 0x9f8);
            puVar6[0x2004] = *(undefined1 *)((puVar4[10] & 0xff) - 0x9f8);
            puVar6[0x2005] = *(undefined1 *)((puVar4[11] & 0xff) - 0x9f8);

            puVar4 = puVar4 + 0xc;  // +12 words
            puVar6 = puVar6 + 0x50;  // +80 bytes (1 scanline)
            iVar2 = iVar2 + -1;
        } while (iVar2 != 0);
    } else {
        // === 모드 1 ===
        puVar4 = (uint *)*(undefined2 *)0x1d25;  // 소스 포인터

        do {
            // 5 + 5 words 복사 (10 words per iteration)
            *puVar6 = *(undefined1 *)((*puVar4 & 0xff) - 0xaf8);
            puVar6[1] = *(undefined1 *)((puVar4[1] & 0xff) - 0xaf8);
            puVar6[2] = *(undefined1 *)((puVar4[2] & 0xff) - 0xaf8);
            puVar6[3] = *(undefined1 *)((puVar4[3] & 0xff) - 0xaf8);
            puVar6[4] = *(undefined1 *)((puVar4[4] & 0xff) - 0xaf8);

            // 다른 평면 (offset +0x2000)
            puVar6[0x2000] = *(undefined1 *)((puVar4[5] & 0xff) - 0xaf8);
            puVar6[0x2001] = *(undefined1 *)((puVar4[6] & 0xff) - 0xaf8);
            puVar6[0x2002] = *(undefined1 *)((puVar4[7] & 0xff) - 0xaf8);
            puVar6[0x2003] = *(undefined1 *)((puVar4[8] & 0xff) - 0xaf8);
            puVar6[0x2004] = *(undefined1 *)((puVar4[9] & 0xff) - 0xaf8);

            puVar4 = puVar4 + 10;    // +10 words
            puVar6 = puVar6 + 0x50;  // +80 bytes
            iVar2 = iVar2 + -1;
        } while (iVar2 != 0);
    }
}
```

#### 메모리 레이아웃

**모드 1 소스**: 0x1d25 (7,461)
**모드 2 소스**: 0x1dc5 (7,621)
**출력 버퍼**: 0x1c70 + DI*2

**변환 오프셋**:
- 모드 1: -0xaf8 (-2,808)
- 모드 2: -0x9f8 (-2,552)

#### 데이터 구조
```
8 반복 × 80 bytes = 640 bytes 출력
8 반복 × 10~12 words = 80~96 words 입력

출력: 8 scanlines
입력: 타일맵 인덱스 배열
```

#### 동작 원리
1. **타일 인덱스 읽기**: puVar4[i] & 0xff
2. **오프셋 변환**: index - 0xaf8/0x9f8
3. **주소 계산**: *(undefined1 *)(converted_index)
4. **버퍼 쓰기**:
   - 첫 5~6 bytes → 현재 평면
   - 다음 5~6 bytes → +0x2000 평면
5. **다음 scanline**: +0x50 (80 bytes)

#### 추정 용도
- **배경 타일맵 렌더링**: PC1 파일 → 화면
- **타일 인덱스 → 픽셀 변환**: 간접 참조
- **8 scanlines 블록**: 타일 높이 8 pixels

---

### 5. FUN_1000_591d - 패턴 Fill / 그리기

**주소**: 1000:591d
**크기**: 124 bytes
**인덱스**: 0x18c6[8]
**역할**: 화면 영역에 패턴 fill (배경, 테두리 등)

#### 코드
```c
void FUN_1000_591d(void) {
    int in_AX;       // Width 파라미터
    int in_CX;       // Pattern 선택
    int unaff_DI;    // Offset 인덱스
    uint uVar4;      // Fill 패턴
    uint *puVar5;    // 출력 버퍼
    int iVar2, iVar3;
    bool bVar7;

    // 1. 패턴 선택
    uVar4 = 0x5555;  // 기본: 01010101 01010101
    if (in_CX != 0x900) {
        uVar4 = 0xaaaa;  // 대체: 10101010 10101010
    }
    if (in_AX == 0) {
        uVar4 = 0;  // 빈 영역
    }
    uVar4 = uVar4 | 0xc0;  // 상위 bits 설정

    // 2. 출력 버퍼 설정
    iVar3 = unaff_DI * 2;
    puVar5 = (uint *)(iVar3 + 0x1d60);
    iVar2 = 6;  // 6 반복
    bVar7 = false;

    // 3. 메인 fill 루프
    do {
        // 8개 위치에 동시 쓰기
        *puVar5 = uVar4;
        puVar5[0x1000] = uVar4;  // +4096 words
        puVar5[0x28] = uVar4;    // +40 words
        puVar5[0x1028] = uVar4;
        puVar5[0x50] = uVar4;    // +80 words
        puVar5[0x1050] = uVar4;
        puVar5[0x78] = uVar4;    // +120 words
        puVar5[0x1078] = uVar4;

        // 4. Width 감소
        in_AX = in_AX + -1;
        if (bVar7 || in_AX == 0) {
            uVar4 = 0xc0;  // 테두리 패턴
        }

        bVar7 = (uint *)0xfffd < puVar5;
        puVar5 = puVar5 + 1;
        iVar2 = iVar2 + -1;
    } while (iVar2 != 0);

    // 5. 추가 영역 fill (0xffff)
    puVar6 = (undefined2 *)(iVar3 + 0x3d10);
    for (iVar2 = 5; iVar2 != 0; iVar2 = iVar2 + -1) {
        *puVar6 = 0xffff;
        puVar6 = puVar6 + 1;
    }
    *(undefined1 *)puVar6 = 0xc0;

    // 6. 추가 영역 fill (0xffff)
    puVar6 = (undefined2 *)(iVar3 + 0x1ea0);
    for (iVar3 = 5; iVar3 != 0; iVar3 = iVar3 + -1) {
        *puVar6 = 0xffff;
        puVar6 = puVar6 + 1;
    }
    *(undefined1 *)puVar6 = 0xc0;
}
```

#### 패턴 정의
```
CX == 0x900:  0x5555 | 0xc0 = 0x55d5
CX != 0x900:  0xaaaa | 0xc0 = 0xaac0
AX == 0:      0x0000 | 0xc0 = 0x00c0

Binary:
  0x5555 = 0101010101010101  (체크보드 1)
  0xaaaa = 1010101010101010  (체크보드 2)
  0x0000 = 0000000000000000  (빈 영역)
```

#### 메모리 레이아웃

**메인 영역** (0x1d60 + DI*2):
```
Base + 0x0000: 주 영역
Base + 0x1000: +4096 words (8,192 bytes)
Base + 0x0028: +40 words (80 bytes)
Base + 0x1028: +40 words (80 bytes)
Base + 0x0050: +80 words (160 bytes)
Base + 0x1050: +80 words (160 bytes)
Base + 0x0078: +120 words (240 bytes)
Base + 0x1078: +120 words (240 bytes)
```

**추가 영역 1** (0x3d10 + DI*2):
- 5 words = 10 bytes, fill with 0xffff

**추가 영역 2** (0x1ea0 + DI*2):
- 5 words = 10 bytes, fill with 0xffff

#### 8개 위치 의미
```
8 scanlines 동시 fill:
  +0x00: scanline 0
  +0x28: scanline 1 (40 words = 80 bytes)
  +0x50: scanline 2
  +0x78: scanline 3
  +0x1000: 다른 평면 scanline 0
  +0x1028: 다른 평면 scanline 1
  +0x1050: 다른 평면 scanline 2
  +0x1078: 다른 평면 scanline 3
```

#### 동작 원리
1. **패턴 선택**: CX, AX 파라미터 기반
2. **6 반복**: 6 words = 12 bytes width
3. **8 위치 동시**: 4 scanlines × 2 planes
4. **테두리 처리**: Width 끝에서 패턴 변경
5. **추가 영역**: 0xffff로 fill (경계 또는 특수 영역)

#### 추정 용도
- **배경 패턴**: 체크보드, 빈 영역
- **테두리 그리기**: UI 경계선
- **영역 초기화**: 화면 클리어

---

## 🧩 통합 호출 그래프

### 렌더링 디스패처 (FUN_1000_48e0)
```
FUN_1000_48e0 (렌더링 디스패처)
    │
    ├─[0]─> FUN_1000_48e4 (파라미터 변환)
    │           ├─> func_0x00014a0d()
    │           ├─> func_0x0001496e() × 2
    │           └─> func_0x0001493e() × 2
    │
    ├─[1-4]─> 스크롤 함수 (UP/DOWN/LEFT/RIGHT)
    │
    ├─[5]─> FUN_1000_8139 (화면 버퍼 복사)
    │           ├─> func_0x0001818e() (경계 처리)
    │           └─> func_0x000181a4() (버퍼 완료)
    │
    ├─[6]─> FUN_1000_810f (전체 업데이트)
    │           ├─> func_0x00018351(주소) (반복)
    │           └─> func_0x00018391() (반복)
    │
    ├─[7]─> FUN_1000_5864 (타일맵 변환)
    │           └─> 타일 인덱스 → 픽셀 변환
    │
    └─[8]─> FUN_1000_591d (패턴 fill)
                └─> 체크보드/빈 영역 그리기
```

### 헬퍼 함수 목록

| 함수 주소 | 호출처 | 추정 용도 |
|-----------|--------|-----------|
| **func_0x00014a0d** | 48e4 | 추가 파라미터 처리 |
| **func_0x0001496e** | 48e4 | 좌표/파라미터 변환 |
| **func_0x0001493e** | 48e4 | 좌표/파라미터 변환 |
| **func_0x0001818e** | 8139 | 화면 경계 처리 |
| **func_0x000181a4** | 8139 | 버퍼 복사 완료 |
| **func_0x00018351** | 810f, 스크롤 | 수직 스크롤 업데이트 |
| **func_0x00018391** | 810f, 스크롤 | 수직 스크롤 완료 |
| **func_0x000183bd** | 스크롤 | 수평 스크롤 업데이트 |
| **func_0x00018455** | 스크롤 | 수평 스크롤 완료 |

---

## 💡 핵심 발견

### 1. 파라미터 변환 시스템
- **0x4640 버퍼**: 입력 파라미터 (7 words)
- **0x464e 버퍼**: 출력 결과 (9 words)
- **변환 파이프라인**: 4-5 단계 변환
- **조건부 업데이트**: 특정 조건에서 누적값 변경

### 2. 화면 버퍼 이중화
- **홀수 라인**: 0x22ee
- **짝수 라인**: 0x32a
- **CGA 인터레이스**: 홀짝 분리 처리
- **60 bytes 복사**: 30 words

### 3. 타일맵 간접 참조
- **타일 인덱스**: 8-bit 값
- **오프셋 변환**: -0xaf8 / -0x9f8
- **주소 계산**: *(index - offset)
- **이중 평면**: +0x2000 오프셋

### 4. 패턴 기반 Fill
- **3가지 패턴**: 0x5555, 0xaaaa, 0x0000
- **8 위치 동시**: 4 scanlines × 2 planes
- **테두리 자동**: Width 끝에서 0xc0

---

## 🔧 C++ 재구현 가이드

### 구조체 정의
```cpp
// 렌더링 파라미터
struct RenderParams {
    int16_t input[7];   // 0x4640
    int16_t result[9];  // 0x464e
    int16_t delta;      // 0x4660
    int16_t accumulator; // 0x4662
};

// 화면 버퍼
struct ScreenBuffers {
    uint8_t odd_lines[8192];   // 0x22ee
    uint8_t even_lines[8192];  // 0x32a
};

// 타일맵
struct TilemapConverter {
    uint16_t *source_mode1;  // 0x1d25
    uint16_t *source_mode2;  // 0x1dc5
    uint8_t *output_buffer;  // 0x1c70 + offset
};

// 패턴 Fill
struct PatternFiller {
    uint16_t pattern;
    int width;
    int offset;
};
```

### 함수 정의
```cpp
class RenderingHelpers {
public:
    // 파라미터 변환
    void transformParams(
        const int16_t *input,
        int16_t *output
    );

    // 화면 버퍼 복사
    void copyScreenBuffer(
        const uint8_t *vram,
        int scanline_offset
    );

    // 전체 업데이트
    void updateFullScreen();

    // 타일맵 변환
    void convertTilemap(
        int mode,  // 1 or 2
        int offset_index
    );

    // 패턴 fill
    void fillPattern(
        int width,
        int pattern_select,
        int offset_index
    );

private:
    RenderParams params;
    ScreenBuffers buffers;
    TilemapConverter tilemap;
};
```

---

## 📊 성능 분석

### 시간 복잡도
- **파라미터 변환**: O(1) - 고정 크기
- **화면 버퍼 복사**: O(n) - 60 bytes
- **전체 업데이트**: O(n) - 9,600 bytes
- **타일맵 변환**: O(n) - 640 bytes
- **패턴 fill**: O(w×h) - 6×8 = 48 words

### 메모리 사용
- **파라미터 버퍼**: 32 bytes
- **화면 버퍼**: 16 KB (홀짝 분리)
- **타일맵 버퍼**: 640+ bytes
- **작업 버퍼**: 수백 bytes

---

## 🎓 역사적 의의

### 1988년 최적화 기법

1. **파라미터 버퍼 재사용**: 고정 메모리 영역
2. **CGA 인터레이스 활용**: 홀짝 분리로 성능 향상
3. **간접 참조**: 타일맵 → 픽셀 변환 효율화
4. **패턴 기반**: 반복 패턴으로 메모리 절약
5. **배치 처리**: 8개 위치 동시 업데이트

이는 **제한된 8088 CPU와 CGA 하드웨어를 극한까지 활용**한 사례입니다.

---

**분석 완료일**: 2025-11-24
**다음 분석**: 0x18c6[9-29] 나머지 21개 함수
**참고 문서**: [RENDERING_SYSTEM.md](../technical/RENDERING_SYSTEM.md), [SCROLL_SYSTEM_ANALYSIS.md](SCROLL_SYSTEM_ANALYSIS.md)
