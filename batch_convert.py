#!/usr/bin/env python3
"""
Batch FBX to MDL Converter for Counter-Strike 1.6
Processes multiple FBX files in a directory
"""

import argparse
import os
import sys
import glob
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from utils.logger import get_logger, create_conversion_logger
    import config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed and the project structure is correct.")
    sys.exit(1)


class BatchConverter:
    """Batch converter for multiple FBX files"""
    
    def __init__(self, args):
        self.args = args
        self.logger = get_logger(__name__)
        self.conversion_logger = create_conversion_logger(__name__)
        self.stats = {
            'total_files': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'start_time': time.time()
        }
        self.lock = threading.Lock()
    
    def find_fbx_files(self, input_dir: str) -> list:
        """Find all FBX files in the input directory"""
        fbx_files = []
        
        # Search patterns
        patterns = ['*.fbx', '*.FBX']
        
        for pattern in patterns:
            if self.args.recursive:
                search_pattern = os.path.join(input_dir, '**', pattern)
                fbx_files.extend(glob.glob(search_pattern, recursive=True))
            else:
                search_pattern = os.path.join(input_dir, pattern)
                fbx_files.extend(glob.glob(search_pattern))
        
        # Remove duplicates and sort
        fbx_files = sorted(list(set(fbx_files)))
        
        self.logger.info(f"Found {len(fbx_files)} FBX files in {input_dir}")
        return fbx_files
    
    def get_output_path(self, input_file: str, output_dir: str) -> str:
        """Generate output path for an input file"""
        input_path = Path(input_file)
        
        if self.args.preserve_structure:
            # Preserve directory structure
            relative_path = input_path.relative_to(self.args.input_dir)
            output_path = Path(output_dir) / relative_path.with_suffix('.mdl')
        else:
            # Flat output structure
            output_filename = input_path.stem + '.mdl'
            output_path = Path(output_dir) / output_filename
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        return str(output_path)
    
    def convert_single_file(self, input_file: str, output_file: str) -> bool:
        """Convert a single FBX file to MDL"""
        try:
            # Import the main converter
            from convert import FBXToMDLConverter
            
            # Create converter arguments
            converter_args = type('Args', (), {
                'optimize_bones': self.args.optimize_bones,
                'optimize_geometry': self.args.optimize_geometry,
                'compress_animations': self.args.compress_animations,
                'generate_hitboxes': self.args.generate_hitboxes,
                'skip_animations': self.args.skip_animations,
                'skip_textures': self.args.skip_textures,
                'validate_output': self.args.validate_output,
                'log_level': 'WARNING' if self.args.quiet else 'INFO',
                'verbose': False,
                'debug': self.args.debug
            })()
            
            # Create converter instance
            converter = FBXToMDLConverter(converter_args)
            
            # Perform conversion
            success = converter.convert(input_file, output_file)
            
            # Update statistics
            with self.lock:
                if success:
                    self.stats['successful_conversions'] += 1
                    if not self.args.quiet:
                        self.logger.info(f"✓ Converted: {os.path.basename(input_file)}")
                else:
                    self.stats['failed_conversions'] += 1
                    self.logger.error(f"✗ Failed: {os.path.basename(input_file)}")
            
            return success
            
        except Exception as e:
            with self.lock:
                self.stats['failed_conversions'] += 1
                self.logger.error(f"✗ Error converting {os.path.basename(input_file)}: {str(e)}")
            return False
    
    def convert_batch(self) -> bool:
        """Convert all FBX files in batch"""
        # Find FBX files
        fbx_files = self.find_fbx_files(self.args.input_dir)
        
        if not fbx_files:
            self.logger.error("No FBX files found in input directory")
            return False
        
        self.stats['total_files'] = len(fbx_files)
        
        # Prepare output directory
        os.makedirs(self.args.output_dir, exist_ok=True)
        
        # Generate conversion tasks
        conversion_tasks = []
        for input_file in fbx_files:
            output_file = self.get_output_path(input_file, self.args.output_dir)
            
            # Skip if output exists and not overwriting
            if os.path.exists(output_file) and not self.args.overwrite:
                if not self.args.quiet:
                    self.logger.info(f"Skipping existing: {os.path.basename(output_file)}")
                continue
            
            conversion_tasks.append((input_file, output_file))
        
        if not conversion_tasks:
            self.logger.info("No files to convert (all outputs exist)")
            return True
        
        self.logger.info(f"Starting batch conversion of {len(conversion_tasks)} files...")
        
        # Perform conversions
        if self.args.parallel and self.args.max_workers > 1:
            success = self._convert_parallel(conversion_tasks)
        else:
            success = self._convert_sequential(conversion_tasks)
        
        # Log final statistics
        self._log_final_stats()
        
        return success
    
    def _convert_sequential(self, tasks: list) -> bool:
        """Convert files sequentially"""
        for i, (input_file, output_file) in enumerate(tasks, 1):
            if not self.args.quiet:
                self.logger.info(f"Processing {i}/{len(tasks)}: {os.path.basename(input_file)}")
            
            self.convert_single_file(input_file, output_file)
        
        return self.stats['failed_conversions'] == 0
    
    def _convert_parallel(self, tasks: list) -> bool:
        """Convert files in parallel"""
        with ThreadPoolExecutor(max_workers=self.args.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.convert_single_file, input_file, output_file): (input_file, output_file)
                for input_file, output_file in tasks
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_task):
                completed += 1
                input_file, output_file = future_to_task[future]
                
                if not self.args.quiet:
                    progress = (completed / len(tasks)) * 100
                    self.logger.info(f"Progress: {completed}/{len(tasks)} ({progress:.1f}%)")
        
        return self.stats['failed_conversions'] == 0
    
    def _log_final_stats(self):
        """Log final conversion statistics"""
        elapsed_time = time.time() - self.stats['start_time']
        
        self.logger.info("=" * 60)
        self.logger.info("Batch Conversion Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"Total files processed: {self.stats['total_files']}")
        self.logger.info(f"Successful conversions: {self.stats['successful_conversions']}")
        self.logger.info(f"Failed conversions: {self.stats['failed_conversions']}")
        
        if self.stats['total_files'] > 0:
            success_rate = (self.stats['successful_conversions'] / self.stats['total_files']) * 100
            self.logger.info(f"Success rate: {success_rate:.1f}%")
        
        self.logger.info(f"Total time: {elapsed_time:.2f} seconds")
        
        if self.stats['successful_conversions'] > 0:
            avg_time = elapsed_time / self.stats['successful_conversions']
            self.logger.info(f"Average time per file: {avg_time:.2f} seconds")
        
        self.logger.info("=" * 60)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Batch convert FBX models to Counter-Strike 1.6 MDL format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_convert.py input_models/ output_models/
  python batch_convert.py input/ output/ --recursive --parallel
  python batch_convert.py models/ converted/ --optimize-bones --compress-animations
        """
    )
    
    # Required arguments
    parser.add_argument('input_dir', help='Input directory containing FBX files')
    parser.add_argument('output_dir', help='Output directory for MDL files')
    
    # Search options
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Search for FBX files recursively in subdirectories')
    parser.add_argument('--preserve-structure', action='store_true',
                       help='Preserve directory structure in output')
    
    # Processing options
    parser.add_argument('--parallel', action='store_true',
                       help='Enable parallel processing')
    parser.add_argument('--max-workers', type=int, default=4,
                       help='Maximum number of parallel workers (default: 4)')
    
    # Conversion options (same as main converter)
    parser.add_argument('--optimize-bones', action='store_true',
                       help='Optimize bone hierarchy and reduce bone count')
    parser.add_argument('--optimize-geometry', action='store_true',
                       help='Optimize geometry (merge vertices, etc.)')
    parser.add_argument('--compress-animations', action='store_true',
                       help='Compress animation data and remove redundant keyframes')
    parser.add_argument('--generate-hitboxes', action='store_true',
                       help='Auto-generate CS 1.6 hitboxes based on bone structure')
    
    # Skip options
    parser.add_argument('--skip-animations', action='store_true',
                       help='Skip animation processing')
    parser.add_argument('--skip-textures', action='store_true',
                       help='Skip texture processing')
    
    # Output options
    parser.add_argument('--overwrite', action='store_true',
                       help='Overwrite existing output files')
    parser.add_argument('--validate-output', action='store_true',
                       help='Validate output models for CS 1.6 compatibility')
    
    # Logging options
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Reduce output verbosity')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with detailed error reporting')
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Validate arguments
    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory not found: {args.input_dir}")
        sys.exit(1)
    
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input path is not a directory: {args.input_dir}")
        sys.exit(1)
    
    # Limit parallel workers
    if args.parallel:
        import multiprocessing
        max_cores = multiprocessing.cpu_count()
        args.max_workers = min(args.max_workers, max_cores)
    
    # Create batch converter and run
    converter = BatchConverter(args)
    success = converter.convert_batch()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()