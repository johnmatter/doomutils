import logging
import argparse
from WADManager import WADManager

def main():
    # Map verbosity levels to logging levels
    log_levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.DEBUG
    }

    parser = argparse.ArgumentParser(description='WAD File Parser')
    parser.add_argument('action', help='Action to perform (dump, append, delete, validate)')
    parser.add_argument('wad_file', help='Path to WAD file')
    parser.add_argument('-v', '--verbosity', type=int, default=1,
                       help='Verbosity level (0-3)')
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Output file path')
    parser.add_argument('-type', '--type', type=str, default='patch',
                       help='Type of lump to append image to (sprite, flat, patch, etc.)')
    parser.add_argument('-i', '--image', type=str, default=None,
                       help='Path to image file to append')
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    logging.basicConfig(
        level=log_levels[args.verbosity],
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    wad = WADManager(args.wad_file, args.output)
    if args.action == "dump":
        wad.dump(args.verbosity)
    elif args.action == "append":
        wad.append(args.image, args.type)
    elif args.action == "delete":
        wad.delete(args.output)
    elif args.action == "validate":
        wad.validate()
    else:
        print("Invalid action. Please use one of: dump, append, delete, validate")

if __name__ == '__main__':
    main()
