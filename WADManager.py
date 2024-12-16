import os
import struct
import logging

from LumpParser import LumpParser

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

class WADManager:
    def __init__(self, filepath):
        self.filepath = filepath
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
            self.header["type"] = f.read(4)
            self.header["lump_count"], self.header["lump_offset"] = struct.unpack("<II", f.read(8))
            f.seek(self.header["lump_offset"])
            for _ in range(self.header["lump_count"]):
                lump_offset, lump_size = struct.unpack("<II", f.read(8))
                lump_name = f.read(8).rstrip(b"\x00").decode("ascii")
                self.lumps.append({"name": lump_name, "offset": lump_offset, "size": lump_size})
        logging.debug(f"Loaded {len(self.lumps)} lumps from WAD file.")

    def save(self):
        """Writes the WAD file with updated header and lump directory."""
        logging.info(f"Saving WAD file: {self.filepath}")
        with open(self.filepath, "wb") as f:
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
        """Ensures that start and end markers exist; adds them if necessary."""
        start_index = self.find_lump_index(start_marker)
        end_index = self.find_lump_index(end_marker)
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
                size = lump.get('size', len(lump.get('data', b'')))
                print(f"{idx:03d} {lump['name']:<10} "
                      f"{offset:10d} (0x{offset:08x}) "
                      f"{size:10d} (0x{size:08x})")
                
                if size > 0 and lump['name'] in self.parsers:
                    parser = self.parsers[lump['name']]
                    parsed_data = parser.parse(lump.get('data', b''))
                    parser.display(parsed_data, verbosity)
