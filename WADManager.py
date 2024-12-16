import os
import struct
import logging

from LumpParser import LumpParser

class WADManager:
    def __init__(self, filepath, output_path=None):
        self.filepath = filepath
        self.output_path = filepath if output_path is None else output_path
        self.lumps = []
        self.header = {
            "type": b"PWAD",
            "lump_count": 0,
            "lump_offset": 12,
        }

        self.parsers = {
            parser.lump_name: parser() 
            for parser in LumpParser.get_all_parsers()
        }

        if os.path.exists(filepath):
            self._read_wad()
        else:
            logging.info(f"Creating new WAD file: {filepath}")
            self.filepath = filepath
            self.create_empty_wad()

    def _read_wad(self):
        """Reads the WAD file and loads its header and lump directory."""
        logging.info(f"Reading WAD file: {self.filepath}")
        with open(self.filepath, "rb") as f:
            # Read header
            self.header["type"] = f.read(4)
            self.header["lump_count"], self.header["lump_offset"] = struct.unpack("<II", f.read(8))
            
            # Read directory entries
            f.seek(self.header["lump_offset"])
            directory = []
            for _ in range(self.header["lump_count"]):
                lump_offset, lump_size = struct.unpack("<II", f.read(8))
                lump_name = f.read(8).rstrip(b"\x00").decode("ascii")
                directory.append((lump_name, lump_offset, lump_size))
            
            # Read actual lump data
            for lump_name, lump_offset, lump_size in directory:
                f.seek(lump_offset)
                lump_data = f.read(lump_size) if lump_size > 0 else b""
                self.lumps.append({
                    "name": lump_name,
                    "offset": lump_offset,
                    "size": lump_size,
                    "data": lump_data
                })
                logging.debug(f"Loaded lump: {lump_name}, size: {lump_size} bytes")
                
        logging.debug(f"Loaded {len(self.lumps)} lumps from WAD file.")

    def save(self):
        """Writes the WAD file with updated header and lump directory."""
        logging.info(f"Saving WAD file: {self.output_path}")
        with open(self.output_path, "wb") as f:
            # Write header
            f.write(self.header["type"])
            f.write(struct.pack("<II", len(self.lumps), 12 + len(self.lumps) * 16))

            # Write lumps
            lump_offset = 12 + len(self.lumps) * 16
            lump_directory = []
            for lump in self.lumps:
                f.seek(lump_offset)
                f.write(lump["data"])
                lump_directory.append((lump_offset, len(lump["data"]), lump["name"].ljust(8, "\x00").encode("ascii")))
                lump_offset += len(lump["data"])

            # Write lump directory
            for lump_offset, lump_size, lump_name in lump_directory:
                f.write(struct.pack("<II", lump_offset, lump_size))
                f.write(lump_name)
        logging.debug("WAD file saved successfully.")

    def add_lump(self, name, data):
        """Adds a new lump to the WAD."""
        if len(name) > 8:
            raise ValueError("Lump name cannot exceed 8 characters.")
        self.lumps.append({"name": name, "data": data})
        logging.debug(f"Added lump: {name}, size: {len(data)} bytes.")

    def find_lump_index(self, name):
        """Finds the index of a lump by name."""
        for index, lump in enumerate(self.lumps):
            if lump["name"] == name:
                return index
        return None

    def insert_lump(self, index, name, data):
        """Inserts a lump at a specific index."""
        if len(name) > 8:
            raise ValueError("Lump name cannot exceed 8 characters.")
        self.lumps.insert(index, {"name": name, "data": data})
        logging.debug(f"Inserted lump: {name} at index: {index}, size: {len(data)} bytes.")

    def ensure_markers(self, start_marker, end_marker):
        """Ensures that start and end markers exist in the correct order."""
        start_index = self.find_lump_index(start_marker)
        end_index = self.find_lump_index(end_marker)
        
        # Remove existing markers if they're in wrong order
        if start_index is not None and end_index is not None and start_index > end_index:
            self.lumps.pop(end_index)
            self.lumps.pop(start_index)
            start_index = end_index = None
        
        # Add markers if missing
        if start_index is None:
            self.add_lump(start_marker, b"")
            start_index = len(self.lumps) - 1
        if end_index is None:
            self.add_lump(end_marker, b"")
            end_index = len(self.lumps) - 1
        
        return start_index, end_index

    def import_texture_patch(self, patch_name, patch_data):
        """Imports a texture patch between P_START and P_END markers."""
        start_marker = "P_START"
        end_marker = "P_END"
        start_index, end_index = self.ensure_markers(start_marker, end_marker)
        # Insert patch before the end marker
        self.insert_lump(end_index, patch_name, patch_data)

    def import_sprite(self, sprite_name, sprite_data):
        """Imports a sprite between S_START and S_END markers."""
        start_marker = "S_START"
        end_marker = "S_END"
        start_index, end_index = self.ensure_markers(start_marker, end_marker)
        # Insert sprite before the end marker
        self.insert_lump(end_index, sprite_name, sprite_data)

    def import_flat(self, flat_name, flat_data):
        """Imports a flat between F_START and F_END markers."""
        start_marker = "F_START"
        end_marker = "F_END"
        start_index, end_index = self.ensure_markers(start_marker, end_marker)
        # Insert flat before the end marker
        self.insert_lump(end_index, flat_name, flat_data)

    def create_empty_wad(self):
        """Initializes an empty WAD and adds a default empty map, flats, textures, and sprites."""
        self.header["type"] = b"PWAD"
        self.lumps = []
        logging.info("Initialized an empty WAD.")
        
        # Create an empty map
        self.create_empty_map("MAP01")
        
        # Initialize flats
        for flat in self.create_default_flats():
            self.add_lump(flat["name"], flat["data"])
        
        # Initialize textures
        for texture in self.create_default_textures():
            self.add_lump(texture["name"], texture["data"])
        
        # Initialize sprites
        for sprite in self.create_default_sprites():
            self.add_lump(sprite["name"], sprite["data"])

    def create_empty_map(self, map_name):
        """Creates an empty map in the WAD."""
        if len(map_name) > 8:
            raise ValueError("Map name cannot exceed 8 characters.")
        map_lumps = ["THINGS", "LINEDEFS", "SIDEDEFS", "VERTEXES", "SEGS", "SSECTORS", "NODES", "SECTORS", "REJECT", "BLOCKMAP"]
        self.add_lump(map_name, b"")
        for lump in map_lumps:
            self.add_lump(lump, b"")
        logging.info(f"Created empty map: {map_name}")

    def create_default_flats(self):
        """Creates default lumps for flats."""
        flats = ["F_START", "F_END"]  # Add any additional flat lumps as needed
        return [{"name": flat, "data": b""} for flat in flats]

    def create_default_textures(self):
        """Creates default lumps for textures."""
        textures = ["T_START", "T_END"]  # Add any additional texture lumps as needed
        return [{"name": texture, "data": b""} for texture in textures]

    def create_default_sprites(self):
        """Creates default lumps for sprites."""
        sprites = ["S_START", "S_END"]  # Add any additional sprite lumps as needed
        return [{"name": sprite, "data": b""} for sprite in sprites]

    def dump(self, verbosity=1):
        """Dumps the WAD structure and contents based on verbosity level."""
        print("\n=== WAD HEADER ===")
        print(f"Type: {self.header['type'].decode('ascii')}")
        print(f"Lump count: {self.header['lump_count']} (0x{self.header['lump_count']:08x})")
        print(f"Directory offset: {self.header['lump_offset']} (0x{self.header['lump_offset']:08x})")
        
        if verbosity >= 3:
            print("\n  Raw header (hex):")
            header_bytes = (
                self.header['type'] +
                struct.pack("<II", self.header['lump_count'], self.header['lump_offset'])
            )
            LumpParser.hex_dump(None, header_bytes, "  ")

        print("\n=== LUMPS ===")
        if verbosity == 0:
            print("IDX  NAME")
            print("-" * 20)
            for idx, lump in enumerate(self.lumps):
                print(f"{idx:03d} {lump['name']:<10}")
        else:
            print("IDX  NAME       OFFSET       SIZE         ")
            print("-" * 42)
            for idx, lump in enumerate(self.lumps):
                offset = lump.get('offset', 0)
                size = len(lump.get('data', b''))
                print(f"{idx:03d} {lump['name']:<10} "
                      f"{offset:10d} (0x{offset:08x}) "
                      f"{size:10d} (0x{size:08x})")
                
                if size > 0:
                    if lump['name'] in self.parsers:
                        try:
                            parser = self.parsers[lump['name']]
                            parsed_data = parser.parse(lump['data'])
                            parser.display(parsed_data, verbosity)
                        except Exception as e:
                            logging.warning(f"Failed to parse {lump['name']}: {e}")
                            if verbosity >= 3:
                                print("\n  Raw data (hex):")
                                LumpParser.hex_dump(None, lump['data'])
                    elif verbosity >= 3:
                        print("\n  Raw data (hex):")
                        LumpParser.hex_dump(None, lump['data'])

    def validate_sprite(self, sprite_data: bytes) -> bool:
        """Validates sprite data format."""
        if len(sprite_data) < 8:  # Minimum header size
            return False
        try:
            width, height = struct.unpack("<HH", sprite_data[:4])
            return len(sprite_data) >= 8 + (width * height)
        except struct.error:
            return False

    def import_sprite(self, sprite_name, sprite_data):
        """Imports a validated sprite between S_START and S_END markers."""
        if not self.validate_sprite(sprite_data):
            raise ValueError(f"Invalid sprite data format for {sprite_name}")
        if len(sprite_name) > 8:
            raise ValueError("Sprite name cannot exceed 8 characters")
        
        start_marker = "S_START"
        end_marker = "S_END"
        start_index, end_index = self.ensure_markers(start_marker, end_marker)
        self.insert_lump(end_index, sprite_name, sprite_data)

    def organize_lumps(self):
        """Organizes lumps in standard WAD order."""
        # Standard order: MAP lumps, Patches, Sprites, Flats
        sections = {
            'maps': [],
            'patches': {'start': 'P_START', 'end': 'P_END', 'lumps': []},
            'sprites': {'start': 'S_START', 'end': 'S_END', 'lumps': []},
            'flats': {'start': 'F_START', 'end': 'F_END', 'lumps': []}
        }
        
        # Collect lumps by section
        current_map = None
        for lump in self.lumps:
            name = lump['name']
            if name.startswith('MAP') or name.startswith('E'):
                current_map = [lump]
            elif current_map is not None and name in ['THINGS', 'LINEDEFS', 'SIDEDEFS', 'VERTEXES', 'SEGS', 'SSECTORS', 'NODES', 'SECTORS', 'REJECT', 'BLOCKMAP']:
                current_map.append(lump)
            elif name in ['P_START', 'P_END', 'S_START', 'S_END', 'F_START', 'F_END']:
                continue
            else:
                # Add to appropriate section
                for section in sections.values():
                    if isinstance(section, dict):
                        section['lumps'].append(lump)
        
        # Rebuild lumps list in correct order
        self.lumps = []
        for map_lumps in sections['maps']:
            self.lumps.extend(map_lumps)
        
        for section in ['patches', 'sprites', 'flats']:
            if sections[section]['lumps']:
                self.add_lump(sections[section]['start'], b"")
                self.lumps.extend(sections[section]['lumps'])
                self.add_lump(sections[section]['end'], b"")

    def validate(self):
        """Validates the WAD file."""
        for lump in self.lumps:
            # TODO: validation checks for other lumps
            if lump['name'] == 'S_START':
                sprite_data = lump['data']
                if not self.validate_sprite(sprite_data):
                    raise ValueError(f"Invalid sprite data format for {lump['name']}")
        # self.organize_lumps()
        # self.save()
        logging.info("WAD file validated.")# and organized.")

    def append(self, image_path, lump_type):
        """Appends a file to the current WAD."""
        if image_path is None:
            raise ValueError("Image path is required")
        if lump_type not in self.parsers:
            raise ValueError(f"Invalid lump type: {lump_type}")
        parser = self.parsers[lump_type]
        parser.parse(image_path)
        self.add_lump(lump_type, parser.parse(image_path))