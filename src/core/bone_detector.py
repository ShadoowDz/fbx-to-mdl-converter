"""
Bone Detection and Processing for Counter-Strike 1.6 MDL Converter
Intelligent bone hierarchy detection and optimization
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import re

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config


class BoneDetector:
    """Intelligent bone detection and hierarchy optimization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bone_patterns = config.BONE_NAME_PATTERNS
        self.cs16_mapping = config.CS16_BONE_MAPPING
        
    def detect_bones(self, fbx_data: Dict[str, Any], optimize: bool = True) -> Dict[str, Any]:
        """Main bone detection and processing method"""
        self.logger.info("Starting bone detection and processing...")
        
        # Extract raw bone data from FBX
        raw_bones = fbx_data.get('bones', {})
        
        if not raw_bones or not raw_bones.get('bones'):
            self.logger.warning("No bones found in FBX data")
            return self._create_empty_bone_data()
        
        # Process bone hierarchy
        processed_bones = self._process_bone_hierarchy(raw_bones)
        
        # Detect bone types and roles
        bone_types = self._detect_bone_types(processed_bones)
        
        # Map to CS 1.6 naming convention
        mapped_bones = self._map_to_cs16_names(processed_bones, bone_types)
        
        # Optimize bone hierarchy if requested
        if optimize:
            optimized_bones = self._optimize_bone_hierarchy(mapped_bones)
        else:
            optimized_bones = mapped_bones
        
        # Validate bone limits
        validated_bones = self._validate_bone_limits(optimized_bones)
        
        # Generate bone attachments
        bone_attachments = self._generate_bone_attachments(validated_bones)
        
        result = {
            'bones': validated_bones['bones'],
            'hierarchy': validated_bones['hierarchy'],
            'bone_types': bone_types,
            'bone_attachments': bone_attachments,
            'root_bone_index': self._find_root_bone(validated_bones['bones']),
            'bone_count': len(validated_bones['bones'])
        }
        
        self.logger.info(f"Bone processing completed: {result['bone_count']} bones")
        return result
    
    def _create_empty_bone_data(self) -> Dict[str, Any]:
        """Create empty bone data structure"""
        return {
            'bones': [],
            'hierarchy': {},
            'bone_types': {},
            'bone_attachments': [],
            'root_bone_index': -1,
            'bone_count': 0
        }
    
    def _process_bone_hierarchy(self, raw_bones: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean up bone hierarchy"""
        bones = raw_bones.get('bones', [])
        
        # Sort bones by hierarchy depth to ensure parents are processed first
        sorted_bones = self._sort_bones_by_hierarchy(bones)
        
        # Build hierarchy mapping
        hierarchy = {}
        for i, bone in enumerate(sorted_bones):
            bone['index'] = i
            hierarchy[bone['name']] = i
        
        # Update parent-child relationships with new indices
        for bone in sorted_bones:
            if bone.get('parent_index', -1) >= 0:
                # Find parent by name and update index
                parent_name = self._find_bone_name_by_old_index(bones, bone['parent_index'])
                if parent_name in hierarchy:
                    bone['parent_index'] = hierarchy[parent_name]
                else:
                    bone['parent_index'] = -1
        
        return {
            'bones': sorted_bones,
            'hierarchy': hierarchy
        }
    
    def _sort_bones_by_hierarchy(self, bones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort bones to ensure proper hierarchy order"""
        # Create a mapping of bone indices to bones
        bone_map = {bone['index']: bone for bone in bones}
        
        # Calculate hierarchy depth for each bone
        def get_hierarchy_depth(bone_index: int, visited: set = None) -> int:
            if visited is None:
                visited = set()
            
            if bone_index in visited:
                return 0  # Circular reference, treat as root
            
            visited.add(bone_index)
            bone = bone_map.get(bone_index)
            
            if not bone or bone.get('parent_index', -1) == -1:
                return 0
            
            parent_depth = get_hierarchy_depth(bone['parent_index'], visited.copy())
            return parent_depth + 1
        
        # Sort by hierarchy depth
        sorted_bones = sorted(bones, key=lambda b: get_hierarchy_depth(b['index']))
        
        return sorted_bones
    
    def _find_bone_name_by_old_index(self, bones: List[Dict[str, Any]], old_index: int) -> str:
        """Find bone name by its old index"""
        for bone in bones:
            if bone.get('index') == old_index:
                return bone.get('name', '')
        return ''
    
    def _detect_bone_types(self, processed_bones: Dict[str, Any]) -> Dict[str, str]:
        """Detect bone types based on naming patterns and hierarchy"""
        bones = processed_bones['bones']
        bone_types = {}
        
        for bone in bones:
            bone_name = bone['name'].lower()
            bone_type = self._classify_bone(bone_name, bone, bones)
            bone_types[bone['name']] = bone_type
        
        return bone_types
    
    def _classify_bone(self, bone_name: str, bone: Dict[str, Any], all_bones: List[Dict[str, Any]]) -> str:
        """Classify a bone based on its name and characteristics"""
        # Root bone detection
        if bone.get('parent_index', -1) == -1:
            if any(pattern in bone_name for pattern in ['bip01', 'root', 'hip', 'pelvis']):
                return 'root'
            return 'root'  # Default root type
        
        # Spine bones
        if any(pattern in bone_name for pattern in ['spine', 'back', 'chest']):
            return 'spine'
        
        # Head and neck
        if 'head' in bone_name:
            return 'head'
        if 'neck' in bone_name:
            return 'neck'
        
        # Arms
        if any(pattern in bone_name for pattern in ['arm', 'shoulder', 'clavicle']):
            if any(side in bone_name for side in ['l ', 'left', ' l']):
                return 'left_arm'
            elif any(side in bone_name for side in ['r ', 'right', ' r']):
                return 'right_arm'
            return 'arm'
        
        # Hands
        if any(pattern in bone_name for pattern in ['hand', 'wrist', 'finger', 'thumb']):
            if any(side in bone_name for side in ['l ', 'left', ' l']):
                return 'left_hand'
            elif any(side in bone_name for side in ['r ', 'right', ' r']):
                return 'right_hand'
            return 'hand'
        
        # Legs
        if any(pattern in bone_name for pattern in ['leg', 'thigh', 'hip']):
            if any(side in bone_name for side in ['l ', 'left', ' l']):
                return 'left_leg'
            elif any(side in bone_name for side in ['r ', 'right', ' r']):
                return 'right_leg'
            return 'leg'
        
        # Feet
        if any(pattern in bone_name for pattern in ['foot', 'ankle', 'toe']):
            if any(side in bone_name for side in ['l ', 'left', ' l']):
                return 'left_foot'
            elif any(side in bone_name for side in ['r ', 'right', ' r']):
                return 'right_foot'
            return 'foot'
        
        # Default classification
        return 'other'
    
    def _map_to_cs16_names(self, processed_bones: Dict[str, Any], bone_types: Dict[str, str]) -> Dict[str, Any]:
        """Map bone names to CS 1.6 naming convention"""
        bones = processed_bones['bones']
        new_hierarchy = {}
        
        for bone in bones:
            original_name = bone['name']
            bone_type = bone_types.get(original_name, 'other')
            
            # Map to CS 1.6 name if possible
            cs16_name = self._get_cs16_bone_name(original_name, bone_type)
            
            bone['original_name'] = original_name
            bone['name'] = cs16_name
            bone['type'] = bone_type
            
            new_hierarchy[cs16_name] = bone['index']
        
        return {
            'bones': bones,
            'hierarchy': new_hierarchy
        }
    
    def _get_cs16_bone_name(self, original_name: str, bone_type: str) -> str:
        """Get appropriate CS 1.6 bone name"""
        # Try direct mapping first
        if bone_type in self.cs16_mapping:
            return self.cs16_mapping[bone_type]
        
        # Pattern-based mapping
        name_lower = original_name.lower()
        
        # Bip01 pattern detection
        if 'bip01' in name_lower:
            return original_name  # Keep Bip01 names as-is
        
        # Mixamo pattern conversion
        if 'mixamorig:' in name_lower:
            mixamo_name = original_name.replace('mixamorig:', '').replace('mixamorig_', '')
            return self._convert_mixamo_to_bip01(mixamo_name)
        
        # Generic bone name conversion
        return self._convert_generic_to_bip01(original_name, bone_type)
    
    def _convert_mixamo_to_bip01(self, mixamo_name: str) -> str:
        """Convert Mixamo bone names to Bip01 convention"""
        mixamo_to_bip01 = {
            'hips': 'Bip01',
            'spine': 'Bip01 Spine',
            'spine1': 'Bip01 Spine1',
            'spine2': 'Bip01 Spine2',
            'neck': 'Bip01 Neck',
            'head': 'Bip01 Head',
            'leftupleg': 'Bip01 L Thigh',
            'rightupleg': 'Bip01 R Thigh',
            'leftleg': 'Bip01 L Calf',
            'rightleg': 'Bip01 R Calf',
            'leftfoot': 'Bip01 L Foot',
            'rightfoot': 'Bip01 R Foot',
            'leftshoulder': 'Bip01 L Clavicle',
            'rightshoulder': 'Bip01 R Clavicle',
            'leftarm': 'Bip01 L UpperArm',
            'rightarm': 'Bip01 R UpperArm',
            'leftforearm': 'Bip01 L Forearm',
            'rightforearm': 'Bip01 R Forearm',
            'lefthand': 'Bip01 L Hand',
            'righthand': 'Bip01 R Hand'
        }
        
        mixamo_lower = mixamo_name.lower()
        return mixamo_to_bip01.get(mixamo_lower, f"Bip01 {mixamo_name}")
    
    def _convert_generic_to_bip01(self, generic_name: str, bone_type: str) -> str:
        """Convert generic bone names to Bip01 convention"""
        type_to_bip01 = {
            'root': 'Bip01',
            'spine': 'Bip01 Spine',
            'head': 'Bip01 Head',
            'neck': 'Bip01 Neck',
            'left_arm': 'Bip01 L UpperArm',
            'right_arm': 'Bip01 R UpperArm',
            'left_hand': 'Bip01 L Hand',
            'right_hand': 'Bip01 R Hand',
            'left_leg': 'Bip01 L Thigh',
            'right_leg': 'Bip01 R Thigh',
            'left_foot': 'Bip01 L Foot',
            'right_foot': 'Bip01 R Foot'
        }
        
        if bone_type in type_to_bip01:
            return type_to_bip01[bone_type]
        
        # Fallback: create a Bip01-style name
        return f"Bip01 {generic_name.replace('_', ' ').title()}"
    
    def _optimize_bone_hierarchy(self, mapped_bones: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize bone hierarchy for CS 1.6"""
        bones = mapped_bones['bones'].copy()
        
        if not config.OPTIMIZE_BONE_HIERARCHY:
            return mapped_bones
        
        self.logger.info("Optimizing bone hierarchy...")
        
        # Remove unnecessary bones
        bones = self._remove_unnecessary_bones(bones)
        
        # Merge redundant bones
        bones = self._merge_redundant_bones(bones)
        
        # Ensure bone count limit
        bones = self._enforce_bone_limit(bones)
        
        # Rebuild hierarchy
        hierarchy = {bone['name']: bone['index'] for bone in bones}
        
        return {
            'bones': bones,
            'hierarchy': hierarchy
        }
    
    def _remove_unnecessary_bones(self, bones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove bones that are not essential for CS 1.6"""
        essential_types = ['root', 'spine', 'head', 'neck', 'left_arm', 'right_arm', 
                          'left_hand', 'right_hand', 'left_leg', 'right_leg', 
                          'left_foot', 'right_foot']
        
        # Keep essential bones and bones with significant influence
        filtered_bones = []
        
        for bone in bones:
            bone_type = bone.get('type', 'other')
            
            # Always keep essential bones
            if bone_type in essential_types:
                filtered_bones.append(bone)
                continue
            
            # Keep bones that have children or significant weights
            if self._bone_has_children(bone, bones) or self._bone_has_significant_weights(bone):
                filtered_bones.append(bone)
                continue
            
            self.logger.debug(f"Removing non-essential bone: {bone['name']}")
        
        # Update indices and parent relationships
        for i, bone in enumerate(filtered_bones):
            bone['index'] = i
        
        self._update_parent_indices(filtered_bones, bones)
        
        return filtered_bones
    
    def _bone_has_children(self, bone: Dict[str, Any], all_bones: List[Dict[str, Any]]) -> bool:
        """Check if bone has children"""
        bone_index = bone['index']
        for other_bone in all_bones:
            if other_bone.get('parent_index') == bone_index:
                return True
        return False
    
    def _bone_has_significant_weights(self, bone: Dict[str, Any]) -> bool:
        """Check if bone has significant vertex weights"""
        # This would require access to mesh data with bone weights
        # For now, assume all bones are potentially significant
        return True
    
    def _merge_redundant_bones(self, bones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge redundant bones that serve similar functions"""
        # Identify candidates for merging
        merge_candidates = self._find_merge_candidates(bones)
        
        # Perform merging
        merged_bones = bones.copy()
        
        for parent_idx, child_indices in merge_candidates.items():
            parent_bone = merged_bones[parent_idx]
            
            # Merge child bones into parent
            for child_idx in child_indices:
                if child_idx < len(merged_bones):
                    child_bone = merged_bones[child_idx]
                    self.logger.debug(f"Merging bone {child_bone['name']} into {parent_bone['name']}")
                    
                    # Update any children of the merged bone to point to parent
                    self._reparent_children(merged_bones, child_idx, parent_idx)
        
        # Remove merged bones
        for parent_idx, child_indices in merge_candidates.items():
            for child_idx in sorted(child_indices, reverse=True):
                if child_idx < len(merged_bones):
                    merged_bones.pop(child_idx)
        
        # Update indices
        for i, bone in enumerate(merged_bones):
            bone['index'] = i
        
        return merged_bones
    
    def _find_merge_candidates(self, bones: List[Dict[str, Any]]) -> Dict[int, List[int]]:
        """Find bones that can be merged"""
        merge_candidates = {}
        
        # Look for single-child chains that can be simplified
        for bone in bones:
            children = self._get_direct_children(bone, bones)
            
            if len(children) == 1:
                child = children[0]
                child_children = self._get_direct_children(child, bones)
                
                # If child has no children or only one child, consider merging
                if len(child_children) <= 1:
                    if bone['index'] not in merge_candidates:
                        merge_candidates[bone['index']] = []
                    merge_candidates[bone['index']].append(child['index'])
        
        return merge_candidates
    
    def _get_direct_children(self, bone: Dict[str, Any], all_bones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get direct children of a bone"""
        children = []
        bone_index = bone['index']
        
        for other_bone in all_bones:
            if other_bone.get('parent_index') == bone_index:
                children.append(other_bone)
        
        return children
    
    def _reparent_children(self, bones: List[Dict[str, Any]], old_parent_idx: int, new_parent_idx: int):
        """Reparent children from old parent to new parent"""
        for bone in bones:
            if bone.get('parent_index') == old_parent_idx:
                bone['parent_index'] = new_parent_idx
    
    def _enforce_bone_limit(self, bones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure bone count doesn't exceed CS 1.6 limits"""
        if len(bones) <= config.MAX_BONES:
            return bones
        
        self.logger.warning(f"Bone count ({len(bones)}) exceeds limit ({config.MAX_BONES}). Reducing...")
        
        # Prioritize bones by importance
        bone_priorities = self._calculate_bone_priorities(bones)
        
        # Sort by priority (higher is better)
        sorted_bones = sorted(enumerate(bones), key=lambda x: bone_priorities[x[0]], reverse=True)
        
        # Keep only the most important bones
        kept_bones = [bone for _, bone in sorted_bones[:config.MAX_BONES]]
        
        # Update indices and fix parent relationships
        for i, bone in enumerate(kept_bones):
            bone['index'] = i
        
        self._fix_parent_relationships(kept_bones)
        
        self.logger.info(f"Reduced bone count from {len(bones)} to {len(kept_bones)}")
        return kept_bones
    
    def _calculate_bone_priorities(self, bones: List[Dict[str, Any]]) -> List[float]:
        """Calculate priority scores for bones"""
        priorities = []
        
        for bone in bones:
            priority = 0.0
            bone_type = bone.get('type', 'other')
            
            # Base priority by type
            type_priorities = {
                'root': 100.0,
                'spine': 80.0,
                'head': 70.0,
                'neck': 60.0,
                'left_arm': 50.0,
                'right_arm': 50.0,
                'left_leg': 50.0,
                'right_leg': 50.0,
                'left_hand': 30.0,
                'right_hand': 30.0,
                'left_foot': 30.0,
                'right_foot': 30.0,
                'other': 10.0
            }
            
            priority += type_priorities.get(bone_type, 10.0)
            
            # Bonus for having children
            child_count = len([b for b in bones if b.get('parent_index') == bone['index']])
            priority += child_count * 5.0
            
            # Bonus for being in main hierarchy
            if self._is_in_main_hierarchy(bone, bones):
                priority += 20.0
            
            priorities.append(priority)
        
        return priorities
    
    def _is_in_main_hierarchy(self, bone: Dict[str, Any], all_bones: List[Dict[str, Any]]) -> bool:
        """Check if bone is part of the main skeletal hierarchy"""
        # Trace up to root
        current_bone = bone
        
        while current_bone:
            if current_bone.get('type') == 'root':
                return True
            
            parent_idx = current_bone.get('parent_index', -1)
            if parent_idx == -1:
                break
            
            # Find parent bone
            current_bone = None
            for b in all_bones:
                if b['index'] == parent_idx:
                    current_bone = b
                    break
        
        return False
    
    def _fix_parent_relationships(self, bones: List[Dict[str, Any]]):
        """Fix parent relationships after bone removal"""
        bone_indices = {bone['index']: i for i, bone in enumerate(bones)}
        
        for bone in bones:
            parent_idx = bone.get('parent_index', -1)
            
            if parent_idx != -1 and parent_idx not in bone_indices:
                # Parent was removed, find closest valid ancestor
                bone['parent_index'] = self._find_closest_ancestor(bone, bones, bone_indices)
    
    def _find_closest_ancestor(self, bone: Dict[str, Any], all_bones: List[Dict[str, Any]], 
                              valid_indices: Dict[int, int]) -> int:
        """Find closest valid ancestor for orphaned bone"""
        # For now, just make it a child of root
        for b in all_bones:
            if b.get('type') == 'root':
                return b['index']
        
        return -1  # No valid parent found
    
    def _update_parent_indices(self, filtered_bones: List[Dict[str, Any]], original_bones: List[Dict[str, Any]]):
        """Update parent indices after filtering"""
        # Create mapping from original indices to new indices
        old_to_new = {}
        for new_idx, bone in enumerate(filtered_bones):
            original_name = bone['name']
            for old_idx, orig_bone in enumerate(original_bones):
                if orig_bone['name'] == original_name:
                    old_to_new[old_idx] = new_idx
                    break
        
        # Update parent indices
        for bone in filtered_bones:
            old_parent_idx = bone.get('parent_index', -1)
            if old_parent_idx != -1 and old_parent_idx in old_to_new:
                bone['parent_index'] = old_to_new[old_parent_idx]
            elif old_parent_idx != -1:
                bone['parent_index'] = -1  # Parent was removed
    
    def _validate_bone_limits(self, bones_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate bone data against CS 1.6 limits"""
        bones = bones_data['bones']
        
        # Check bone count
        if len(bones) > config.MAX_BONES:
            self.logger.error(f"Bone count ({len(bones)}) exceeds CS 1.6 limit ({config.MAX_BONES})")
        
        # Check bone name lengths
        for bone in bones:
            name = bone.get('name', '')
            if len(name) > 32:  # CS 1.6 bone name limit
                self.logger.warning(f"Bone name too long: {name}")
                bone['name'] = name[:32]
        
        # Validate hierarchy
        self._validate_hierarchy(bones)
        
        return bones_data
    
    def _validate_hierarchy(self, bones: List[Dict[str, Any]]):
        """Validate bone hierarchy for circular references"""
        for bone in bones:
            if self._has_circular_reference(bone, bones):
                self.logger.warning(f"Circular reference detected for bone: {bone['name']}")
                bone['parent_index'] = -1  # Break the cycle
    
    def _has_circular_reference(self, bone: Dict[str, Any], all_bones: List[Dict[str, Any]], 
                               visited: set = None) -> bool:
        """Check for circular references in bone hierarchy"""
        if visited is None:
            visited = set()
        
        bone_idx = bone['index']
        if bone_idx in visited:
            return True
        
        visited.add(bone_idx)
        
        parent_idx = bone.get('parent_index', -1)
        if parent_idx == -1:
            return False
        
        # Find parent bone
        for parent_bone in all_bones:
            if parent_bone['index'] == parent_idx:
                return self._has_circular_reference(parent_bone, all_bones, visited.copy())
        
        return False
    
    def _generate_bone_attachments(self, bones_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate bone attachments for CS 1.6"""
        if not config.AUTO_GENERATE_BONE_ATTACHMENTS:
            return []
        
        bones = bones_data['bones']
        attachments = []
        
        # Common attachment points for CS 1.6 models
        attachment_bones = ['Bip01 Head', 'Bip01 L Hand', 'Bip01 R Hand', 'Bip01']
        
        for attachment_name in attachment_bones:
            bone_index = self._find_bone_index_by_name(bones, attachment_name)
            
            if bone_index != -1:
                attachment = {
                    'name': f"attachment_{len(attachments)}",
                    'bone_index': bone_index,
                    'position': [0.0, 0.0, 0.0],
                    'rotation': [0.0, 0.0, 0.0]
                }
                attachments.append(attachment)
                
                if len(attachments) >= config.MAX_BONE_ATTACHMENTS:
                    break
        
        self.logger.info(f"Generated {len(attachments)} bone attachments")
        return attachments
    
    def _find_bone_index_by_name(self, bones: List[Dict[str, Any]], name: str) -> int:
        """Find bone index by name"""
        for bone in bones:
            if bone.get('name') == name:
                return bone.get('index', -1)
        return -1
    
    def _find_root_bone(self, bones: List[Dict[str, Any]]) -> int:
        """Find the root bone index"""
        for bone in bones:
            if bone.get('parent_index', -1) == -1:
                return bone.get('index', -1)
        return -1