# 핵심 알고리즘

**목적**: Double Dragon에서 사용된 5개 핵심 알고리즘을 **의사코드**로 정리하여, 어떤 언어로든 구현 가능하게 만듭니다.

---

## 📋 알고리즘 목록

### [RLE_COMPRESSION.md](RLE_COMPRESSION.md)
**Run-Length Encoding 압축/해제**
- 커스텀 RLE 포맷
- 스프라이트 데이터 압축 (평균 3:1)
- 200 스캔라인 × 4 평면 처리

**사용처**: 스프라이트 블리팅 (FUN_1000_2865)
**복잡도**: ⭐⭐ (중하)
**구현 우선순위**: 1 (독립적)

---

### [LZW_COMPRESSION.md](LZW_COMPRESSION.md)
**Lempel-Ziv-Welch 압축/해제**
- Unix compress 호환
- 매직 넘버: 0x9d1f
- 9-16 bit 가변 코드
- 초기화/재개 모드

**사용처**: 에셋 파일 로딩 (6개 함수)
**복잡도**: ⭐⭐⭐⭐ (상)
**구현 우선순위**: 2 (독립적)

---

### [SPRITE_BLITTING.md](SPRITE_BLITTING.md)
**4-plane CGA 스프라이트 블리팅**
- 4-평면 인터리빙
- VRAM 래핑 처리
- 임계값 기반 디스패칭 (0x1DC1)
- 직접 vs 래핑 블릿

**사용처**: 렌더링 시스템 (7개 함수)
**복잡도**: ⭐⭐⭐⭐ (상)
**구현 우선순위**: 7 (렌더링 의존)

---

### [MANHATTAN_AI.md](MANHATTAN_AI.md)
**맨하탄 거리 기반 AI**
- 거리 계산 (|dx| + |dy|)
- 타겟 선택 (P1 vs P2)
- 생존 체크
- 애니메이션 매핑

**사용처**: AI 시스템 (FUN_1000_3384)
**복잡도**: ⭐⭐ (중하)
**구현 우선순위**: 5 (엔티티 의존)

---

### [VSYNC_TIMING.md](VSYNC_TIMING.md)
**VSync 동기화**
- Port 0x3DA 폴링
- 2-단계 대기
- ±1 스캔라인 정확도

**사용처**: 하드웨어 I/O (FUN_1000_0604)
**복잡도**: ⭐ (하)
**구현 우선순위**: 3 (독립적)

---

## 🎯 문서 구조 (모든 알고리즘 공통)

각 알고리즘 문서는 다음 구조를 따릅니다:

```markdown
# 알고리즘 이름

## 1. 개요
- 목적
- 입력/출력
- 복잡도

## 2. 배경
- 왜 필요한가
- 원본 구현 분석
- 역사적 맥락

## 3. 의사코드
```
function algorithm_name(input):
  step 1
  step 2
  return output
```

## 4. 단계별 설명
- 각 단계 상세 설명
- 엣지 케이스
- 최적화 포인트

## 5. 예제
- 입력 데이터
- 처리 과정
- 출력 결과

## 6. 복잡도 분석
- 시간 복잡도
- 공간 복잡도
- 실제 성능

## 7. 구현 시 주의사항
- 함정 (pitfalls)
- 언어별 고려사항
- 테스트 케이스

## 8. 참고
- 원본 함수
- 관련 시스템
- 외부 참조
```

---

## 📊 알고리즘 비교

| 알고리즘 | 복잡도 (시간) | 복잡도 (공간) | 독립성 | 난이도 |
|----------|---------------|---------------|--------|--------|
| RLE 압축 | O(n) | O(1) | ⭐⭐⭐ | ⭐⭐ |
| LZW 압축 | O(n) | O(4096) | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 스프라이트 블릿 | O(n) | O(160) | ⭐ | ⭐⭐⭐⭐ |
| 맨하탄 AI | O(1) | O(1) | ⭐⭐ | ⭐⭐ |
| VSync 타이밍 | O(1) | O(1) | ⭐⭐⭐ | ⭐ |

**독립성**: 다른 시스템 의존도 (높을수록 독립적)
**난이도**: 구현 난이도

---

## 🔗 알고리즘 의존성

```
압축 알고리즘 (독립적)
├─ RLE → 스프라이트 블리팅
└─ LZW → 에셋 로딩

타이밍 (독립적)
└─ VSync → 렌더링

AI (엔티티 의존)
└─ 맨하탄 거리 → 타겟 선택

블리팅 (압축 + 렌더링 의존)
└─ 4-plane 블릿 → 화면 출력
```

---

## 🎓 알고리즘별 학습 포인트

### RLE 압축
**배울 점**:
- 간단하지만 효과적인 압축
- 상태 기반 파싱
- 마커 값 처리

**적용 분야**:
- 이미지 압축 (PCX, BMP RLE)
- 네트워크 프로토콜
- 비디오 압축 (기초)

---

### LZW 압축
**배울 점**:
- 사전 기반 압축
- 가변 비트 인코딩
- 상태 보존/재개

**적용 분야**:
- GIF 이미지
- Unix compress
- ZIP (일부)

---

### 스프라이트 블리팅
**배울 점**:
- 평면 인터리빙
- 하드웨어 제약 처리
- 래핑 주소 계산

**적용 분야**:
- 레트로 게임 개발
- 하드웨어 시뮬레이션
- 저수준 그래픽

---

### 맨하탄 거리 AI
**배울 점**:
- 휴리스틱 근사
- 성능 vs 정확도 트레이드오프
- 게임 AI 최적화

**적용 분야**:
- 경로 찾기 (A*)
- 게임 AI
- 클러스터링

---

### VSync 타이밍
**배울 점**:
- 하드웨어 폴링
- 동기화 패턴
- 정확한 타이밍

**적용 분야**:
- 게임 루프
- 애니메이션 동기화
- 하드웨어 인터페이스

---

## 📐 의사코드 작성 원칙

### ✅ 좋은 의사코드

```python
# 명확한 함수 시그니처
function decompress_rle(input_stream, output_buffer):
  # 초기화
  position = 0

  # 메인 루프
  while not end_of_stream(input_stream):
    # 제어 바이트 읽기
    control_byte = read_byte(input_stream)

    # 케이스 분기
    if control_byte == SKIP_MARKER:
      continue
    elif control_byte < 0:  # Repeat run
      count = 1 - control_byte
      value = read_byte(input_stream)
      fill(output_buffer, position, value, count)
      position += count
    else:  # Literal run
      count = control_byte + 1
      copy(input_stream, output_buffer, position, count)
      position += count

  return position  # 출력 크기
```

**특징**:
- 주석으로 의도 설명
- 명확한 변수명
- 단계별 구조
- 엣지 케이스 처리

---

### ❌ 나쁜 의사코드

```python
# 모호한 이름
function f(x, y):
  i = 0
  while true:  # 종료 조건 불명확
    b = x[i]  # 무슨 의미?
    if b < 0:
      // ...
```

**문제점**:
- 변수명 불명확 (x, y, i, b)
- 종료 조건 없음
- 의도 불분명
- 주석 없음

---

## 🧪 테스트 데이터

각 알고리즘 문서는 다음을 포함합니다:

1. **기본 케이스**: 정상 동작
2. **엣지 케이스**: 경계값
3. **에러 케이스**: 잘못된 입력
4. **실제 데이터**: Double Dragon에서 추출

### 예시: RLE 테스트

```
# 기본 케이스
입력:  [0xFF, 0xAA, 0x00, 0xBB]
의미:  Repeat 0xAA 1회, Literal 0xBB
출력:  [0xAA, 0xBB]

# 엣지 케이스: 최대 반복
입력:  [0x81, 0xFF]
의미:  Repeat 0xFF 127회
출력:  [0xFF] × 127

# 에러 케이스: 잘못된 마커
입력:  [0x80]
의미:  Skip marker
출력:  (스킵)
```

---

## 🔍 원본 함수 매핑

| 알고리즘 | 주요 함수 | 보조 함수 | Phase 4 문서 |
|----------|-----------|-----------|--------------|
| RLE | FUN_1000_2865 | 2840, 2894 | FINAL_SYSTEMS |
| LZW | FUN_1000_6009 | 5ff3, 604e, 605b, 6091 | STAGE_INIT |
| 블리팅 | FUN_1000_28c0 | 28ef, 293e | FINAL_SYSTEMS |
| 맨하탄 AI | FUN_1000_3384 | 3824, 3265 | FINAL_SYSTEMS |
| VSync | FUN_1000_0604 | 0612 | CAMERA_VSYNC |

---

## 💡 구현 가이드

### 단계별 접근

1. **의사코드 이해** (30분)
   - 알고리즘 문서 정독
   - 예제 손으로 따라하기
   - 엣지 케이스 이해

2. **테스트 작성** (1시간)
   - 문서의 테스트 케이스 변환
   - 단위 테스트 프레임워크 사용
   - 실패 케이스부터 작성

3. **구현** (2-4시간)
   - 의사코드 → 선택 언어
   - 테스트 통과시키기
   - 리팩토링

4. **검증** (30분)
   - 원본 데이터로 테스트
   - 성능 측정
   - 엣지 케이스 재확인

---

### 언어별 변환 예시

**의사코드**:
```python
function read_code(bit_stream):
  if bit_stream.bits_available < code_width:
    bit_stream.refill()
  return bit_stream.read_bits(code_width)
```

**TypeScript**:
```typescript
function readCode(bitStream: BitStream): number {
  if (bitStream.bitsAvailable < codeWidth) {
    bitStream.refill();
  }
  return bitStream.readBits(codeWidth);
}
```

**C++**:
```cpp
uint16_t read_code(BitStream& bit_stream) {
  if (bit_stream.bits_available < code_width) {
    bit_stream.refill();
  }
  return bit_stream.read_bits(code_width);
}
```

**Rust**:
```rust
fn read_code(bit_stream: &mut BitStream) -> u16 {
  if bit_stream.bits_available < code_width {
    bit_stream.refill();
  }
  bit_stream.read_bits(code_width)
}
```

---

## 📚 추가 자료

### 시스템 맥락
- [`../systems/01_RENDERING.md`](../systems/01_RENDERING.md) - 블리팅 사용
- [`../systems/02_ENTITY_AI.md`](../systems/02_ENTITY_AI.md) - 맨하탄 AI 사용
- [`../systems/07_COMPRESSION.md`](../systems/07_COMPRESSION.md) - RLE + LZW 사용

### 원본 분석
- [`../archive/phase4-analysis/FINAL_SYSTEMS_ANALYSIS.md`](../archive/phase4-analysis/FINAL_SYSTEMS_ANALYSIS.md)
- [`../archive/phase4-analysis/STAGE_INIT_RESPAWN_ANALYSIS.md`](../archive/phase4-analysis/STAGE_INIT_RESPAWN_ANALYSIS.md)

### 외부 참조
- RLE: https://en.wikipedia.org/wiki/Run-length_encoding
- LZW: https://en.wikipedia.org/wiki/Lempel–Ziv–Welch
- Manhattan Distance: https://en.wikipedia.org/wiki/Taxicab_geometry

---

## 🚀 빠른 시작

### 학습 순서
1. VSync (가장 단순)
2. 맨하탄 AI (간단한 수학)
3. RLE (압축 기초)
4. LZW (압축 심화)
5. 블리팅 (복잡한 메모리 처리)

### 구현 순서
1. RLE (독립적, 먼저 필요)
2. LZW (독립적, 에셋 로딩)
3. VSync (독립적, 타이밍)
4. 맨하탄 AI (엔티티 후)
5. 블리팅 (렌더링 시)

---

**작성 상태**:
- [x] README.md (이 파일)
- [ ] RLE_COMPRESSION.md
- [ ] LZW_COMPRESSION.md
- [ ] SPRITE_BLITTING.md
- [ ] MANHATTAN_AI.md
- [ ] VSYNC_TIMING.md

**다음 작업**: 알고리즘 문서 작성 (RLE부터)

**관련 문서**:
- [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)
- [../systems/README.md](../systems/README.md)
- [../methodology/README.md](../methodology/README.md)
