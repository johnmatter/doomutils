# WAD File Parser

A Python-based parser for DOOM WAD files. Currently supports parsing and displaying basic map structures.

## Features
- Parse PWAD and IWAD files
- Display WAD structure with configurable verbosity
- Parse common map lumps (THINGS, VERTEXES, LINEDEFS, SECTORS, SIDEDEFS)
- Create empty WAD files with basic structure

## Usage
```
python main.py path_to_wad_file [-v VERBOSITY]
```

Verbosity levels:
- 0: Show only header and lump names
- 1: Show header, lump info, and basic stats
- 2: Show header, lump info, and parse common lump types

## Project Structure
- `main.py`: Entry point and argument parsing
- `WADManager.py`: Core WAD file handling and management
- `LumpParser.py`: Parsers for individual lump types

## Requirements
- Python 3.9+
- No external dependencies

## Todo 
- [ ] Support for additional lump types (SEGS, SSECTORS, NODES, etc.)
- [ ] Texture and sprite handling
- [ ] WAD modification and creation tools
- [ ] Better error handling and validation