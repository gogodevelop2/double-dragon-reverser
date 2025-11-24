# Spice86 Memory Dump Analysis

## Dump Information

- **File**: spice86dumpMemoryDump.bin
- **Size**: 1,114,095 bytes (1.06 MB)
- **Dump Time**: Likely taken at game initialization (before main graphics loaded)

## Key Findings

### 1. Compressed Data Found
- **Location**: Offset 0x000076e3
- **Signature**: `0x1F 0x9D` (LZW compression)
- **Count**: 1 instance
- This is likely compressed game data still in memory waiting to be decompressed

### 2. Graphics Data Candidates
- **Total Candidates**: 1,588 regions
- **Top Candidates by Entropy (~5.5)**:
  1. Offset 0x00007900 - 86 unique bytes
  2. Offset 0x0006a400 - 109 unique bytes (looks most promising)
  3. Offset 0x0003e700 - 139 unique bytes
  4. Offset 0x00009e00 - 115 unique bytes
  5. Offset 0x00002600 - 111 unique bytes

### 3. Video Memory Status
- **CGA Video RAM** (0xB8000-0xBFFFF): **All zeros**
- **Conclusion**: Dump taken before game rendered graphics to screen

### 4. Memory Distribution
- 79.37% null bytes (0x00) - mostly empty memory
- 2.43% 0xFF bytes
- Rest scattered data

## Analysis of Extracted Regions

### Region 1 (0x7900)
- Contains x86 assembly code mixed with data
- Patterns like `13 db d0 d8` repeating
- Likely code segment, not pure graphics

### Region 2 (0x6a400) ⭐ Most Promising
- More bitmap-like patterns
- Values like `0x7f`, `0x7e`, `0x40` common in CGA planar format
- Repeating patterns (`4ff`) typical of sprite data
- Could be decompressed sprite data

## Problem: Early Dump

The memory dump was captured too early in the game execution. We need to:

1. **Re-run the game in Spice86**
2. **Progress to actual gameplay** (not just title screen)
3. **Dump memory when graphics are visible**

At that point:
- Video RAM (0xB8000) will have actual screen data
- More decompressed sprites will be in memory
- Game state/level data will be accessible

## Recommended Next Steps

### Option A: Get Better Dump (Recommended)
```bash
# 1. Run Spice86 again
# 2. Start game, get to level 1
# 3. Press dump button during gameplay
# 4. Analyze new dump
```

### Option B: Screenshot-Based Asset Extraction
Since we're having trouble getting the right memory timing:
```bash
# 1. Run game in DOSBox-X
# 2. Capture screenshots of all sprites/screens
# 3. Use image editing tools to extract sprites
# 4. Convert to web-ready format
```

### Option C: Analyze Compressed Files Directly
The compressed file signature at 0x76e3 suggests we could:
```bash
# 1. Extract that region
# 2. Try to decompress using the routine we found
# 3. If successful, that's the sprite data
```

## Files Generated
- `graphics_candidate_1.bin` - Code segment (16KB)
- `graphics_candidate_2.bin` - Possible sprite data (16KB)

## Conclusion

The Spice86 dump is valid but captured at the wrong game state. We need graphics to be actively loaded and displayed before dumping. The dump does show we can access game memory, we just need better timing.

**Best immediate action**: Run the game again, play to level 1, then dump during active gameplay.
