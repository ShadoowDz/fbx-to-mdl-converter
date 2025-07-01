"""
MDL Format Definitions for Counter-Strike 1.6
Binary format structures and constants for GoldSrc engine MDL files
"""

import struct
from typing import Dict, List, Tuple, Any
from enum import IntEnum


class MDLConstants:
    """Constants for MDL file format"""
    
    # File signature
    MDL_SIGNATURE = b'IDST'
    MDL_VERSION = 10
    
    # Maximum limits
    MAX_STUDIO_BONES = 128
    MAX_STUDIO_MODELS = 32
    MAX_STUDIO_BODYPARTS = 32
    MAX_STUDIO_GROUPS = 16
    MAX_STUDIO_ANIMATIONS = 256
    MAX_STUDIO_MESHES = 256
    MAX_STUDIO_TRIANGLES = 65536
    MAX_STUDIO_VERTS = 2048
    MAX_STUDIO_SEQUENCES = 256
    MAX_STUDIO_SKINS = 100
    MAX_STUDIO_SRCBONES = 512
    MAX_STUDIO_ATTACHMENTS = 4
    MAX_STUDIO_HITBOXES = 21
    MAX_STUDIO_EVENTS = 1024
    MAX_STUDIO_PIVOTS = 256
    MAX_STUDIO_CONTROLLERS = 8
    
    # String lengths
    MAX_STUDIO_NAME = 64
    MAX_QPATH = 64


class MotionFlags(IntEnum):
    """Motion flags for animations"""
    STUDIO_X = 0x0001
    STUDIO_Y = 0x0002
    STUDIO_Z = 0x0004
    STUDIO_XR = 0x0008
    STUDIO_YR = 0x0010
    STUDIO_ZR = 0x0020
    STUDIO_LX = 0x0040
    STUDIO_LY = 0x0080
    STUDIO_LZ = 0x0100
    STUDIO_AX = 0x0200
    STUDIO_AY = 0x0400
    STUDIO_AZ = 0x0800
    STUDIO_AXR = 0x1000
    STUDIO_AYR = 0x2000
    STUDIO_AZR = 0x4000
    STUDIO_TYPES = 0x7FFF
    STUDIO_RLOOP = 0x8000


class StudioFlags(IntEnum):
    """Studio model flags"""
    STUDIO_ROCKET = 1
    STUDIO_GRENADE = 2
    STUDIO_GIB = 4
    STUDIO_ROTATE = 8
    STUDIO_TRACER = 16
    STUDIO_ZOMGIB = 32
    STUDIO_TRACER2 = 64
    STUDIO_TRACER3 = 128


class MDLHeader:
    """MDL file header structure"""
    
    def __init__(self):
        self.id = MDLConstants.MDL_SIGNATURE  # 4 bytes
        self.version = MDLConstants.MDL_VERSION  # 4 bytes
        self.name = b'\x00' * MDLConstants.MAX_STUDIO_NAME  # 64 bytes
        self.length = 0  # 4 bytes - file size
        
        # Eye position
        self.eyeposition = [0.0, 0.0, 0.0]  # 12 bytes
        
        # Bounding box
        self.min = [0.0, 0.0, 0.0]  # 12 bytes
        self.max = [0.0, 0.0, 0.0]  # 12 bytes
        
        # Bounding box
        self.bbmin = [0.0, 0.0, 0.0]  # 12 bytes
        self.bbmax = [0.0, 0.0, 0.0]  # 12 bytes
        
        self.flags = 0  # 4 bytes
        
        # Counts and offsets
        self.numbones = 0  # 4 bytes
        self.boneindex = 0  # 4 bytes
        
        self.numbonecontrollers = 0  # 4 bytes
        self.bonecontrollerindex = 0  # 4 bytes
        
        self.numhitboxes = 0  # 4 bytes
        self.hitboxindex = 0  # 4 bytes
        
        self.numseq = 0  # 4 bytes
        self.seqindex = 0  # 4 bytes
        
        self.numseqgroups = 0  # 4 bytes
        self.seqgroupindex = 0  # 4 bytes
        
        self.numtextures = 0  # 4 bytes
        self.textureindex = 0  # 4 bytes
        self.texturedataindex = 0  # 4 bytes
        
        self.numskinref = 0  # 4 bytes
        self.numskinfamilies = 0  # 4 bytes
        self.skinindex = 0  # 4 bytes
        
        self.numbodyparts = 0  # 4 bytes
        self.bodypartindex = 0  # 4 bytes
        
        self.numattachments = 0  # 4 bytes
        self.attachmentindex = 0  # 4 bytes
        
        self.soundtable = 0  # 4 bytes
        self.soundindex = 0  # 4 bytes
        self.soundgroups = 0  # 4 bytes
        self.soundgroupindex = 0  # 4 bytes
        
        self.numtransitions = 0  # 4 bytes
        self.transitionindex = 0  # 4 bytes
    
    def pack(self) -> bytes:
        """Pack header into binary format"""
        return struct.pack(
            '<4sI64sIffffff ffffff I'  # Basic header
            'II II II II II II II II II II II II',  # Counts and indices
            self.id,
            self.version,
            self.name,
            self.length,
            self.eyeposition[0], self.eyeposition[1], self.eyeposition[2],
            self.min[0], self.min[1], self.min[2],
            self.max[0], self.max[1], self.max[2],
            self.bbmin[0], self.bbmin[1], self.bbmin[2],
            self.bbmax[0], self.bbmax[1], self.bbmax[2],
            self.flags,
            self.numbones, self.boneindex,
            self.numbonecontrollers, self.bonecontrollerindex,
            self.numhitboxes, self.hitboxindex,
            self.numseq, self.seqindex,
            self.numseqgroups, self.seqgroupindex,
            self.numtextures, self.textureindex, self.texturedataindex,
            self.numskinref, self.numskinfamilies, self.skinindex,
            self.numbodyparts, self.bodypartindex,
            self.numattachments, self.attachmentindex,
            self.soundtable, self.soundindex, self.soundgroups, self.soundgroupindex,
            self.numtransitions, self.transitionindex
        )
    
    @classmethod
    def size(cls) -> int:
        """Get header size in bytes"""
        return 244  # Total header size


class StudioBone:
    """Studio bone structure"""
    
    def __init__(self):
        self.name = b'\x00' * 32  # 32 bytes
        self.parent = -1  # 4 bytes
        self.flags = 0  # 4 bytes
        self.bonecontroller = [-1, -1, -1, -1, -1, -1]  # 24 bytes
        self.value = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # 24 bytes
        self.scale = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]  # 24 bytes
    
    def pack(self) -> bytes:
        """Pack bone into binary format"""
        return struct.pack(
            '<32sIIiiiiii ffffff ffffff',
            self.name,
            self.parent,
            self.flags,
            *self.bonecontroller,
            *self.value,
            *self.scale
        )
    
    @classmethod
    def size(cls) -> int:
        """Get bone structure size in bytes"""
        return 112


class StudioBoneController:
    """Studio bone controller structure"""
    
    def __init__(self):
        self.bone = -1  # 4 bytes
        self.type = 0  # 4 bytes
        self.start = 0.0  # 4 bytes
        self.end = 0.0  # 4 bytes
        self.rest = 0  # 4 bytes
        self.index = 0  # 4 bytes
    
    def pack(self) -> bytes:
        """Pack bone controller into binary format"""
        return struct.pack('<IIfIfI', self.bone, self.type, self.start, self.end, self.rest, self.index)
    
    @classmethod
    def size(cls) -> int:
        """Get bone controller structure size in bytes"""
        return 24


class StudioHitbox:
    """Studio hitbox structure"""
    
    def __init__(self):
        self.bone = 0  # 4 bytes
        self.group = 0  # 4 bytes
        self.bbmin = [0.0, 0.0, 0.0]  # 12 bytes
        self.bbmax = [0.0, 0.0, 0.0]  # 12 bytes
    
    def pack(self) -> bytes:
        """Pack hitbox into binary format"""
        return struct.pack('<IIffffff', self.bone, self.group, *self.bbmin, *self.bbmax)
    
    @classmethod
    def size(cls) -> int:
        """Get hitbox structure size in bytes"""
        return 32


class StudioSequenceDesc:
    """Studio sequence description structure"""
    
    def __init__(self):
        self.label = b'\x00' * 32  # 32 bytes
        self.fps = 30.0  # 4 bytes
        self.flags = 0  # 4 bytes
        self.activity = 0  # 4 bytes
        self.actweight = 0  # 4 bytes
        self.numevents = 0  # 4 bytes
        self.eventindex = 0  # 4 bytes
        self.numframes = 0  # 4 bytes
        self.numpivots = 0  # 4 bytes
        self.pivotindex = 0  # 4 bytes
        self.motiontype = 0  # 4 bytes
        self.motionbone = 0  # 4 bytes
        self.linearmovement = [0.0, 0.0, 0.0]  # 12 bytes
        self.automoveposindex = 0  # 4 bytes
        self.automoveangleindex = 0  # 4 bytes
        self.bbmin = [0.0, 0.0, 0.0]  # 12 bytes
        self.bbmax = [0.0, 0.0, 0.0]  # 12 bytes
        self.numblends = 1  # 4 bytes
        self.animindex = 0  # 4 bytes
        self.blendtype = [0, 0]  # 8 bytes
        self.blendstart = [0.0, 0.0]  # 8 bytes
        self.blendend = [0.0, 0.0]  # 8 bytes
        self.blendparent = 0  # 4 bytes
        self.seqgroup = 0  # 4 bytes
        self.entrynode = 0  # 4 bytes
        self.exitnode = 0  # 4 bytes
        self.nodeflags = 0  # 4 bytes
        self.nextseq = 0  # 4 bytes
    
    def pack(self) -> bytes:
        """Pack sequence description into binary format"""
        return struct.pack(
            '<32sfIIIIIIIII fff II fff fff I I II ff ff IIIIII',
            self.label, self.fps, self.flags, self.activity, self.actweight,
            self.numevents, self.eventindex, self.numframes, self.numpivots, self.pivotindex,
            self.motiontype, self.motionbone, *self.linearmovement,
            self.automoveposindex, self.automoveangleindex,
            *self.bbmin, *self.bbmax, self.numblends, self.animindex,
            *self.blendtype, *self.blendstart, *self.blendend,
            self.blendparent, self.seqgroup, self.entrynode, self.exitnode,
            self.nodeflags, self.nextseq
        )
    
    @classmethod
    def size(cls) -> int:
        """Get sequence description structure size in bytes"""
        return 176


class StudioSeqGroup:
    """Studio sequence group structure"""
    
    def __init__(self):
        self.label = b'\x00' * 32  # 32 bytes
        self.name = b'\x00' * 64  # 64 bytes
        self.cache = 0  # 4 bytes
        self.data = 0  # 4 bytes
    
    def pack(self) -> bytes:
        """Pack sequence group into binary format"""
        return struct.pack('<32s64sII', self.label, self.name, self.cache, self.data)
    
    @classmethod
    def size(cls) -> int:
        """Get sequence group structure size in bytes"""
        return 104


class StudioTexture:
    """Studio texture structure"""
    
    def __init__(self):
        self.name = b'\x00' * 64  # 64 bytes
        self.flags = 0  # 4 bytes
        self.width = 0  # 4 bytes
        self.height = 0  # 4 bytes
        self.index = 0  # 4 bytes
    
    def pack(self) -> bytes:
        """Pack texture into binary format"""
        return struct.pack('<64sIIII', self.name, self.flags, self.width, self.height, self.index)
    
    @classmethod
    def size(cls) -> int:
        """Get texture structure size in bytes"""
        return 80


class StudioBodyPart:
    """Studio body part structure"""
    
    def __init__(self):
        self.name = b'\x00' * 64  # 64 bytes
        self.nummodels = 0  # 4 bytes
        self.base = 0  # 4 bytes
        self.modelindex = 0  # 4 bytes
    
    def pack(self) -> bytes:
        """Pack body part into binary format"""
        return struct.pack('<64sIII', self.name, self.nummodels, self.base, self.modelindex)
    
    @classmethod
    def size(cls) -> int:
        """Get body part structure size in bytes"""
        return 76


class StudioModel:
    """Studio model structure"""
    
    def __init__(self):
        self.name = b'\x00' * 64  # 64 bytes
        self.type = 0  # 4 bytes
        self.boundingradius = 0.0  # 4 bytes
        self.nummesh = 0  # 4 bytes
        self.meshindex = 0  # 4 bytes
        self.numverts = 0  # 4 bytes
        self.vertinfoindex = 0  # 4 bytes
        self.vertindex = 0  # 4 bytes
        self.numnorms = 0  # 4 bytes
        self.norminfoindex = 0  # 4 bytes
        self.normindex = 0  # 4 bytes
        self.numgroups = 0  # 4 bytes
        self.groupindex = 0  # 4 bytes
    
    def pack(self) -> bytes:
        """Pack model into binary format"""
        return struct.pack(
            '<64sIfIIIIIIIII',
            self.name, self.type, self.boundingradius, self.nummesh, self.meshindex,
            self.numverts, self.vertinfoindex, self.vertindex,
            self.numnorms, self.norminfoindex, self.normindex,
            self.numgroups, self.groupindex
        )
    
    @classmethod
    def size(cls) -> int:
        """Get model structure size in bytes"""
        return 112


class StudioMesh:
    """Studio mesh structure"""
    
    def __init__(self):
        self.numtris = 0  # 4 bytes
        self.triindex = 0  # 4 bytes
        self.skinref = 0  # 4 bytes
        self.numnorms = 0  # 4 bytes
        self.normindex = 0  # 4 bytes
    
    def pack(self) -> bytes:
        """Pack mesh into binary format"""
        return struct.pack('<IIIII', self.numtris, self.triindex, self.skinref, self.numnorms, self.normindex)
    
    @classmethod
    def size(cls) -> int:
        """Get mesh structure size in bytes"""
        return 20


class StudioAttachment:
    """Studio attachment structure"""
    
    def __init__(self):
        self.name = b'\x00' * 32  # 32 bytes
        self.type = 0  # 4 bytes
        self.bone = 0  # 4 bytes
        self.org = [0.0, 0.0, 0.0]  # 12 bytes
        self.vectors = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]  # 36 bytes
    
    def pack(self) -> bytes:
        """Pack attachment into binary format"""
        return struct.pack(
            '<32sII fff fff fff fff',
            self.name, self.type, self.bone, *self.org,
            *self.vectors[0], *self.vectors[1], *self.vectors[2]
        )
    
    @classmethod
    def size(cls) -> int:
        """Get attachment structure size in bytes"""
        return 84


class StudioAnimValue:
    """Studio animation value structure"""
    
    def __init__(self):
        self.num = 0  # 1 byte
        self.valid = 0  # 1 byte
        # Variable length data follows
    
    def pack(self) -> bytes:
        """Pack animation value into binary format"""
        return struct.pack('<BB', self.num, self.valid)
    
    @classmethod
    def size(cls) -> int:
        """Get animation value structure size in bytes"""
        return 2


class MDLStructureSizes:
    """Container for all MDL structure sizes"""
    
    HEADER = MDLHeader.size()
    BONE = StudioBone.size()
    BONE_CONTROLLER = StudioBoneController.size()
    HITBOX = StudioHitbox.size()
    SEQUENCE_DESC = StudioSequenceDesc.size()
    SEQ_GROUP = StudioSeqGroup.size()
    TEXTURE = StudioTexture.size()
    BODY_PART = StudioBodyPart.size()
    MODEL = StudioModel.size()
    MESH = StudioMesh.size()
    ATTACHMENT = StudioAttachment.size()
    ANIM_VALUE = StudioAnimValue.size()


def calculate_offset(base_offset: int, count: int, structure_size: int) -> int:
    """Calculate offset for a structure array"""
    return base_offset + (count * structure_size)


def align_to_boundary(offset: int, boundary: int = 4) -> int:
    """Align offset to specified byte boundary"""
    return ((offset + boundary - 1) // boundary) * boundary


def pack_string(text: str, max_length: int) -> bytes:
    """Pack string into fixed-length byte array"""
    text_bytes = text.encode('ascii', errors='ignore')[:max_length-1]
    return text_bytes + b'\x00' * (max_length - len(text_bytes))


def pack_vec3(vector: List[float]) -> bytes:
    """Pack 3D vector into binary format"""
    return struct.pack('<fff', vector[0], vector[1], vector[2])


def pack_matrix3x4(matrix: List[List[float]]) -> bytes:
    """Pack 3x4 matrix into binary format"""
    data = []
    for row in matrix[:3]:  # Only use first 3 rows
        for col in row[:4]:  # Only use first 4 columns
            data.append(col)
    return struct.pack('<' + 'f' * len(data), *data)