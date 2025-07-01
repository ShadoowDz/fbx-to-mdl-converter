"""
FBX Parser for Counter-Strike 1.6 MDL Converter
Extracts geometry, bones, animations, and materials from FBX files
"""

import os
import sys
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

# Try to import FBX SDK
try:
    import FbxCommon
    from fbx import *
except ImportError:
    print("Warning: FBX SDK not found. Please install Autodesk FBX SDK 2020.3")
    print("Download from: https://www.autodesk.com/developer-network/platform-technologies/fbx-sdk-2020-3")
    # Create mock classes for development
    class FbxManager:
        @staticmethod
        def Create(): return None
    class FbxIOSettings:
        @staticmethod
        def Create(): return None
    class FbxImporter:
        @staticmethod
        def Create(): return None
    class FbxScene:
        @staticmethod
        def Create(): return None


class FBXParser:
    """Parser for FBX files with intelligent data extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.manager = None
        self.scene = None
        self.importer = None
        self._initialize_fbx_sdk()
    
    def _initialize_fbx_sdk(self):
        """Initialize FBX SDK components"""
        try:
            # Create FBX manager
            self.manager = FbxManager.Create()
            if not self.manager:
                raise RuntimeError("Failed to create FBX manager")
            
            # Create IO settings
            ios = FbxIOSettings.Create(self.manager, IOSROOT)
            self.manager.SetIOSettings(ios)
            
            # Create scene
            self.scene = FbxScene.Create(self.manager, "Scene")
            if not self.scene:
                raise RuntimeError("Failed to create FBX scene")
            
            self.logger.info("FBX SDK initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"FBX SDK initialization failed: {e}")
            self.manager = None
            self.scene = None
    
    def parse(self, fbx_path: str) -> Optional[Dict[str, Any]]:
        """Parse FBX file and extract all relevant data"""
        if not self.manager or not self.scene:
            self.logger.error("FBX SDK not initialized")
            return None
        
        if not os.path.exists(fbx_path):
            self.logger.error(f"FBX file not found: {fbx_path}")
            return None
        
        try:
            # Create importer
            self.importer = FbxImporter.Create(self.manager, "")
            
            # Initialize importer
            if not self.importer.Initialize(fbx_path, -1, self.manager.GetIOSettings()):
                error = self.importer.GetStatus().GetErrorString()
                self.logger.error(f"Failed to initialize FBX importer: {error}")
                return None
            
            # Import scene
            if not self.importer.Import(self.scene):
                error = self.importer.GetStatus().GetErrorString()
                self.logger.error(f"Failed to import FBX scene: {error}")
                return None
            
            self.logger.info(f"Successfully loaded FBX file: {fbx_path}")
            
            # Extract data
            fbx_data = {
                'geometry': self._extract_geometry(),
                'bones': self._extract_bones(),
                'animations': self._extract_animations(),
                'materials': self._extract_materials(),
                'metadata': self._extract_metadata()
            }
            
            return fbx_data
            
        except Exception as e:
            self.logger.error(f"Error parsing FBX file: {e}")
            return None
        
        finally:
            if self.importer:
                self.importer.Destroy()
    
    def _extract_geometry(self) -> Dict[str, Any]:
        """Extract geometry data (vertices, triangles, normals, UV)"""
        geometry_data = {
            'meshes': [],
            'vertices': [],
            'triangles': [],
            'normals': [],
            'uvs': [],
            'vertex_colors': []
        }
        
        try:
            # Triangulate the scene to ensure all polygons are triangles
            converter = FbxGeometryConverter(self.manager)
            converter.Triangulate(self.scene, True)
            
            # Process all mesh nodes
            root_node = self.scene.GetRootNode()
            self._process_mesh_node(root_node, geometry_data)
            
            self.logger.info(f"Extracted geometry: {len(geometry_data['vertices'])} vertices, "
                           f"{len(geometry_data['triangles'])} triangles")
            
        except Exception as e:
            self.logger.error(f"Error extracting geometry: {e}")
        
        return geometry_data
    
    def _process_mesh_node(self, node: 'FbxNode', geometry_data: Dict[str, Any]):
        """Recursively process mesh nodes"""
        if not node:
            return
        
        # Process mesh if present
        mesh = node.GetMesh()
        if mesh:
            self._extract_mesh_data(mesh, geometry_data, node.GetName())
        
        # Process child nodes
        for i in range(node.GetChildCount()):
            child = node.GetChild(i)
            self._process_mesh_node(child, geometry_data)
    
    def _extract_mesh_data(self, mesh: 'FbxMesh', geometry_data: Dict[str, Any], mesh_name: str):
        """Extract data from a single mesh"""
        if not mesh:
            return
        
        mesh_data = {
            'name': mesh_name,
            'vertices': [],
            'triangles': [],
            'normals': [],
            'uvs': [],
            'vertex_colors': [],
            'bone_weights': []
        }
        
        # Extract vertices
        vertex_count = mesh.GetControlPointsCount()
        control_points = mesh.GetControlPoints()
        
        for i in range(vertex_count):
            vertex = control_points[i]
            mesh_data['vertices'].append([vertex[0], vertex[1], vertex[2]])
        
        # Extract triangles
        polygon_count = mesh.GetPolygonCount()
        vertex_id = 0
        
        for i in range(polygon_count):
            polygon_size = mesh.GetPolygonSize(i)
            
            if polygon_size == 3:  # Triangle
                triangle = []
                for j in range(3):
                    triangle.append(mesh.GetPolygonVertex(i, j))
                mesh_data['triangles'].append(triangle)
            else:
                self.logger.warning(f"Non-triangle polygon found (size: {polygon_size})")
        
        # Extract normals
        self._extract_normals(mesh, mesh_data)
        
        # Extract UV coordinates
        self._extract_uvs(mesh, mesh_data)
        
        # Extract vertex colors
        self._extract_vertex_colors(mesh, mesh_data)
        
        # Extract bone weights
        self._extract_bone_weights(mesh, mesh_data)
        
        # Add to global geometry data
        vertex_offset = len(geometry_data['vertices'])
        geometry_data['vertices'].extend(mesh_data['vertices'])
        geometry_data['normals'].extend(mesh_data['normals'])
        geometry_data['uvs'].extend(mesh_data['uvs'])
        geometry_data['vertex_colors'].extend(mesh_data['vertex_colors'])
        
        # Adjust triangle indices for global vertex array
        for triangle in mesh_data['triangles']:
            adjusted_triangle = [idx + vertex_offset for idx in triangle]
            geometry_data['triangles'].append(adjusted_triangle)
        
        mesh_data['vertex_offset'] = vertex_offset
        geometry_data['meshes'].append(mesh_data)
    
    def _extract_normals(self, mesh: 'FbxMesh', mesh_data: Dict[str, Any]):
        """Extract normal vectors"""
        normals = []
        
        # Get normal element
        normal_element = mesh.GetElementNormal(0)
        if not normal_element:
            # Generate normals if not present
            normals = self._generate_normals(mesh_data['vertices'], mesh_data['triangles'])
        else:
            mapping_mode = normal_element.GetMappingMode()
            reference_mode = normal_element.GetReferenceMode()
            
            if mapping_mode == FbxGeometryElement.eByControlPoint:
                for i in range(mesh.GetControlPointsCount()):
                    if reference_mode == FbxGeometryElement.eDirect:
                        normal = normal_element.GetDirectArray().GetAt(i)
                    else:
                        index = normal_element.GetIndexArray().GetAt(i)
                        normal = normal_element.GetDirectArray().GetAt(index)
                    normals.append([normal[0], normal[1], normal[2]])
            
            elif mapping_mode == FbxGeometryElement.eByPolygonVertex:
                vertex_id = 0
                for i in range(mesh.GetPolygonCount()):
                    for j in range(mesh.GetPolygonSize(i)):
                        if reference_mode == FbxGeometryElement.eDirect:
                            normal = normal_element.GetDirectArray().GetAt(vertex_id)
                        else:
                            index = normal_element.GetIndexArray().GetAt(vertex_id)
                            normal = normal_element.GetDirectArray().GetAt(index)
                        normals.append([normal[0], normal[1], normal[2]])
                        vertex_id += 1
        
        mesh_data['normals'] = normals
    
    def _extract_uvs(self, mesh: 'FbxMesh', mesh_data: Dict[str, Any]):
        """Extract UV coordinates"""
        uvs = []
        
        # Get UV element
        uv_element = mesh.GetElementUV(0)
        if not uv_element:
            # No UVs present, create default UVs
            uvs = [[0.0, 0.0] for _ in mesh_data['vertices']]
        else:
            mapping_mode = uv_element.GetMappingMode()
            reference_mode = uv_element.GetReferenceMode()
            
            if mapping_mode == FbxGeometryElement.eByControlPoint:
                for i in range(mesh.GetControlPointsCount()):
                    if reference_mode == FbxGeometryElement.eDirect:
                        uv = uv_element.GetDirectArray().GetAt(i)
                    else:
                        index = uv_element.GetIndexArray().GetAt(i)
                        uv = uv_element.GetDirectArray().GetAt(index)
                    uvs.append([uv[0], uv[1]])
            
            elif mapping_mode == FbxGeometryElement.eByPolygonVertex:
                vertex_id = 0
                for i in range(mesh.GetPolygonCount()):
                    for j in range(mesh.GetPolygonSize(i)):
                        if reference_mode == FbxGeometryElement.eDirect:
                            uv = uv_element.GetDirectArray().GetAt(vertex_id)
                        else:
                            index = uv_element.GetIndexArray().GetAt(vertex_id)
                            uv = uv_element.GetDirectArray().GetAt(index)
                        uvs.append([uv[0], uv[1]])
                        vertex_id += 1
        
        mesh_data['uvs'] = uvs
    
    def _extract_vertex_colors(self, mesh: 'FbxMesh', mesh_data: Dict[str, Any]):
        """Extract vertex colors"""
        vertex_colors = []
        
        # Get vertex color element
        color_element = mesh.GetElementVertexColor(0)
        if not color_element:
            # No vertex colors, create default white
            vertex_colors = [[1.0, 1.0, 1.0, 1.0] for _ in mesh_data['vertices']]
        else:
            mapping_mode = color_element.GetMappingMode()
            reference_mode = color_element.GetReferenceMode()
            
            if mapping_mode == FbxGeometryElement.eByControlPoint:
                for i in range(mesh.GetControlPointsCount()):
                    if reference_mode == FbxGeometryElement.eDirect:
                        color = color_element.GetDirectArray().GetAt(i)
                    else:
                        index = color_element.GetIndexArray().GetAt(i)
                        color = color_element.GetDirectArray().GetAt(index)
                    vertex_colors.append([color[0], color[1], color[2], color[3]])
        
        mesh_data['vertex_colors'] = vertex_colors
    
    def _extract_bone_weights(self, mesh: 'FbxMesh', mesh_data: Dict[str, Any]):
        """Extract bone weights and influences"""
        bone_weights = [[] for _ in mesh_data['vertices']]
        
        # Get skin deformer
        skin_count = mesh.GetDeformerCount(FbxDeformer.eSkin)
        
        for skin_index in range(skin_count):
            skin = mesh.GetDeformer(skin_index, FbxDeformer.eSkin)
            if not skin:
                continue
            
            cluster_count = skin.GetClusterCount()
            
            for cluster_index in range(cluster_count):
                cluster = skin.GetCluster(cluster_index)
                if not cluster:
                    continue
                
                # Get bone name
                bone_node = cluster.GetLink()
                if not bone_node:
                    continue
                
                bone_name = bone_node.GetName()
                
                # Get vertex indices and weights
                indices = cluster.GetControlPointIndices()
                weights = cluster.GetControlPointWeights()
                
                for i in range(cluster.GetControlPointIndicesCount()):
                    vertex_index = indices[i]
                    weight = weights[i]
                    
                    if vertex_index < len(bone_weights) and weight > 0.001:
                        bone_weights[vertex_index].append({
                            'bone_name': bone_name,
                            'bone_index': cluster_index,
                            'weight': weight
                        })
        
        mesh_data['bone_weights'] = bone_weights
    
    def _generate_normals(self, vertices: List[List[float]], triangles: List[List[int]]) -> List[List[float]]:
        """Generate normal vectors for vertices"""
        normals = [[0.0, 0.0, 0.0] for _ in vertices]
        
        # Calculate face normals and accumulate
        for triangle in triangles:
            if len(triangle) != 3:
                continue
            
            v0, v1, v2 = [np.array(vertices[i]) for i in triangle]
            
            # Calculate face normal
            edge1 = v1 - v0
            edge2 = v2 - v0
            face_normal = np.cross(edge1, edge2)
            
            # Normalize
            length = np.linalg.norm(face_normal)
            if length > 0:
                face_normal = face_normal / length
            
            # Add to vertex normals
            for vertex_index in triangle:
                normals[vertex_index][0] += face_normal[0]
                normals[vertex_index][1] += face_normal[1]
                normals[vertex_index][2] += face_normal[2]
        
        # Normalize vertex normals
        for normal in normals:
            length = np.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
            if length > 0:
                normal[0] /= length
                normal[1] /= length
                normal[2] /= length
        
        return normals
    
    def _extract_bones(self) -> Dict[str, Any]:
        """Extract bone hierarchy and transform data"""
        bone_data = {
            'bones': [],
            'hierarchy': {},
            'bind_poses': {}
        }
        
        try:
            # Find all skeleton nodes
            root_node = self.scene.GetRootNode()
            self._find_skeleton_nodes(root_node, bone_data)
            
            self.logger.info(f"Found {len(bone_data['bones'])} bones")
            
        except Exception as e:
            self.logger.error(f"Error extracting bones: {e}")
        
        return bone_data
    
    def _find_skeleton_nodes(self, node: 'FbxNode', bone_data: Dict[str, Any]):
        """Recursively find skeleton nodes"""
        if not node:
            return
        
        # Check if this is a skeleton node
        skeleton = node.GetSkeleton()
        if skeleton or self._is_bone_node(node):
            self._extract_bone_data(node, bone_data)
        
        # Process children
        for i in range(node.GetChildCount()):
            child = node.GetChild(i)
            self._find_skeleton_nodes(child, bone_data)
    
    def _is_bone_node(self, node: 'FbxNode') -> bool:
        """Determine if a node is a bone based on naming conventions"""
        name = node.GetName().lower()
        bone_keywords = ['bip01', 'bone', 'joint', 'mixamorig', 'spine', 'arm', 'leg', 'hand', 'foot', 'head', 'neck']
        return any(keyword in name for keyword in bone_keywords)
    
    def _extract_bone_data(self, node: 'FbxNode', bone_data: Dict[str, Any]):
        """Extract data from a bone node"""
        bone_info = {
            'name': node.GetName(),
            'index': len(bone_data['bones']),
            'parent_index': -1,
            'children': [],
            'transform': self._get_node_transform(node),
            'bind_pose': self._get_bind_pose(node),
            'local_transform': self._get_local_transform(node)
        }
        
        # Find parent bone
        parent_node = node.GetParent()
        if parent_node and parent_node != self.scene.GetRootNode():
            parent_name = parent_node.GetName()
            for i, bone in enumerate(bone_data['bones']):
                if bone['name'] == parent_name:
                    bone_info['parent_index'] = i
                    bone['children'].append(bone_info['index'])
                    break
        
        bone_data['bones'].append(bone_info)
        bone_data['hierarchy'][bone_info['name']] = bone_info['index']
    
    def _get_node_transform(self, node: 'FbxNode') -> List[List[float]]:
        """Get global transformation matrix of a node"""
        transform = node.EvaluateGlobalTransform()
        matrix = []
        for i in range(4):
            row = []
            for j in range(4):
                row.append(transform.Get(i, j))
            matrix.append(row)
        return matrix
    
    def _get_local_transform(self, node: 'FbxNode') -> List[List[float]]:
        """Get local transformation matrix of a node"""
        transform = node.EvaluateLocalTransform()
        matrix = []
        for i in range(4):
            row = []
            for j in range(4):
                row.append(transform.Get(i, j))
            matrix.append(row)
        return matrix
    
    def _get_bind_pose(self, node: 'FbxNode') -> List[List[float]]:
        """Get bind pose transformation matrix"""
        # For now, use the current global transform as bind pose
        # In a more sophisticated implementation, we would look for bind pose data
        return self._get_node_transform(node)
    
    def _extract_animations(self) -> Dict[str, Any]:
        """Extract animation data"""
        animation_data = {
            'sequences': [],
            'keyframes': {},
            'frame_rate': 30.0
        }
        
        try:
            # Get animation stacks (sequences)
            stack_count = self.scene.GetSrcObjectCount(FbxAnimStack.ClassId)
            
            for i in range(stack_count):
                anim_stack = self.scene.GetSrcObject(FbxAnimStack.ClassId, i)
                if anim_stack:
                    self._extract_animation_sequence(anim_stack, animation_data)
            
            self.logger.info(f"Found {len(animation_data['sequences'])} animation sequences")
            
        except Exception as e:
            self.logger.error(f"Error extracting animations: {e}")
        
        return animation_data
    
    def _extract_animation_sequence(self, anim_stack: 'FbxAnimStack', animation_data: Dict[str, Any]):
        """Extract data from an animation sequence"""
        sequence_name = anim_stack.GetName()
        
        # Get time span
        time_span = anim_stack.GetLocalTimeSpan()
        start_time = time_span.GetStart()
        stop_time = time_span.GetStop()
        
        sequence_data = {
            'name': sequence_name,
            'start_frame': int(start_time.GetFrameCount()),
            'end_frame': int(stop_time.GetFrameCount()),
            'frame_rate': animation_data['frame_rate'],
            'keyframes': {}
        }
        
        # Set current animation stack
        self.scene.SetCurrentAnimationStack(anim_stack)
        
        # Extract keyframes for all bones
        root_node = self.scene.GetRootNode()
        self._extract_node_animation(root_node, sequence_data, start_time, stop_time)
        
        animation_data['sequences'].append(sequence_data)
    
    def _extract_node_animation(self, node: 'FbxNode', sequence_data: Dict[str, Any], start_time, stop_time):
        """Extract animation data for a node"""
        if not node:
            return
        
        node_name = node.GetName()
        
        # Check if this node has animation
        if self._has_animation(node):
            keyframes = []
            
            # Sample animation at regular intervals
            frame_time = FbxTime()
            frame_rate = sequence_data['frame_rate']
            frame_count = int(stop_time.GetFrameCount() - start_time.GetFrameCount())
            
            for frame in range(frame_count):
                frame_time.SetFrame(start_time.GetFrameCount() + frame)
                
                # Get transformation at this time
                transform = node.EvaluateLocalTransform(frame_time)
                
                # Extract translation, rotation, scale
                translation = transform.GetT()
                rotation = transform.GetR()
                scale = transform.GetS()
                
                keyframe = {
                    'frame': frame,
                    'time': frame / frame_rate,
                    'translation': [translation[0], translation[1], translation[2]],
                    'rotation': [rotation[0], rotation[1], rotation[2]],
                    'scale': [scale[0], scale[1], scale[2]]
                }
                
                keyframes.append(keyframe)
            
            if keyframes:
                sequence_data['keyframes'][node_name] = keyframes
        
        # Process children
        for i in range(node.GetChildCount()):
            child = node.GetChild(i)
            self._extract_node_animation(child, sequence_data, start_time, stop_time)
    
    def _has_animation(self, node: 'FbxNode') -> bool:
        """Check if a node has animation curves"""
        # Check translation curves
        if node.LclTranslation.GetCurve(FbxAnimLayer.ClassId, "X"):
            return True
        if node.LclTranslation.GetCurve(FbxAnimLayer.ClassId, "Y"):
            return True
        if node.LclTranslation.GetCurve(FbxAnimLayer.ClassId, "Z"):
            return True
        
        # Check rotation curves
        if node.LclRotation.GetCurve(FbxAnimLayer.ClassId, "X"):
            return True
        if node.LclRotation.GetCurve(FbxAnimLayer.ClassId, "Y"):
            return True
        if node.LclRotation.GetCurve(FbxAnimLayer.ClassId, "Z"):
            return True
        
        # Check scale curves
        if node.LclScaling.GetCurve(FbxAnimLayer.ClassId, "X"):
            return True
        if node.LclScaling.GetCurve(FbxAnimLayer.ClassId, "Y"):
            return True
        if node.LclScaling.GetCurve(FbxAnimLayer.ClassId, "Z"):
            return True
        
        return False
    
    def _extract_materials(self) -> Dict[str, Any]:
        """Extract material and texture data"""
        material_data = {
            'materials': [],
            'textures': []
        }
        
        try:
            # Get all materials
            material_count = self.scene.GetMaterialCount()
            
            for i in range(material_count):
                material = self.scene.GetMaterial(i)
                if material:
                    self._extract_material_data(material, material_data)
            
            self.logger.info(f"Found {len(material_data['materials'])} materials, "
                           f"{len(material_data['textures'])} textures")
            
        except Exception as e:
            self.logger.error(f"Error extracting materials: {e}")
        
        return material_data
    
    def _extract_material_data(self, material: 'FbxSurfaceMaterial', material_data: Dict[str, Any]):
        """Extract data from a material"""
        material_info = {
            'name': material.GetName(),
            'diffuse_color': [1.0, 1.0, 1.0],
            'specular_color': [0.0, 0.0, 0.0],
            'ambient_color': [0.0, 0.0, 0.0],
            'diffuse_texture': None,
            'normal_texture': None,
            'specular_texture': None
        }
        
        # Extract diffuse texture
        diffuse_property = material.FindProperty(FbxSurfaceMaterial.sDiffuse)
        if diffuse_property.IsValid():
            texture_count = diffuse_property.GetSrcObjectCount(FbxTexture.ClassId)
            if texture_count > 0:
                texture = diffuse_property.GetSrcObject(FbxTexture.ClassId, 0)
                if texture:
                    material_info['diffuse_texture'] = self._extract_texture_data(texture, material_data)
        
        # Extract other textures (normal, specular, etc.)
        # ... additional texture extraction code ...
        
        material_data['materials'].append(material_info)
    
    def _extract_texture_data(self, texture: 'FbxTexture', material_data: Dict[str, Any]) -> Optional[str]:
        """Extract texture data"""
        file_texture = FbxCast(FbxFileTexture, texture)
        if file_texture:
            filename = file_texture.GetFileName()
            
            texture_info = {
                'name': texture.GetName(),
                'filename': filename,
                'uv_set': file_texture.GetUVSet()
            }
            
            material_data['textures'].append(texture_info)
            return filename
        
        return None
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from the FBX file"""
        metadata = {
            'creator': 'Unknown',
            'creation_time': 'Unknown',
            'units': 'cm',
            'up_axis': 'Y',
            'coordinate_system': 'Right-handed'
        }
        
        try:
            # Get scene info
            scene_info = self.scene.GetSceneInfo()
            if scene_info:
                metadata['creator'] = scene_info.mCreator.Buffer()
                metadata['creation_time'] = scene_info.mCreationTimeStamp.Buffer()
            
            # Get global settings
            global_settings = self.scene.GetGlobalSettings()
            if global_settings:
                # Get units
                unit_scale = global_settings.GetSystemUnit().GetScaleFactor()
                if unit_scale == 1.0:
                    metadata['units'] = 'cm'
                elif unit_scale == 0.01:
                    metadata['units'] = 'm'
                elif unit_scale == 0.0254:
                    metadata['units'] = 'inch'
                
                # Get axis system
                axis_system = global_settings.GetAxisSystem()
                up_vector = axis_system.GetUpVector()
                if up_vector == FbxAxisSystem.eYAxis:
                    metadata['up_axis'] = 'Y'
                elif up_vector == FbxAxisSystem.eZAxis:
                    metadata['up_axis'] = 'Z'
                
        except Exception as e:
            self.logger.warning(f"Error extracting metadata: {e}")
        
        return metadata
    
    def __del__(self):
        """Cleanup FBX SDK resources"""
        if self.manager:
            self.manager.Destroy()