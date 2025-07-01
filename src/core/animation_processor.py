"""
Animation Processor for Counter-Strike 1.6 MDL Converter
Processes and optimizes animation data for CS 1.6 compatibility
"""

import logging
from typing import Dict, List, Any, Optional

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config


class AnimationProcessor:
    """Processes animation data for CS 1.6 compatibility"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_animations(self, animation_data: Dict[str, Any], bone_data: Dict[str, Any], 
                          compress: bool = True) -> Optional[Dict[str, Any]]:
        """Process animation sequences for CS 1.6"""
        
        if not animation_data or not animation_data.get('sequences'):
            self.logger.info("No animations to process")
            return None
        
        sequences = animation_data.get('sequences', [])
        self.logger.info(f"Processing {len(sequences)} animation sequences")
        
        processed_sequences = []
        
        for sequence in sequences:
            processed_seq = self._process_sequence(sequence, bone_data, compress)
            if processed_seq:
                processed_sequences.append(processed_seq)
        
        result = {
            'sequences': processed_sequences,
            'frame_rate': animation_data.get('frame_rate', 30.0)
        }
        
        self.logger.info(f"Processed {len(processed_sequences)} animation sequences")
        return result
    
    def _process_sequence(self, sequence: Dict[str, Any], bone_data: Dict[str, Any], 
                         compress: bool) -> Optional[Dict[str, Any]]:
        """Process a single animation sequence"""
        
        sequence_name = sequence.get('name', 'unnamed')
        self.logger.debug(f"Processing sequence: {sequence_name}")
        
        # Basic validation
        if not sequence.get('keyframes'):
            self.logger.warning(f"Sequence {sequence_name} has no keyframes")
            return None
        
        # Process keyframes
        processed_keyframes = self._process_keyframes(
            sequence['keyframes'], bone_data, compress
        )
        
        # Create processed sequence
        processed_sequence = {
            'name': sequence_name,
            'frame_rate': sequence.get('frame_rate', 30.0),
            'start_frame': sequence.get('start_frame', 0),
            'end_frame': sequence.get('end_frame', 0),
            'keyframes': processed_keyframes,
            'loop': sequence.get('loop', False)
        }
        
        return processed_sequence
    
    def _process_keyframes(self, keyframes: Dict[str, List[Dict[str, Any]]], 
                          bone_data: Dict[str, Any], compress: bool) -> Dict[str, List[Dict[str, Any]]]:
        """Process keyframes for all bones"""
        
        processed_keyframes = {}
        bones = bone_data.get('bones', [])
        bone_name_map = {bone['name']: bone['index'] for bone in bones}
        
        for bone_name, bone_keyframes in keyframes.items():
            # Map bone name to CS 1.6 convention
            cs16_bone_name = self._map_bone_name(bone_name, bone_name_map)
            
            if cs16_bone_name not in bone_name_map:
                self.logger.debug(f"Skipping keyframes for unmapped bone: {bone_name}")
                continue
            
            # Process keyframes for this bone
            processed_frames = self._process_bone_keyframes(bone_keyframes, compress)
            
            if processed_frames:
                processed_keyframes[cs16_bone_name] = processed_frames
        
        return processed_keyframes
    
    def _process_bone_keyframes(self, keyframes: List[Dict[str, Any]], 
                               compress: bool) -> List[Dict[str, Any]]:
        """Process keyframes for a single bone"""
        
        if not keyframes:
            return []
        
        processed_frames = []
        
        for frame in keyframes:
            processed_frame = {
                'frame': frame.get('frame', 0),
                'time': frame.get('time', 0.0),
                'translation': frame.get('translation', [0.0, 0.0, 0.0]),
                'rotation': frame.get('rotation', [0.0, 0.0, 0.0]),
                'scale': frame.get('scale', [1.0, 1.0, 1.0])
            }
            processed_frames.append(processed_frame)
        
        # Apply compression if requested
        if compress and config.KEYFRAME_REDUCTION:
            processed_frames = self._compress_keyframes(processed_frames)
        
        return processed_frames
    
    def _compress_keyframes(self, keyframes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compress keyframes by removing redundant ones"""
        
        if len(keyframes) <= 2:
            return keyframes  # Can't compress with 2 or fewer frames
        
        compressed = [keyframes[0]]  # Always keep first frame
        tolerance = config.ANIMATION_COMPRESSION
        
        for i in range(1, len(keyframes) - 1):
            current = keyframes[i]
            prev = compressed[-1]
            next_frame = keyframes[i + 1]
            
            # Check if this frame can be interpolated from prev and next
            if not self._can_interpolate_frame(prev, current, next_frame, tolerance):
                compressed.append(current)
        
        compressed.append(keyframes[-1])  # Always keep last frame
        
        reduction = len(keyframes) - len(compressed)
        if reduction > 0:
            self.logger.debug(f"Compressed keyframes: {len(keyframes)} -> {len(compressed)} (-{reduction})")
        
        return compressed
    
    def _can_interpolate_frame(self, prev_frame: Dict[str, Any], current_frame: Dict[str, Any], 
                              next_frame: Dict[str, Any], tolerance: float) -> bool:
        """Check if a frame can be interpolated between two others"""
        
        # Simple linear interpolation check
        prev_trans = prev_frame['translation']
        curr_trans = current_frame['translation']
        next_trans = next_frame['translation']
        
        # Calculate interpolated position
        frame_ratio = (current_frame['frame'] - prev_frame['frame']) / \
                     (next_frame['frame'] - prev_frame['frame'])
        
        interpolated = [
            prev_trans[i] + (next_trans[i] - prev_trans[i]) * frame_ratio
            for i in range(3)
        ]
        
        # Check if difference is within tolerance
        for i in range(3):
            if abs(curr_trans[i] - interpolated[i]) > tolerance:
                return False
        
        return True
    
    def _map_bone_name(self, original_name: str, bone_name_map: Dict[str, int]) -> str:
        """Map original bone name to CS 1.6 bone name"""
        
        # If already in map, return as-is
        if original_name in bone_name_map:
            return original_name
        
        # Try to find matching CS 1.6 bone name
        name_lower = original_name.lower()
        
        for cs16_name in bone_name_map.keys():
            if cs16_name.lower() in name_lower or name_lower in cs16_name.lower():
                return cs16_name
        
        return original_name  # Return original if no mapping found