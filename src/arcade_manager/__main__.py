from parser import Committer, Extractor
from argparse import ArgumentParser
from pathlib import Path
import shutil

def main():
    # Options for commit, extract, and initialize toolbox
    arg_parser = ArgumentParser()
    arg_parser.add_argument('mode', choices=['extract', 'commit', 'init'], help='Mode to run the arcade manager in')
    arg_parser.add_argument('-d','--database', help='Path to the file database')
    arg_parser.add_argument('-r','--repo', help='Path to the repository')
    arg_parser.add_argument('-t','--toolbox', help='Path to the toolbox')
    args = arg_parser.parse_args()
    
    if args.mode == 'extract':
        Extractor(args.database, args.repo).extract()
    elif args.mode == 'commit':
        Committer(args.database, args.repo).commit()
    elif args.mode == 'init':
        toolbox_location = args.toolbox
        # Copy this repository to the toolbox location
        toolbox_location = Path(toolbox_location)
        module_location = Path(__file__).parent
        toolbox_location.mkdir(parents=True, exist_ok=True)
        shutil.copytree(module_location, toolbox_location / 'arcade_manager')
        print(f"Initialized toolbox at {toolbox_location / 'arcade_manager' / 'toolbox' / 'ArcadeTools.pyt'}")
            
if __name__ == '__main__':
    main()