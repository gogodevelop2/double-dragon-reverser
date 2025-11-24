# 함수 분석 디렉토리

**목적**: 137개 함수의 상세 분석 및 시스템 이해

---

## 📁 디렉토리 구조

```
function-analysis/
├── README.md                           ← 이 파일
├── INDEX.md                            ← 전체 함수 목록
│
├── 📊 시스템 분석 (System-Level Analysis)
│   ├── MAIN_LOOP_COMPLETE_ANALYSIS.md  ⭐ 메인 루프 완전 분석
│   ├── CALL_GRAPH.md                   호출 구조
│   ├── FUNCTION_POINTERS.md            함수 포인터 시스템
│   └── MODE2_COMPLETE_ANALYSIS.md      Mode 2 (EGA) 완전 분석
│
├── 📝 방법론 (Methodology)
│   ├── RECOVERING_MISSED_FUNCTIONS.md  함수 복구 방법
│   ├── ANALYSIS_MISTAKES.md            실수 및 교훈
│   └── PROGRESS_REPORT.md              진행 보고서
│
├── 🏷️ 요약 (Summaries)
│   ├── MODE1_FUNCTIONS_SUMMARY.md      Mode 1 함수 요약
│   └── FUNCTION_POINTER_TABLE_ANALYSIS.md  함수 포인터 테이블
│
├── 📂 categories/                      ← 카테고리별 분석
│   └── 01_asset_loading.md
│
└── 📂 functions/                       ← 개별 함수 상세 분석
    ├── FUN_1000_0b94.md                (스프라이트 로딩)
    ├── FUN_1000_0cd1.md                (비트 재배열)
    ├── FUN_1000_48e0.md                (디스패처)
    ├── FUN_1000_599d.md                (화면 업데이트)
    ├── FUN_1000_3830.md                ⭐ 메인 게임 루프
    ├── FUN_1000_0360.md                ⭐ 객체 업데이트
    └── ...
```

---

## 🎯 주요 문서

### 시스템 레벨 분석 (읽기 시작점)

1. **[MAIN_LOOP_COMPLETE_ANALYSIS.md](MAIN_LOOP_COMPLETE_ANALYSIS.md)** ⭐⭐⭐
   - 메인 게임 루프 완전 분석
   - 7개 객체 시스템
   - 렌더링 파이프라인
   - 메모리 맵 총정리
   - **최신 분석**: 2025-11-24

2. **[CALL_GRAPH.md](CALL_GRAPH.md)**
   - 전체 호출 구조
   - 실행 경로
   - 함수 간 관계

3. **[FUNCTION_POINTERS.md](FUNCTION_POINTERS.md)**
   - 11개 디스패처 테이블
   - 가상 함수 테이블 패턴
   - 동적 함수 호출

4. **[MODE2_COMPLETE_ANALYSIS.md](MODE2_COMPLETE_ANALYSIS.md)**
   - Mode 1 vs Mode 2 비교
   - CGA vs EGA 시스템
   - 22개 함수 복구 과정
   - 34KB, 매우 상세!

### 방법론

5. **[RECOVERING_MISSED_FUNCTIONS.md](RECOVERING_MISSED_FUNCTIONS.md)**
   - Ghidra가 놓친 함수 복구 3단계
   - Mode 1/Mode 2 함수 찾기
   - pyghidra 활용법

6. **[ANALYSIS_MISTAKES.md](ANALYSIS_MISTAKES.md)**
   - 실수 기록 및 교훈
   - 성공/실패한 접근법

### 개별 함수 분석

7. **functions/** 디렉토리
   - 현재 6개 함수 상세 분석
   - 각 함수별 독립 문서
   - 템플릿 기반 일관된 형식

---

## 📊 분석 현황 (2025-11-24)

### 전체 통계
- **전체 함수**: 137개 (118 + 19 복구)
- **상세 분석 완료**: 7개 (5%)
- **시스템 이해도**: 40%
- **문서화 완료**: 11개

### 분석 완료 함수 (7개)

| 함수 | 카테고리 | 중요도 | 문서 |
|------|----------|--------|------|
| FUN_1000_3830 | 메인 루프 | ⭐⭐⭐ | MAIN_LOOP_COMPLETE_ANALYSIS.md |
| FUN_1000_0360 | 객체 업데이트 | ⭐⭐⭐ | MAIN_LOOP_COMPLETE_ANALYSIS.md |
| FUN_1000_3e6d | 상태 관리 | ⭐⭐ | MAIN_LOOP_COMPLETE_ANALYSIS.md |
| FUN_1000_3f71 | 렌더링 | ⭐⭐⭐ | MAIN_LOOP_COMPLETE_ANALYSIS.md |
| FUN_1000_0b94 | 에셋 로딩 | ⭐⭐⭐ | functions/FUN_1000_0b94.md |
| FUN_1000_0cd1 | 비트 재배열 | ⭐⭐⭐ | functions/FUN_1000_0cd1.md |
| FUN_1000_48e0 | 디스패처 | ⭐⭐ | functions/FUN_1000_48e0.md |

### 다음 우선순위 (P0)

1. ⭐⭐⭐ **FUN_1000_12c0** - Blit 함수 (미발견!)
2. ⭐⭐ **메인 루프 14개 함수** - 나머지 분석
3. ⭐⭐ **입력 처리 함수** - 찾기 필요

---

## 🔍 문서 찾기

### 주제별

**메인 루프 이해하고 싶다면**:
→ [MAIN_LOOP_COMPLETE_ANALYSIS.md](MAIN_LOOP_COMPLETE_ANALYSIS.md)

**함수 포인터 시스템 이해하고 싶다면**:
→ [FUNCTION_POINTERS.md](FUNCTION_POINTERS.md)

**Mode 2 (EGA) 이해하고 싶다면**:
→ [MODE2_COMPLETE_ANALYSIS.md](MODE2_COMPLETE_ANALYSIS.md)

**특정 함수 찾고 싶다면**:
→ [INDEX.md](INDEX.md) 또는 `functions/` 디렉토리

**분석 방법 배우고 싶다면**:
→ [RECOVERING_MISSED_FUNCTIONS.md](RECOVERING_MISSED_FUNCTIONS.md)

### 함수 주소로 찾기

```bash
# 함수 주소로 문서 찾기
grep -r "1000:3830" docs/function-analysis/

# 메모리 주소로 찾기
grep -r "0x16c8" docs/function-analysis/
```

---

## 📝 새 함수 분석하기

### 1. 템플릿 사용
```bash
# 템플릿 복사
cp docs/ANALYSIS_DOCUMENTATION_GUIDE.md 참조
```

### 2. 파일 생성
```bash
# 위치: functions/FUN_1000_XXXX.md
# 형식: 가이드 참조
```

### 3. 체크포인트 업데이트
```bash
# output/checkpoints/phase4.json 수정
```

---

## 🔗 관련 문서

- [분석 문서화 가이드](../ANALYSIS_DOCUMENTATION_GUIDE.md) - 작성 방법
- [작업 원칙](../WORK_PRINCIPLES.md) - 기본 원칙
- [진행 상황](../PROGRESS.md) - 전체 로드맵
- [기술 문서](../technical/) - LZW, 스프라이트, 실행 경로

---

**최종 업데이트**: 2025-11-24
**Phase**: Phase 4 진행중 (75%)
**다음 목표**: FUN_1000_12c0 찾기
