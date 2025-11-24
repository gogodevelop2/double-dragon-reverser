// Double Dragon - 추출된 데이터 구조
// 디컴파일된 C 코드 패턴 분석 기반
// Generated: 2025-11-24

#pragma once

#include <cstdint>
#include <vector>
#include <array>

namespace DoubleDragon {

// =============================================================================
// 게임 엔티티 (플레이어, 적 등)
// =============================================================================

struct Entity {
    int16_t x;           // X 좌표
    int16_t y;           // Y 좌표
    int16_t width;       // 충돌 박스 너비
    int16_t height;      // 충돌 박스 높이
    uint8_t is_active;   // 활성화 상태
    uint8_t type;        // 엔티티 타입
    uint8_t direction;   // 방향 (좌/우)
    uint8_t anim_frame;  // 애니메이션 프레임
    int16_t health;      // 체력
    int16_t speed_x;     // X 속도
    int16_t speed_y;     // Y 속도
};

// 메모리 패턴: 0x3542 ~ 0x35AE (18 bytes 구조체 배열)
constexpr size_t MAX_ENEMIES = 6;

// =============================================================================
// 스프라이트 데이터
// =============================================================================

struct Sprite {
    uint16_t data_offset;   // 그래픽 데이터 오프셋
    uint8_t  width;         // 스프라이트 너비
    uint8_t  height;        // 스프라이트 높이
    uint16_t flags;         // 플래그 (mirrored, transparent 등)
};

// =============================================================================
// LZW 압축 해제 상태
// =============================================================================

struct LZWState {
    uint8_t* source_ptr;       // 압축 데이터 포인터
    uint8_t* dest_ptr;         // 출력 버퍼 포인터
    uint16_t remaining_bytes;  // 남은 입력 바이트
    uint8_t  bit_buffer;       // 비트 버퍼
    uint8_t  bits_available;   // 남은 비트 수
    uint16_t dict_size;        // 딕셔너리 크기
    void*    dict_base;        // 딕셔너리 베이스 주소
};

// 전역 위치: 0x6536, 0x6538, 0x653A

// =============================================================================
// CGA 그래픽 버퍼
// =============================================================================

struct CGABuffer {
    static constexpr uint16_t VIDEO_SEG = 0xB800;
    static constexpr size_t   WIDTH = 320;
    static constexpr size_t   HEIGHT = 200;
    static constexpr size_t   NUM_PLANES = 16;

    uint8_t planes[NUM_PLANES][WIDTH * HEIGHT / 8];
};

// =============================================================================
// 게임 상태
// =============================================================================

struct GameState {
    uint8_t  mode;          // 게임 모드 (0x38D1)
    uint16_t frame_counter; // 프레임 카운터 (0x38D3)
    uint8_t  level;         // 현재 레벨
    uint8_t  lives;         // 남은 목숨
    uint16_t score;         // 점수

    Entity player;          // 플레이어
    std::array<Entity, MAX_ENEMIES> enemies;  // 적 배열

    uint8_t input_state;    // 입력 상태 (키보드)
    uint8_t prev_input;     // 이전 입력

    // 애니메이션 관련
    uint16_t anim_timer;    // 애니메이션 타이머 (0x442E)
    uint8_t  anim_state;    // 애니메이션 상태

    // 충돌 감지
    bool collision_detected;
};

// =============================================================================
// 파일 로드 정보
// =============================================================================

struct FileHeader {
    uint16_t magic;         // 매직 넘버 (0x1F9D for LZW)
    uint16_t compressed_size;
    uint16_t uncompressed_size;
};

// =============================================================================
// 메모리 맵 (중요 주소들)
// =============================================================================

namespace MemoryMap {
    constexpr uint16_t GAME_STATE = 0x38D0;
    constexpr uint16_t ENEMY_ARRAY = 0x3542;
    constexpr uint16_t SPRITE_DATA = 0x16C6;
    constexpr uint16_t LZW_STATE = 0x6536;
    constexpr uint16_t PLAYER_X = 0x16C0;
    constexpr uint16_t PLAYER_Y = 0x16C2;
    constexpr uint16_t CGA_VIDEO = 0xB800;
}

} // namespace DoubleDragon
