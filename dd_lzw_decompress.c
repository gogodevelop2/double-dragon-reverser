/**
 * Double Dragon LZW 압축 해제
 *
 * 디컴파일된 함수를 기반으로 정확히 재구현
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// 전역 변수 (0x6534~0x653a)
static int bits_to_read = 9;      // 0x6534
static int remaining_bytes = 0;   // 0x6536
static int bits_available = 0;    // 0x6538
static uint8_t bit_buffer = 0;    // 0x653a

// 입력 포인터
static uint8_t *input_ptr;

// 딕셔너리: 출력 버퍼의 포인터 배열
static uint8_t *dictionary[8192];
static int dict_size = 0;

// 출력 버퍼
static uint8_t *output_start;
static uint8_t *output_ptr;

/**
 * FUN_1000_604e: 초기화
 */
void init_decoder(void) {
    bits_available = 0;
    bits_to_read = 9;
    dict_size = 0;
}

/**
 * FUN_1000_6091: MSB-first 비트 읽기
 */
uint16_t read_bits(void) {
    uint16_t result = 0;
    int bits_needed = bits_to_read;

    while (bits_needed > 0) {
        bits_available--;

        if (bits_available < 0) {
            // 버퍼 리필
            if (remaining_bytes <= 0) {
                return 0xFFFF;  // 에러
            }

            bit_buffer = *input_ptr++;
            remaining_bytes--;
            bits_available = 7;  // 8비트 로드, 7개 남음
        }

        // MSB 추출
        uint8_t msb = (bit_buffer & 0x80) ? 1 : 0;

        // 왼쪽 시프트
        bit_buffer <<= 1;

        // 결과에 비트 추가
        result = (result << 1) | msb;

        bits_needed--;
    }

    return result;
}

/**
 * FUN_1000_605b: LZW 코드 디코드
 *
 * 딕셔너리는 [start_ptr, end_ptr] 쌍으로 저장됨
 * BP + (code - 0x101) * 2에 시작 포인터
 * BP + (code - 0x101) * 2 + 2에 끝 포인터
 */
void decode_code(uint16_t code) {
    if (code < 256) {
        // 리터럴 바이트
        *output_ptr++ = (uint8_t)code;
    }
    else {
        // 딕셔너리 참조 (code >= 257)
        // dict_idx = (code - 0x101) = (code - 257)
        int dict_idx = code - 257;

        if (dict_idx * 2 + 1 >= dict_size) {
            fprintf(stderr, "ERROR: Invalid dict index %d (code=%d, dict_size=%d)\n",
                    dict_idx, code, dict_size);
            return;
        }

        // 시작과 끝 포인터
        uint8_t *start = dictionary[dict_idx * 2];
        uint8_t *end = dictionary[dict_idx * 2 + 1];

        // 복사
        uint8_t *src = start;
        while (src < end) {
            *output_ptr++ = *src++;
        }
    }
}

/**
 * 딕셔너리 엔트리 저장
 *
 * FUN_1000_5ff3 라인 17-18:
 *   *unaff_SI = unaff_DI;    // 시작 포인터 저장
 *   unaff_SI = unaff_SI + 1;
 *
 * 다음 호출 전에 output_ptr이 증가하므로, 끝 포인터는 다음 엔트리의 시작
 */
void save_dictionary_entry(uint8_t *start_ptr) {
    if (dict_size < 8192 * 2) {
        dictionary[dict_size++] = start_ptr;  // 시작 포인터
    }
}

/**
 * FUN_1000_5ff3: 메인 LZW 디코더
 */
int decompress_lzw_main(uint8_t *input, int input_size, uint8_t *output, int max_output) {
    // 매직 체크
    if (input_size < 3 || input[0] != 0x1F || input[1] != 0x9D) {
        fprintf(stderr, "ERROR: Invalid magic number\n");
        return -1;
    }

    uint8_t flags = input[2];
    printf("Flags: 0x%02X (max_bits=%d, block=%d)\n",
           flags, (flags & 0x1F) + 9, (flags & 0x80) ? 1 : 0);

    // 초기화
    input_ptr = input + 3;
    remaining_bytes = input_size - 3;
    output_start = output;
    output_ptr = output;

    init_decoder();

    // 메인 루프 (FUN_1000_5ff3 정확히 재현)
    int codes_read = 0;

    while (1) {
        // 1. 딕셔너리에 현재 output_ptr 저장
        save_dictionary_entry(output_ptr);

        // 2. 코드 읽기 (256 스킵)
        uint16_t code;
        while (1) {
            code = read_bits();
            if (code == 0xFFFF) goto done;

            codes_read++;
            if (codes_read <= 50) {
                printf("Code #%d: %u (bits=%d, dict_size/2=%d)\n",
                       codes_read, code, bits_to_read, dict_size / 2);
            }

            if (code == 256) {
                bits_to_read++;
                printf("  -> bits_to_read increased to %d\n", bits_to_read);
            } else {
                break;
            }
        }

        // 3. 입력 끝 체크
        if (remaining_bytes == 0) {
            break;
        }

        // 4. 코드 디코드
        decode_code(code);

        // 5. 다음 코드 읽기
        while (1) {
            code = read_bits();
            if (code == 0xFFFF) goto done;

            codes_read++;

            if (code == 256) {
                bits_to_read++;
            } else {
                break;
            }
        }

        // 6. 입력 끝 체크
        if (remaining_bytes == 0) {
            break;
        }

        // 7. 두 번째 코드 디코드
        decode_code(code);
    }

done:
    printf("\nTotal codes: %d\n", codes_read);
    printf("Dictionary size: %d\n", dict_size);
    printf("Output size: %ld bytes\n", output_ptr - output_start);

    return output_ptr - output_start;
}

/**
 * 메인 함수
 */
int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <input.EG1> <output.dat>\n", argv[0]);
        return 1;
    }

    // 입력 파일 읽기
    FILE *fin = fopen(argv[1], "rb");
    if (!fin) {
        perror("fopen input");
        return 1;
    }

    fseek(fin, 0, SEEK_END);
    long input_size = ftell(fin);
    fseek(fin, 0, SEEK_SET);

    uint8_t *input = malloc(input_size);
    fread(input, 1, input_size, fin);
    fclose(fin);

    printf("Input file: %s (%ld bytes)\n", argv[1], input_size);

    // 출력 버퍼 (충분히 크게)
    uint8_t *output = malloc(1024 * 1024);  // 1MB

    // 압축 해제
    int output_size = decompress_lzw_main(input, input_size, output, 1024 * 1024);

    if (output_size > 0) {
        // 출력 파일 쓰기
        FILE *fout = fopen(argv[2], "wb");
        if (!fout) {
            perror("fopen output");
            return 1;
        }

        fwrite(output, 1, output_size, fout);
        fclose(fout);

        printf("SUCCESS: %s (%d bytes)\n", argv[2], output_size);
    }

    free(input);
    free(output);

    return output_size > 0 ? 0 : 1;
}
