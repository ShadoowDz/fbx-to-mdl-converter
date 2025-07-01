"""
Validation utilities for Counter-Strike 1.6 MDL Converter
Validates models against CS 1.6 requirements and limits
"""

import os
import logging
from typing import Dict, List, Any, Optional, NamedTuple

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config


class ValidationResult(NamedTuple):
    """Result of a validation check"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class ModelValidator:
    """Validates model data against CS 1.6 requirements"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_model_data(self, geometry_data: Dict[str, Any], bone_data: Dict[str, Any], 
                           animation_data: Optional[Dict[str, Any]], 
                           texture_data: Optional[Dict[str, Any]]) -> ValidationResult:
        """Validate complete model data"""
        
        errors = []
        warnings = []
        
        self.logger.info("Validating model data...")
        
        # Validate geometry
        geom_result = self.validate_geometry(geometry_data)
        errors.extend(geom_result.errors)
        warnings.extend(geom_result.warnings)
        
        # Validate bones
        bone_result = self.validate_bones(bone_data)
        errors.extend(bone_result.errors)
        warnings.extend(bone_result.warnings)
        
        # Validate animations if present
        if animation_data:
            anim_result = self.validate_animations(animation_data, bone_data)
            errors.extend(anim_result.errors)
            warnings.extend(anim_result.warnings)
        
        # Validate textures if present
        if texture_data:
            tex_result = self.validate_textures(texture_data)
            errors.extend(tex_result.errors)
            warnings.extend(tex_result.warnings)
        
        is_valid = len(errors) == 0
        
        if is_valid:
            self.logger.info("Model validation passed")
        else:
            self.logger.warning(f"Model validation failed with {len(errors)} errors and {len(warnings)} warnings")
        
        return ValidationResult(is_valid, errors, warnings)
    
    def validate_geometry(self, geometry_data: Dict[str, Any]) -> ValidationResult:
        """Validate geometry data"""
        
        errors = []
        warnings = []
        
        vertices = geometry_data.get('vertices', [])
        triangles = geometry_data.get('triangles', [])
        
        # Check vertex count
        if len(vertices) > config.MAX_VERTICES_PER_MESH:
            errors.append(f"Vertex count ({len(vertices)}) exceeds CS 1.6 limit ({config.MAX_VERTICES_PER_MESH})")
        elif len(vertices) > config.RECOMMENDED_MAX_TRIANGLES // 3:
            warnings.append(f"High vertex count ({len(vertices)}) may impact performance")
        
        # Check triangle count
        if len(triangles) > config.MAX_TRIANGLES_PER_MESH:
            errors.append(f"Triangle count ({len(triangles)}) exceeds CS 1.6 limit ({config.MAX_TRIANGLES_PER_MESH})")
        elif len(triangles) > config.RECOMMENDED_MAX_TRIANGLES:
            warnings.append(f"High triangle count ({len(triangles)}) may impact performance")
        
        # Check for degenerate triangles
        degenerate_count = self._count_degenerate_triangles(triangles, vertices)
        if degenerate_count > 0:
            warnings.append(f"Found {degenerate_count} degenerate triangles")
        
        # Check for valid indices
        max_vertex_index = len(vertices) - 1
        invalid_indices = 0
        
        for triangle in triangles:
            for vertex_idx in triangle:
                if vertex_idx < 0 or vertex_idx > max_vertex_index:
                    invalid_indices += 1
        
        if invalid_indices > 0:
            errors.append(f"Found {invalid_indices} invalid vertex indices")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def validate_bones(self, bone_data: Dict[str, Any]) -> ValidationResult:
        """Validate bone data"""
        
        errors = []
        warnings = []
        
        bones = bone_data.get('bones', [])
        
        # Check bone count
        if len(bones) > config.MAX_BONES:
            errors.append(f"Bone count ({len(bones)}) exceeds CS 1.6 limit ({config.MAX_BONES})")
        elif len(bones) > config.RECOMMENDED_BONE_COUNT:
            warnings.append(f"High bone count ({len(bones)}) may impact performance")
        
        # Check bone names
        for bone in bones:
            bone_name = bone.get('name', '')
            
            if len(bone_name) > 32:
                errors.append(f"Bone name too long: {bone_name}")
            
            if not bone_name.strip():
                errors.append("Found bone with empty name")
        
        # Check for circular references
        circular_refs = self._check_circular_bone_references(bones)
        if circular_refs:
            errors.extend([f"Circular bone reference: {ref}" for ref in circular_refs])
        
        # Check root bone
        root_bones = [bone for bone in bones if bone.get('parent_index', -1) == -1]
        if len(root_bones) == 0:
            errors.append("No root bone found")
        elif len(root_bones) > 1:
            warnings.append(f"Multiple root bones found ({len(root_bones)})")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def validate_animations(self, animation_data: Dict[str, Any], bone_data: Dict[str, Any]) -> ValidationResult:
        """Validate animation data"""
        
        errors = []
        warnings = []
        
        sequences = animation_data.get('sequences', [])
        
        # Check sequence count
        if len(sequences) > config.MAX_ANIMATION_SEQUENCES:
            errors.append(f"Animation sequence count ({len(sequences)}) exceeds CS 1.6 limit ({config.MAX_ANIMATION_SEQUENCES})")
        
        # Validate each sequence
        for sequence in sequences:
            seq_name = sequence.get('name', 'unnamed')
            
            # Check sequence name length
            if len(seq_name) > 32:
                warnings.append(f"Animation sequence name too long: {seq_name}")
            
            # Check frame count
            start_frame = sequence.get('start_frame', 0)
            end_frame = sequence.get('end_frame', 0)
            frame_count = end_frame - start_frame + 1
            
            if frame_count > config.MAX_KEYFRAMES_PER_SEQUENCE:
                warnings.append(f"Sequence {seq_name} has {frame_count} frames (limit: {config.MAX_KEYFRAMES_PER_SEQUENCE})")
            
            # Check keyframes reference valid bones
            keyframes = sequence.get('keyframes', {})
            bone_names = {bone['name'] for bone in bone_data.get('bones', [])}
            
            for bone_name in keyframes.keys():
                if bone_name not in bone_names:
                    warnings.append(f"Animation references unknown bone: {bone_name}")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def validate_textures(self, texture_data: Dict[str, Any]) -> ValidationResult:
        """Validate texture data"""
        
        errors = []
        warnings = []
        
        textures = texture_data.get('textures', [])
        
        for texture in textures:
            texture_name = texture.get('name', 'unnamed')
            width = texture.get('width', 0)
            height = texture.get('height', 0)
            
            # Check texture size limits
            if width > config.MAX_TEXTURE_WIDTH:
                errors.append(f"Texture {texture_name} width ({width}) exceeds limit ({config.MAX_TEXTURE_WIDTH})")
            
            if height > config.MAX_TEXTURE_HEIGHT:
                errors.append(f"Texture {texture_name} height ({height}) exceeds limit ({config.MAX_TEXTURE_HEIGHT})")
            
            # Check if texture is power of 2
            if not self._is_power_of_2(width) or not self._is_power_of_2(height):
                warnings.append(f"Texture {texture_name} dimensions are not power of 2 ({width}x{height})")
            
            # Check texture name length
            if len(texture_name) > config.MAX_TEXTURE_NAME_LENGTH:
                warnings.append(f"Texture name too long: {texture_name}")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def validate_mdl_file(self, mdl_path: str) -> bool:
        """Validate an MDL file"""
        
        if not os.path.exists(mdl_path):
            self.logger.error(f"MDL file not found: {mdl_path}")
            return False
        
        file_size = os.path.getsize(mdl_path)
        if file_size == 0:
            self.logger.error(f"MDL file is empty: {mdl_path}")
            return False
        
        # Basic file format validation
        try:
            with open(mdl_path, 'rb') as f:
                signature = f.read(4)
                if signature != b'IDST':
                    self.logger.error(f"Invalid MDL signature in {mdl_path}")
                    return False
        except Exception as e:
            self.logger.error(f"Error reading MDL file {mdl_path}: {e}")
            return False
        
        self.logger.info(f"MDL file validation passed: {mdl_path}")
        return True
    
    def _count_degenerate_triangles(self, triangles: List[List[int]], vertices: List[List[float]]) -> int:
        """Count degenerate triangles (zero area)"""
        
        count = 0
        
        for triangle in triangles:
            if len(triangle) != 3:
                continue
            
            try:
                v1 = vertices[triangle[0]]
                v2 = vertices[triangle[1]]
                v3 = vertices[triangle[2]]
                
                # Calculate triangle area using cross product
                edge1 = [v2[i] - v1[i] for i in range(3)]
                edge2 = [v3[i] - v1[i] for i in range(3)]
                
                cross = [
                    edge1[1] * edge2[2] - edge1[2] * edge2[1],
                    edge1[2] * edge2[0] - edge1[0] * edge2[2],
                    edge1[0] * edge2[1] - edge1[1] * edge2[0]
                ]
                
                area = 0.5 * (cross[0]**2 + cross[1]**2 + cross[2]**2)**0.5
                
                if area < 1e-6:  # Very small area threshold
                    count += 1
                    
            except (IndexError, TypeError):
                count += 1  # Treat invalid triangles as degenerate
        
        return count
    
    def _check_circular_bone_references(self, bones: List[Dict[str, Any]]) -> List[str]:
        """Check for circular references in bone hierarchy"""
        
        circular_refs = []
        
        for bone in bones:
            visited = set()
            current_bone = bone
            path = []
            
            while current_bone:
                bone_idx = current_bone.get('index', -1)
                bone_name = current_bone.get('name', f'bone_{bone_idx}')
                
                if bone_idx in visited:
                    circular_refs.append(' -> '.join(path + [bone_name]))
                    break
                
                visited.add(bone_idx)
                path.append(bone_name)
                
                parent_idx = current_bone.get('parent_index', -1)
                if parent_idx == -1:
                    break
                
                # Find parent bone
                current_bone = None
                for parent_bone in bones:
                    if parent_bone.get('index') == parent_idx:
                        current_bone = parent_bone
                        break
        
        return circular_refs
    
    def _is_power_of_2(self, n: int) -> bool:
        """Check if number is power of 2"""
        return n > 0 and (n & (n - 1)) == 0