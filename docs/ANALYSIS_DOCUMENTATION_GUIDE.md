# 분석 문서화 가이드

**프로젝트**: Double Dragon (1988) 리버스 엔지니어링
**목적**: 일관되고 체계적인 분석 기록 방법 확립

---

## 📚 문서 구조 개요

### 핵심 원칙

> **"모든 발견은 즉시 기록한다. 나중에는 잊어버린다."**

### 문서 계층

```
docs/
├── 📋 작업 관리 (How to Work)
│   ├── WORK_PRINCIPLES.md      ⭐ 작업 원칙 (절대 원칙)
│   ├── PROGRESS.md              진행 상황 (전체 로드맵)
│   └── GAME_RECONSTRUCTION_ROADMAP.md  최종 목표
│
├── 📊 Phase 리포트 (What We Did)
│   └── reports/
│       ├── PHASE0_SETUP.md
│       ├── PHASE1_DECOMPILE.md
│       ├── PHASE3_ASSETS.md
│       └── PHASE4_SPRITES.md
│
├── 🔍 함수 분석 (Detailed Analysis)
│   └── function-analysis/
│       ├── INDEX.md                    함수 목록
│       ├── CALL_GRAPH.md               호출 구조
│       ├── MAIN_LOOP_COMPLETE_ANALYSIS.md  메인 루프
│       ├── FUNCTION_POINTERS.md        함수 포인터
│       │
│       ├── categories/                 카테고리별
│       │   └── 01_asset_loading.md
│       │
│       └── functions/                  개별 함수
│           ├── FUN_1000_0b94.md
│           └── FUN_1000_0360.md
│
├── 🛠️ 기술 문서 (Technical Details)
│   └── technical/
│       ├── EXECUTION_PATH.md           실행 경로
│       ├── LZW_COMPRESSION.md          압축 알고리즘
│       ├── SPRITE_FORMAT.md            스프라이트 포맷
│       └── MEMORY_MAP.md               메모리 레이아웃
│
└── 📖 가이드 (How to Use Tools)
    └── guides/
        ├── GHIDRA_GUIDE.md
        ├── DOSBOX_GUIDE.md
        └── PYGHIDRA_GUIDE.md
```

---

## 📝 Phase 4: 게임 로직 분석 - 기록 방법

### 1. 일일 작업 흐름

#### 오전: 분석 시작
```bash
1. docs/PROGRESS.md 확인 - 현재 위치 파악
2. 오늘의 목표 설정 (1-3개 함수)
3. output/checkpoints/phase4.json 확인 (마지막 체크포인트)
```

#### 작업 중: 실시간 기록
```bash
1. 코드 읽으면서 주석 작성 (output/decompiled/*.c)
2. 발견 즉시 메모 (임시 노트)
3. 함수 간 관계 파악되면 → 다이어그램
```

#### 저녁: 정리 및 문서화
```bash
1. 오늘 분석한 함수 → docs/function-analysis/functions/
2. 새로운 시스템 발견 → docs/technical/
3. 체크포인트 업데이트 → output/checkpoints/phase4.json
4. docs/PROGRESS.md 업데이트
```

### 2. 함수 분석 템플릿

**파일 위치**: `docs/function-analysis/functions/FUN_1000_XXXX.md`

```markdown
# FUN_1000_XXXX - [함수명]

**주소**: 1000:XXXX
**크기**: XX bytes
**복잡도**: 낮음/중간/높음
**카테고리**: [렌더링/입력/AI/...]
**분석일**: 2025-11-XX

---

## 📊 개요

**기능**: 한 줄 요약

**호출자**:
- FUN_1000_YYYY (메인 루프)
- FUN_1000_ZZZZ

**호출하는 함수**:
- FUN_1000_AAAA
- FUN_1000_BBBB

---

## 🔍 상세 분석

### 파라미터
| 레지스터 | 타입 | 용도 |
|----------|------|------|
| AX | int | ... |
| BX | ptr | ... |

### 반환값
- AX: 결과 코드

### 알고리즘
```
1. 초기화
2. 루프
3. 반환
```

### 중요 메모리 주소
| 주소 | 용도 | 읽기/쓰기 |
|------|------|-----------|
| 0x16c8 | 플레이어1 상태 | R/W |

---

## 💡 발견 사항

- [ ] 이 함수는 ...
- [ ] 흥미로운 점: ...

---

## 🔗 관련 함수
- [FUN_1000_YYYY](FUN_1000_YYYY.md) - 호출자
- [메인 루프 분석](../MAIN_LOOP_COMPLETE_ANALYSIS.md)

---

## 📌 TODO
- [ ] 정확한 파라미터 타입 확인
- [ ] 반환값 의미 파악
```

### 3. 시스템 분석 템플릿

**파일 위치**: `docs/technical/[SYSTEM_NAME].md`

```markdown
# [시스템명] - 완전 분석

**분석일**: 2025-11-XX
**관련 Phase**: Phase 4
**상태**: 진행중/완료

---

## 📊 개요

**목적**: 시스템의 역할 한 줄 요약

**관련 함수**: 10개
**메모리 범위**: 0xXXXX ~ 0xYYYY

---

## 🏗️ 구조

### 데이터 구조
```c
struct ObjectData {
    uint8_t type;      // +0x00
    uint8_t state;     // +0x01
    int16_t x;         // +0x02
    int16_t y;         // +0x04
    // ...
};
```

### 메모리 맵
| 주소 | 크기 | 용도 |
|------|------|------|
| 0x16c6 ~ 0x176e | 168 bytes | 7개 객체 배열 |

---

## 🔄 처리 흐름

```
초기화:
  FUN_1000_XXXX()
  └─ 메모리 할당
  └─ 초기값 설정

메인 루프:
  for each 객체:
    1. 업데이트
    2. 렌더링
    3. 충돌 체크
```

---

## 💡 핵심 발견

### 발견 1: ...
**날짜**: 2025-11-XX
**내용**: ...
**영향**: ...

---

## 🎯 미해결 문제
- [ ] 정확한 구조체 크기
- [ ] 특정 필드 의미

---

## 📚 관련 문서
- [메인 루프](../function-analysis/MAIN_LOOP_COMPLETE_ANALYSIS.md)
- [FUN_1000_0360](../function-analysis/functions/FUN_1000_0360.md)
```

### 4. 체크포인트 형식

**파일**: `output/checkpoints/phase4.json`

```json
{
  "phase": 4,
  "title": "게임 로직 완전 분석",
  "last_updated": "2025-11-24T14:30:00",
  "progress": 75,
  "status": "in_progress",

  "tasks": {
    "rendering": {
      "status": "in_progress",
      "progress": 80,
      "functions_analyzed": [
        "FUN_1000_3830",
        "FUN_1000_0360",
        "FUN_1000_3e6d",
        "FUN_1000_3f71"
      ],
      "next": ["FUN_1000_12c0"]
    },
    "input": {
      "status": "pending",
      "progress": 0,
      "functions_analyzed": [],
      "next": ["찾기 필요"]
    },
    "ai": {
      "status": "pending",
      "progress": 0
    }
  },

  "discoveries": [
    {
      "date": "2025-11-24",
      "title": "7개 객체 배열 발견",
      "description": "0x16c6 ~ 0x176e, 24 bytes each",
      "impact": "high",
      "documented_in": "docs/function-analysis/MAIN_LOOP_COMPLETE_ANALYSIS.md"
    }
  ],

  "memory_map": {
    "0x16c6": "객체 배열 시작",
    "0x176e": "객체 배열 끝",
    "0x168f": "작업 버퍼",
    "0xf396": "화면 기준 X",
    "0xf398": "화면 기준 Y"
  },

  "next_steps": [
    "FUN_1000_12c0 찾기 (Blit 함수)",
    "입력 처리 시스템 분석",
    "AI 시스템 분석"
  ]
}
```

---

## 🔄 분석 워크플로우

### Phase 4 전용 워크플로우

```
1️⃣ 새 함수 선택
   ├─ docs/function-analysis/INDEX.md 확인
   └─ 우선순위 결정 (메인 루프 > 디스패처 > 나머지)

2️⃣ 함수 읽기
   ├─ output/decompiled/FUN_1000_XXXX.c 열기
   ├─ 한 줄씩 읽으며 주석 작성
   └─ 호출하는 함수들 리스트업

3️⃣ 실험 (필요시)
   ├─ 간단한 Python/C 구현
   ├─ 실제 데이터로 테스트
   └─ 결과 확인

4️⃣ 문서화
   ├─ docs/function-analysis/functions/FUN_1000_XXXX.md 작성
   ├─ 시스템 문서 업데이트 (해당시)
   └─ 체크포인트 업데이트

5️⃣ 연관 분석
   ├─ 호출하는 함수들 분석 대상 추가
   ├─ 호출 그래프 업데이트
   └─ 다음 함수 선택

6️⃣ 일일 정리
   ├─ docs/PROGRESS.md 업데이트
   ├─ Git 커밋
   └─ 내일 계획
```

---

## 📋 분석 체크리스트

### 함수 분석 시

- [ ] 함수 이름/주소/크기 확인
- [ ] 호출자/피호출자 파악
- [ ] 파라미터/반환값 분석
- [ ] 사용하는 메모리 주소 기록
- [ ] 알고리즘 이해
- [ ] 주석 작성 (디컴파일 코드)
- [ ] 문서 작성 (Markdown)
- [ ] 관련 함수 연결
- [ ] 체크포인트 업데이트

### 시스템 분석 시

- [ ] 관련 함수 전부 나열
- [ ] 데이터 구조 파악
- [ ] 메모리 레이아웃 정리
- [ ] 처리 흐름 다이어그램
- [ ] 핵심 발견 기록
- [ ] 미해결 문제 리스트
- [ ] 기술 문서 작성

### 주간 정리

- [ ] 이번 주 분석 함수 개수
- [ ] 새로 발견된 시스템
- [ ] 완성된 문서 개수
- [ ] 다음 주 목표 설정
- [ ] Git 커밋 정리

---

## 💡 문서 작성 원칙

### 1. 명확성 > 완벽함
- 100% 이해 못해도 현재까지 이해한 것 기록
- "추정", "아마도", "불명확" 명시 OK
- 틀린 내용은 나중에 수정

### 2. 구조화
- 계층적 구조 (개요 → 상세)
- 일관된 템플릿 사용
- 섹션 구분 명확히

### 3. 링크 활용
- 관련 문서 상호 연결
- 함수 간 참조 링크
- 체크포인트 ↔ 문서 연결

### 4. 코드 예시
- 원본 디컴파일 코드 인용
- 이해한 내용을 의사코드로
- 실험 코드 첨부

### 5. 시각화
- 다이어그램 적극 활용
- 메모리 맵 표
- 호출 그래프

---

## 📂 파일 명명 규칙

### 함수 분석
```
docs/function-analysis/functions/FUN_1000_[주소].md

예시:
- FUN_1000_3830.md
- FUN_1000_0360.md
```

### 시스템 분석
```
docs/technical/[시스템명]_[서브시스템].md

예시:
- RENDERING_SYSTEM.md
- INPUT_KEYBOARD.md
- AI_ENEMY_BEHAVIOR.md
```

### 카테고리별 요약
```
docs/function-analysis/categories/[번호]_[카테고리명].md

예시:
- 01_asset_loading.md
- 02_rendering.md
- 03_input_handling.md
```

---

## 🎯 Phase 4 목표별 문서

### 목표: 렌더링 시스템 완성

**진행 상황 기록**:
- `output/checkpoints/phase4.json` - tasks.rendering
- `docs/PROGRESS.md` - Phase 4 섹션

**새 발견 기록**:
- `docs/function-analysis/functions/FUN_1000_12c0.md` (찾으면)
- `docs/technical/RENDERING_SYSTEM.md` (완성되면)

**관련 함수들**:
- `docs/function-analysis/MAIN_LOOP_COMPLETE_ANALYSIS.md` (이미 있음)

### 목표: 입력 처리 시스템

**새 문서**:
- `docs/technical/INPUT_SYSTEM.md`
- `docs/function-analysis/functions/FUN_1000_[입력함수].md`

### 목표: AI 시스템

**새 문서**:
- `docs/technical/AI_SYSTEM.md`
- `docs/function-analysis/categories/04_ai_behavior.md`

---

## 🔍 검색 및 탐색

### 문서 찾기

```bash
# 특정 주소 관련 문서
grep -r "1000:12c0" docs/

# 특정 키워드
grep -r "충돌 감지" docs/

# 함수 참조
grep -r "FUN_1000_3830" docs/
```

### 문서 인덱스

**docs/function-analysis/INDEX.md** - 모든 함수 목록
**docs/PROGRESS.md** - 전체 진행 상황
**PROJECT_STRUCTURE.md** - 파일 구조

---

## 📊 진행 상황 추적

### 매일
- [ ] 체크포인트 업데이트 (JSON)
- [ ] Git 커밋 메시지에 진행률

### 매주
- [ ] docs/PROGRESS.md 업데이트
- [ ] Phase 리포트 업데이트

### Phase 완료 시
- [ ] docs/reports/PHASE4_FINAL.md 작성
- [ ] 모든 체크포인트 최종 확인
- [ ] 다음 Phase 준비

---

## ✅ 문서 품질 체크

### 좋은 문서
- ✅ 명확한 제목과 개요
- ✅ 구조화된 섹션
- ✅ 코드 예시 포함
- ✅ 관련 문서 링크
- ✅ 미해결 문제 명시
- ✅ 날짜 기록

### 개선 필요
- ❌ 제목만 있고 내용 없음
- ❌ 코드 없이 설명만
- ❌ 링크 없음
- ❌ 추정/확정 구분 없음

---

## 🚀 빠른 참조

### 새 함수 분석 시작
```bash
# 1. 템플릿 복사
cp docs/function-analysis/functions/TEMPLATE.md \
   docs/function-analysis/functions/FUN_1000_XXXX.md

# 2. 디컴파일 코드 열기
cat output/decompiled/FUN_1000_XXXX.c

# 3. 분석 시작!
```

### 시스템 문서 생성
```bash
# 1. 새 파일
touch docs/technical/NEW_SYSTEM.md

# 2. 템플릿 참조
cat docs/technical/RENDERING_SYSTEM.md
```

### 체크포인트 업데이트
```bash
# JSON 편집
vim output/checkpoints/phase4.json

# 검증
python3 -m json.tool output/checkpoints/phase4.json
```

---

**작성일**: 2025-11-24
**Phase**: Phase 4 진행 중
**목적**: 일관된 분석 기록 방법 확립
