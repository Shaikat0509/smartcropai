# SmartCrop AI - Installation Guide

## AI-Powered Media Processing Platform

This application uses advanced AI models for professional-grade media processing:

- **YOLOv8**: Object detection and classification
- **MediaPipe**: Face detection, pose estimation, hand tracking
- **OpenCV**: Computer vision and image processing
- **FFmpeg**: Video processing and encoding
- **Sharp**: High-performance image processing

## Prerequisites

### 1. Node.js and npm
```bash
# Install Node.js (version 16 or higher)
# Download from https://nodejs.org/
node --version
npm --version
```

### 2. Python 3.8+
```bash
# Check Python version
python3 --version
```

### 3. FFmpeg (Required for Video Processing)

#### macOS:
```bash
# Using Homebrew
brew install ffmpeg

# Using MacPorts
sudo port install ffmpeg
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows:
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to a folder (e.g., C:\ffmpeg)
3. Add C:\ffmpeg\bin to your PATH environment variable

#### Verify FFmpeg Installation:
```bash
ffmpeg -version
```

## Installation Steps

### 1. Clone and Setup
```bash
git clone <repository-url>
cd smartcropai
npm install
```

### 2. Install Python AI Dependencies
```bash
# Install required Python packages
python3 -m pip install opencv-python mediapipe ultralytics pillow numpy

# Verify installation
python3 -c "import cv2, mediapipe, ultralytics; print('AI libraries installed successfully')"
```

### 3. Download AI Models
The first time you run the application, it will automatically download:
- YOLOv8n model (~6MB) - for object detection
- MediaPipe models (~10MB) - for face/pose detection

### 4. Create Required Directories
```bash
mkdir -p uploads/images uploads/optimize uploads/videos
mkdir -p uploads/processed/images uploads/processed/optimize uploads/processed/videos uploads/processed/zips
```

### 5. Start the Application
```bash
npm run dev
```

The application will be available at: http://localhost:3000

## Features

### Image Processing
- **AI Face Detection**: MediaPipe face detection with confidence scoring
- **Object Detection**: YOLOv8 for detecting people, animals, vehicles, etc.
- **Smart Cropping**: Content-aware cropping based on detected subjects
- **Multiple Platforms**: Process for 15+ social media platforms simultaneously
- **Batch Processing**: ZIP downloads for multiple processed images
- **Preview System**: Preview images before downloading

### Video Processing
- **AI Content Analysis**: Analyzes multiple frames to find consistent subjects
- **Smart Video Cropping**: Crops videos to keep important content in frame
- **Multiple Platform Support**: Instagram Reels, TikTok, YouTube, etc.
- **Advanced Compression**: Quality-optimized encoding with FFmpeg
- **Batch Processing**: Process multiple platform formats simultaneously

### Optimization
- **Lossless Optimization**: Smart compression without quality loss
- **Format Conversion**: JPEG, PNG, WebP with optimal settings
- **Dimension Control**: Reduce image dimensions with quality preservation

## Troubleshooting

### FFmpeg Not Found
If you get "FFmpeg is not installed" errors:
1. Install FFmpeg using the instructions above
2. Restart your terminal/command prompt
3. Verify with `ffmpeg -version`
4. Restart the application

### Python Dependencies
If AI processing fails:
```bash
# Reinstall Python dependencies
python3 -m pip install --upgrade opencv-python mediapipe ultralytics pillow numpy

# Check for conflicts
python3 -m pip check
```

### Memory Issues
For large files or batch processing:
- Increase Node.js memory limit: `node --max-old-space-size=4096 server/index.js`
- Process fewer files simultaneously
- Use lower quality settings for videos

### Port Conflicts
If port 3000 is in use:
1. Change the port in `server/index.ts`
2. Or set environment variable: `PORT=8080 npm run dev`

## Performance Tips

### For Best AI Detection:
- Use high-quality source images/videos
- Ensure good lighting and clear subjects
- Avoid heavily compressed or low-resolution inputs

### For Faster Processing:
- Use smaller batch sizes
- Enable compression for videos
- Use "medium" quality setting instead of "high"

### For Better Results:
- Let the AI models download completely on first run
- Use original/unprocessed source files when possible
- Review preview before downloading to ensure quality

## API Endpoints

- `GET /` - Landing page
- `GET /resize-image` - Image resize tool
- `GET /optimize-convert` - Image optimization tool
- `GET /resize-compress-video` - Video processing tool
- `POST /api/resize-image` - Process image resize
- `POST /api/optimize-convert` - Process image optimization
- `POST /api/resize-compress-video` - Process video
- `POST /api/create-zip` - Create ZIP from multiple files
- `GET /api/download/images/:filename` - Download processed image
- `GET /api/download/videos/:filename` - Download processed video
- `GET /api/download/zips/:filename` - Download ZIP file

## System Requirements

### Minimum:
- 4GB RAM
- 2GB free disk space
- Node.js 16+
- Python 3.8+

### Recommended:
- 8GB+ RAM
- 5GB+ free disk space
- SSD storage
- Multi-core CPU for faster processing

## License

This project uses several open-source libraries:
- YOLOv8 (AGPL-3.0)
- MediaPipe (Apache 2.0)
- OpenCV (Apache 2.0)
- FFmpeg (LGPL/GPL)

Please ensure compliance with respective licenses for commercial use.
