# Phase 4: 스프라이트 이미지 변환 - 요약 리포트

**날짜**: 2025-11-24
**상태**: 부분 완료 - 구조 분석 완료, 실제 렌더링은 미완

---

## 📊 작업 요약

### 목표
- 압축 해제된 스프라이트 데이터를 PNG 이미지로 변환
- 스프라이트 파일 포맷 완전 파악

### 달성 내용
✅ 스프라이트 파일 바이너리 구조 분석
✅ 관련 변환 함수 3개 완전 분석 (FUN_1000_0786, 0cd1, 2865)
✅ 문자열 테이블 구조 파악
✅ 초기 렌더링 시도 (48개 테스트 PNG 생성)
⏸️ 올바른 렌더링 미완성 (노이즈만 출력)

---

## 🔍 발견 사항

### 1. 스프라이트 파일 구조

**압축 해제된 파일들**:

| 파일 | 크기 | 첫 바이트 | 특징 |
|------|------|-----------|------|
| LINDA.dat | 237 bytes | 0x3D (61) | 가장 작음 |
| ABOBO.dat | 508 bytes | 0x7F (127) | 중간 크기 |
| PLAYER1.dat | 2,711 bytes | 0xC8 (200) | 가장 큼 |
| WEAPONS.dat | 980 bytes | ? | 여러 무기 프레임 |
| WILLIAM.dat | 861 bytes | ? | 플레이어2 |
| BIGBWLY.dat | 869 bytes | ? | 적 캐릭터 |

**공통 특징**:
- 첫 바이트가 파일마다 다름
- `86 C8 0B` 패턴이 PLAYER1.dat에서 반복 출현
- 바이트 분포가 다양 (추가 압축 없음)
- 텍스트 아님, 순수 바이너리 데이터

### 2. 변환 함수 분석

#### FUN_1000_0786: CGA 16-plane De-interleave

**위치**: 1000:0786
**크기**: 435 bytes

**기능**: 16개 평면으로 인터리브된 데이터를 복원

**알고리즘**:
```c
// 130회 또는 240회 루프
for (int loop = 0; loop < iterations; loop++) {
    // 64개 워드(128 bytes)를 출력
    // 16개 평면에서 각각 4개 워드씩 추출

    output[0] = input[0x000];
    output[1] = input[0x050];  // +80 워드
    output[2] = input[0x0a0];  // +160 워드
    // ...
    output[15] = input[0x4b0]; // +1200 워드

    // 16개 항목 4번 반복 = 64 워드

    // 다음 4워드로 이동
    input += 4;

    // 160 bytes마다 큰 점프
    if (processed == 160) {
        input += (0x4b4 - 4);  // +2408 bytes
        processed = 0;
    }
}
```

**평면 오프셋 (워드 단위)**:
```
0x000, 0x050, 0x0a0, 0x0f0,
0x140, 0x190, 0x1e0, 0x230,
0x280, 0x2d0, 0x320, 0x370,
0x3c0, 0x410, 0x460, 0x4b0
```

**용도**:
- 전체 화면 배경용 (*.PC1 파일)
- 작은 스프라이트에는 적용 안 됨
- 2400 bytes 단위 스트라이드

#### FUN_1000_0cd1: 비트 재배열

**위치**: 1000:0cd1
**크기**: 147 bytes

**기능**: 4개 바이트의 비트들을 재배열

**알고리즘**:
```c
// 4개 바이트 (2워드) 처리
byte0 = input[0];
byte1 = input[1];
byte2 = input[2];
byte3 = input[3];

// 각 바이트의 동일한 비트 위치를 모아서 재배열
// bit 7,6,5,4,3,2,1,0 순으로
// 4바이트 x 8비트 = 32비트를 2워드로 재구성
```

**용도**:
- CGA planar → chunky 변환
- 비트 평면 재배열

#### FUN_1000_2865: RLE 압축 해제

**위치**: 1000:2865
**크기**: 47 bytes

**기능**: PackBits 스타일 RLE 압축 해제

**알고리즘**:
```c
for (int remain = 39; remain > 0; ) {
    control_byte = *input++;

    if (control_byte == 0x80) {
        // No-op
    }
    else if (control_byte < 0) {
        // 반복 모드
        count = 1 - control_byte;
        value = *input++;
        // value를 count번 출력
        remain -= count;
    }
    else {
        // 리터럴 모드
        count = control_byte + 1;
        // input에서 count 바이트 복사
        remain -= count;
    }
}
```

**발견**:
- 디컴파일된 코드에서 이 함수를 호출하는 곳을 찾지 못함
- 스프라이트 데이터가 RLE 압축되지 않았을 가능성

### 3. 문자열 테이블 구조

**위치**: 1000:aff0 ~ 1000:b090

**발견된 문자열들**:
```
1000:aff0: WILLIAM.EG1
1000:affc: LINDA.EG1
1000:b006: ABOBO.EG1
1000:b010: PLAYER1.EG1
1000:b020: PLAYER1.EG2
1000:b028: WEAPONS.EG1
1000:b034: CHARSET.BIN
1000:b040: SPRT1.PL1
1000:b04c: SPRT2.PL1
1000:b058: SPRT1.WEP
1000:b064: SPRT1.WIL
1000:b070: SPRT1.LIN
1000:b07c: SPRT1.ABO
1000:b088: SPRT1.BOS
1000:b086: BIGBWLY.EG1
```

**특징**:
- Null-terminated 문자열들
- 코드에서 직접 참조 없음 (인덱싱 방식 사용)
- .EG1, .EG2, .PL1, .BIN 등 여러 포맷

### 4. 렌더링 시도 결과

**생성된 테스트 이미지**: 48개
- 3개 스프라이트 (LINDA, ABOBO, PLAYER1)
- 8개 폭 (32, 40, 48, 64, 80, 96, 128, 160 pixels)
- 2개 팔레트 (CGA Palette 0, Palette 1)

**렌더링 방법**:
```python
def render_sprite_simple(data, width=40, palette=CGA_PALETTE_1):
    pixels = []
    for byte in data:
        # 2 bits per pixel, MSB first
        for shift in [6, 4, 2, 0]:
            color_index = (byte >> shift) & 0x03
            pixels.append(palette[color_index])

    height = len(pixels) // width
    img = Image.new('RGB', (width, height))
    img.putdata(pixels[:width * height])
    return img
```

**결과**:
- ❌ 모든 이미지가 노이즈로 보임
- ❌ 인식 가능한 스프라이트 없음

**실패 원인 추정**:
1. 바이트 순서가 인터리브되어 있음
2. FUN_1000_0786, FUN_1000_0cd1 변환 필요
3. 헤더 구조 미파악 (첫 N바이트 스킵 필요)
4. 여러 프레임이 하나의 파일에 혼재
5. CGA 평면 구조 적용 안 됨

---

## 🔧 생성된 도구

### 1. phase4_analyze_sprite.py
- 스프라이트 데이터 통계 분석
- 바이트 분포, 반복 패턴 체크
- 헤더 필드 추정

### 2. phase4_render_sprite.py
- 간단한 2bpp 렌더러
- 여러 폭/팔레트 조합 시도
- 48개 테스트 PNG 생성

### 3. find_string_refs.py (pyghidra)
- Ghidra 프로젝트에서 문자열 참조 검색
- 성공적으로 문자열 위치 발견
- 직접 참조는 없음 (간접 접근)

### 4. analyze_string_table.py (pyghidra)
- 문자열 테이블 구조 분석
- 메모리 덤프 및 데이터 타입 체크
- 파일명 목록 완전 파악

---

## 📚 학습 내용

### CGA 그래픽 아키텍처

**Mode 4 (320x200, 4색)**:
- 2 bits per pixel
- 메모리 분리: 짝수/홀수 스캔라인
- MSB-first 비트 순서
- 4가지 색상 (팔레트 0 또는 1)

**Planar vs Chunky**:
- **Planar**: 색상 비트가 분리된 평면에 저장
- **Chunky**: 픽셀 데이터가 연속으로 저장
- Double Dragon은 planar 방식 사용

### 16-way Interleave 구조

**발견**:
- 16개 평면이 80워드(160 bytes) 간격으로 배치
- 총 1200워드(2400 bytes) 스트라이드
- 160 bytes마다 큰 점프 (2408 bytes)

**계산**:
- 160 bytes = 640 pixels (2bpp)
- 640 / 16 planes = 40 pixels/plane
- 40 pixels = 타일 폭?

### DOS 게임 파일 구조

**파일 인덱싱**:
- 문자열 테이블에 직접 참조 없음
- 런타임 인덱싱 또는 계산된 오프셋 사용
- .EG1, .EG2, .PL1 등 여러 파일 타입

---

## ⚠️ 미해결 문제

### 1. 스프라이트 파일 포맷

**문제**:
- 첫 바이트의 의미 불명 (0x3D, 0x7F, 0xC8)
- 헤더 크기 불명
- 프레임 구조 불명
- 메타데이터 위치 불명

**필요**:
- 실제 스프라이트 로딩 함수 찾기
- 파싱 코드 분석
- 프레임 인덱스 테이블 발견

### 2. 변환 파이프라인

**문제**:
- LZW 해제 후 어떤 변환이 필요한지 불명확
- FUN_1000_0786은 배경용, 스프라이트용 함수는 별도?
- RLE 해제 함수가 사용되는지 불명

**필요**:
- 전체 변환 체인 파악
- 스프라이트 전용 처리 함수 찾기

### 3. 코드 참조 부재

**문제**:
- 파일명 문자열에 직접 참조 없음
- 메모리 주소 0x2949 (LZW 출력 버퍼) 사용 코드 미발견

**필요**:
- 간접 참조 방식 파악
- 런타임 주소 계산 로직 찾기

---

## 🎯 다음 단계 제안

### 단기 (즉시 가능)

1. **레벨 배경 파일 테스트**
   - LEVEL*.PC1 파일에 FUN_1000_0786 적용
   - 16-plane de-interleave가 맞는지 검증

2. **Ghidra GUI로 직접 분석**
   - 문자열 1000:aff0 주변 데이터 구조 보기
   - Cross-reference 수동 추적
   - 메모리 레이아웃 시각화

3. **다른 변환 함수 찾기**
   - 작은 스프라이트용 변환 함수 검색
   - FUN_1000_0786 호출하는 함수 역추적

### 중기 (추가 분석 필요)

4. **메인 게임 루프 완전 분석**
   - FUN_1000_3830, FUN_1000_3b20 상세 분석
   - 렌더링 체인 완전 파악

5. **DOSBox 디버깅**
   - 실제 게임 실행 중 메모리 덤프
   - 스프라이트 로딩 시점 추적
   - 변환 전후 데이터 비교

6. **유사 게임 참고**
   - 같은 시대 DOS CGA 게임 분석
   - 표준 포맷 조사

### 장기 (대안 접근)

7. **다른 리버싱 도구 사용**
   - IDA Pro로 재분석
   - radare2로 동적 분석
   - Binary Ninja 시도

8. **커뮤니티 조사**
   - Double Dragon PC 리버싱 기존 작업 검색
   - DOS 게임 보존 커뮤니티 문의

---

## 📁 생성된 파일

**문서**:
- `output/docs/phase4_sprite_analysis.md` - 상세 분석 노트
- `output/docs/phase4_summary.md` - 이 문서

**스크립트**:
- `phase4_analyze_sprite.py` - 데이터 분석
- `phase4_render_sprite.py` - 렌더링 시도
- `find_string_refs.py` - pyghidra 문자열 검색
- `analyze_string_table.py` - pyghidra 테이블 분석

**출력**:
- `output/assets/rendered_test/` - 48개 테스트 PNG
  - LINDA_w{32,40,48,64,80,96,128,160}_pal{0,1}.png
  - ABOBO_w{32,40,48,64,80,96,128,160}_pal{0,1}.png
  - PLAYER1_w{32,40,48,64,80,96,128,160}_pal{0,1}.png

---

## 💡 핵심 교훈

### 성공 요소

1. **수동 분석의 중요성**
   - 자동화 도구 실패 시 수동 분석으로 구조 파악
   - 디컴파일 코드 한 줄씩 읽기
   - 바이너리 덤프 직접 확인

2. **pyghidra 활용**
   - Phase 1에서 설정한 환경 재사용
   - 문자열, 데이터 구조 동적 탐색 가능
   - Python으로 자동화 가능

3. **체계적 기록**
   - 모든 발견 사항 문서화
   - 실패한 시도도 기록 (중요!)
   - 코드 주석으로 이해 내용 보존

### 어려움

1. **30년 전 게임의 특수성**
   - 현대 표준과 다른 커스텀 포맷
   - 문서 없음
   - 최적화된 비트 레벨 조작

2. **간접 참조 구조**
   - 문자열 직접 참조 없음
   - 런타임 계산된 주소
   - 인덱스 기반 접근

3. **복잡한 변환 체인**
   - LZW → RLE? → Planar → CGA
   - 여러 단계 변환
   - 데이터 타입마다 다른 처리

---

**작성일**: 2025-11-24
**Phase 4 상태**: 구조 분석 완료, 실제 렌더링 미완
**다음 Phase**: 레벨 배경 분석 또는 Ghidra GUI 직접 분석
