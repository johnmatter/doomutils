from WADManager import WADManager

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Parse a WAD file.")
    parser.add_argument("wad_file", help="Path to the WAD file to parse.")
    parser.add_argument("-v", "--verbosity", type=int, default=1, help="Verbosity level (0-2).")
    return parser.parse_args()  

def main():
    args = parse_args()
    wad = WADManager(args.wad_file)
    wad.dump(args.verbosity)

if __name__ == "__main__":
    main()