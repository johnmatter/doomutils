from abc import ABC, abstractmethod
import struct
import inspect
import sys
from collections import namedtuple

# Data structures for parsed lumps
Thing = namedtuple('Thing', 'x y angle type flags')
Vertex = namedtuple('Vertex', 'x y')
Linedef = namedtuple('Linedef', 'start end flags special tag right_side left_side')
Sector = namedtuple('Sector', 'floor_height ceiling_height floor_tex ceiling_tex light special tag')
Sidedef = namedtuple('Sidedef', 'x_off y_off upper_tex lower_tex middle_tex sector')

class LumpParser(ABC):
    """Abstract base class for parsing WAD lumps."""
    
    def __init__(self):
        if not hasattr(self, 'lump_name'):
            raise ValueError(f"Parser class {self.__class__.__name__} must define lump_name")
        if not hasattr(self, 'RECORD_SIZE'):
            raise ValueError(f"Parser class {self.__class__.__name__} must define RECORD_SIZE")
    
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
    def display(self, parsed_data: list, verbosity: int = 1) -> None:
        """Display the parsed data according to verbosity level."""
        pass
    
    @property
    @abstractmethod
    def lump_name(self) -> str:
        """Return the name of the lump type this parser handles."""
        pass

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
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        things = []
        for i in range(0, len(data), self.RECORD_SIZE):
            x, y, angle, type_, flags = struct.unpack("<hhHHH", data[i:i+self.RECORD_SIZE])
            things.append(Thing(x, y, angle, type_, flags))
        return things
    
    def display(self, things: list[Thing], verbosity: int = 1) -> None:
        if verbosity < 2:
            return
            
        print("\n  Thing Data:")
        print("  X      Y      Angle  Type   Flags")
        print("  " + "-" * 40)
        
        for thing in things:
            print(f"  {thing.x:6d} {thing.y:6d} {thing.angle:6d} "
                  f"{thing.type:6d} {thing.flags:6d}")

class VertexesParser(LumpParser):
    lump_name = "VERTEXES"
    RECORD_SIZE = struct.calcsize("<hh")  # 4 bytes
    
    def parse(self, data: bytes) -> list[Vertex]:
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        vertices = []
        for i in range(0, len(data), self.RECORD_SIZE):
            x, y = struct.unpack("<hh", data[i:i+self.RECORD_SIZE])
            vertices.append(Vertex(x, y))
        return vertices
    
    def display(self, vertices: list[Vertex], verbosity: int = 1) -> None:
        if verbosity < 2:
            return
            
        print("\n  Vertex Data:")
        print("  X      Y")
        print("  " + "-" * 20)
        
        for vertex in vertices:
            print(f"  {vertex.x:6d} {vertex.y:6d}")

class LinedefsParser(LumpParser):
    lump_name = "LINEDEFS"
    RECORD_SIZE = struct.calcsize("<HHHHHHH")  # 14 bytes
    
    def parse(self, data: bytes) -> list[Linedef]:
        if len(data) % self.RECORD_SIZE != 0:
            raise ValueError(f"Invalid {self.lump_name} lump size: {len(data)}")
            
        linedefs = []
        for i in range(0, len(data), self.RECORD_SIZE):
            start, end, flags, special, tag, right_side, left_side = struct.unpack("<HHHHHHH", data[i:i+self.RECORD_SIZE])
            linedefs.append(Linedef(start, end, flags, special, tag, right_side, left_side))
        return linedefs
    
    def display(self, linedefs: list[Linedef], verbosity: int = 1) -> None:
        if verbosity < 2:
            return
            
        print("\n  Linedef Data:")
        print("  Start  End    Flags   Special Type  Sector Tag")
        print("  " + "-" * 50)
        
        for linedef in linedefs:
            print(f"  {linedef.start:6d} {linedef.end:6d} {linedef.flags:6d} "
                  f"{linedef.special:6d} {linedef.tag:6d}")

class SectorsParser(LumpParser):
    lump_name = "SECTORS"
    # 2 shorts + 2 8-byte strings + 3 shorts = 26 bytes
    RECORD_SIZE = struct.calcsize("<hh8s8sHHH")
    
    def parse(self, data: bytes) -> list[Sector]:
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
        if verbosity < 2:
            return
            
        print("\n  Sector Data:")
        print("  Floor  Ceil   Light  Special Type  Tag")
        print("  " + "-" * 50)
        
        for sector in sectors:
            print(f"  {sector.floor_height:6d} {sector.ceiling_height:6d} "
                  f"{sector.light:6d} {sector.special:6d} {sector.tag:6d}")

class SidedefsParser(LumpParser):
    lump_name = "SIDEDEFS"
    # 2 shorts + 3 8-byte strings + 1 short = 30 bytes
    RECORD_SIZE = struct.calcsize("<hh8s8s8sH")
    
    def parse(self, data: bytes) -> list[Sidedef]:
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
        if verbosity < 2:
            return
            
        print("\n  Sidedef Data:")
        print("  X-Off  Y-Off  Upper    Lower    Middle   Sector")
        print("  " + "-" * 60)
        
        for sidedef in sidedefs:
            print(f"  {sidedef.x_off:6d} {sidedef.y_off:6d} {sidedef.upper_tex:<8s} "
                  f"{sidedef.lower_tex:<8s} {sidedef.middle_tex:<8s} {sidedef.sector:6d}")