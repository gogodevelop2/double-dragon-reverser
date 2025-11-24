# Double Dragon DOS 원본 파일 아카이브

더블 드래곤 DOS 버전 원본 파일들의 백업 아카이브

## 아카이브 내용

### Ddragon_1996_original.tar.gz
- **출처**: 1996년 버전
- **DDMAIN.EXE 크기**: 132,523 bytes
- **MD5**: 753a3e2b1f452235d32671c0ae619fb3
- **특징**:
  - 기본 게임 파일만 포함
  - READ.ME 파일 포함 (게임 설명서)
  - file_id.diz 포함
- **상태**: 테스트 완료, 정상 작동 확인

### Double_Dragon_DOS_Files_EN.zip
- **출처**: oldgamesdownload.com (2024년 3월)
- **DDMAIN.EXE 크기**: 105,352 bytes
- **MD5**: c7468a707c53e3c71cebc511f7cf6995
- **특징**:
  - Windows 호환성 파일 포함 (.PIF)
  - 듀얼 플레이 유틸리티 (DUAL.EXE)
  - 조이스틱/키보드 설정 도구
  - 비디오 모드 설정 도구
- **상태**: 테스트 완료, 정상 작동 확인
- **선택 사유**: 웹 복각 프로젝트의 레퍼런스 버전으로 선정

## 두 버전 비교

| 항목 | 1996 버전 | 2024 EN 버전 |
|------|-----------|--------------|
| EXE 크기 | 132KB | 105KB |
| 설정 도구 | 없음 | 있음 (3종) |
| Windows 지원 | 없음 | PIF 파일 포함 |
| 듀얼 플레이 | 기본 | DUAL.EXE |
| 문서 | READ.ME | ReadMe.txt |

## 사용 방법

### 압축 해제
```bash
# 1996 버전 압축 해제
tar -xzf Ddragon_1996_original.tar.gz

# 2024 EN 버전 압축 해제
unzip Double_Dragon_DOS_Files_EN.zip
```

### DOSBox-X 실행
```bash
# macOS (Homebrew)
/opt/homebrew/bin/dosbox-x DDMAIN.EXE -exit

# 또는 DRAGON.BAT 사용
/opt/homebrew/bin/dosbox-x DRAGON.BAT
```

## 주의사항

- 두 버전 모두 정상 작동이 확인되었습니다.
- 웹 복각 프로젝트는 2024 EN 버전을 레퍼런스로 사용합니다.
- 1996 버전은 비교 및 연구 목적으로 보관됩니다.
- 게임 에셋 추출 시 저작권에 유의하세요.

## 테스트 환경

- **OS**: macOS (Darwin 25.1.0)
- **에뮬레이터**: DOSBox-X 2025.10.07
- **테스트 날짜**: 2025-11-23
- **결과**: 두 버전 모두 정상 실행 확인

## 다음 단계

활성 프로젝트는 `/double-dragon-web/` 폴더에서 진행됩니다.
레퍼런스 파일은 `/reference/dos-original/` 폴더에 복사되어 있습니다.
