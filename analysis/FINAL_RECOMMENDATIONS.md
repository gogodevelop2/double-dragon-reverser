# Double Dragon 바이너리 분석 최종 결론 및 권장사항

## 분석 결과 요약

### 압축 포맷
- ✅ 시그니처: `0x1F 0x9D` (LZW 유사)
- ❌ 표준 Unix compress 포맷 아님
- ❌ unlzw3 라이브러리로 압축 해제 실패
- **결론**: **커스텀 LZW 변형 또는 게임 전용 압축 포맷**

### 문제점
1. 모든 파일(40개)에서 "Invalid Header Flags Byte" 에러
2. 표준 LZW 디코더와 호환되지 않음
3. 1988년 DOS 게임 특유의 커스텀 포맷으로 추정

## 현실적인 해결 방안

### ✅ 권장 방법 1: 스크린샷 기반 에셋 재생성 (가장 빠름)

**장점**:
- 바로 시작 가능
- 100% 작동 보장
- 웹 최적화 가능

**프로세스**:
```bash
1. DOSBox-X로 게임 실행
2. 캐릭터 모든 동작 스크린샷 (F5 키)
   - 플레이어: 서기, 걷기, 펀치, 킥, 점프 등
   - 적들: 각 캐릭터별 동작
3. 배경/레벨 스크린샷
4. UI 요소 캡처
5. Aseprite/GIMP로 스프라이트 시트 생성
```

**예상 시간**: 2-3일

### ✅ 권장 방법 2: 온라인 리소스 활용

**The Spriters Resource 확인**:
```
https://www.spriters-resource.com/search/?q=double+dragon
```

**검색 결과**:
- NES 버전: 스프라이트 있음
- 아케이드 버전: 스프라이트 있음
- **DOS 버전**: 직접 확인 필요

**대안**: NES/아케이드 스프라이트를 베이스로 DOS 스타일로 수정

**예상 시간**: 1-2일

### ⚠️ 방법 3: DOSBox 메모리 덤프 (중급)

**DOSBox-X 디버거 사용**:
```bash
# DOSBox-X 실행
/opt/homebrew/bin/dosbox-x -startmapper

# 게임 로드 후
Alt + Pause (디버거 진입)

# 메모리 검색
SR 0 0xFFFFF 00 FF  # 특정 패턴 검색

# 메모리 덤프
MEMDUMPBIN 시작주소 길이 파일명.bin
```

**장점**: 압축 해제된 실제 데이터 획득
**단점**: 시행착오 필요, 메모리 주소 찾기 어려움

**예상 시간**: 3-5일

### ❌ 방법 4: 압축 알고리즘 리버스 엔지니어링 (비추천)

**필요 작업**:
- DDMAIN.EXE 디스어셈블리
- 압축 해제 루틴 찾기
- 알고리즘 재구현

**예상 시간**: 2-4주
**권장하지 않음**: 복각 프로젝트에 비효율적

## 최종 권장사항

### 🎯 추천 로드맵

#### Phase 1: 에셋 수집 (1주)
1. **온라인 검색** (1일)
   - Spriters Resource 전체 탐색
   - Reddit, Archive.org 검색
   - 레트로 게임 커뮤니티 질문

2. **스크린샷 캡처** (2-3일)
   ```
   - 플레이어 캐릭터: ~20 프레임
   - 적 4종: 각 ~15 프레임
   - 보스: ~20 프레임
   - 무기/아이템: ~10개
   - 배경 타일: ~50 타일
   - UI 요소: ~10개
   ```

3. **스프라이트 시트 생성** (2-3일)
   - Aseprite로 프레임 정리
   - 투명 배경 처리
   - JSON 메타데이터 생성

#### Phase 2: 게임 로직 분석 (3일)
1. **게임 플레이 관찰**
   - 플레이어 이동 속도 측정
   - 공격 범위/데미지 파악
   - 적 AI 패턴 기록
   - 레벨 구조 스케치

2. **수치 문서화**
   ```json
   {
     "player": {
       "walkSpeed": 측정값,
       "jumpHeight": 측정값,
       "punchDamage": 관찰값,
       "health": 100
     },
     "enemies": [...]
   }
   ```

#### Phase 3: 프로토타입 개발 (1주)
1. Phaser 3 프로젝트 초기화
2. 플레이어 캐릭터 구현
3. 기본 이동/공격
4. 레벨 1 일부 구현

## 구체적인 다음 단계

### 즉시 실행 가능한 작업

#### 1. 스크린샷 수집 스크립트
```bash
# DOSBox-X 설정 수정하여 스크린샷 품질 향상
# ~/.config/dosbox-x/dosbox-x-*.conf

[render]
scaler=none
aspect=true

[dosbox]
captures=/Users/joejeon/Documents/develop/Double Dragon/captures
```

#### 2. 게임 플레이 가이드 작성
```markdown
# 캡처할 동작 체크리스트

## 플레이어 (빌리/지미)
- [ ] 서 있기 (좌/우)
- [ ] 걷기 (프레임 1-4, 좌/우)
- [ ] 펀치 (프레임 1-3)
- [ ] 킥 (프레임 1-3)
- [ ] 점프 (프레임 1-4)
- [ ] 피격 (프레임 1-2)
- [ ] 승리 포즈
...
```

#### 3. 온라인 리소스 조사
```bash
# 검색 키워드
- "Double Dragon DOS sprites"
- "Double Dragon PC graphics rip"
- "Double Dragon 1988 assets"
- "Double Dragon tileset"
```

## 도구 및 리소스

### 필수 도구
```bash
# 설치 필요
brew install aseprite      # 스프라이트 편집 (또는 유료 구매)
# 대안: Piskel (무료 웹), GraphicsGale (무료)

# 이미 있음
- DOSBox-X
- Python
- 이미지 편집 도구 (GIMP, Photoshop 등)
```

### 참고 프로젝트
- [Streets of Rage Remake](http://www.soronline.net/) - 비슷한 복각 사례
- [OpenBOR](https://github.com/DCurrent/openbor) - 벨트스크롤 게임 엔진
- [Phaser 예제](https://phaser.io/examples) - 참고용 코드

## 바이너리 분석 결과 파일

생성된 분석 도구 및 문서:
```
analysis/
├── analyze_binary.py          # 바이너리 구조 분석 도구
├── decompress_lzw.py          # LZW 패턴 분석
├── extract_all.py             # 전체 파일 처리 시도
├── BINARY_ANALYSIS_REPORT.md  # 상세 분석 보고서
└── FINAL_RECOMMENDATIONS.md   # 이 문서
```

## 결론

**바이너리 직접 분석은 비효율적입니다.**

이유:
1. 커스텀 압축 포맷 (표준 도구로 해제 불가)
2. 리버스 엔지니어링 시간 대비 효과 낮음
3. 더 빠르고 확실한 방법 존재

**권장 접근**:
1. ✅ 스크린샷 기반 에셋 재생성 (2-3일)
2. ✅ 게임 플레이 관찰로 로직 파악 (2-3일)
3. ✅ Phaser 3로 프로토타입 제작 (1주)

**총 예상 시간**: 2-3주면 플레이 가능한 프로토타입 완성

---

**다음 단계**:
1. Spriters Resource 확인
2. DOSBox로 스크린샷 캡처 시작
3. Phaser 3 프로젝트 초기화

질문이나 도움이 필요하면 언제든 말씀해주세요!
