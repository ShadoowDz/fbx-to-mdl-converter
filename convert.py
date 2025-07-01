#!/usr/bin/env python3
"""
FBX to MDL Converter for Counter-Strike 1.6
Main conversion script with command-line interface
"""

import argparse
import sys
import os
import time
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.fbx_parser import FBXParser
    from core.mdl_writer import MDLWriter
    from core.bone_detector import BoneDetector
    from core.animation_processor import AnimationProcessor
    from utils.logger import setup_logger
    from utils.validation import ModelValidator
    from utils.texture_utils import TextureProcessor
    import config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed and the project structure is correct.")
    sys.exit(1)


class FBXToMDLConverter:
    """Main converter class that orchestrates the conversion process"""
    
    def __init__(self, args):
        self.args = args
        self.logger = setup_logger(__name__, args.log_level)
        self.stats = {
            'start_time': time.time(),
            'vertices_processed': 0,
            'triangles_processed': 0,
            'bones_processed': 0,
            'animations_processed': 0,
            'textures_processed': 0
        }
        
        # Initialize components
        self.fbx_parser = FBXParser()
        self.bone_detector = BoneDetector()
        self.animation_processor = AnimationProcessor()
        self.texture_processor = TextureProcessor()
        self.mdl_writer = MDLWriter()
        self.validator = ModelValidator()
        
    def convert(self, input_path, output_path):
        """Main conversion method"""
        try:
            self.logger.info(f"Starting conversion: {input_path} -> {output_path}")
            
            # Validate input file
            if not self._validate_input(input_path):
                return False
            
            # Parse FBX file
            self.logger.info("Parsing FBX file...")
            fbx_data = self.fbx_parser.parse(input_path)
            if not fbx_data:
                self.logger.error("Failed to parse FBX file")
                return False
            
            # Process geometry
            self.logger.info("Processing geometry...")
            geometry_data = self._process_geometry(fbx_data)
            
            # Detect and process bones
            self.logger.info("Detecting bones...")
            bone_data = self.bone_detector.detect_bones(fbx_data, self.args.optimize_bones)
            self.stats['bones_processed'] = len(bone_data.get('bones', []))
            
            # Process animations
            animation_data = None
            if fbx_data.get('animations') and not self.args.skip_animations:
                self.logger.info("Processing animations...")
                animation_data = self.animation_processor.process_animations(
                    fbx_data['animations'], 
                    bone_data,
                    compress=self.args.compress_animations
                )
                self.stats['animations_processed'] = len(animation_data.get('sequences', []))
            
            # Process textures
            texture_data = None
            if fbx_data.get('materials') and not self.args.skip_textures:
                self.logger.info("Processing textures...")
                texture_data = self.texture_processor.process_textures(
                    fbx_data['materials'], 
                    os.path.dirname(output_path)
                )
                self.stats['textures_processed'] = len(texture_data.get('textures', []))
            
            # Generate hitboxes if requested
            hitbox_data = None
            if self.args.generate_hitboxes:
                self.logger.info("Generating hitboxes...")
                hitbox_data = self._generate_hitboxes(bone_data)
            
            # Validate model before writing
            if self.args.validate_output:
                self.logger.info("Validating model data...")
                validation_result = self.validator.validate_model_data(
                    geometry_data, bone_data, animation_data, texture_data
                )
                if not validation_result.is_valid:
                    self.logger.error(f"Model validation failed: {validation_result.errors}")
                    if config.STOP_ON_ERROR:
                        return False
            
            # Write MDL file
            self.logger.info("Writing MDL file...")
            mdl_data = {
                'geometry': geometry_data,
                'bones': bone_data,
                'animations': animation_data,
                'textures': texture_data,
                'hitboxes': hitbox_data
            }
            
            success = self.mdl_writer.write_mdl(mdl_data, output_path)
            if not success:
                self.logger.error("Failed to write MDL file")
                return False
            
            # Final validation
            if self.args.validate_output:
                self.logger.info("Performing final validation...")
                if not self.validator.validate_mdl_file(output_path):
                    self.logger.warning("Final validation warnings detected")
            
            # Log statistics
            self._log_statistics()
            
            self.logger.info(f"Conversion completed successfully: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Conversion failed with error: {str(e)}")
            if self.args.debug:
                import traceback
                self.logger.debug(traceback.format_exc())
            return False
    
    def _validate_input(self, input_path):
        """Validate input file"""
        if not os.path.exists(input_path):
            self.logger.error(f"Input file not found: {input_path}")
            return False
        
        if not input_path.lower().endswith('.fbx'):
            self.logger.error(f"Input file must be FBX format: {input_path}")
            return False
        
        file_size = os.path.getsize(input_path)
        if file_size == 0:
            self.logger.error(f"Input file is empty: {input_path}")
            return False
        
        self.logger.info(f"Input file validated: {input_path} ({file_size} bytes)")
        return True
    
    def _process_geometry(self, fbx_data):
        """Process geometry data with optimization"""
        geometry = fbx_data.get('geometry', {})
        
        # Update statistics
        vertices = geometry.get('vertices', [])
        triangles = geometry.get('triangles', [])
        self.stats['vertices_processed'] = len(vertices)
        self.stats['triangles_processed'] = len(triangles)
        
        # Optimize geometry if requested
        if self.args.optimize_geometry:
            from utils.geometry_utils import GeometryOptimizer
            optimizer = GeometryOptimizer()
            geometry = optimizer.optimize(geometry)
            self.logger.info(f"Geometry optimized: {len(geometry.get('vertices', []))} vertices, {len(geometry.get('triangles', []))} triangles")
        
        # Validate geometry limits
        if len(vertices) > config.MAX_VERTICES_PER_MESH:
            self.logger.warning(f"Vertex count ({len(vertices)}) exceeds CS 1.6 limit ({config.MAX_VERTICES_PER_MESH})")
        
        if len(triangles) > config.MAX_TRIANGLES_PER_MESH:
            self.logger.warning(f"Triangle count ({len(triangles)}) exceeds CS 1.6 limit ({config.MAX_TRIANGLES_PER_MESH})")
        
        return geometry
    
    def _generate_hitboxes(self, bone_data):
        """Generate hitboxes based on bone structure"""
        if not config.AUTO_GENERATE_HITBOXES:
            return None
        
        hitboxes = []
        bones = bone_data.get('bones', [])
        
        for bone in bones:
            bone_name = bone.get('name', '')
            
            # Map bone to hitbox group
            hitbox_group = config.HITBOX_BONE_MAPPING.get(bone_name, 0)
            
            if hitbox_group > 0:  # Skip generic group
                hitbox = {
                    'bone_index': bone.get('index', 0),
                    'group': hitbox_group,
                    'min_bounds': bone.get('min_bounds', [0, 0, 0]),
                    'max_bounds': bone.get('max_bounds', [0, 0, 0])
                }
                hitboxes.append(hitbox)
        
        self.logger.info(f"Generated {len(hitboxes)} hitboxes")
        return {'hitboxes': hitboxes}
    
    def _log_statistics(self):
        """Log conversion statistics"""
        elapsed_time = time.time() - self.stats['start_time']
        
        self.logger.info("=== Conversion Statistics ===")
        self.logger.info(f"Processing time: {elapsed_time:.2f} seconds")
        self.logger.info(f"Vertices processed: {self.stats['vertices_processed']}")
        self.logger.info(f"Triangles processed: {self.stats['triangles_processed']}")
        self.logger.info(f"Bones processed: {self.stats['bones_processed']}")
        self.logger.info(f"Animations processed: {self.stats['animations_processed']}")
        self.logger.info(f"Textures processed: {self.stats['textures_processed']}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Convert FBX models to Counter-Strike 1.6 MDL format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert.py model.fbx model.mdl
  python convert.py model.fbx model.mdl --optimize-bones --compress-animations
  python convert.py model.fbx model.mdl --generate-hitboxes --validate-output
        """
    )
    
    # Required arguments
    parser.add_argument('input', help='Input FBX file path')
    parser.add_argument('output', help='Output MDL file path')
    
    # Optional processing flags
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
    
    # Validation options
    parser.add_argument('--validate-output', action='store_true',
                       help='Validate output model for CS 1.6 compatibility')
    parser.add_argument('--no-validation', action='store_true',
                       help='Skip all validation checks')
    
    # Logging options
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with detailed error reporting')
    
    # Output options
    parser.add_argument('--backup', action='store_true',
                       help='Create backup of existing output file')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite output file without confirmation')
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Set debug mode if requested
    if args.debug:
        args.log_level = 'DEBUG'
        args.verbose = True
    
    # Validate arguments
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Check if output file exists
    if os.path.exists(args.output) and not args.force:
        if args.backup:
            backup_path = args.output + '.backup'
            import shutil
            shutil.copy2(args.output, backup_path)
            print(f"Created backup: {backup_path}")
        else:
            response = input(f"Output file exists: {args.output}. Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("Conversion cancelled")
                sys.exit(0)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Initialize converter and run conversion
    converter = FBXToMDLConverter(args)
    success = converter.convert(args.input, args.output)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()