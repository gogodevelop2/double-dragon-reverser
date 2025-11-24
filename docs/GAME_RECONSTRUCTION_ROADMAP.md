# Double Dragon 게임 복각 로드맵

**최종 목표**: 1988년 DOS 게임을 현대 C++ 코드로 재구성하여 웹 브라우저에서 플레이 가능하게 만들기

**현재 진행**: Phase 4 (70%)
**전체 진행**: 약 40%

---

## 📊 전체 로드맵

```
[완료] Phase 0-3: 분석 및 에셋 추출 (40%)
[진행] Phase 4: 게임 로직 완전 분석 (70% → 100%)
[예정] Phase 5: C++ 게임 엔진 구현 (0%)
[예정] Phase 6: 검증 및 디버깅 (0%)
[예정] Phase 7: 웹 이식 (0%)
[예정] Phase 8: 폴리싱 (0%)
```

---

## 🔄 Phase 4: 게임 로직 완전 분석 (남은 작업)

**목표**: 원본 게임의 모든 로직을 완전히 이해

### 4.1 렌더링 시스템 완성 ⭐⭐⭐ (최우선)

**현재 상태**:
- ✅ 메인 루프 파악
- ✅ 객체 업데이트 파이프라인 파악
- ❌ FUN_1000_12c0 (Blit 함수) 미발견
- ❌ 스프라이트 → 화면 최종 렌더링 미완성

**작업**:
```bash
1. FUN_1000_12c0 함수 찾기
   - Ghidra에서 1000:12c0 주소 직접 확인
   - 디컴파일 실패 원인 파악
   - 수동 어셈블리 분석

2. 스프라이트 렌더링 완성
   - LINDA.EG1 → PNG 성공적으로 변환
   - 나머지 5개 스프라이트 변환
   - 애니메이션 프레임 구조 파악

3. 배경 렌더링
   - LEVEL*.PC1 → PNG 변환
   - 16-plane de-interleave 검증
   - 타일맵 구조 파악
```

**산출물**:
- 모든 스프라이트 PNG (플레이어, 적, 무기)
- 모든 배경 PNG (레벨 1-5)
- 렌더링 알고리즘 C++ 구현

### 4.2 입력 처리 시스템

**현재 상태**:
- ❌ 키보드/조이스틱 입력 함수 미분석

**작업**:
```bash
1. 입력 함수 찾기
   - DOS INT 16h (키보드) 호출 검색
   - INT 21h, 0x84 (조이스틱) 검색

2. 입력 매핑 파악
   - 이동: 방향키/WASD
   - 공격: Ctrl/Alt
   - 점프: Space
   - 특수 기술: 조합키

3. 입력 버퍼 구조
   - 입력 상태 저장 위치
   - 버튼 눌림/떼짐 감지
```

**산출물**:
- 입력 처리 로직 문서
- 키 매핑 테이블

### 4.3 게임 로직 분석

**현재 상태**:
- ✅ 메인 루프 16개 함수 목록 파악
- ❌ 각 함수 역할 미분석

**작업**:
```bash
1. 전투 시스템
   - 공격 판정 (히트박스)
   - 데미지 계산
   - 체력 관리
   - 콤보 시스템

2. AI 시스템
   - 적 AI 패턴
   - 난이도별 차이
   - 보스 AI

3. 레벨 진행
   - 스테이지 전환
   - 스크롤링 로직
   - 이벤트 트리거

4. 충돌 감지
   - 플레이어-적 충돌
   - 플레이어-무기 충돌
   - 플레이어-배경 충돌
```

**산출물**:
- 게임 로직 완전 분석 문서
- 상태 다이어그램
- 데이터 테이블 (체력, 데미지, 속도 등)

### 4.4 사운드 시스템 (선택)

**작업**:
```bash
1. 사운드 파일 찾기
   - .SND, .VOC 파일 검색
   - PC Speaker 출력 코드 검색

2. 사운드 재생 로직
   - 효과음 트리거
   - 배경음악 루프
```

**예상 기간**: 2주

---

## 🏗️ Phase 5: C++ 게임 엔진 구현

**목표**: 원본 로직을 현대 C++17로 재구성

### 5.1 프로젝트 구조 설계

```
DoubleDragonRemake/
├── CMakeLists.txt
├── include/
│   ├── Engine/
│   │   ├── GameEngine.hpp
│   │   ├── Renderer.hpp
│   │   ├── InputManager.hpp
│   │   ├── AudioManager.hpp
│   │   └── ResourceManager.hpp
│   ├── Game/
│   │   ├── GameObject.hpp
│   │   ├── Player.hpp
│   │   ├── Enemy.hpp
│   │   ├── Weapon.hpp
│   │   └── Level.hpp
│   └── Utils/
│       ├── LZWDecompressor.hpp
│       ├── SpriteLoader.hpp
│       └── Vector2D.hpp
├── src/
│   ├── Engine/
│   ├── Game/
│   └── main.cpp
├── assets/
│   ├── sprites/
│   ├── levels/
│   └── sounds/
└── tests/
```

### 5.2 핵심 클래스 구현

#### 5.2.1 게임 엔진
```cpp
class GameEngine {
public:
    void init();
    void run();
    void shutdown();

private:
    void update(float deltaTime);
    void render();

    Renderer renderer_;
    InputManager input_;
    AudioManager audio_;
    ResourceManager resources_;

    std::vector<GameObject*> objects_;  // 7개 객체
    Level currentLevel_;

    // 원본 메모리 맵 재현
    uint8_t player1State_;  // 0x16c8
    uint8_t player2State_;  // 0x16e0
    uint16_t frameCounter_; // 0x16b0
};
```

#### 5.2.2 렌더링 시스템
```cpp
class Renderer {
public:
    void init(int width, int height);
    void clear();
    void drawSprite(const Sprite& sprite, int x, int y);
    void drawBackground(const Background& bg);
    void present();

private:
    // SDL2 또는 SFML
    SDL_Renderer* sdlRenderer_;

    // 원본 VGA 동기화 재현
    void waitVSync();
};
```

#### 5.2.3 게임 객체
```cpp
struct GameObject {
    uint8_t type;      // 0x168f
    uint8_t state;     // 0x1691
    uint8_t timer;     // 0x1694
    uint16_t spriteId; // 0x1695
    int16_t x;         // 0x1697
    int16_t y;         // 0x1699

    // 가상 함수 (원본 함수 포인터 재현)
    virtual void update() = 0;
    virtual void render(Renderer& renderer) = 0;
};

class Player : public GameObject {
public:
    void update() override;
    void render(Renderer& renderer) override;

    void handleInput(const InputState& input);
    void attack();
    void jump();

private:
    int health_;
    int lives_;
};

class Enemy : public GameObject {
public:
    void update() override;
    void render(Renderer& renderer) override;

    void updateAI();

private:
    AIState aiState_;
};
```

#### 5.2.4 리소스 관리
```cpp
class ResourceManager {
public:
    void loadAllAssets();

    Sprite* getSprite(const std::string& name);
    Background* getBackground(const std::string& name);
    Sound* getSound(const std::string& name);

private:
    LZWDecompressor decompressor_;
    SpriteLoader spriteLoader_;

    std::map<std::string, Sprite> sprites_;
    std::map<std::string, Background> backgrounds_;
};
```

### 5.3 원본 로직 이식

**전략**: 디컴파일 코드를 한 줄씩 C++로 변환

**예시**: FUN_1000_0360 → GameEngine::updateObjects()
```cpp
// 원본 (디컴파일)
void FUN_1000_0360(void) {
  uStack_2 = 0x16c6;
  do {
    if ((uStack_2 < 0x16f6) || (*(char *)(uStack_2 + 2) != '\0')) {
      FUN_1000_0412();
      // ...
    }
    uStack_2 = uStack_2 + 0x18;
  } while (uStack_2 != 0x176e);
}

// C++ 버전
void GameEngine::updateObjects() {
  for (GameObject* obj : objects_) {
    if (obj->isActive()) {
      obj->update();

      if (obj->needsCollisionCheck()) {
        checkCollisions(obj);
      }

      obj->updateBehavior();
      obj->render(renderer_);
    }
  }
}
```

### 5.4 데이터 주도 설계

**게임 데이터를 코드에서 분리**:

```json
// data/characters.json
{
  "player1": {
    "name": "Billy Lee",
    "health": 100,
    "speed": 2,
    "sprites": {
      "idle": "PLAYER1_idle.png",
      "walk": "PLAYER1_walk.png",
      "punch": "PLAYER1_punch.png"
    },
    "attacks": [
      {"name": "punch", "damage": 10, "frames": 5},
      {"name": "kick", "damage": 15, "frames": 8}
    ]
  }
}

// data/levels.json
{
  "level1": {
    "background": "LEVEL11.png",
    "music": "level1.ogg",
    "enemies": [
      {"type": "abobo", "x": 100, "y": 50, "count": 3}
    ]
  }
}
```

**예상 기간**: 4주

---

## 🧪 Phase 6: 검증 및 디버깅

**목표**: 원본과 동일하게 동작하는지 확인

### 6.1 단위 테스트

```cpp
// tests/test_lzw.cpp
TEST(LZWDecompressor, DecompressLinda) {
    LZWDecompressor decompressor;
    auto result = decompressor.decompress("LINDA.EG1");

    // 원본 결과와 비교
    EXPECT_EQ(result.size(), 237);
    EXPECT_EQ(result[0], 0x3D);
}

// tests/test_collision.cpp
TEST(CollisionDetection, PlayerEnemyCollision) {
    Player player(100, 100);
    Enemy enemy(105, 100);

    EXPECT_TRUE(checkCollision(player, enemy));
}
```

### 6.2 통합 테스트

**시나리오 기반 테스트**:
```cpp
TEST(GameScenario, Level1Complete) {
    GameEngine engine;
    engine.loadLevel(1);

    // 시뮬레이션
    for (int frame = 0; frame < 1000; frame++) {
        engine.update(1.0f/60.0f);
    }

    EXPECT_EQ(engine.getPlayerScore(), expectedScore);
}
```

### 6.3 원본과 비교 검증

**방법**:
1. DOSBox에서 원본 실행 → 스크린샷
2. 리메이크 실행 → 스크린샷
3. 픽셀 단위 비교

```python
# verify_rendering.py
import cv2
import numpy as np

original = cv2.imread('original_frame.png')
remake = cv2.imread('remake_frame.png')

diff = cv2.absdiff(original, remake)
similarity = 100 - (np.sum(diff) / diff.size)

print(f"Similarity: {similarity}%")
```

**예상 기간**: 2주

---

## 🌐 Phase 7: 웹 이식

**목표**: 브라우저에서 플레이 가능하게 만들기

### 7.1 Emscripten 컴파일

```bash
# CMakeLists.txt 수정
if(EMSCRIPTEN)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -s USE_SDL=2")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -s WASM=1")
endif()

# 빌드
emconfigure cmake ..
emmake make
```

### 7.2 웹 렌더링

**SDL2 → Canvas API**:
```cpp
#ifdef __EMSCRIPTEN__
    #include <emscripten.h>
    #include <emscripten/html5.h>

    void mainLoop() {
        gameEngine.update(1.0f/60.0f);
        gameEngine.render();
    }

    int main() {
        gameEngine.init();
        emscripten_set_main_loop(mainLoop, 60, 1);
    }
#else
    int main() {
        gameEngine.init();
        while (running) {
            gameEngine.update(deltaTime);
            gameEngine.render();
        }
    }
#endif
```

### 7.3 웹 UI

```html
<!DOCTYPE html>
<html>
<head>
    <title>Double Dragon - Browser Edition</title>
    <style>
        #canvas {
            border: 2px solid black;
            image-rendering: pixelated;
        }
    </style>
</head>
<body>
    <h1>Double Dragon (1988) - Remake</h1>
    <canvas id="canvas" width="320" height="200"></canvas>

    <div id="controls">
        <p>Arrow Keys: Move</p>
        <p>Z: Punch, X: Kick, C: Jump</p>
    </div>

    <script src="double-dragon.js"></script>
</body>
</html>
```

### 7.4 모바일 대응

**터치 컨트롤**:
```javascript
// virtual-gamepad.js
const gamepad = {
    up: false,
    down: false,
    left: false,
    right: false,
    punch: false,
    kick: false
};

document.getElementById('btn-up').addEventListener('touchstart', () => {
    gamepad.up = true;
});
```

**예상 기간**: 2주

---

## ✨ Phase 8: 폴리싱

**목표**: 게임 경험 향상

### 8.1 그래픽 향상 (선택)

- **업스케일링**: CGA 4색 → HD 렌더링
- **CRT 쉐이더**: 레트로 느낌
- **스무스 애니메이션**: 보간

### 8.2 사운드 개선

- **오리지널 PC Speaker → 현대 오디오**
- **배경음악 리마스터**
- **효과음 개선**

### 8.3 추가 기능

- **세이브/로드**
- **리플레이 기능**
- **온라인 협동**
- **리더보드**

### 8.4 문서화

```
DoubleDragonRemake/
├── README.md
├── BUILDING.md
├── ARCHITECTURE.md
├── REVERSE_ENGINEERING.md
└── LICENSE.md
```

**예상 기간**: 2주

---

## 📅 전체 타임라인

| Phase | 작업 | 기간 | 누적 |
|-------|------|------|------|
| 0-3 | 분석 및 에셋 추출 | - | 완료 |
| 4 | 게임 로직 완전 분석 | 2주 | 2주 |
| 5 | C++ 게임 엔진 구현 | 4주 | 6주 |
| 6 | 검증 및 디버깅 | 2주 | 8주 |
| 7 | 웹 이식 | 2주 | 10주 |
| 8 | 폴리싱 | 2주 | 12주 |

**총 예상 기간**: 약 3개월 (풀타임 기준)

---

## 🎯 즉시 시작할 작업

### 1. FUN_1000_12c0 찾기 (1일)

```bash
# Ghidra에서 직접 확인
cd /Users/joejeon/Documents/develop/Double\ Dragon
source venv/bin/activate

python3 << 'EOF'
import pyghidra

# Ghidra 프로젝트 열기
project_location = "ghidra-project/DoubleDragon"
project_name = "DoubleDragon"

pyghidra.start()
project = pyghidra.open_program(
    "reference/dos-original/DDMAIN.EXE",
    project_location=project_location,
    project_name=project_name
)

from ghidra.program.model.address import AddressSet
from ghidra.app.decompiler import DecompInterface

# 1000:12c0 주소
addr = currentProgram.getAddressFactory().getAddress("1000:12c0")
func = getFunctionAt(addr)

if func:
    print(f"✅ 함수 발견: {func.getName()}")
    print(f"크기: {func.getBody().getNumAddresses()} bytes")

    # 디컴파일
    decompiler = DecompInterface()
    decompiler.openProgram(currentProgram)
    results = decompiler.decompileFunction(func, 30, None)

    if results.decompileCompleted():
        print("디컴파일 성공!")
        print(results.getDecompiledFunction().getC())
    else:
        print("디컴파일 실패, 어셈블리 확인:")
        listing = currentProgram.getListing()
        instructions = listing.getInstructions(func.getBody(), True)
        for instr in instructions:
            print(f"{instr.getAddress()}: {instr}")
else:
    print("❌ 함수 없음 - 수동 생성 필요")

    # 해당 위치 코드 확인
    listing = currentProgram.getListing()
    codeUnit = listing.getCodeUnitAt(addr)
    print(f"코드 유닛: {codeUnit}")
EOF
```

### 2. 첫 스프라이트 완벽 렌더링 (2일)

```bash
# LINDA.EG1 완벽 렌더링
python3 render_sprite_final.py
```

### 3. 미니 프로토타입 (1주)

**목표**: 플레이어 캐릭터만 움직이는 최소 데모

```cpp
// prototype/main.cpp
#include <SDL2/SDL.h>

int main() {
    SDL_Init(SDL_INIT_VIDEO);
    SDL_Window* window = SDL_CreateWindow("DD Proto",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        640, 400, 0);
    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, 0);

    // 플레이어 위치
    int playerX = 100, playerY = 100;

    bool running = true;
    while (running) {
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) running = false;
        }

        // 키보드 입력
        const Uint8* keys = SDL_GetKeyboardState(NULL);
        if (keys[SDL_SCANCODE_LEFT]) playerX -= 2;
        if (keys[SDL_SCANCODE_RIGHT]) playerX += 2;

        // 렌더링
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
        SDL_RenderClear(renderer);

        // 플레이어 (임시 사각형)
        SDL_Rect player = {playerX, playerY, 32, 48};
        SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255);
        SDL_RenderFillRect(renderer, &player);

        SDL_RenderPresent(renderer);
        SDL_Delay(16);  // ~60 FPS
    }

    SDL_Quit();
    return 0;
}
```

---

## 🎮 최종 비전

**6개월 후 완성 모습**:

```
https://yourdomain.com/double-dragon

┌─────────────────────────────────────────┐
│  DOUBLE DRAGON (1988) - Browser Remake  │
├─────────────────────────────────────────┤
│                                         │
│     [게임 화면 - 640x400 Canvas]        │
│                                         │
│  🕹️ Controls:                           │
│  Arrow Keys: Move                       │
│  Z: Punch  X: Kick  C: Jump             │
│                                         │
│  💾 Save  🔊 Sound: ON  📊 FPS: 60      │
│                                         │
│  📜 About | 🐙 GitHub | 📖 Docs         │
└─────────────────────────────────────────┘
```

**기술 스택**:
- C++17
- SDL2 (네이티브) / Emscripten (웹)
- WebAssembly
- Canvas API

**라이선스**: MIT + 원작 저작권 명시

---

**작성일**: 2025-11-24
**현재 위치**: Phase 4 (70%)
**다음 마일스톤**: Phase 4 완료 (2주 예상)
