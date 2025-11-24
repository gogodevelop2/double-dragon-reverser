# Double Dragon - C++ 클래스 설계

**날짜**: 2025-11-24
**기반**: Phase 1 디컴파일 코드 분석

---

## 📐 아키텍처 개요

```
┌─────────────────────────────────────────┐
│          GameEngine (메인 루프)         │
├─────────────────────────────────────────┤
│  - Initialize()                         │
│  - MainLoop()                          │
│  - Shutdown()                          │
└────────┬───────────┬──────────┬─────────┘
         │           │          │
    ┌────▼───┐  ┌───▼────┐ ┌──▼──────┐
    │Graphics│  │ Input  │ │GameLogic│
    │System  │  │Handler │ │         │
    └────┬───┘  └────────┘ └──┬──────┘
         │                    │
    ┌────▼───────┐      ┌────▼─────┐
    │Compression │      │ Entity   │
    │  (LZW/RLE) │      │ System   │
    └────────────┘      └──────────┘
```

---

## 🎯 핵심 클래스

### 1. GameEngine
**책임**: 게임 메인 루프 및 시스템 조율

```cpp
class GameEngine {
public:
    GameEngine();
    ~GameEngine();

    bool Initialize();
    void MainLoop();        // FUN_1000_3830 기반
    void Shutdown();

private:
    GraphicsSystem graphics_;
    InputHandler input_;
    GameState state_;
    EntityManager entities_;

    void ProcessInput();    // FUN_1000_0518
    void UpdateGame();
    void RenderFrame();     // FUN_1000_3c7e
};
```

**매핑**:
- `FUN_1000_3830` → `GameEngine::MainLoop()`
- `entry` → `main()` + `GameEngine::Initialize()`

---

### 2. GraphicsSystem
**책임**: CGA 그래픽 렌더링 및 압축 해제

```cpp
class GraphicsSystem {
public:
    bool Initialize();
    void RenderFrame(const GameState& state);
    void DrawSprite(int x, int y, const Sprite& sprite);  // FUN_1000_4780

private:
    // CGA 관련
    void ConvertToCGAPlanes(const uint8_t* src, size_t len);  // FUN_1000_0786
    void WriteToVideoMemory(const uint8_t* buffer);            // FUN_1000_09d1
    void BlitSprite(int x, int y, const Sprite& spr);          // FUN_1000_0cd1

    CGABuffer video_buffer_;
    std::vector<uint8_t> temp_buffer_;
};
```

**매핑**:
- `FUN_1000_0786` → `GraphicsSystem::ConvertToCGAPlanes()`
- `FUN_1000_09d1` → `GraphicsSystem::WriteToVideoMemory()`
- `FUN_1000_0cd1` → `GraphicsSystem::BlitSprite()`
- `FUN_1000_4780` → `GraphicsSystem::DrawSprite()`

---

### 3. CompressionSystem
**책임**: LZW 및 RLE 압축 해제

```cpp
class CompressionSystem {
public:
    // LZW (Unix compress 호환)
    std::vector<uint8_t> DecompressLZW(const uint8_t* data, size_t size);

    // RLE
    std::vector<uint8_t> DecompressRLE(const uint8_t* data, size_t size);

private:
    // LZW 헬퍼
    uint16_t ReadBits(int num_bits);     // FUN_1000_6091
    void DecodeLZWCode(uint16_t code);   // FUN_1000_605b

    LZWState lzw_state_;
};
```

**매핑**:
- `FUN_1000_6091` → `CompressionSystem::ReadBits()`
- `FUN_1000_605b` → `CompressionSystem::DecodeLZWCode()`
- `FUN_1000_2865` → `CompressionSystem::DecompressRLE()`

---

### 4. EntityManager
**책임**: 플레이어 및 적 엔티티 관리

```cpp
class EntityManager {
public:
    void Update(float delta_time);
    void UpdateEnemies(const Entity& player);  // FUN_1000_3e6d

    Entity& GetPlayer() { return player_; }
    std::array<Entity, MAX_ENEMIES>& GetEnemies() { return enemies_; }

private:
    void UpdatePositions();     // FUN_1000_029a
    bool CheckCollision(const Entity& a, const Entity& b);  // FUN_1000_034b
    void MovePlayer(int dx, int dy);  // FUN_1000_0360
    void UpdateAnimation(Entity& entity);  // FUN_1000_03ca

    Entity player_;
    std::array<Entity, MAX_ENEMIES> enemies_;
};
```

**매핑**:
- `FUN_1000_029a` → `EntityManager::UpdatePositions()`
- `FUN_1000_034b` → `EntityManager::CheckCollision()`
- `FUN_1000_0360` → `EntityManager::MovePlayer()`
- `FUN_1000_03ca` → `EntityManager::UpdateAnimation()`
- `FUN_1000_3e6d` → `EntityManager::UpdateEnemies()`

---

### 5. InputHandler
**책임**: 키보드 입력 처리

```cpp
class InputHandler {
public:
    void Update();
    bool IsKeyPressed(Key key) const;
    uint8_t GetInputState() const { return input_state_; }

private:
    uint8_t ReadKeyboard();  // FUN_1000_0612

    uint8_t input_state_;
    uint8_t prev_input_;
};
```

**매핑**:
- `FUN_1000_0612` → `InputHandler::ReadKeyboard()`
- `FUN_1000_0518` → `InputHandler::Update()` + 게임 로직 연동

---

### 6. ResourceLoader
**책임**: 파일 로드 및 압축 해제

```cpp
class ResourceLoader {
public:
    std::vector<uint8_t> LoadFile(const std::string& filename);
    std::vector<Sprite> LoadSprites(const std::string& filename);

private:
    bool FileOpen(const std::string& path);  // FUN_1000_1e8a
    size_t FileRead(void* buffer, size_t size);  // FUN_1000_0d8e

    CompressionSystem compressor_;
    FILE* current_file_;
};
```

**매핑**:
- `FUN_1000_1e8a` → `ResourceLoader::FileOpen()`
- `FUN_1000_0d8e` → `ResourceLoader::FileRead()`

---

## 🔧 유틸리티 함수

분석 결과 35개의 유틸리티 함수 발견:

```cpp
namespace Util {
    // 메모리 조작
    void MemoryCopy(void* dest, const void* src, size_t n);  // FUN_1000_0771

    // 문자열
    int StringCompare(const char* a, const char* b);  // FUN_1000_0b54

    // 수학
    int Multiply(int a, int b);  // FUN_1000_0dd6

    // 난수
    uint16_t RandomNumber();  // FUN_1000_0e30

    // 타이머
    uint32_t TimerRead();  // FUN_1000_16e0
}
```

---

## 📦 데이터 흐름

### 게임 시작 흐름

```
main()
  ↓
GameEngine::Initialize()
  ├─> GraphicsSystem::Initialize()
  │     └─> FUN_1000_093a (CGA 모드 설정)
  │
  ├─> ResourceLoader::LoadSprites()
  │     ├─> FUN_1000_1e8a (파일 열기)
  │     ├─> FUN_1000_0d8e (파일 읽기)
  │     └─> CompressionSystem::DecompressLZW()
  │           ├─> FUN_1000_6091 (비트 읽기)
  │           └─> FUN_1000_605b (LZW 디코딩)
  │
  └─> EntityManager::Reset()
        └─> FUN_1000_0b94 (게임 데이터 로드)
```

### 메인 루프 흐름

```
GameEngine::MainLoop()  [FUN_1000_3830]
  ↓
  ├─> InputHandler::Update()  [FUN_1000_0518]
  │     └─> FUN_1000_0612 (키보드 읽기)
  │
  ├─> EntityManager::Update()
  │     ├─> UpdatePositions()  [FUN_1000_029a]
  │     ├─> UpdateEnemies()    [FUN_1000_3e6d]
  │     ├─> CheckCollision()   [FUN_1000_034b]
  │     └─> UpdateAnimation()  [FUN_1000_03ca]
  │
  └─> GraphicsSystem::RenderFrame()  [FUN_1000_3c7e]
        └─> DrawSprite()  [FUN_1000_4780]
              ├─> ConvertToCGAPlanes()  [FUN_1000_0786]
              └─> WriteToVideoMemory()  [FUN_1000_09d1]
```

---

## 🎯 다음 단계 (Phase 3)

1. **실제 C++ 구현**
   - 각 클래스 헤더 파일 작성
   - 소스 파일 구현
   - CMake 빌드 시스템

2. **에셋 추출**
   - .EG1, .PC1 파일 파싱
   - 스프라이트 추출
   - PNG로 변환

3. **테스트**
   - 압축 해제 검증
   - 그래픽 렌더링 확인
   - 게임 로직 동작 테스트

---

**생성**: 2025-11-24
**상태**: Phase 2 설계 완료
