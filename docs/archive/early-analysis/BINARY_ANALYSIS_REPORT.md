# Double Dragon DOS 바이너리 분석 보고서

## 분석 요약

### 파일 포맷 확인

모든 게임 에셋 파일은 **LZW (Lempel-Ziv-Welch) 압축**을 사용합니다.
- 시그니처: `0x1F 0x9D` (Unix compress 형식)
- 압축 비트: 14-22 bits (파일마다 다름)
- 블록 모드: 대부분 활성화

| 파일 타입 | 예시 | 압축 비트 | 파일 크기 | 엔트로피 |
|-----------|------|-----------|-----------|----------|
| 스프라이트 (.EG1) | PLAYER1.EG1 | 22 bits | 25,820 bytes | 7.68 |
| 스프라이트 (.EG1) | ABOBO.EG1 | 20 bits | 16,362 bytes | 7.70 |
| 레벨 데이터 (.PC1) | LEVEL11.PC1 | 15 bits | 22,405 bytes | 7.60 |
| 화면 데이터 (.CGA) | LDSCRN.CGA | 17 bits | 6,839 bytes | 7.65 |
| 문자 세트 (.BIN) | CHARSET.BIN | 14 bits | 276 bytes | 6.80 |

### 엔트로피 분석

- 모든 파일의 엔트로피가 7.6-7.7 bits/byte
- 이는 데이터가 잘 압축되어 있음을 의미 (최대 8.0)
- 압축 해제 후에는 구조적 패턴이 나타날 것으로 예상

## 압축 해제 방법

### 1. 표준 Unix compress 도구 (실패)

```bash
uncompress PLAYER1.EG1.Z
```

**문제점**:
- macOS의 `uncompress`가 파일 확장자를 요구함
- 확장자를 `.Z`로 바꿔도 "Inappropriate file type" 에러 발생
- DOS 시대의 압축 포맷과 현대 도구의 호환성 문제

### 2. Python lzw 라이브러리

```python
# 파이썬 표준 라이브러리에는 Unix compress LZW 디코더 없음
# 서드파티 라이브러리 필요: unlzw, lzw 등
```

**추천 라이브러리**:
```bash
pip install unlzw3
```

### 3. DOSBox 메모리 덤프 (권장)

게임을 실행한 상태에서 메모리를 덤프하면 압축 해제된 데이터를 직접 얻을 수 있습니다.

**DOSBox 디버거 사용**:
```
1. DOSBox-X 실행
2. 디버거 모드 활성화
3. 게임 실행
4. 메모리 덤프 (MEMDUMP 명령어)
```

### 4. 온라인 리소스 활용 (가장 빠름)

**The Spriters Resource**: https://www.spriters-resource.com/
- 많은 레트로 게임의 스프라이트가 이미 추출되어 있음
- Double Dragon 검색 시 NES/아케이드 버전 존재
- DOS 버전은 직접 추출 필요할 수 있음

## 데이터 구조 추정

### 스프라이트 파일 (.EG1, .EG2)

압축 해제 후 예상 구조:
```
[헤더]
  - 스프라이트 개수 (2 bytes)
  - 팔레트 정보 (CGA 4색)

[스프라이트 데이터]
  - 스프라이트 1:
    - 너비 (1-2 bytes)
    - 높이 (1-2 bytes)
    - 픽셀 데이터 (비트맵)
  - 스프라이트 2...
```

**CGA 4색 팔레트**:
- 0: 검정 (배경)
- 1: 청록/마젠타 (팔레트 모드에 따라)
- 2: 흰색/빨강
- 3: 밝은 흰색/연한 청록

### 레벨 데이터 (.PC1)

```
[헤더]
  - 레벨 너비/높이
  - 스크롤 정보

[배경 타일맵]
  - 타일 인덱스 배열

[오브젝트 배치]
  - 적 위치 및 타입
  - 아이템 위치
  - 트리거 포인트
```

### 애니메이션 프레임 (.NW1~.NW5)

5개 레벨에 대응하는 미니 캐릭터 애니메이션:
- NW1: 레벨 1
- NW2: 레벨 2
- NW3: 레벨 3
- NW4: 레벨 4 (데이터 있지만 레벨은 누락)
- NW5: 레벨 5

## 실행 파일 분석 (DDMAIN.EXE)

### 게임 로직 추출 방법

1. **디스어셈블리**
   ```bash
   # IDA Pro, Ghidra, Radare2 사용
   r2 DDMAIN.EXE
   ```

2. **DOSBox 디버거**
   - 브레이크포인트 설정
   - 메모리 워치
   - 레지스터 추적

3. **역공학 포인트**
   - 플레이어 입력 처리
   - 충돌 감지 알고리즘
   - 적 AI 패턴
   - 점수 계산
   - 레벨 전환 로직

### 주요 게임 상수 찾기

검색할 값들:
- 플레이어 초기 체력 (아마도 255 또는 100)
- 레벨 개수 (8)
- 캐릭터 이동 속도
- 공격 데미지 값

## 실전 추출 전략

### Phase 1: 스프라이트 추출 (우선순위 높음)

**방법 A: 온라인 검색**
1. Spriters Resource 확인
2. Archive.org에서 DOS 게임 리소스 검색
3. 커뮤니티 (Reddit r/gamedev, r/retrogaming)

**방법 B: 스크린샷 캡처** (가장 확실)
1. DOSBox-X로 게임 실행
2. 모든 캐릭터 애니메이션 프레임 스크린샷
3. 배경 타일 스크린샷
4. 이미지 편집 도구로 정리

**방법 C: Python unlzw3 사용**
```python
pip install unlzw3
import unlzw3

with open('PLAYER1.EG1', 'rb') as f:
    compressed = f.read()

decompressed = unlzw3.unlzw(compressed)
# 이후 바이너리 구조 분석
```

### Phase 2: 게임 로직 분석 (선택적)

실제로는 게임을 플레이하며 관찰하는 것이 더 빠를 수 있음:
- 플레이어 이동 속도 측정
- 공격 범위 측정
- 적 AI 패턴 관찰
- 레벨 구조 스케치

### Phase 3: 사운드 추출

DOS 버전은 PC 스피커 사운드일 가능성:
- DOSBox 오디오 녹음 기능 사용
- Audacity로 편집
- 웹용으로 MP3/OGG 변환

## 도구 및 리소스

### 필수 도구
- **DOSBox-X**: 게임 실행 및 디버깅
- **Python**: 바이너리 분석 스크립트
- **Hex Editor**: HxD, 010 Editor
- **Aseprite**: 스프라이트 편집
- **GIMP**: 이미지 편집

### 추천 라이브러리
```bash
pip install unlzw3          # LZW 압축 해제
pip install pillow          # 이미지 처리
pip install numpy           # 데이터 분석
```

### 참고 링크
- [DOS Game Modding Wiki](http://www.shikadi.net/moddingwiki/)
- [The Spriters Resource](https://www.spriters-resource.com/)
- [DOSBox Debugger Guide](https://www.dosbox.com/wiki/Debugger)
- [CGA Graphics Format](https://www.seasip.info/VintagePC/cga.html)

## 다음 단계

1. ✅ 바이너리 포맷 확인 (LZW 압축)
2. ⬜ unlzw3로 압축 해제 시도
3. ⬜ 압축 해제된 데이터 구조 분석
4. ⬜ 스프라이트 추출 또는 스크린샷 캡처
5. ⬜ 게임 로직 관찰 및 문서화
6. ⬜ 웹 버전 프로토타입 개발 시작

## 현실적인 접근

**가장 빠른 방법**:
1. DOSBox로 게임 플레이하며 스크린샷 캡처
2. 온라인에서 유사한 스프라이트 검색
3. 필요시 수동으로 픽셀 아트 재생성
4. 게임 로직은 관찰하며 재구현

**장기적 접근**:
1. 압축 해제 도구 개발
2. 바이너리 포맷 완전 분석
3. 자동 추출 파이프라인 구축
4. 원본 게임 완벽 복원

웹 복각이 목표라면 **첫 번째 방법을 권장**합니다.
