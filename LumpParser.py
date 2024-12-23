from abc import ABC, abstractmethod
import struct
import inspect
import sys
from collections import namedtuple
import logging
from typing import Any, Callable
from PIL import Image
        

# Data structures for parsed lumps
Thing = namedtuple('Thing', 'x y angle type flags')
Vertex = namedtuple('Vertex', 'x y')
Linedef = namedtuple('Linedef', 'start end flags special tag right_side left_side')
Sector = namedtuple('Sector', 'floor_height ceiling_height floor_tex ceiling_tex light special tag')
Sidedef = namedtuple('Sidedef', 'x_off y_off upper_tex lower_tex middle_tex sector')
Seg = namedtuple('Seg', 'start_vertex end_vertex angle line_def side direction offset')
Subsector = namedtuple('Subsector', 'seg_count first_seg')
Node = namedtuple('Node', 'x y dx dy right_bbox_top right_bbox_bottom right_bbox_left right_bbox_right left_bbox_top left_bbox_bottom left_bbox_left left_bbox_right right_child left_child')
Blockmap = namedtuple('Blockmap', 'origin_x origin_y blocks_width blocks_height')
Patch = namedtuple('Patch', 'originx originy patch_num stepdir colormap')
Texture = namedtuple('Texture', 'name width height patches')
PatchMap = namedtuple('PatchMap', 'name width height')
Sprite = namedtuple('Sprite', 'width height left_offset top_offset pixels')

class LumpParser(ABC):
    """Abstract base class for parsing WAD lumps."""
    
    def __init__(self):
        if not hasattr(self, 'lump_name'):
            raise ValueError(f"Parser class {self.__class__.__name__} must define lump_name")
        if not hasattr(self, 'RECORD_SIZE') and not hasattr(self, 'HEADER_SIZE'):
            raise ValueError(f"Parser class {self.__class__.__name__} must define either RECORD_SIZE or HEADER_SIZE")
    
    @classmethod
    def get_all_parsers(cls):
        """Returns all concrete parser classes that inherit from LumpParser."""
        def is_concrete_parser(obj):
            return (inspect.isclass(obj) and 
                   issubclass(obj, LumpParser) and 
                   obj != LumpParser)
        
        return [obj for _, obj in inspect.getmembers(sys.modules[__name__], is_concrete_parser)]
    
    @abstractmethod
    def parse(self, data: bytes) -> list:
        """Parse the lump data into a list of named tuples."""
        pass

    @abstractmethod
    def encode(self, data: Any) -> bytes:
        """Encode the data into a binary format.
        
        Args:
            data: The data to encode. Could be:
                - A filename (str) for image-based lumps (sprites, flats)
                - A list of namedtuples for structural lumps (things, vertexes, etc.)
                - Raw bytes for direct binary data
                
        Returns:
            bytes: The encoded binary data in WAD format
        """
        if isinstance(data, bytes):
            return data
        raise NotImplementedError("Encode method must be implemented by subclass")
    
    def base_display(self, data: Any, verbosity: int, display_func: Callable) -> None:
        """Base display method with common verbosity handling.
        
        Args:
            data: The parsed data to display
            verbosity: Verbosity level (0-3)
            display_func: Function that handles the actual data display
        """
        if verbosity < 2:
            return
            
        display_func(data, verbosity)
        
        if verbosity >= 3 and hasattr(self, '_raw_data'):
            print("\n  Raw data (hex):")
            self.hex_dump(self._raw_data[:min(64, len(self._raw_data))])
    
    @property
    @abstractmethod
    def lump_name(self) -> str:
        """Return the name of the lump type this parser handles."""
        pass

    def hex_dump(self, data: bytes, indent: str = "  ") -> None:
        """Helper method to create hex dumps of binary data."""
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_values = ' '.join(f'{b:02x}' for b in chunk)
            ascii_values = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            print(f"{indent}{i:08x}: {hex_values:<48} {ascii_values}")

class ThingsParser(LumpParser):
    lump_name = "THINGS"
    RECORD_SIZE = struct.calcsize("<hhHHH")  # 10 bytes
    
    # Thing flags
    EASY = 1
    MEDIUM = 2
    HARD = 4
    DEAF = 8
    MULTIPLAYER = 16
    
    def parse(self, data: bytes) -> list[Thing]:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        things = []
        for i in range(0, len(data), self.RECORD_SIZE):
            x, y, angle, type_, flags = struct.unpack("<hhHHH", data[i:i+self.RECORD_SIZE])
            things.append(Thing(x, y, angle, type_, flags))
        return things
    
    def display(self, things: list[Thing], verbosity: int = 1) -> None:
        def display_things(data, verbosity):
            print("\n  Thing Data:")
            print("  X      Y      Angle  Type   Flags")
            print("  " + "-" * 40)
            for thing in data:
                print(f"  {thing.x:6d} {thing.y:6d} {thing.angle:6d} "
                      f"{thing.type:6d} {thing.flags:6d}")
        self.base_display(things, verbosity, display_things)

    def encode(self, things: list[Thing]) -> bytes:
        """Encode a list of Things into binary format.
        
        Args:
            things: List of Thing namedtuples
            
        Returns:
            bytes: Binary thing data
        """
        result = bytearray()
        for thing in things:
            result.extend(struct.pack("<hhHHH", 
                thing.x, thing.y, thing.angle, thing.type, thing.flags))
        return bytes(result)

class VertexesParser(LumpParser):
    lump_name = "VERTEXES"
    RECORD_SIZE = struct.calcsize("<hh")  # 4 bytes
    
    def parse(self, data: bytes) -> list[Vertex]:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        vertices = []
        for i in range(0, len(data), self.RECORD_SIZE):
            x, y = struct.unpack("<hh", data[i:i+self.RECORD_SIZE])
            vertices.append(Vertex(x, y))
        return vertices
    
    def display(self, vertices: list[Vertex], verbosity: int = 1) -> None:
        def display_vertices(data, verbosity):
            print("\n  Vertex Data:")
            print("  X      Y")
            print("  " + "-" * 20)
            for vertex in data:
                print(f"  {vertex.x:6d} {vertex.y:6d}")
        self.base_display(vertices, verbosity, display_vertices)

    def encode(self, vertices: list[Vertex]) -> bytes:
        """Encode a list of Vertices into binary format."""
        result = bytearray()
        for vertex in vertices:
            result.extend(struct.pack("<hh", vertex.x, vertex.y))
        return bytes(result)

class LinedefsParser(LumpParser):
    lump_name = "LINEDEFS"
    RECORD_SIZE = struct.calcsize("<HHHHHHH")  # 14 bytes
    
    def parse(self, data: bytes) -> list[Linedef]:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        linedefs = []
        for i in range(0, len(data), self.RECORD_SIZE):
            start, end, flags, special, tag, right_side, left_side = struct.unpack("<HHHHHHH", data[i:i+self.RECORD_SIZE])
            linedefs.append(Linedef(start, end, flags, special, tag, right_side, left_side))
        return linedefs
    
    def display(self, linedefs: list[Linedef], verbosity: int = 1) -> None:
        def display_linedefs(data, verbosity):
            print("\n  Linedef Data:")
            print("  Start  End    Flags   Special Type  Sector Tag")
            print("  " + "-" * 50)
            for linedef in data:
                print(f"  {linedef.start:6d} {linedef.end:6d} {linedef.flags:6d} "
                      f"{linedef.special:6d} {linedef.tag:6d}")
        self.base_display(linedefs, verbosity, display_linedefs)

    def encode(self, linedefs: list[Linedef]) -> bytes:
        """Encode a list of Linedefs into binary format."""
        result = bytearray()
        for linedef in linedefs:
            result.extend(struct.pack("<HHHHHHH",
                linedef.start_vertex,
                linedef.end_vertex,
                linedef.flags,
                linedef.special_type,
                linedef.sector_tag,
                linedef.right_sidedef,
                linedef.left_sidedef))
        return bytes(result)

class SectorsParser(LumpParser):
    lump_name = "SECTORS"
    # 2 shorts + 2 8-byte strings + 3 shorts = 26 bytes
    RECORD_SIZE = struct.calcsize("<hh8s8sHHH")
    
    def parse(self, data: bytes) -> list[Sector]:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        sectors = []
        for i in range(0, len(data), self.RECORD_SIZE):
            floor_h, ceil_h, floor_tex_raw, ceil_tex_raw, light, special, tag = struct.unpack(
                "<hh8s8sHHH", data[i:i+self.RECORD_SIZE]
            )
            floor_tex = floor_tex_raw.rstrip(b"\x00").decode("ascii")
            ceil_tex = ceil_tex_raw.rstrip(b"\x00").decode("ascii")
            sectors.append(Sector(floor_h, ceil_h, floor_tex, ceil_tex, light, special, tag))
        return sectors
    
    def display(self, sectors: list[Sector], verbosity: int = 1) -> None:
        def display_sectors(data, verbosity):
            print("\n  Sector Data:")
            print("  Floor  Ceil   Light  Special Type  Tag")
            print("  " + "-" * 50)
            for sector in data:
                print(f"  {sector.floor_height:6d} {sector.ceiling_height:6d} "
                      f"{sector.light:6d} {sector.special:6d} {sector.tag:6d}")
        self.base_display(sectors, verbosity, display_sectors)

    def encode(self, sectors: list[Sector]) -> bytes:
        """Encode a list of Sectors into binary format."""
        result = bytearray()
        for sector in sectors:
            result.extend(struct.pack("<hh8s8sHHH",
                sector.floor_height,
                sector.ceiling_height,
                sector.floor_tex.encode('ascii').ljust(8, b'\x00'),
                sector.ceiling_tex.encode('ascii').ljust(8, b'\x00'),
                sector.light,
                sector.special,
                sector.tag))
        return bytes(result)

class SidedefsParser(LumpParser):
    lump_name = "SIDEDEFS"
    # 2 shorts + 3 8-byte strings + 1 short = 30 bytes
    RECORD_SIZE = struct.calcsize("<hh8s8s8sH")
    
    def parse(self, data: bytes) -> list[Sidedef]:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        sidedefs = []
        for i in range(0, len(data), self.RECORD_SIZE):
            x_off, y_off, upper_tex_raw, lower_tex_raw, middle_tex_raw, sector = struct.unpack(
                "<hh8s8s8sH", data[i:i+self.RECORD_SIZE]
            )
            upper_tex = upper_tex_raw.rstrip(b"\x00").decode("ascii")
            lower_tex = lower_tex_raw.rstrip(b"\x00").decode("ascii")
            middle_tex = middle_tex_raw.rstrip(b"\x00").decode("ascii")
            sidedefs.append(Sidedef(x_off, y_off, upper_tex, lower_tex, middle_tex, sector))
        return sidedefs
    
    def display(self, sidedefs: list[Sidedef], verbosity: int = 1) -> None:
        def display_sidedefs(data, verbosity):
            print("\n  Sidedef Data:")
            print("  X-Off  Y-Off  Upper    Lower    Middle   Sector")
            print("  " + "-" * 60)
            for sidedef in data:
                print(f"  {sidedef.x_off:6d} {sidedef.y_off:6d} {sidedef.upper_tex:<8s} "
                      f"{sidedef.lower_tex:<8s} {sidedef.middle_tex:<8s} {sidedef.sector:6d}")
        self.base_display(sidedefs, verbosity, display_sidedefs)

    def encode(self, sidedefs: list[Sidedef]) -> bytes:
        """Encode a list of Sidedefs into binary format."""
        result = bytearray()
        for sidedef in sidedefs:
            result.extend(struct.pack("<hh8s8s8sH",
                sidedef.x_off,
                sidedef.y_off,
                sidedef.upper_tex.encode('ascii').ljust(8, b'\x00'),
                sidedef.lower_tex.encode('ascii').ljust(8, b'\x00'),
                sidedef.middle_tex.encode('ascii').ljust(8, b'\x00'),
                sidedef.sector))
        return bytes(result)

class SegsParser(LumpParser):
    lump_name = "SEGS"
    HEADER_SIZE = struct.calcsize("<HHHHHHH")  # 14 bytes
    
    def parse(self, data: bytes) -> list[Seg]:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) < self.HEADER_SIZE:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        segs = []
        for i in range(0, len(data), self.HEADER_SIZE):
            start_vertex, end_vertex, angle, line_def, side, direction, offset = struct.unpack(
                "<HHHHHHH", data[i:i+self.HEADER_SIZE]
            )
            segs.append(Seg(start_vertex, end_vertex, angle, line_def, side, direction, offset))
        return segs
    
    def display(self, segs: list[Seg], verbosity: int = 1) -> None:
        def display_segs(data, verbosity):
            print("\n  Seg Data:")
            print("  Start  End    Angle  Line   Side   Offset")
            print("  " + "-" * 50)
            for seg in data:
                print(f"  {seg.start_vertex:6d} {seg.end_vertex:6d} {seg.angle:6d} "
                      f"{seg.line_def:6d} {seg.side:6d} {seg.offset:6d}")
        self.base_display(segs, verbosity, display_segs)

    def encode(self, segs: list[Seg]) -> bytes:
        """Encode a list of Segs into binary format."""
        result = bytearray()
        for seg in segs:
            result.extend(struct.pack("<HHHHHHH",
                seg.start_vertex,
                seg.end_vertex,
                seg.angle,
                seg.line_def,
                seg.side,
                seg.direction,
                seg.offset))
        return bytes(result)

class SubsectorsParser(LumpParser):
    lump_name = "SSECTORS"
    RECORD_SIZE = struct.calcsize("<HH")  # 4 bytes
    
    def parse(self, data: bytes) -> list[Subsector]:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        subsectors = []
        for i in range(0, len(data), self.RECORD_SIZE):
            seg_count, first_seg = struct.unpack("<HH", data[i:i+self.RECORD_SIZE])
            subsectors.append(Subsector(seg_count, first_seg))
        return subsectors
    
    def display(self, subsectors: list[Subsector], verbosity: int = 1) -> None:
        def display_subsectors(data, verbosity):
            print("\n  Subsector Data:")
            print("  Count  First Seg")
            print("  " + "-" * 20)
            for subsector in data:
                print(f"  {subsector.seg_count:6d} {subsector.first_seg:6d}")
        self.base_display(subsectors, verbosity, display_subsectors)

    def encode(self, subsectors: list[Subsector]) -> bytes:
        """Encode a list of Subsectors into binary format."""
        result = bytearray()
        for subsector in subsectors:
            result.extend(struct.pack("<HH",
                subsector.seg_count, subsector.first_seg))
        return bytes(result)

class NodesParser(LumpParser):
    lump_name = "NODES"
    RECORD_SIZE = struct.calcsize("<hhhhhhhhhhhhHH")  # 28 bytes
    
    def parse(self, data: bytes) -> list[Node]:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        nodes = []
        for i in range(0, len(data), self.RECORD_SIZE):
            values = struct.unpack("<hhhhhhhhhhhhHH", data[i:i+self.RECORD_SIZE])
            nodes.append(Node(*values))
        return nodes
    
    def display(self, nodes: list[Node], verbosity: int = 1) -> None:
        def display_nodes(data, verbosity):
            print("\n  Node Data:")
            print("  X      Y      DX     DY     Right Child  Left Child")
            print("  " + "-" * 50)
            for node in data:
                print(f"  {node.x:6d} {node.y:6d} {node.dx:6d} {node.dy:6d} "
                      f"{node.right_child:11d} {node.left_child:10d}")
        self.base_display(nodes, verbosity, display_nodes)

    def encode(self, nodes: list[Node]) -> bytes:
        """Encode a list of Nodes into binary format."""
        result = bytearray()
        for node in nodes:
            result.extend(struct.pack("<hhhhhhhhhhhhHH",
                node.x, node.y, node.dx, node.dy,
                node.right_bbox_top, node.right_bbox_bottom,
                node.right_bbox_left, node.right_bbox_right,
                node.left_bbox_top, node.left_bbox_bottom,
                node.left_bbox_left, node.left_bbox_right,
                node.right_child, node.left_child))
        return bytes(result)

class RejectParser(LumpParser):
    lump_name = "REJECT"
    RECORD_SIZE = 1  # 1 byte per sector-to-sector visibility flag
    
    def parse(self, data: bytes) -> list[bytes]:
        # REJECT is a bit array, so we'll just return the raw bytes
        return list(data)
    
    def display(self, reject_data: bytes, verbosity: int = 1) -> None:
        def display_reject(data, verbosity):
            print("\n  Reject Data:")
            print(f"  Size: {len(data)} bytes")
        self.base_display(reject_data, verbosity, display_reject)

    def encode(self, reject_data: list[int]) -> bytes:
        """Encode reject table into binary format."""
        return bytes(reject_data)

class BlockmapParser(LumpParser):
    lump_name = "BLOCKMAP"
    HEADER_SIZE = struct.calcsize("<HHHH")  # origin_x, origin_y, blocks_width, blocks_height
    
    def parse(self, data: bytes) -> Blockmap:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) < self.HEADER_SIZE:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        origin_x, origin_y, blocks_width, blocks_height = struct.unpack(
            "<HHHH", data[:self.HEADER_SIZE]
        )
        # Note: The rest of the data contains the offset table and blocklists
        # but we're only parsing the header for now
        return Blockmap(origin_x, origin_y, blocks_width, blocks_height)
    
    def display(self, blockmap: Blockmap, verbosity: int = 1) -> None:
        def display_blockmap(data, verbosity):
            print("\n  Blockmap Data:")
            print("  Origin     Size")
            print("  " + "-" * 30)
            print(f"  {data.origin_x:4d},{data.origin_y:<4d}  {data.blocks_width:4d}x{data.blocks_height:4d}")
        self.base_display(blockmap, verbosity, display_blockmap)

    def encode(self, blockmap: Blockmap) -> bytes:
        """Encode Blockmap header into binary format."""
        return struct.pack("<HHHH",
            blockmap.origin_x, blockmap.origin_y,
            blockmap.blocks_width, blockmap.blocks_height)

class PNamesParser(LumpParser):
    lump_name = "PNAMES"
    NAME_LENGTH = 8
    HEADER_SIZE = 4  # Size of num_patches field
    
    def parse(self, data: bytes) -> list[str]:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) < self.HEADER_SIZE:
            raise ValueError(f"Invalid {self.lump_name} header size: {len(data)}")
            
        num_patches = struct.unpack("<I", data[:4])[0]
        patches = []
        offset = 4
        
        for _ in range(num_patches):
            name = data[offset:offset+self.NAME_LENGTH].rstrip(b"\x00").decode("ascii")
            patches.append(name)
            offset += self.NAME_LENGTH
        return patches
    
    def display(self, patches: list[str], verbosity: int = 1) -> None:
        def display_patches(data, verbosity):
            print("\n  Patch Names:")
            print("  Index  Name")
            print("  " + "-" * 20)
            for idx, name in enumerate(data):
                print(f"  {idx:5d}  {name}")
        self.base_display(patches, verbosity, display_patches)

    def encode(self, patch_names: list[str]) -> bytes:
        """Encode patch names into binary format."""
        result = bytearray(struct.pack("<I", len(patch_names)))
        for name in patch_names:
            name_bytes = name.encode('ascii')
            if len(name_bytes) > self.NAME_LENGTH:
                raise ValueError(f"Patch name '{name}' exceeds {self.NAME_LENGTH} characters")
            result.extend(name_bytes.ljust(self.NAME_LENGTH, b'\x00'))
        return bytes(result)

class TextureParser(LumpParser):
    lump_name = "TEXTURE1"  # Also handles TEXTURE2
    HEADER_SIZE = 4
    TEXTURE_HEADER_SIZE = struct.calcsize("<8sIHHHH")  # name, _, width, height, _, num_patches
    PATCH_SIZE = struct.calcsize("<HHHHHH")  # originx, originy, patch_num, _, _, _
    
    def parse(self, data: bytes) -> list[Texture]:
        self._raw_data = data  # Store raw data for hex dumps
        num_textures = struct.unpack("<I", data[:self.HEADER_SIZE])[0]
        offsets = struct.unpack(f"<{num_textures}I", 
                            data[self.HEADER_SIZE:self.HEADER_SIZE + 4*num_textures])
        
        textures = []
        for offset in offsets:
            tex_data = data[offset:]
            name_raw, _, width, height, _, num_patches = struct.unpack(
                "<8sIHHHH", tex_data[:self.TEXTURE_HEADER_SIZE]
            )
            name = name_raw.rstrip(b"\x00").decode("ascii")
            
            patches = []
            patch_offset = self.TEXTURE_HEADER_SIZE
            for _ in range(num_patches):
                patch_values = struct.unpack("<HHHHHH", 
                    tex_data[patch_offset:patch_offset + self.PATCH_SIZE])
                patches.append(Patch(*patch_values[:5]))  # Skip last value
                patch_offset += self.PATCH_SIZE
                
            textures.append(Texture(name, width, height, patches))
        return textures
 
    
    def display(self, textures: list[Texture], verbosity: int = 1) -> None:
        def display_textures(data, verbosity):
            print("\n  Texture Data:")
            print("  Name     Width  Height  Patches")
            print("  " + "-" * 40)
            for texture in data:
                print(f"  {texture.name:<8s} {texture.width:6d} {texture.height:6d} "
                      f"{len(texture.patches):6d}")
                if verbosity >= 2:
                    for i, patch in enumerate(texture.patches):
                        print(f"    Patch {i}: ({patch.originx}, {patch.originy}) -> {patch.patch_num}")
        self.base_display(textures, verbosity, display_textures)

    def encode(self, textures: list[Texture]) -> bytes:
        """Encode texture definitions into binary format."""
        # Calculate size needed for offset table
        offset_table_size = 4 + (4 * len(textures))
        current_offset = offset_table_size
        
        # Build texture data first
        texture_data = bytearray()
        offsets = []
        
        for texture in textures:
            offsets.append(current_offset)
            # Pack texture header
            texture_data.extend(struct.pack("<8sIHHHH",
                texture.name.encode('ascii').ljust(8, b'\x00'),
                0,  # Unused value
                texture.width,
                texture.height,
                0,  # Unused value
                len(texture.patches)))
            
            # Pack patches
            for patch in texture.patches:
                texture_data.extend(struct.pack("<HHHHHH",
                    patch.originx, patch.originy, patch.patch_num,
                    patch.stepdir, patch.colormap, 0))  # Last value unused
            
            current_offset += len(texture_data)
        
        # Build final data with offset table
        result = bytearray(struct.pack("<I", len(textures)))
        result.extend(struct.pack(f"<{len(textures)}I", *offsets))
        result.extend(texture_data)
        
        return bytes(result)

class FlatParser(LumpParser):
    lump_name = "FLAT"
    RECORD_SIZE = 4096  # 64x64 pixels, 1 byte per pixel
    
    def parse(self, data: bytes) -> bytes:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) != self.RECORD_SIZE:
            raise ValueError(f"Invalid {self.lump_name} size: {len(data)}")
        return data
    
    def display(self, flat_data: bytes, verbosity: int = 1) -> None:
        def display_flat(data, verbosity):
            print("\n  Flat Data:")
            print(f"  Size: {len(data)} bytes")
            print("  Standard 64x64 flat")
        self.base_display(flat_data, verbosity, display_flat)

    def encode(self, data: str) -> bytes:
        """Encode a PNG file into a flat format (64x64 pixels, 1 byte per pixel).
        
        Args:
            data: Path to PNG file
            
        Returns:
            bytes: 4096 bytes of pixel data
        """
        with Image.open(data) as img:
            if img.size != (64, 64):
                img = img.resize((64, 64))
            if img.mode != 'P':
                img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
            return img
class SpriteParser(LumpParser):
    lump_name = "SPRITE"
    HEADER_SIZE = struct.calcsize("<HHHHH")  # width, height, left_offset, top_offset, num_pixels
    
    def parse(self, data: bytes) -> Sprite:
        self._raw_data = data  # Store raw data for hex dumps
        if len(data) < self.HEADER_SIZE:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        width, height, left_offset, top_offset, _ = struct.unpack("<HHHHH", data[:self.HEADER_SIZE])
        pixels = data[self.HEADER_SIZE:]
        return Sprite(width, height, left_offset, top_offset, pixels)
    
    def display(self, sprite: Sprite, verbosity: int = 1) -> None:
        def display_sprite(data, verbosity):
            print("\n  Sprite Data:")
            print(f"  Size: {data.width}x{data.height}")
            print(f"  Offset: ({data.left_offset}, {data.top_offset})")
            print(f"  Pixels: {len(data.pixels)} bytes")
        self.base_display(sprite, verbosity, display_sprite)

    def encode(self, data: str) -> bytes:
        """Encode a PNG file into a DOOM sprite format.
        
        Args:
            data: Path to PNG file
            
        Returns:
            bytes: Sprite header followed by pixel data
        """
        with Image.open(data) as img:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                
            width, height = img.size
            # Calculate sprite offset (center point)
            left_offset = width // 2
            top_offset = height
            
            # Convert to indexed color with transparency
            img = img.convert('P', palette=Image.ADAPTIVE, colors=255)
            
            # Pack header
            header = struct.pack("<HHHHH", width, height, left_offset, top_offset, width * height)
            return header + img.tobytes()