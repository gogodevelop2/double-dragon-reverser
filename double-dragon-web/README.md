# Double Dragon Web Remake

오리지널 DOS 게임 더블 드래곤(1988)의 웹 버전 복각 프로젝트

## 프로젝트 구조

```
double-dragon-web/
├── src/                      # 소스 코드
│   ├── game/                 # 게임 로직
│   │   ├── entities/         # 게임 엔티티 (플레이어, 적, 아이템 등)
│   │   ├── systems/          # 게임 시스템 (충돌, AI, 물리 등)
│   │   ├── scenes/           # 게임 씬 (메뉴, 레벨, 게임오버 등)
│   │   └── assets/           # 에셋 로더 및 관리
│   ├── engine/               # 게임 엔진 코어
│   ├── ui/                   # UI 컴포넌트
│   └── utils/                # 유틸리티 함수
├── public/                   # 정적 파일
│   ├── assets/               # 게임 에셋
│   │   ├── sprites/          # 스프라이트 이미지
│   │   ├── audio/            # 사운드/음악
│   │   └── fonts/            # 폰트
│   └── data/                 # 게임 데이터 (레벨, 설정 등)
├── docs/                     # 프로젝트 문서
└── reference/                # 원본 DOS 게임 참조 파일
    └── dos-original/         # DOS 게임 원본 파일들

archive/                      # 아카이브 (프로젝트 외부)
├── Ddragon_1996_original.tar.gz          # 1996년 버전 백업
└── Double_Dragon_DOS_Files_EN.zip        # 2024년 버전 원본
```

## 기술 스택 (예정)

- **게임 엔진**: Phaser 3 / PixiJS (선택 필요)
- **언어**: TypeScript
- **빌드 도구**: Vite
- **스타일**: CSS/SCSS

## 개발 로드맵

### Phase 1: 분석 및 기획
- [ ] DOS 게임 에셋 분석 및 추출
- [ ] 게임 메카닉 분석
- [ ] 기술 스택 결정
- [ ] 프로토타입 개발

### Phase 2: 코어 개발
- [ ] 게임 엔진 기본 구조
- [ ] 플레이어 캐릭터 구현
- [ ] 기본 전투 시스템
- [ ] 레벨 1 구현

### Phase 3: 콘텐츠 확장
- [ ] 전체 레벨 구현
- [ ] 적 AI 구현
- [ ] 사운드/음악 추가
- [ ] UI/UX 개선

### Phase 4: 최적화 및 배포
- [ ] 성능 최적화
- [ ] 모바일 지원
- [ ] 웹 배포

## 참조

원본 DOS 게임 파일은 `reference/dos-original/` 폴더에 보관되어 있습니다.
