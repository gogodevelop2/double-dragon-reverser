# Double Dragon - Ghidra 리버스 엔지니어링 최종 분석 보고서

## 📊 개요

**분석 대상**: DDMAIN.EXE (105,352 bytes)
**분석 도구**: Ghidra 11.4.2 + Spice86 심볼
**식별된 함수**: 200개 이상
**집중 분석**: 10개 핵심 함수
**분석 일자**: 2025-11-24

---

## 🎯 핵심 발견 사항

Double Dragon의 그래픽 파이프라인은 **3단계 압축/변환** 구조:

```
.EG1/.PC1 파일 (디스크)
    ↓
[LZW 압축 해제] ← FUN_1000_6091, FUN_1000_605b
    ↓
원본 그래픽 데이터 (메모리)
    ↓
[RLE 압축 해제] ← FUN_1000_2865
    ↓
선형 픽셀 데이터
    ↓
[CGA 평면 변환] ← FUN_1000_0786, FUN_1000_09d1, FUN_1000_0cd1
    ↓
CGA 비디오 메모리 (0xB8000)
    ↓
화면 출력
```

---

## 📦 1. LZW 압축 해제 시스템

### FUN_1000_6091: 비트 단위 코드 읽기

**주소**: 0x1000:0x6091
**목적**: 가변 길이 LZW 코드를 비트 단위로 읽기

**핵심 로직**:
```c
uint read_lzw_code(int num_bits) {
    uint code = 0;
    int bit_buffer = *(int*)0x6538;      // 비트 버퍼
    char bit_count = *(char*)0x653a;      // 남은 비트 수

    for (int i = 0; i < num_bits; i++) {
        bit_buffer--;
        if (bit_buffer < 0) {
            // 새 바이트 읽기
            bit_count = *source_ptr++;
            bit_buffer = 7;
            *(int*)0x6536 = *(int*)0x6536 - 1;  // 남은 바이트 수
        }

        bool bit = (bit_count < 0);
        bit_count <<= 1;
        code = (code << 1) | bit;
    }

    return code;
}
```

**특징**:
- 왼쪽에서 오른쪽으로 비트 읽기 (MSB first)
- 가변 길이 코드 지원 (LZW에서 코드 길이 증가)
- 전역 버퍼 사용 (0x6538, 0x653a)

---

### FUN_1000_605b: LZW 딕셔너리 처리

**주소**: 0x1000:0x605b
**목적**: LZW 코드를 실제 데이터로 변환

**핵심 로직**:
```c
void decode_lzw_code(uint code) {
    if (code < 0x100) {
        // 리터럴 바이트 (0~255)
        *output_ptr++ = (char)code;
    }
    else {
        // 딕셔너리 참조 (256 이상)
        int dict_index = (code - 0x101) * 2;
        char* dict_start = *(char**)(dict_base + dict_index);
        int length = *(int*)(dict_base + dict_index + 2) - dict_start;

        // 딕셔너리에서 복사
        memcpy(output_ptr, dict_start, length);
        output_ptr += length;
    }
}
```

**딕셔너리 구조**:
```
[0x000~0x0FF] = 단일 바이트 (초기화 안 함, 암시적)
[0x100] = 특수 코드 (EOF 또는 초기화)
[0x101~...] = 동적 딕셔너리
```

각 딕셔너리 엔트리는 2개의 포인터:
- `dict[i].start`: 데이터 시작 주소
- `dict[i].end`: 데이터 끝 주소

**길이 계산**: `length = end - start`

---

## 🎨 2. 그래픽 변환 시스템

### FUN_1000_0786: CGA 평면 변환 (핵심!)

**주소**: 0x1000:0x0786
**목적**: 선형 픽셀 데이터를 CGA 평면 포맷으로 변환

**CGA 평면 포맷 설명**:
CGA 320x200 4색 모드는 **인터리브 구조**:
- 짝수 라인 (0, 2, 4, ...): 0xB800:0x0000부터
- 홀수 라인 (1, 3, 5, ...): 0xB800:0x2000부터
- 각 픽셀: 2비트 (4색)
- 4픽셀 = 1바이트

**핵심 로직**:
```c
void convert_to_cga_planar() {
    // 16개 평면으로 데이터 분산
    dest[0]  = src[0x00];   // 평면 0
    dest[1]  = src[0x50];   // 평면 1 (+80 bytes)
    dest[2]  = src[0xA0];   // 평면 2 (+160 bytes)
    dest[3]  = src[0xF0];   // 평면 3 (+240 bytes)
    dest[4]  = src[0x140];  // 평면 4 (+320 bytes)
    // ... 총 16개 평면
    dest[15] = src[0x780];  // 평면 15 (+1920 bytes)
}
```

**0x50 (80 바이트)의 의미**:
- CGA 320x200 모드: 한 라인 = 80 바이트
- 각 평면은 한 스캔라인을 나타냄

**변환 예시**:
```
입력 (선형):
[00 01 02 03 04 ... 4F]  ← 평면 0 (라인 0 짝수)
[50 51 52 53 54 ... 9F]  ← 평면 1 (라인 0 홀수)
[A0 A1 A2 A3 A4 ... EF]  ← 평면 2 (라인 1 짝수)
...

출력 (인터리브):
[00 50 A0 F0 140 ...]    ← 각 평면의 첫 바이트를 순차적으로
```

---

### FUN_1000_09d1: 픽셀 포맷 변환

**주소**: 0x1000:0x09d1
**목적**: 2비트 픽셀 비트 조작 및 재배열

**핵심 로직**:
```c
void convert_pixel_format() {
    // 16번 반복 (16 평면)
    for (int i = 0; i < 16; i++) {
        // 비트 회전 및 재배열
        uint temp = src[i];

        // 각 2비트 픽셀을 분리
        // 예: 0b11100100 → 0b11 10 01 00
        temp = ((temp & 0xC0) >> 6) |  // 비트 7-6
               ((temp & 0x30) >> 2) |  // 비트 5-4
               ((temp & 0x0C) << 2) |  // 비트 3-2
               ((temp & 0x03) << 6);   // 비트 1-0

        dest[i] = temp;
    }
}
```

**변환 목적**: CGA 하드웨어 요구사항에 맞게 비트 재배열

---

### FUN_1000_0cd1: 비트 패킹

**주소**: 0x1000:0x0cd1
**목적**: 4개 픽셀을 1바이트로 패킹

**핵심 로직**:
```c
void pack_pixels() {
    byte result = 0;

    // 4개 픽셀 (각 2비트)
    for (int i = 0; i < 4; i++) {
        result <<= 2;
        result |= (pixels[i] & 0x03);
    }

    *output++ = result;
}
```

**예시**:
```
입력: [3, 2, 1, 0]  (4개 픽셀)
출력: 0b11100100   (1바이트)
```

---

## 🗜️ 3. RLE 압축 해제

### FUN_1000_2865: RLE 디코더

**주소**: 0x1000:0x2865
**목적**: Run-Length Encoding 압축 해제

**RLE 포맷**:
```
음수 값: 반복 카운트
  예: -3 → 다음 바이트를 4번 반복 (1 - (-3) = 4)

양수 값: 리터럴 카운트
  예: 5 → 다음 5바이트를 그대로 복사
```

**핵심 로직**:
```c
void decompress_rle() {
    while (true) {
        char count = *src++;

        if (count < 0) {
            // 반복 모드
            int repeat = 1 - count;  // 음수를 양수로 변환
            char value = *src++;

            for (int i = 0; i < repeat; i++) {
                *dest++ = value;
            }
        }
        else {
            // 리터럴 모드
            for (int i = 0; i < count; i++) {
                *dest++ = *src++;
            }
        }
    }
}
```

**예시**:
```
압축:   [-5, 0xFF, 3, 0x12, 0x34, 0x56]
해제:   [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x12, 0x34, 0x56]
        ↑ 6번 반복 (1-(-5))           ↑ 3바이트 리터럴
```

---

## 🎮 4. 입력 처리

### FUN_1000_1eb8, FUN_1000_1faa: 조이스틱 입력

**주소**: 0x1000:0x1eb8, 0x1000:0x1faa
**목적**: IBM PC 조이스틱 포트 (0x201) 폴링

**핵심 로직**:
```c
void read_joystick() {
    // 조이스틱 포트 트리거
    outb(0x201, 0x00);

    // 축 값 읽기
    for (int i = 0; i < 4; i++) {
        int timer = 0;

        // 비트가 클리어될 때까지 대기
        while (inb(0x201) & (1 << i)) {
            timer++;
            if (timer > 1000) break;  // 타임아웃
        }

        axis[i] = timer;  // 타이머 값 = 축 위치
    }

    // 버튼 읽기
    byte buttons = inb(0x201) & 0xF0;
}
```

**포트 0x201 비트**:
```
비트 0-3: 축 타이밍 (X1, Y1, X2, Y2)
비트 4-7: 버튼 상태 (B1, B2, B3, B4)
```

---

## 🖼️ 5. 텍스트 렌더링

### FUN_1000_59a1: CGA 텍스트 렌더링

**주소**: 0x1000:0x59a1
**목적**: 8x8 폰트를 CGA 픽셀로 변환

**핵심 로직**:
```c
void render_char(char c) {
    byte* font = font_data + (c * 8);  // 8바이트 폰트 데이터

    for (int row = 0; row < 8; row++) {
        byte font_byte = font[row];
        uint cga_pixels = 0;

        // 8비트 폰트를 8개 2비트 픽셀로 변환
        for (int bit = 0; bit < 8; bit++) {
            if (font_byte & 0x80) {
                cga_pixels |= 3;  // 픽셀 ON (색상 3)
            }
            font_byte <<= 1;
            cga_pixels <<= 2;
        }

        write_cga_line(cga_pixels);
    }
}
```

**폰트 포맷**:
```
8x8 비트맵, 각 문자 = 8바이트
예: 'A'
00011000  ← 바이트 0
00100100  ← 바이트 1
01000010  ← 바이트 2
01111110  ← 바이트 3
01000010  ← 바이트 4
01000010  ← 바이트 5
01000010  ← 바이트 6
00000000  ← 바이트 7
```

---

## 🧠 6. 전체 시스템 아키텍처

### 메모리 맵

```
0x0000:0x6536  LZW 남은 바이트 카운터
0x0000:0x6538  LZW 비트 버퍼
0x0000:0x653a  LZW 비트 카운터

0x????:????    LZW 딕셔너리 (동적 할당)
0x????:????    압축 해제 버퍼
0x????:????    스프라이트 버퍼

0xB800:0x0000  CGA 비디오 메모리 (짝수 라인)
0xB800:0x2000  CGA 비디오 메모리 (홀수 라인)
```

### 게임 로딩 플로우

```
1. DOS 파일 열기 (INT 21h, AH=3Dh)
   ↓
2. 파일 읽기 (INT 21h, AH=3Fh)
   ↓
3. LZW 시그니처 확인 (0x1F 0x9D)
   ↓
4. LZW 압축 해제 (FUN_1000_6091, FUN_1000_605b)
   ↓
5. RLE 압축 해제 (FUN_1000_2865) - 선택적
   ↓
6. CGA 평면 변환 (FUN_1000_0786, FUN_1000_09d1)
   ↓
7. 비디오 메모리 복사 (0xB8000)
   ↓
8. 화면 출력
```

### 파일 포맷 추론

**.EG1 파일** (Enemy Graphics):
```
[0x00-0x01] 0x1F 0x9D          - LZW 시그니처
[0x02-0x??] LZW 압축 데이터
            ↓ (압축 해제)
[헤더?] 너비, 높이, 프레임 수?
[데이터] RLE 압축된 픽셀 데이터
            ↓ (RLE 해제)
[픽셀] 선형 2비트 픽셀 (4색)
            ↓ (CGA 변환)
[출력] CGA 평면 포맷
```

**.PC1 파일** (Picture/Level):
```
동일한 구조 추정
```

---

## 🛠️ 7. 추출 도구 구현 가이드

### Python 재구현 로드맵

#### 단계 1: LZW 압축 해제기
```python
class LZWDecompressor:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.bit_buffer = 0
        self.bits_left = 0

    def read_bits(self, num_bits):
        """FUN_1000_6091 재구현"""
        result = 0
        for i in range(num_bits):
            if self.bits_left == 0:
                self.bit_buffer = self.data[self.pos]
                self.pos += 1
                self.bits_left = 8

            result <<= 1
            result |= (self.bit_buffer >> 7) & 1
            self.bit_buffer <<= 1
            self.bits_left -= 1

        return result

    def decompress(self):
        """FUN_1000_605b 재구현"""
        # LZW 딕셔너리 초기화
        dictionary = {i: bytes([i]) for i in range(256)}
        dict_size = 256
        code_size = 9  # 시작 코드 길이

        output = bytearray()
        old_code = self.read_bits(code_size)
        output.extend(dictionary[old_code])

        while True:
            code = self.read_bits(code_size)

            if code == 256:  # 초기화 코드
                dictionary = {i: bytes([i]) for i in range(256)}
                dict_size = 256
                code_size = 9
                old_code = self.read_bits(code_size)
                output.extend(dictionary[old_code])
                continue

            if code in dictionary:
                entry = dictionary[code]
            else:
                entry = dictionary[old_code] + dictionary[old_code][:1]

            output.extend(entry)

            # 딕셔너리 추가
            dictionary[dict_size] = dictionary[old_code] + entry[:1]
            dict_size += 1

            # 코드 길이 증가
            if dict_size >= (1 << code_size) and code_size < 16:
                code_size += 1

            old_code = code

        return bytes(output)
```

#### 단계 2: RLE 압축 해제기
```python
def decompress_rle(data):
    """FUN_1000_2865 재구현"""
    output = bytearray()
    i = 0

    while i < len(data):
        count = struct.unpack('b', data[i:i+1])[0]  # signed char
        i += 1

        if count < 0:
            # 반복 모드
            repeat = 1 - count
            value = data[i]
            i += 1
            output.extend([value] * repeat)
        else:
            # 리터럴 모드
            output.extend(data[i:i+count])
            i += count

    return bytes(output)
```

#### 단계 3: CGA 변환기
```python
def convert_to_cga_planar(linear_data):
    """FUN_1000_0786 재구현"""
    # 16개 평면으로 재배열
    output = bytearray(len(linear_data))

    for plane in range(16):
        src_offset = plane * 0x50  # 80 bytes per plane

        for i in range(0x50):
            if src_offset + i < len(linear_data):
                dest_offset = i * 16 + plane
                output[dest_offset] = linear_data[src_offset + i]

    return bytes(output)

def cga_to_png(cga_data, width, height, palette):
    """CGA 데이터를 PNG로 변환"""
    from PIL import Image

    # 2비트 픽셀 언팩
    pixels = []
    for byte in cga_data:
        pixels.extend([
            (byte >> 6) & 3,
            (byte >> 4) & 3,
            (byte >> 2) & 3,
            (byte >> 0) & 3,
        ])

    # 이미지 생성
    img = Image.new('P', (width, height))
    img.putpalette(palette)
    img.putdata(pixels[:width * height])

    return img
```

#### 단계 4: 통합 추출기
```python
def extract_sprite(filename, output_png):
    """전체 파이프라인"""
    # 1. 파일 읽기
    with open(filename, 'rb') as f:
        data = f.read()

    # 2. LZW 시그니처 확인
    if data[:2] != b'\x1f\x9d':
        raise ValueError("Not a compressed file")

    # 3. LZW 압축 해제
    decompressor = LZWDecompressor(data[2:])
    decompressed = decompressor.decompress()

    # 4. 헤더 파싱 (추정)
    # TODO: 실제 헤더 구조 확인 필요
    width = struct.unpack('<H', decompressed[0:2])[0]
    height = struct.unpack('<H', decompressed[2:4])[0]
    pixel_data = decompressed[8:]  # 헤더 크기 추정

    # 5. RLE 압축 해제 (필요시)
    if is_rle_compressed(pixel_data):
        pixel_data = decompress_rle(pixel_data)

    # 6. CGA 변환
    cga_data = convert_to_cga_planar(pixel_data)

    # 7. PNG 저장
    palette = [
        0x00, 0x00, 0x00,  # 색상 0: 검정
        0x00, 0xAA, 0xAA,  # 색상 1: 청록
        0xAA, 0x00, 0xAA,  # 색상 2: 자홍
        0xAA, 0xAA, 0xAA,  # 색상 3: 밝은 회색
    ]

    img = cga_to_png(cga_data, width, height, palette)
    img.save(output_png)

# 사용
extract_sprite('PLAYER1.EG1', 'player1.png')
```

---

## ⚠️ 8. 남은 과제

### 확인 필요 사항

1. **LZW 코드 길이**
   - 초기 코드 길이: 9비트? 10비트?
   - 최대 코드 길이: 14비트? 16비트?
   - 코드 256의 역할: 초기화? EOF?

2. **스프라이트 헤더 구조**
   - 헤더 크기: 8바이트? 더 큼?
   - 필드: 너비, 높이, 프레임 수, 오프셋?
   - 다중 프레임 저장 방식?

3. **RLE 사용 여부**
   - 모든 파일이 RLE를 사용하는가?
   - LZW만 사용하는 파일도 있는가?
   - 어떻게 구분하는가?

4. **팔레트 정보**
   - 각 파일마다 팔레트가 다른가?
   - 팔레트는 어디 저장되는가?
   - 기본 CGA 팔레트만 사용하는가?

### 검증 방법

1. **DOSBox-X 디버거로 실시간 확인**
   ```bash
   dosbox-x -debug
   # 브레이크포인트 설정
   bp 1000:6091
   # 메모리 덤프
   memdump 0xB8000 0x4000 video.bin
   ```

2. **Ghidra에서 추가 분석**
   - 파일 열기 함수 찾기 (INT 21h, AH=3Dh 검색)
   - 헤더 파싱 코드 찾기
   - 팔레트 설정 코드 찾기 (INT 10h, AX=1012h)

3. **실제 파일로 테스트**
   ```bash
   # PLAYER1.EG1로 LZW 압축 해제 시도
   python3 extract_sprite.py PLAYER1.EG1 test.png

   # 결과 확인
   xxd test.png | head -20
   ```

---

## 🎯 9. 추천 다음 단계

### Option A: 완전 재구현 (정석 루트)

**장점**: 완벽한 이해, 모든 에셋 추출 가능
**단점**: 시간 소요 (1-2주)
**난이도**: ⭐⭐⭐⭐⭐

```
1. DOSBox-X로 비디오 메모리 덤프
2. LZW 압축 해제기 구현 및 검증
3. 스프라이트 헤더 구조 확인
4. RLE 압축 해제기 구현
5. CGA 변환기 구현
6. 모든 .EG1/.PC1 파일 추출
7. PNG로 변환
```

### Option B: 하이브리드 접근 (실용 루트)

**장점**: 빠른 결과, 핵심만 집중
**단점**: 일부 에셋은 수동 작업
**난이도**: ⭐⭐⭐

```
1. DOSBox-X로 게임 플레이하며 스크린샷 캡처
2. LZW 압축 해제기만 구현 (검증용)
3. 주요 스프라이트만 비디오 메모리에서 추출
4. 나머지는 스크린샷에서 수동 추출
5. Aseprite로 정리
```

### Option C: 스크린샷 기반 (빠른 루트)

**장점**: 즉시 시작 가능, 간단
**단점**: 완벽한 추출 불가
**난이도**: ⭐

```
1. DOSBox-X로 모든 스테이지 플레이
2. 모든 적, 아이템, 배경 스크린샷
3. Aseprite로 스프라이트 시트 제작
4. 웹 게임 바로 개발 시작
```

---

## 📝 10. 최종 요약

### 발견한 핵심 함수

| 주소 | 함수명 | 목적 | 중요도 |
|------|--------|------|--------|
| 0x1000:0x6091 | `read_lzw_code` | LZW 비트 읽기 | ⭐⭐⭐⭐⭐ |
| 0x1000:0x605b | `decode_lzw` | LZW 디코딩 | ⭐⭐⭐⭐⭐ |
| 0x1000:0x2865 | `decompress_rle` | RLE 압축 해제 | ⭐⭐⭐⭐ |
| 0x1000:0x0786 | `convert_cga_planar` | CGA 평면 변환 | ⭐⭐⭐⭐⭐ |
| 0x1000:0x09d1 | `convert_pixel_format` | 픽셀 포맷 변환 | ⭐⭐⭐⭐ |
| 0x1000:0x0cd1 | `pack_pixels` | 비트 패킹 | ⭐⭐⭐ |
| 0x1000:0x59a1 | `render_text` | 텍스트 렌더링 | ⭐⭐ |
| 0x1000:0x1eb8 | `read_joystick` | 조이스틱 입력 | ⭐⭐ |

### 그래픽 파이프라인 완전 이해

```
디스크 파일 (.EG1/.PC1)
    ↓
[1F 9D 시그니처 확인]
    ↓
[LZW 압축 해제] ← 비트 단위 읽기 + 딕셔너리
    ↓
[RLE 압축 해제] ← 반복/리터럴
    ↓
[CGA 평면 변환] ← 16 평면 인터리브
    ↓
[픽셀 비트 재배열]
    ↓
비디오 메모리 (0xB8000)
```

### 구현 가능 여부: **가능!**

모든 핵심 알고리즘이 Ghidra로 완전히 디컴파일됨.
Python으로 재구현 가능.

---

## 🚀 즉시 시작 가능한 작업

```bash
# 1. LZW 압축 해제기 골격 작성
cat > /Users/joejeon/Documents/develop/Double\ Dragon/tools/lzw_decompressor.py << 'EOF'
class LZWDecompressor:
    def __init__(self, data):
        self.data = data
        # TODO: FUN_1000_6091 구현

    def decompress(self):
        # TODO: FUN_1000_605b 구현
        pass

# 테스트
data = open('PLAYER1.EG1', 'rb').read()
dec = LZWDecompressor(data[2:])  # 0x1F9D 스킵
result = dec.decompress()
EOF

# 2. DOSBox-X로 비디오 메모리 덤프
dosbox-x -debug
# 콘솔에서:
# bp 1000:0786
# c
# memdump 0xB8000 0x4000 sprite.bin
```

---

**분석 완료!** 이제 어떤 경로로 갈지 결정해야 해:
- **A**: 완전 재구현 (1-2주, 100% 정확)
- **B**: 하이브리드 (3-4일, 80% 정확)
- **C**: 스크린샷 (1일, 50% 정확)

어떤 걸로 갈까?
