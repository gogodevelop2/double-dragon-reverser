#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/**
 * CGA Planar to Chunky 변환
 * FUN_1000_0cd1 재구현
 */
void cga_planar_to_chunky(uint8_t *data, size_t num_groups) {
    for (size_t i = 0; i < num_groups; i++) {
        uint8_t *ptr = data + (i * 4);

        // 4바이트 읽기
        uint8_t plane0 = ptr[0];
        uint8_t plane1 = ptr[1];
        uint8_t plane2 = ptr[2];
        uint8_t plane3 = ptr[3];

        // 2개 워드(4바이트) 출력
        uint16_t word0 = 0;
        uint16_t word1 = 0;

        // 각 비트 위치에서 4개 plane의 비트를 추출하여 재배열
        for (int bit = 7; bit >= 0; bit--) {
            int b0 = (plane0 >> bit) & 1;
            int b1 = (plane1 >> bit) & 1;
            int b2 = (plane2 >> bit) & 1;
            int b3 = (plane3 >> bit) & 1;

            int pixel = (b0 << 3) | (b1 << 2) | (b2 << 1) | b3;

            if (bit >= 4) {
                word0 = (word0 << 4) | pixel;
            } else {
                word1 = (word1 << 4) | pixel;
            }
        }

        // Little-endian으로 출력 (in-place)
        ptr[0] = word0 & 0xFF;
        ptr[1] = (word0 >> 8) & 0xFF;
        ptr[2] = word1 & 0xFF;
        ptr[3] = (word1 >> 8) & 0xFF;
    }
}

int main() {
    const char *input_file = "output/assets/raw_sprites/LINDA.dat";
    const char *output_file = "output/assets/processed/LINDA_processed.dat";

    printf("=== LINDA.EG1 Planar to Chunky 변환 ===\n\n");

    // 파일 읽기
    FILE *fp = fopen(input_file, "rb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open %s\n", input_file);
        return 1;
    }

    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    printf("입력 파일: %s\n", input_file);
    printf("파일 크기: %ld bytes\n", file_size);

    uint8_t *data = malloc(file_size);
    if (!data) {
        fprintf(stderr, "Error: Memory allocation failed\n");
        fclose(fp);
        return 1;
    }

    fread(data, 1, file_size, fp);
    fclose(fp);

    // 첫 바이트 확인
    printf("첫 바이트: 0x%02X (%d)\n\n", data[0], data[0]);

    // 첫 16바이트 출력 (변환 전)
    printf("변환 전 첫 16바이트:\n");
    for (int i = 0; i < 16; i++) {
        printf("%02X ", data[i]);
        if ((i + 1) % 4 == 0) printf(" ");
    }
    printf("\n\n");

    // 변환 수행
    // 파일 크기가 4의 배수여야 함
    size_t num_groups = file_size / 4;
    printf("변환 그룹 수: %zu (4바이트씩)\n", num_groups);

    cga_planar_to_chunky(data, num_groups);

    // 첫 16바이트 출력 (변환 후)
    printf("변환 후 첫 16바이트:\n");
    for (int i = 0; i < 16; i++) {
        printf("%02X ", data[i]);
        if ((i + 1) % 4 == 0) printf(" ");
    }
    printf("\n\n");

    // 픽셀 값 해석 (첫 8픽셀)
    printf("첫 8개 픽셀 값 (4-bit each):\n");
    for (int i = 0; i < 4; i++) {
        uint8_t byte = data[i];
        int pixel0 = (byte >> 4) & 0xF;
        int pixel1 = byte & 0xF;
        printf("  Pixel %d: %X, Pixel %d: %X\n",
               i*2, pixel0, i*2+1, pixel1);
    }
    printf("\n");

    // 파일 저장
    fp = fopen(output_file, "wb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot write %s\n", output_file);
        free(data);
        return 1;
    }

    fwrite(data, 1, file_size, fp);
    fclose(fp);
    free(data);

    printf("출력 파일: %s\n", output_file);
    printf("완료!\n");

    return 0;
}
