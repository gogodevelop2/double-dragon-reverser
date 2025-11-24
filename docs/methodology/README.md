# DOS 게임 리버스 엔지니어링 방법론

**목적**: Double Dragon DOS 프로젝트에서 검증된 리버스 엔지니어링 방법론을 체계화하여, 다른 DOS 게임 프로젝트에서 재사용 가능하게 만듭니다.

---

## 📖 문서 목록

### [01_PROCESS_OVERVIEW.md](01_PROCESS_OVERVIEW.md)
**Phase 0-4 전체 프로세스**
- 5단계 리버스 엔지니어링 프로세스
- 각 Phase의 목표와 산출물
- 시간 배분 및 우선순위
- Double Dragon 프로젝트 타임라인

**읽어야 하는 사람**: 모두 (전체 프로세스 이해)

---

### [02_TOOLS_AND_SETUP.md](02_TOOLS_AND_SETUP.md)
**도구 세팅 및 환경 구성**
- Ghidra 11.4.2 설치 및 설정
- pyghidra 2.2.0 세팅
- Spice86 실행 추적
- DOSBox-X 디버깅
- Python 스크립트 환경

**읽어야 하는 사람**: 프로젝트 시작하는 사람

---

### [03_DECOMPILATION.md](03_DECOMPILATION.md)
**디컴파일 전략**
- 자동 vs 수동 디컴파일
- 함수 포인터 처리
- thunk 함수 처리
- 점프 테이블 복구
- 일괄 디컴파일 스크립트

**읽어야 하는 사람**: Phase 1 작업자

---

### [04_ANALYSIS_TECHNIQUES.md](04_ANALYSIS_TECHNIQUES.md)
**함수 분석 기법**
- 실행 경로 추적 (가장 중요!)
- 호출 그래프 활용
- 메모리 패턴 인식
- Work Buffer 패턴
- 점프 테이블 발견
- 압축 알고리즘 식별

**읽어야 하는 사람**: Phase 2-4 작업자 (핵심!)

---

### [05_DOCUMENTATION.md](05_DOCUMENTATION.md)
**문서화 방법**
- 언어 중립적 문서 작성
- 의사코드 작성법
- 메모리 맵 기록
- 시스템 다이어그램
- 아카이빙 전략

**읽어야 하는 사람**: 문서 작성자

---

### [06_LESSONS_LEARNED.md](06_LESSONS_LEARNED.md)
**실수와 배운 점**
- 실패한 접근법 (피해야 할 것)
- 성공한 접근법 (따라할 것)
- 시간 낭비 방지
- 도구 선택 기준
- 분석 우선순위

**읽어야 하는 사람**: 모두 (필독!)

---

## 🎯 이 방법론의 특징

### 1. 검증됨
- Double Dragon DOS (72KB, 161개 함수) 100% 완료
- 14시간 만에 완전 분석
- 18,096줄 문서화

### 2. 재사용 가능
- 게임 특정 내용 분리
- 일반적 패턴 추출
- 도구 체인 정립

### 3. 효율적
- Phase 1: 118개 함수 자동 디컴파일 (2.2분)
- Phase 4.5: 15개 누락 함수 복구 (5분)
- Phase 4.6: 9개 점프 테이블 복구 (5분)

---

## 🔬 핵심 원칙

### "실행 경로를 따라가라"
> 72KB 프로그램은 entry point부터 순차적으로 따라가면 모든 것을 알 수 있다.

**성공한 방법**:
1. Entry point 찾기 (`FUN_1000_029a`)
2. 초기화 함수 추적
3. 메인 루프 발견
4. 함수 포인터 추적
5. 점프 테이블 복구

**실패한 방법**:
- ❌ 개별 함수만 분석
- ❌ 메모리 덤프에서 데이터 추출
- ❌ 중요도 모르고 순서 없이 분석

---

## 📊 프로세스 요약

```
Phase 0: 환경 준비 (5분)
  → Ghidra + pyghidra + Spice86

Phase 1: 자동 디컴파일 (2.2분)
  → 118개 함수 자동 추출

Phase 2: 코드 분석 (1시간)
  → 카테고리 분류, 네이밍

Phase 3: 에셋 분석 (2시간)
  → LZW 압축 해제, 36개 파일

Phase 4: 완전 분석 (14시간)
  → 161개 함수 100% 분석
  → 5개 점프 테이블 발견
  → 18,096줄 문서화
```

---

## 🛠️ 필요한 도구

### 필수
- **Ghidra 11.4.2**: 디컴파일러
- **Python 3.9+**: 스크립트 환경
- **pyghidra 2.2.0**: Python ↔ Ghidra 브릿지

### 권장
- **Spice86**: 실행 추적 (호출 그래프)
- **DOSBox-X**: 디버깅
- **HxD**: 16진수 편집기

### 선택
- **IDA Pro**: 대안 디컴파일러
- **Radare2**: 명령줄 분석
- **Ghidra MCP**: Claude Code 통합

---

## 📈 예상 소요 시간 (72KB 게임 기준)

| Phase | 시간 | 자동화 가능 |
|-------|------|-------------|
| 0: 환경 준비 | 5분 | 50% |
| 1: 디컴파일 | 5분 | 95% |
| 2: 코드 분석 | 1-2시간 | 30% |
| 3: 에셋 분석 | 2-4시간 | 50% |
| 4: 완전 분석 | 10-20시간 | 20% |
| **총계** | **15-30시간** | **40%** |

---

## 🎓 적용 대상

### 이 방법론이 적합한 게임
- ✅ DOS 시대 게임 (1985-1995)
- ✅ 작은 크기 (50-500KB 실행 파일)
- ✅ x86 16-bit (Real Mode)
- ✅ 단일 실행 파일

### 수정 필요한 경우
- 🔄 Protected Mode (32-bit)
- 🔄 큰 게임 (1MB+)
- 🔄 다중 실행 파일
- 🔄 복잡한 DRM/암호화

---

## 📚 참고 자료

### Double Dragon 프로젝트
- [PROGRESS.md](../PROGRESS.md): 전체 진행 상황
- [archive/phase4-analysis/](../archive/phase4-analysis/): 원본 분석 문서
- [WORK_PRINCIPLES.md](../WORK_PRINCIPLES.md): 작업 원칙

### 외부 자료
- Ghidra 공식 문서: https://ghidra-sre.org/
- pyghidra GitHub: https://github.com/dod-cyber-crime-center/pyghidra
- Spice86 GitHub: https://github.com/OpenRakis/Spice86

---

## 🚀 빠른 시작

### 1단계: 도구 설치
```bash
# Ghidra 11.4.2 다운로드 및 설치
# Java JDK 21 설치
# Python 환경 설정
pip install pyghidra
```

### 2단계: 방법론 읽기
1. `01_PROCESS_OVERVIEW.md` (15분)
2. `02_TOOLS_AND_SETUP.md` (30분)
3. `04_ANALYSIS_TECHNIQUES.md` (1시간) ← 핵심!
4. `06_LESSONS_LEARNED.md` (30분)

### 3단계: 프로젝트 시작
- Phase 0부터 순차적으로
- 각 Phase 완료 후 문서화
- 막히면 `06_LESSONS_LEARNED.md` 참조

---

## 💬 피드백

이 방법론은 **살아있는 문서**입니다. 다른 프로젝트 경험을 반영하여 지속적으로 개선됩니다.

개선 제안:
- 새로운 기법 발견
- 도구 업데이트
- 더 효율적인 방법
- 실수 사례

---

**작성일**: 2025-11-24
**기반 프로젝트**: Double Dragon DOS
**검증 상태**: ✅ 100% 완료
**다음 적용 대상**: TBD

**관련 문서**:
- [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)
- [../systems/README.md](../systems/README.md)
