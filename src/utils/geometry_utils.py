"""
Geometry processing utilities for Counter-Strike 1.6 MDL Converter
Handles mesh optimization and processing
"""

import logging
import numpy as np
from typing import Dict, List, Any, Tuple

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config


class GeometryOptimizer:
    """Optimizes geometry data for CS 1.6 compatibility"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def optimize(self, geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize geometry data"""
        
        self.logger.info("Optimizing geometry...")
        
        optimized_data = geometry_data.copy()
        
        if config.MERGE_DUPLICATE_VERTICES:
            optimized_data = self._merge_duplicate_vertices(optimized_data)
        
        if config.REMOVE_UNUSED_MATERIALS:
            optimized_data = self._remove_unused_data(optimized_data)
        
        if config.OPTIMIZE_TRIANGLE_ORDER:
            optimized_data = self._optimize_triangle_order(optimized_data)
        
        self.logger.info("Geometry optimization completed")
        return optimized_data
    
    def _merge_duplicate_vertices(self, geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge duplicate vertices"""
        
        vertices = geometry_data.get('vertices', [])
        triangles = geometry_data.get('triangles', [])
        normals = geometry_data.get('normals', [])
        uvs = geometry_data.get('uvs', [])
        
        if not vertices:
            return geometry_data
        
        # Create vertex mapping
        vertex_map = {}
        unique_vertices = []
        unique_normals = []
        unique_uvs = []
        
        threshold = config.WELD_VERTICES_THRESHOLD
        
        for i, vertex in enumerate(vertices):
            # Find existing vertex within threshold
            found_index = None
            
            for j, unique_vertex in enumerate(unique_vertices):
                distance = sum((vertex[k] - unique_vertex[k])**2 for k in range(3))**0.5
                if distance < threshold:
                    found_index = j
                    break
            
            if found_index is not None:
                vertex_map[i] = found_index
            else:
                vertex_map[i] = len(unique_vertices)
                unique_vertices.append(vertex)
                
                if i < len(normals):
                    unique_normals.append(normals[i])
                else:
                    unique_normals.append([0.0, 0.0, 1.0])
                
                if i < len(uvs):
                    unique_uvs.append(uvs[i])
                else:
                    unique_uvs.append([0.0, 0.0])
        
        # Update triangle indices
        updated_triangles = []
        for triangle in triangles:
            updated_triangle = [vertex_map[idx] for idx in triangle]
            updated_triangles.append(updated_triangle)
        
        # Create optimized geometry
        optimized_data = geometry_data.copy()
        optimized_data['vertices'] = unique_vertices
        optimized_data['triangles'] = updated_triangles
        optimized_data['normals'] = unique_normals
        optimized_data['uvs'] = unique_uvs
        
        reduction = len(vertices) - len(unique_vertices)
        if reduction > 0:
            self.logger.info(f"Merged {reduction} duplicate vertices")
        
        return optimized_data
    
    def _remove_unused_data(self, geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove unused vertices and data"""
        
        vertices = geometry_data.get('vertices', [])
        triangles = geometry_data.get('triangles', [])
        
        if not vertices or not triangles:
            return geometry_data
        
        # Find used vertices
        used_vertices = set()
        for triangle in triangles:
            for vertex_idx in triangle:
                if 0 <= vertex_idx < len(vertices):
                    used_vertices.add(vertex_idx)
        
        # Create mapping from old to new indices
        old_to_new = {}
        new_vertices = []
        new_normals = []
        new_uvs = []
        
        normals = geometry_data.get('normals', [])
        uvs = geometry_data.get('uvs', [])
        
        for old_idx in sorted(used_vertices):
            new_idx = len(new_vertices)
            old_to_new[old_idx] = new_idx
            
            new_vertices.append(vertices[old_idx])
            
            if old_idx < len(normals):
                new_normals.append(normals[old_idx])
            else:
                new_normals.append([0.0, 0.0, 1.0])
            
            if old_idx < len(uvs):
                new_uvs.append(uvs[old_idx])
            else:
                new_uvs.append([0.0, 0.0])
        
        # Update triangle indices
        new_triangles = []
        for triangle in triangles:
            if all(idx in old_to_new for idx in triangle):
                new_triangle = [old_to_new[idx] for idx in triangle]
                new_triangles.append(new_triangle)
        
        # Create optimized geometry
        optimized_data = geometry_data.copy()
        optimized_data['vertices'] = new_vertices
        optimized_data['triangles'] = new_triangles
        optimized_data['normals'] = new_normals
        optimized_data['uvs'] = new_uvs
        
        removed = len(vertices) - len(new_vertices)
        if removed > 0:
            self.logger.info(f"Removed {removed} unused vertices")
        
        return optimized_data
    
    def _optimize_triangle_order(self, geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize triangle order for better cache performance"""
        
        triangles = geometry_data.get('triangles', [])
        
        if len(triangles) < 2:
            return geometry_data
        
        # Simple optimization: group triangles by shared vertices
        optimized_triangles = []
        remaining_triangles = triangles.copy()
        
        if remaining_triangles:
            # Start with first triangle
            optimized_triangles.append(remaining_triangles.pop(0))
            
            # Greedily add triangles with shared vertices
            while remaining_triangles:
                best_triangle = None
                best_index = -1
                best_shared_vertices = 0
                
                last_triangle = optimized_triangles[-1]
                last_vertices = set(last_triangle)
                
                for i, triangle in enumerate(remaining_triangles):
                    shared = len(last_vertices.intersection(set(triangle)))
                    if shared > best_shared_vertices:
                        best_shared_vertices = shared
                        best_triangle = triangle
                        best_index = i
                
                if best_triangle is not None:
                    optimized_triangles.append(remaining_triangles.pop(best_index))
                else:
                    # No shared vertices, just add the first remaining triangle
                    optimized_triangles.append(remaining_triangles.pop(0))
        
        # Update geometry data
        optimized_data = geometry_data.copy()
        optimized_data['triangles'] = optimized_triangles
        
        return optimized_data