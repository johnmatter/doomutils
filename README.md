# WAD File Parser

A Python-based parser for DOOM WAD files. Supports parsing and displaying map structures, textures, sprites, and other WAD data.

## Features
- Parse PWAD and IWAD files
- Display WAD structure with configurable verbosity
- Parse all standard map lumps:
  - THINGS: Monsters, items, players, etc.
  - VERTEXES: Map geometry vertices
  - LINEDEFS: Wall segments and triggers
  - SECTORS: Room definitions
  - SIDEDEFS: Wall texturing information
  - SEGS: BSP tree segments
  - SSECTORS: BSP leaf nodes
  - NODES: BSP tree nodes
  - REJECT: Sector visibility matrix
  - BLOCKMAP: Collision detection grid
- Parse texture and graphic data:
  - PNAMES: Patch name directory
  - TEXTURE1/2: Texture definitions
  - Flats (F_START/F_END)
  - Sprites (S_START/S_END)
- Create empty WAD files with basic structure

## Usage
```
python main.py path_to_wad_file [-v VERBOSITY]
```

Verbosity levels:
- 0: Show only header and lump names
- 1: Show header, lump info, and basic stats
- 2: Show header, lump info, and parse all supported lumps
- 3: Show detailed data including hex dumps for binary lumps

## Project Structure
- `main.py`: Entry point and argument parsing
- `WADManager.py`: Core WAD file handling and management
- `LumpParser.py`: Parsers for individual lump types

## Requirements
- Python 3.9+
- No external dependencies

## Todo 
- [ ] Support for additional graphic formats (patches, colormaps)
- [ ] WAD modification and creation tools
- [ ] Better error handling and validation
- [ ] Documentation for lump formats and data structures