"""
FBX to MDL Converter Configuration
Settings for Counter-Strike 1.6 model conversion
"""

import os
from pathlib import Path

# ============================================================================
# COUNTER-STRIKE 1.6 MODEL LIMITS
# ============================================================================

# Geometry limits
MAX_VERTICES_PER_MESH = 2048
MAX_TRIANGLES_PER_MESH = 4080
MAX_MESHES_PER_MODEL = 32
MAX_SUBMODELS = 256

# Skeletal animation limits
MAX_BONES = 128
MAX_BONE_ATTACHMENTS = 4
MAX_BONE_CONTROLLERS = 8
MAX_ANIMATION_SEQUENCES = 256
MAX_KEYFRAMES_PER_SEQUENCE = 512

# Texture limits
MAX_TEXTURE_WIDTH = 512
MAX_TEXTURE_HEIGHT = 512
MAX_TEXTURE_NAME_LENGTH = 64
TEXTURE_BIT_DEPTH = 8  # 8-bit indexed color

# Performance recommendations
RECOMMENDED_MAX_TRIANGLES = 9000  # Total model triangles
RECOMMENDED_BONE_COUNT = 64

# ============================================================================
# CONVERTER SETTINGS
# ============================================================================

# Model optimization
OPTIMIZE_GEOMETRY = True
MERGE_DUPLICATE_VERTICES = True
SMOOTH_NORMALS = True
WELD_VERTICES_THRESHOLD = 0.001
REMOVE_UNUSED_MATERIALS = True
OPTIMIZE_TRIANGLE_ORDER = True

# Bone processing
AUTO_GENERATE_BONE_ATTACHMENTS = True
OPTIMIZE_BONE_HIERARCHY = True
VALIDATE_BONE_WEIGHTS = True
BONE_WEIGHT_THRESHOLD = 0.001
MAX_INFLUENCES_PER_VERTEX = 4
NORMALIZE_BONE_WEIGHTS = True

# Animation settings
KEYFRAME_REDUCTION = True
ANIMATION_COMPRESSION = 0.001
MAX_ANIMATION_LENGTH = 512
SAMPLE_RATE = 30.0  # FPS
INTERPOLATION_TYPE = "LINEAR"  # LINEAR, BEZIER, STEP
REMOVE_REDUNDANT_KEYFRAMES = True

# Texture processing
CONVERT_TEXTURES_TO_BMP = True
TEXTURE_MAX_SIZE = 512
TEXTURE_QUALITY = 95
GENERATE_MIPMAPS = False
TEXTURE_FILTER = "LANCZOS"  # LANCZOS, BILINEAR, NEAREST

# Material handling
CONVERT_MATERIALS_TO_SIMPLE = True
PRESERVE_UV_COORDINATES = True
FLATTEN_TEXTURE_HIERARCHY = True
EXTRACT_EMBEDDED_TEXTURES = True

# ============================================================================
# FILE PATHS AND NAMING
# ============================================================================

# FBX SDK path (customize based on installation)
FBX_SDK_PATH = r"C:\Program Files\Autodesk\FBX\FBX SDK\2020.3"
FBX_PYTHON_BINDINGS = os.path.join(FBX_SDK_PATH, "lib", "Python37_x64")

# Output settings
OUTPUT_DIRECTORY = "./output"
TEMP_DIRECTORY = "./temp"
BACKUP_ORIGINAL = True

# File naming conventions
MDL_EXTENSION = ".mdl"
TEXTURE_EXTENSION = ".bmp"
QC_EXTENSION = ".qc"
SMD_EXTENSION = ".smd"

# ============================================================================
# BONE NAMING CONVENTIONS
# ============================================================================

# Common bone name patterns for auto-detection
BONE_NAME_PATTERNS = {
    'root': ['Bip01', 'mixamorig:Hips', 'Root', 'Armature', 'Skeleton'],
    'spine': ['Bip01 Spine', 'mixamorig:Spine', 'Spine', 'Back'],
    'head': ['Bip01 Head', 'mixamorig:Head', 'Head'],
    'neck': ['Bip01 Neck', 'mixamorig:Neck', 'Neck'],
    'left_arm': ['Bip01 L UpperArm', 'mixamorig:LeftArm', 'L_UpperArm'],
    'right_arm': ['Bip01 R UpperArm', 'mixamorig:RightArm', 'R_UpperArm'],
    'left_hand': ['Bip01 L Hand', 'mixamorig:LeftHand', 'L_Hand'],
    'right_hand': ['Bip01 R Hand', 'mixamorig:RightHand', 'R_Hand'],
    'left_leg': ['Bip01 L Thigh', 'mixamorig:LeftUpLeg', 'L_Thigh'],
    'right_leg': ['Bip01 R Thigh', 'mixamorig:RightUpLeg', 'R_Thigh'],
}

# CS 1.6 standard bone names (Bip01 convention)
CS16_BONE_MAPPING = {
    'root': 'Bip01',
    'pelvis': 'Bip01 Pelvis',
    'spine': 'Bip01 Spine',
    'spine1': 'Bip01 Spine1',
    'spine2': 'Bip01 Spine2',
    'neck': 'Bip01 Neck',
    'head': 'Bip01 Head',
    'left_clavicle': 'Bip01 L Clavicle',
    'left_upperarm': 'Bip01 L UpperArm',
    'left_forearm': 'Bip01 L Forearm',
    'left_hand': 'Bip01 L Hand',
    'right_clavicle': 'Bip01 R Clavicle',
    'right_upperarm': 'Bip01 R UpperArm',
    'right_forearm': 'Bip01 R Forearm',
    'right_hand': 'Bip01 R Hand',
    'left_thigh': 'Bip01 L Thigh',
    'left_calf': 'Bip01 L Calf',
    'left_foot': 'Bip01 L Foot',
    'right_thigh': 'Bip01 R Thigh',
    'right_calf': 'Bip01 R Calf',
    'right_foot': 'Bip01 R Foot',
}

# ============================================================================
# VALIDATION SETTINGS
# ============================================================================

# Validation options
VALIDATE_GEOMETRY = True
VALIDATE_BONES = True
VALIDATE_ANIMATIONS = True
VALIDATE_TEXTURES = True
VALIDATE_CS16_COMPATIBILITY = True

# Error handling
STOP_ON_ERROR = False
LOG_WARNINGS = True
DETAILED_ERROR_REPORTING = True

# ============================================================================
# HITBOX GENERATION
# ============================================================================

# Automatic hitbox generation
AUTO_GENERATE_HITBOXES = True
HITBOX_GROUPS = {
    0: 'generic',
    1: 'head',
    2: 'chest',
    3: 'stomach',
    4: 'left_arm',
    5: 'right_arm',
    6: 'left_leg',
    7: 'right_leg'
}

# Hitbox bone mapping
HITBOX_BONE_MAPPING = {
    'Bip01 Head': 1,
    'Bip01 Neck': 1,
    'Bip01 Spine2': 2,
    'Bip01 Spine1': 2,
    'Bip01 Spine': 3,
    'Bip01 Pelvis': 3,
    'Bip01 L UpperArm': 4,
    'Bip01 L Forearm': 4,
    'Bip01 L Hand': 4,
    'Bip01 R UpperArm': 5,
    'Bip01 R Forearm': 5,
    'Bip01 R Hand': 5,
    'Bip01 L Thigh': 6,
    'Bip01 L Calf': 6,
    'Bip01 L Foot': 6,
    'Bip01 R Thigh': 7,
    'Bip01 R Calf': 7,
    'Bip01 R Foot': 7,
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging levels
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
LOG_FILE_PATH = "./logs/conversion.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# DEVELOPMENT SETTINGS
# ============================================================================

# Debug options
DEBUG_MODE = False
VERBOSE_OUTPUT = False
SAVE_INTERMEDIATE_FILES = False
BENCHMARK_PERFORMANCE = False

# Testing
RUN_VALIDATION_TESTS = True
GENERATE_TEST_REPORTS = True
COMPARE_WITH_REFERENCE = False

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check FBX SDK path
    if not os.path.exists(FBX_SDK_PATH):
        errors.append(f"FBX SDK path not found: {FBX_SDK_PATH}")
    
    # Check limits
    if MAX_VERTICES_PER_MESH > 2048:
        errors.append("MAX_VERTICES_PER_MESH exceeds CS 1.6 limit")
    
    if MAX_TRIANGLES_PER_MESH > 4080:
        errors.append("MAX_TRIANGLES_PER_MESH exceeds CS 1.6 limit")
    
    if MAX_BONES > 128:
        errors.append("MAX_BONES exceeds CS 1.6 limit")
    
    # Create directories if they don't exist
    Path(OUTPUT_DIRECTORY).mkdir(parents=True, exist_ok=True)
    Path(TEMP_DIRECTORY).mkdir(parents=True, exist_ok=True)
    
    if LOG_TO_FILE:
        Path(os.path.dirname(LOG_FILE_PATH)).mkdir(parents=True, exist_ok=True)
    
    return errors

def get_fbx_sdk_path():
    """Get the correct FBX SDK path for current system"""
    import platform
    
    system = platform.system()
    architecture = platform.architecture()[0]
    
    if system == "Windows":
        if architecture == "64bit":
            return os.path.join(FBX_SDK_PATH, "lib", "Python37_x64")
        else:
            return os.path.join(FBX_SDK_PATH, "lib", "Python37_x86")
    elif system == "Darwin":  # macOS
        return os.path.join(FBX_SDK_PATH, "lib", "Python37_ub")
    elif system == "Linux":
        return os.path.join(FBX_SDK_PATH, "lib", "Python37_x64")
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration validation passed!")