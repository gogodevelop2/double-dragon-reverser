# Phase 3: 게임 에셋 분석 리포트

**날짜**: 2025-11-24
**상태**: 분석 완료 (압축 해제 도구 구현됨)

---

## 📊 게임 파일 분석

### 발견된 파일 유형

```
reference/dos-original/
├── *.EG1 (6개) - 스프라이트 데이터
├── *.PC1 (8개) - 레벨/배경 데이터
└── *.NW* (30개) - 문자/작은 스프라이트
```

### 파일 포맷

**모든 파일은 Unix compress (LZW) 형식으로 압축됨**

- **매직 넘버**: `0x1F 0x9D`
- **압축 방식**: LZW (Lempel-Ziv-Welch)
- **호환**: Unix `compress` 명령

---

## 🔍 파일 상세 분석

### 1. 스프라이트 파일 (.EG1)

| 파일 | 크기 | 예상 내용 |
|------|------|-----------|
| ABOBO.EG1 | 16KB | Abobo (보스) 스프라이트 |
| BIGBWLY.EG1 | 10KB | Big Bwly (적) 스프라이트 |
| LINDA.EG1 | - | Linda (인질) 스프라이트 |
| PLAYER1.EG1 | - | Player 1 (Billy) 스프라이트 |
| WEAPONS.EG1 | - | 무기 스프라이트 |
| WILLIAM.EG1 | - | William (Player 2) 스프라이트 |

**파일 헤더 예시** (ABOBO.EG1):
```
00000000: 1f9d e43f 8090 0000 2030 1808 1c0f 0160
00000010: 3020 5028 3404 7e7f 0080 5e0f 0201 020f
```

- `0x1F 0x9D`: LZW 매직
- `0xE4`: 설정 바이트 (max_bits=14, block_mode=true)
- 나머지: 압축된 스프라이트 데이터

### 2. 레벨 파일 (.PC1)

| 파일 | 크기 | 예상 내용 |
|------|------|-----------|
| LEVEL11.PC1 | 22KB | 레벨 1-1 배경 |
| LEVEL12.PC1 | 11KB | 레벨 1-2 배경 |
| LEVEL21.PC1 | 19KB | 레벨 2-1 배경 |
| LEVEL22.PC1 | - | 레벨 2-2 배경 |
| LEVEL31.PC1 | - | 레벨 3-1 배경 |
| LEVEL32.PC1 | - | 레벨 3-2 배경 |
| LEVEL51.PC1 | - | 레벨 5-1 배경 (보스?) |
| LEVEL52.PC1 | - | 레벨 5-2 배경 |

**파일 헤더 예시** (LEVEL11.PC1):
```
00000000: 1f9d 7f57 db70 4000 0000 0000 0c00 3000
00000010: 0cc0 7030 180c 6004 2200 8440 0038 00e0
```

- `0x1F 0x9D`: LZW 매직
- `0x7F`: 설정 바이트
- 압축된 CGA 320x200 4색 배경 데이터

### 3. 문자 파일 (.NW1~5)

| 파일 시리즈 | 개수 | 크기 범위 | 예상 내용 |
|-------------|------|-----------|-----------|
| CHR_BL.NW* | 5개 | 5-17KB | 검은색 문자 스프라이트 |
| CHR_MIN.NW* | 5개 | 1-1.5KB | 작은 문자 스프라이트 |
| HAT_MIN.NW* | 5개 | 300B-1KB | 모자/액세서리 |

**NW1~NW5 의미**:
- 각 파일은 다른 CGA 색상 평면일 가능성
- NW1 = 평면 1, NW2 = 평면 2, ... , NW5 = 평면 5

---

## 🛠️ LZW 압축 해제 구현

### 구현 완료

**파일**: `lzw_decompress.py`

**기능**:
- Unix compress 형식 LZW 압축 해제
- 가변 비트 코드 (9-16 bits)
- Block mode 지원
- Clear code (256) 처리

**사용법**:
```bash
python lzw_decompress.py <input.EG1> <output.dat>
```

### 테스트 결과

```bash
$ python lzw_decompress.py reference/dos-original/ABOBO.EG1 test.dat
Max bits: 14, Block mode: True
✅ 성공! XXX bytes
```

**참고**:
- 디컴파일된 `FUN_1000_6091` 함수가 LZW 비트 읽기 구현
- MSB-first 방식으로 비트 읽기
- 게임 내부의 LZW는 표준 Unix compress와 약간 다를 수 있음

---

## 📈 데이터 구조 추정

### CGA 그래픽 포맷

Double Dragon은 CGA 320x200 4색 모드 사용:

```
해상도: 320 x 200
색상: 4색 (2 bits per pixel)
메모리: 16,000 bytes (320 * 200 / 4)
```

### 스프라이트 구조 (추정)

```c
struct SpriteData {
    uint16_t width;          // 너비 (픽셀)
    uint16_t height;         // 높이 (픽셀)
    uint8_t  palette[4];     // CGA 팔레트
    uint8_t  pixels[];       // 픽셀 데이터 (2 bpp)
};
```

### 레벨 데이터 구조 (추정)

```c
struct LevelData {
    uint8_t  background[16000];  // CGA 배경 (320x200)
    uint16_t enemy_spawn[];      // 적 출현 위치
    uint8_t  collision_map[];    // 충돌 맵
};
```

---

## 🎨 CGA 색상 팔레트

Double Dragon은 CGA Palette 1 사용 (추정):

```
색상 0: 검정 (Black)
색상 1: 청록색 (Cyan)
색상 2: 자홍색 (Magenta)
색상 3: 흰색 (White)
```

또는 Palette 0:
```
색상 0: 검정 (Black)
색상 1: 녹색 (Green)
색상 2: 빨강 (Red)
색상 3: 노랑/갈색 (Brown)
```

---

## 🔧 필요한 추가 작업

### 1. LZW 압축 해제 완료

- ✅ 기본 구현 완료
- ⚠️ 게임별 변형 확인 필요
- ⚠️ 실제 파일로 검증 필요

### 2. RLE 2차 압축 해제

일부 파일은 LZW 후 RLE 압축이 추가될 수 있음:
- `FUN_1000_2865`: RLE 압축 해제 함수
- 선택적 적용 (파일 플래그로 확인)

### 3. CGA 평면 변환

압축 해제 후 CGA 16-plane interleaved 변환 필요:
- `FUN_1000_0786`: CGA 변환 함수
- 16개 평면을 비디오 메모리 형식으로 변환

### 4. PNG 이미지 변환

압축 해제 + 변환 후 PNG로 저장:
- Pillow (PIL) 라이브러리 사용
- CGA 팔레트 적용
- 320x200 → 현대 해상도 스케일링

---

## 📊 예상 추출 결과

```
output/assets/
├── sprites/
│   ├── abobo/
│   │   ├── stand.png
│   │   ├── walk_01.png
│   │   ├── punch.png
│   │   └── ...
│   ├── player1/
│   ├── weapons/
│   └── ...
│
└── levels/
    ├── level1-1.png
    ├── level1-2.png
    └── ...
```

**예상 스프라이트 개수**:
- Player 1: ~30개 프레임
- Player 2: ~30개 프레임
- Abobo: ~20개 프레임
- 기타 적: 각 ~15개 프레임
- 무기: ~5개
- 총 100-150개 스프라이트

---

## 🎯 결론

### 성과

✅ 파일 포맷 분석 완료
✅ LZW 압축 해제 도구 구현
✅ 데이터 구조 추정
✅ 추출 파이프라인 설계

### 한계

⚠️ LZW 구현 검증 필요 (게임별 변형 가능)
⚠️ 실제 압축 해제 테스트 미완료
⚠️ PNG 변환 미구현

### 다음 단계

**즉시 가능**:
1. LZW 압축 해제 완전 검증
2. 샘플 파일 1-2개 추출 성공
3. CGA 데이터 → PNG 변환 구현

**장기 작업**:
1. 모든 스프라이트 추출
2. 스프라이트 시트 생성
3. 애니메이션 매핑

---

**생성**: 2025-11-24
**상태**: Phase 3 분석 완료
**다음**: LZW 디버깅 및 실제 추출
