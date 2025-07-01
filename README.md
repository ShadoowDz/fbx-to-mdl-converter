# FBX to MDL Converter for Counter-Strike 1.6

A comprehensive tool for converting FBX files to Counter-Strike 1.6 compatible MDL format with intelligent bone and animation detection.

## Features

✅ **Smart Bone Detection**
- Automatic skeletal hierarchy analysis
- Bone naming convention recognition
- Parent-child relationship mapping
- Bone constraint detection

✅ **Animation Processing**
- Frame-by-frame animation conversion
- Keyframe optimization
- Animation sequence detection
- Blend animation support

✅ **Material & Texture Handling**
- Automatic texture extraction
- BMP format conversion (8-bit)
- UV mapping preservation
- Material property transfer

✅ **CS 1.6 Compliance**
- Enforces CS 1.6 model limits
- Proper MDL format structure
- Bone attachment support
- Hitbox generation

✅ **Quality Assurance**
- Model validation
- Error reporting
- Performance optimization
- Compatibility testing

## Technical Specifications

### Supported Formats
- **Input**: FBX (2010.0 and later)
- **Output**: MDL (GoldSrc/Half-Life format)

### Model Limits (CS 1.6 Compliant)
- **Vertices**: 2,048 per mesh
- **Triangles**: 4,080 per mesh  
- **Bones**: 128 maximum
- **Animation Sequences**: 256 maximum
- **Textures**: 8-bit BMP, max 512x512
- **Bone Attachments**: 4 maximum

### Dependencies
- Python 3.8+
- FBX SDK 2020.3
- NumPy
- Pillow (PIL)
- Struct

## Installation

### Prerequisites
1. Install Python 3.8 or higher
2. Download Autodesk FBX SDK 2020.3
3. Install required Python packages

```bash
pip install numpy pillow fbx
```

### Setup
1. Clone this repository
```bash
git clone https://github.com/your-username/fbx-to-mdl-cs16.git
cd fbx-to-mdl-cs16
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure FBX SDK path in `config.py`

## Usage

### Basic Conversion
```bash
python convert.py input_model.fbx output_model.mdl
```

### Advanced Options
```bash
python convert.py input_model.fbx output_model.mdl \
  --optimize-bones \
  --compress-animations \
  --generate-hitboxes \
  --validate-output
```

### Batch Conversion
```bash
python batch_convert.py input_folder/ output_folder/
```

### GUI Interface
```bash
python gui_converter.py
```

## Configuration

Edit `config.py` to customize conversion settings:

```python
# Model optimization
OPTIMIZE_GEOMETRY = True
MERGE_DUPLICATE_VERTICES = True
SMOOTH_NORMALS = True

# Bone processing
AUTO_GENERATE_BONE_ATTACHMENTS = True
OPTIMIZE_BONE_HIERARCHY = True
VALIDATE_BONE_WEIGHTS = True

# Animation settings
KEYFRAME_REDUCTION = True
ANIMATION_COMPRESSION = 0.001
MAX_ANIMATION_LENGTH = 512

# Texture processing
CONVERT_TEXTURES_TO_BMP = True
TEXTURE_MAX_SIZE = 512
TEXTURE_QUALITY = 95
```

## Project Structure

```
fbx-to-mdl-cs16/
├── src/
│   ├── core/
│   │   ├── fbx_parser.py          # FBX file parsing
│   │   ├── mdl_writer.py          # MDL file generation
│   │   ├── bone_detector.py       # Bone analysis
│   │   └── animation_processor.py # Animation handling
│   ├── utils/
│   │   ├── geometry_utils.py      # Mesh processing
│   │   ├── texture_utils.py       # Texture conversion
│   │   ├── validation.py          # Model validation
│   │   └── logger.py              # Logging system
│   └── formats/
│       ├── mdl_format.py          # MDL format definitions
│       ├── smd_format.py          # SMD format support
│       └── qc_generator.py        # QC file generation
├── tests/
│   ├── test_conversion.py
│   ├── test_validation.py
│   └── sample_models/
├── docs/
│   ├── technical_spec.md
│   ├── cs16_limits.md
│   └── troubleshooting.md
├── tools/
│   ├── gui_converter.py
│   ├── batch_converter.py
│   └── model_viewer.py
├── config.py
├── requirements.txt
└── README.md
```

## Technical Details

### Bone Detection Algorithm
1. **Hierarchy Analysis**: Traverses FBX scene graph to identify bone structures
2. **Naming Convention**: Recognizes common bone naming patterns (Bip01, mixamorig, etc.)
3. **Influence Mapping**: Analyzes vertex weights to validate bone relationships
4. **Constraint Detection**: Identifies IK chains and bone constraints

### Animation Processing
1. **Keyframe Extraction**: Samples animation curves at specified intervals
2. **Data Compression**: Removes redundant keyframes within tolerance
3. **Format Conversion**: Transforms to CS 1.6 animation format
4. **Sequence Optimization**: Combines related animation clips

### Model Validation
1. **Geometry Checks**: Validates triangle count, vertex limits
2. **Bone Validation**: Ensures bone count and hierarchy compliance
3. **Texture Verification**: Confirms texture format and size limits
4. **CS 1.6 Compatibility**: Tests against engine requirements

## Troubleshooting

### Common Issues

**"Bone count exceeds limit"**
- Enable bone optimization: `--optimize-bones`
- Manually reduce bone count in source model

**"Texture format not supported"**
- Ensure textures are in supported formats
- Enable automatic conversion: `--convert-textures`

**"Animation data corrupted"**
- Check source FBX animation integrity
- Try reducing keyframe density

**"Model validation failed"**
- Review CS 1.6 model limits
- Check geometry complexity

### Debug Mode
```bash
python convert.py input.fbx output.mdl --debug --verbose
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Valve Software for MDL format documentation
- Autodesk for FBX SDK
- Counter-Strike community for testing and feedback
- GoldSrc modding community for technical insights

## Disclaimer

This tool is for educational and modding purposes. Ensure you have proper rights to convert and use any 3D models. The converter is designed to work with Counter-Strike 1.6 and may not be compatible with other versions of the game.