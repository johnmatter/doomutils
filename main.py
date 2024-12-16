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
    parser.add_argument('wad_file', help='Path to WAD file')
    parser.add_argument('-v', '--verbosity', type=int, default=1,
                       help='Verbosity level (0-3)')
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    logging.basicConfig(
        level=log_levels[args.verbosity],
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    wad = WADManager(args.wad_file)
    wad.dump(args.verbosity)

if __name__ == '__main__':
    main()