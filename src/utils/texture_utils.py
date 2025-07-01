"""
Texture Processing Utilities for Counter-Strike 1.6 MDL Converter
Handles texture conversion and optimization for CS 1.6 compatibility
"""

import os
import logging
from typing import Dict, List, Any, Optional
from PIL import Image

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config


class TextureProcessor:
    """Processes textures for CS 1.6 compatibility"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_textures(self, material_data: Dict[str, Any], output_dir: str) -> Optional[Dict[str, Any]]:
        """Process textures from material data"""
        
        if not material_data or not material_data.get('textures'):
            self.logger.info("No textures to process")
            return None
        
        textures = material_data.get('textures', [])
        self.logger.info(f"Processing {len(textures)} textures")
        
        processed_textures = []
        
        for texture in textures:
            processed_texture = self._process_single_texture(texture, output_dir)
            if processed_texture:
                processed_textures.append(processed_texture)
        
        result = {
            'textures': processed_textures,
            'texture_count': len(processed_textures)
        }
        
        self.logger.info(f"Processed {len(processed_textures)} textures")
        return result
    
    def _process_single_texture(self, texture_info: Dict[str, Any], output_dir: str) -> Optional[Dict[str, Any]]:
        """Process a single texture"""
        
        texture_filename = texture_info.get('filename', '')
        if not texture_filename or not os.path.exists(texture_filename):
            self.logger.warning(f"Texture file not found: {texture_filename}")
            return None
        
        try:
            # Load image
            with Image.open(texture_filename) as img:
                # Convert to appropriate format for CS 1.6
                converted_img = self._convert_for_cs16(img)
                
                # Generate output filename
                base_name = os.path.splitext(os.path.basename(texture_filename))[0]
                output_filename = f"{base_name}.bmp"
                output_path = os.path.join(output_dir, output_filename)
                
                # Save converted texture
                converted_img.save(output_path, 'BMP')
                
                processed_texture = {
                    'name': texture_info.get('name', base_name),
                    'original_file': texture_filename,
                    'output_file': output_path,
                    'width': converted_img.width,
                    'height': converted_img.height,
                    'format': 'BMP'
                }
                
                self.logger.debug(f"Processed texture: {texture_filename} -> {output_path}")
                return processed_texture
                
        except Exception as e:
            self.logger.error(f"Failed to process texture {texture_filename}: {e}")
            return None
    
    def _convert_for_cs16(self, img: Image.Image) -> Image.Image:
        """Convert image for CS 1.6 compatibility"""
        
        # Resize if too large
        max_size = (config.MAX_TEXTURE_WIDTH, config.MAX_TEXTURE_HEIGHT)
        if img.width > max_size[0] or img.height > max_size[1]:
            img = img.resize(max_size, Image.LANCZOS)
            self.logger.debug(f"Resized texture to {img.width}x{img.height}")
        
        # Convert to 8-bit indexed color if needed
        if config.TEXTURE_BIT_DEPTH == 8:
            if img.mode != 'P':
                img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                self.logger.debug("Converted texture to 8-bit indexed color")
        
        return img