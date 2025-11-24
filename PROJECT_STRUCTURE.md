# 더블 드래곤 웹 복각 프로젝트 구조

## 전체 디렉토리 구조

```
Double Dragon/
│
├── double-dragon-web/              # 🎮 웹 복각 프로젝트 (메인 작업 폴더)
│   ├── src/
│   │   ├── game/
│   │   │   ├── entities/           # 플레이어, 적, 아이템 엔티티
│   │   │   ├── systems/            # 충돌, AI, 물리 시스템
│   │   │   ├── scenes/             # 메뉴, 레벨, 게임오버 씬
│   │   │   └── assets/             # 에셋 로더 및 관리
│   │   ├── engine/                 # 게임 엔진 코어
│   │   ├── ui/                     # UI 컴포넌트
│   │   └── utils/                  # 유틸리티 함수
│   ├── public/
│   │   ├── assets/
│   │   │   ├── sprites/            # 추출/변환된 스프라이트
│   │   │   ├── audio/              # 사운드/음악 파일
│   │   │   └── fonts/              # 폰트 파일
│   │   └── data/                   # 레벨, 설정 JSON 데이터
│   ├── docs/                       # 개발 문서
│   └── README.md                   # 프로젝트 메인 문서
│
├── reference/                      # 📚 레퍼런스 파일 (읽기 전용)
│   ├── dos-original/               # DOS 게임 원본 파일 (작업용 복사본)
│   │   ├── DDMAIN.EXE             # 메인 실행 파일
│   │   ├── *.EG1, *.EG2           # 캐릭터 스프라이트
│   │   ├── LEVEL*.PC1             # 레벨 데이터
│   │   ├── *.NW1~NW5              # 애니메이션 프레임
│   │   └── ...
│   └── DOS_ASSETS_ANALYSIS.md      # 에셋 분석 문서
│
├── archive/                        # 📦 원본 백업 (보관용)
│   ├── Ddragon_1996_original.tar.gz          # 1996년 버전 백업
│   ├── Double_Dragon_DOS_Files_EN.zip        # 2024년 EN 버전 원본
│   └── README.md                              # 아카이브 설명 문서
│
├── Ddragon/                        # ⚠️ 삭제 예정 (archive에 백업됨)
│   └── [1996년 버전 파일들...]
│
├── Double_Dragon_DOS_Files_EN/     # ⚠️ 삭제 예정 (reference에 복사됨)
│   └── [2024년 EN 버전 파일들...]
│
└── PROJECT_STRUCTURE.md            # 이 문서
```

## 폴더별 상세 설명

### 🎮 double-dragon-web/
**용도**: 웹 복각 프로젝트의 메인 작업 폴더
**상태**: 개발 진행 중
**기술**: TypeScript + Phaser3/PixiJS (예정)

### 📚 reference/
**용도**: DOS 원본 게임 파일 레퍼런스
**상태**: 읽기 전용
**내용**: Double_Dragon_DOS_Files_EN의 DD1 폴더 복사본
**DOSBox 실행**:
```bash
cd reference/dos-original
/opt/homebrew/bin/dosbox-x DDMAIN.EXE -exit
```

### 📦 archive/
**용도**: 원본 파일 백업 보관
**상태**: 보관 전용 (수정 금지)
**내용**:
- 1996년 버전 (tar.gz)
- 2024년 EN 버전 (zip)
- 두 버전 비교 문서

## 정리 예정 항목

다음 항목들은 정리가 완료되어 삭제 예정입니다:

- ❌ `Ddragon/` - archive/Ddragon_1996_original.tar.gz에 백업됨
- ❌ `Double_Dragon_DOS_Files_EN/` - archive에 백업, reference에 복사됨

삭제 전 확인 사항:
```bash
# 아카이브 확인
ls -lh archive/

# 레퍼런스 확인
ls -lh reference/dos-original/
```

## 개발 워크플로우

1. **에셋 분석**: `reference/dos-original/` 파일들을 분석
2. **에셋 추출**: DOS 파일에서 그래픽/데이터 추출
3. **웹 변환**: `double-dragon-web/public/assets/`에 변환된 파일 저장
4. **개발**: `double-dragon-web/src/`에서 게임 로직 구현
5. **테스트**: 원본 DOS 게임과 비교하며 테스트

## 다음 단계

1. [ ] Ddragon 및 Double_Dragon_DOS_Files_EN 폴더 삭제 확인
2. [ ] 기술 스택 결정 (Phaser 3 vs PixiJS)
3. [ ] package.json 및 개발 환경 설정
4. [ ] DOS 에셋 추출 도구 조사
5. [ ] 첫 번째 프로토타입 개발 시작

## 참고 문서

- 프로젝트 개요: `double-dragon-web/README.md`
- 에셋 분석: `reference/DOS_ASSETS_ANALYSIS.md`
- 아카이브 정보: `archive/README.md`
