#!/usr/bin/env python3
"""
Double Dragon 커스텀 LZW 압축 해제 구현

FUN_1000_6091과 FUN_1000_605b 디컴파일 코드 기반
"""

import struct
from pathlib import Path

class DoubleDragonLZW:
    """Double Dragon 커스텀 LZW 압축 해제 (MSB-first 비트 읽기)"""

    def __init__(self):
        self.INIT_BITS = 9
        self.MAX_BITS = 13  # Double Dragon은 13비트 사용

        # FUN_1000_6091 전역 변수 (0x6534~0x653a)
        self.bits_to_read = 0      # 0x6534
        self.remaining_bytes = 0   # 0x6536
        self.bits_available = 0    # 0x6538
        self.bit_buffer = 0        # 0x653a
        self.source_ptr = 0

    def read_bits_msb(self, compressed_data, num_bits):
        """
        FUN_1000_6091 구현: MSB-first 비트 읽기

        게임의 실제 구현과 동일:
        - MSB부터 읽음 (cVar5 << 1)
        - 8비트 버퍼 사용
        """
        result = 0
        self.bits_to_read = num_bits

        while self.bits_to_read > 0:
            # 버퍼가 비었으면 새 바이트 읽기
            if self.bits_available <= 0:
                if self.remaining_bytes <= 0:
                    return None  # 데이터 끝

                self.bit_buffer = compressed_data[self.source_ptr]
                self.source_ptr += 1
                self.remaining_bytes -= 1
                self.bits_available = 8

            # MSB 추출 (게임 코드: bVar6 = cVar5 < '\0')
            msb = (self.bit_buffer >> 7) & 1

            # 버퍼 왼쪽 시프트 (게임 코드: cVar5 = cVar5 << 1)
            self.bit_buffer = (self.bit_buffer << 1) & 0xFF

            # 결과에 비트 추가 (게임 코드: uVar2 = uVar2 << 1 | (uint)bVar6)
            result = (result << 1) | msb

            self.bits_available -= 1
            self.bits_to_read -= 1

        return result

    def decompress(self, data):
        """LZW 압축 해제 (게임의 실제 알고리즘 사용)"""

        if len(data) < 3:
            raise ValueError("Data too small")

        # 헤더 확인
        if data[0] != 0x1F or data[1] != 0x9D:
            raise ValueError(f"Invalid magic: 0x{data[0]:02X} 0x{data[1]:02X}")

        # 헤더 파싱
        flags = data[2]
        max_bits = (flags & 0x1F) + 9  # Unix compress 표준: 실제 비트수 = 값 + 9
        block_mode = (flags & 0x80) != 0

        print(f"    Flags: 0x{flags:02X}, Max bits: {max_bits} (raw={flags & 0x1F}), Block mode: {block_mode}")

        # 압축 데이터 초기화
        compressed = data[3:]
        self.source_ptr = 0
        self.remaining_bytes = len(compressed)
        self.bits_available = 0
        self.bit_buffer = 0

        # LZW 딕셔너리 (FUN_1000_605b 스타일)
        # FUN_1000_605b: (in_AX + -0x101) 즉 code - 257이 딕셔너리 인덱스
        # 따라서 code 256은 딕셔너리 시작이 아니라 clear code가 아님!
        # 하지만 block_mode에서는 256이 clear code로 사용될 수 있음

        # dictionary[dict_index] = (start_offset, end_offset) in output
        dictionary = []
        output = bytearray()

        code_size = self.INIT_BITS
        prev_code = None

        # 디코딩 루프
        codes_read = 0
        while True:
            # MSB-first 비트 읽기
            code = self.read_bits_msb(compressed, code_size)

            if code is None:
                break

            codes_read += 1

            # 디버깅 (처음 20개 코드만)
            if codes_read <= 20:
                print(f"      Code #{codes_read}: {code} (code_size={code_size}, dict_len={len(dictionary)})")

            # Clear code (256) - block mode에서만
            if block_mode and code == 256:
                dictionary = []
                code_size = self.INIT_BITS
                prev_code = None
                continue

            # FUN_1000_605b 로직: code < 0x100 (256)은 리터럴
            if code < 256:
                output.append(code)

                # 이전 코드와 결합하여 새 엔트리 생성
                if prev_code is not None:
                    # 이전 시퀀스 + 현재 바이트
                    if prev_code < 256:
                        # 이전이 리터럴
                        new_entry = (len(output) - 2, len(output))
                    else:
                        # 이전이 딕셔너리 참조
                        dict_idx = prev_code - 257
                        if dict_idx < len(dictionary):
                            start, _ = dictionary[dict_idx]
                            new_entry = (start, len(output))
                        else:
                            new_entry = None

                    if new_entry and len(dictionary) < (1 << max_bits) - 257:
                        dictionary.append(new_entry)

                        # 비트 크기 증가
                        next_code = 257 + len(dictionary)
                        if next_code >= (1 << code_size) and code_size < max_bits:
                            code_size += 1

            # code >= 257: 딕셔너리 참조
            elif code >= 257:
                dict_idx = code - 257

                if dict_idx < len(dictionary):
                    start, end = dictionary[dict_idx]
                    sequence = output[start:end]

                    # 이전 코드와 결합하여 새 엔트리
                    if prev_code is not None:
                        if prev_code < 256:
                            new_start = len(output) - 1
                        else:
                            prev_idx = prev_code - 257
                            if prev_idx < len(dictionary):
                                new_start, _ = dictionary[prev_idx]
                            else:
                                new_start = len(output)

                        new_entry = (new_start, len(output) + 1)
                        if len(dictionary) < (1 << max_bits) - 257:
                            dictionary.append(new_entry)

                            next_code = 257 + len(dictionary)
                            if next_code >= (1 << code_size) and code_size < max_bits:
                                code_size += 1

                    output.extend(sequence)

                # 특수 케이스: code == 현재 추가될 엔트리
                elif dict_idx == len(dictionary) and prev_code is not None:
                    if prev_code < 256:
                        # 리터럴 반복
                        output.append(prev_code)
                        output.append(prev_code)
                        sequence = bytes([prev_code, prev_code])
                    else:
                        prev_idx = prev_code - 257
                        if prev_idx < len(dictionary):
                            start, end = dictionary[prev_idx]
                            sequence = output[start:end]
                            output.extend(sequence)
                            output.append(sequence[0])

                    # 엔트리 추가
                    if len(dictionary) < (1 << max_bits) - 257:
                        new_start = len(output) - len(sequence) - 1 if prev_code >= 257 else len(output) - 2
                        dictionary.append((new_start, len(output)))

                        next_code = 257 + len(dictionary)
                        if next_code >= (1 << code_size) and code_size < max_bits:
                            code_size += 1
                else:
                    print(f"    ⚠️ Invalid code: {code} (dict_idx={dict_idx}, dict_len={len(dictionary)})")
                    break
            # code == 256은 block mode clear code로 이미 처리됨
            # 그 외의 값은 오류
            else:
                print(f"    ⚠️ Unexpected code: {code}")
                break

            prev_code = code

            # 진행 상황 출력 (큰 파일용)
            if codes_read % 1000 == 0:
                print(f"    ... {codes_read} codes, {len(output)} bytes")

        print(f"    Total codes: {codes_read}, output: {len(output)} bytes")
        return bytes(output)

def decompress_file(input_file, output_file):
    """파일 압축 해제"""

    with open(input_file, 'rb') as f:
        compressed_data = f.read()

    decompressor = DoubleDragonLZW()

    try:
        decompressed_data = decompressor.decompress(compressed_data)

        with open(output_file, 'wb') as f:
            f.write(decompressed_data)

        return len(decompressed_data)

    except Exception as e:
        print(f"    ⚠️ 압축 해제 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """테스트"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python lzw_decompress.py <input> <output>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    print(f"압축 해제: {input_file} → {output_file}")

    size = decompress_file(input_file, output_file)

    if size:
        print(f"✅ 성공! {size:,} bytes")
    else:
        print("❌ 실패")

if __name__ == "__main__":
    main()
