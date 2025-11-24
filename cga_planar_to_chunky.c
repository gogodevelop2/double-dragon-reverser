#include <stdio.h>
#include <stdint.h>
#include <string.h>

/**
 * CGA Planar to Chunky 변환
 *
 * FUN_1000_0cd1 함수 재구현
 *
 * 입력: 4개 바이트 (4 planar planes)
 * 출력: 4개 바이트 (8 pixels, chunky)
 *
 * 각 입력 바이트의 같은 비트 위치를 모아서
 * 하나의 4-bit 픽셀로 만듦
 */
void cga_planar_to_chunky(const uint8_t *input, uint8_t *output, size_t num_groups) {
    for (size_t i = 0; i < num_groups; i++) {
        // 4바이트 읽기
        uint8_t plane0 = input[0];
        uint8_t plane1 = input[1];
        uint8_t plane2 = input[2];
        uint8_t plane3 = input[3];

        // 2개 워드(4바이트) 출력
        uint16_t word0 = 0;
        uint16_t word1 = 0;

        // 각 비트 위치에서 4개 plane의 비트를 추출하여 재배열
        // bit 7부터 bit 0까지
        for (int bit = 7; bit >= 0; bit--) {
            // 각 plane에서 해당 비트 추출 (MSB first)
            int b0 = (plane0 >> bit) & 1;
            int b1 = (plane1 >> bit) & 1;
            int b2 = (plane2 >> bit) & 1;
            int b3 = (plane3 >> bit) & 1;

            // 4비트를 합쳐서 하나의 픽셀 색상 값 (0-15)
            int pixel = (b0 << 3) | (b1 << 2) | (b2 << 1) | b3;

            // bit 7-4는 word0에, bit 3-0은 word1에 저장
            if (bit >= 4) {
                word0 = (word0 << 4) | pixel;
            } else {
                word1 = (word1 << 4) | pixel;
            }
        }

        // Little-endian으로 출력
        output[0] = word0 & 0xFF;
        output[1] = (word0 >> 8) & 0xFF;
        output[2] = word1 & 0xFF;
        output[3] = (word1 >> 8) & 0xFF;

        input += 4;
        output += 4;
    }
}

// 테스트 함수
void test_conversion() {
    printf("=== CGA Planar to Chunky 변환 테스트 ===\n\n");

    // 테스트 케이스 1: 간단한 패턴
    uint8_t input1[4] = {
        0xFF,  // plane 0: 11111111
        0x00,  // plane 1: 00000000
        0xFF,  // plane 2: 11111111
        0x00   // plane 3: 00000000
    };
    uint8_t output1[4];

    cga_planar_to_chunky(input1, output1, 1);

    printf("테스트 1:\n");
    printf("입력:  %02X %02X %02X %02X\n",
           input1[0], input1[1], input1[2], input1[3]);
    printf("출력:  %02X %02X %02X %02X\n\n",
           output1[0], output1[1], output1[2], output1[3]);

    // 테스트 케이스 2: 체커보드 패턴
    uint8_t input2[4] = {
        0xAA,  // plane 0: 10101010
        0x55,  // plane 1: 01010101
        0xAA,  // plane 2: 10101010
        0x55   // plane 3: 01010101
    };
    uint8_t output2[4];

    cga_planar_to_chunky(input2, output2, 1);

    printf("테스트 2:\n");
    printf("입력:  %02X %02X %02X %02X\n",
           input2[0], input2[1], input2[2], input2[3]);
    printf("출력:  %02X %02X %02X %02X\n\n",
           output2[0], output2[1], output2[2], output2[3]);

    // 테스트 케이스 3: 실제 데이터 (LINDA.dat 첫 4바이트)
    uint8_t input3[4] = {
        0x3D,  // 00111101
        0x78,  // 01111000
        0xF8,  // 11111000
        0x38   // 00111000
    };
    uint8_t output3[4];

    cga_planar_to_chunky(input3, output3, 1);

    printf("테스트 3 (LINDA.dat):\n");
    printf("입력:  %02X %02X %02X %02X\n",
           input3[0], input3[1], input3[2], input3[3]);
    printf("출력:  %02X %02X %02X %02X\n\n",
           output3[0], output3[1], output3[2], output3[3]);

    // 픽셀 해석
    printf("픽셀 값 (4-bit each):\n");
    for (int i = 0; i < 4; i++) {
        uint8_t byte = output3[i];
        int pixel0 = (byte >> 4) & 0xF;
        int pixel1 = byte & 0xF;
        printf("  Byte %d: pixel %d = %X, pixel %d = %X\n",
               i, i*2, pixel0, i*2+1, pixel1);
    }
}

int main() {
    test_conversion();
    return 0;
}
