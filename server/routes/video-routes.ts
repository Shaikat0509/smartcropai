import type { Express } from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import { nanoid } from "nanoid";
import { spawn } from "child_process";

// Configure multer for video uploads
const videoStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(process.cwd(), "uploads", "videos");
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueName = `${nanoid()}-${file.originalname}`;
    cb(null, uniqueName);
  }
});

const videoUpload = multer({
  storage: videoStorage,
  limits: { fileSize: 150 * 1024 * 1024 }, // 150MB limit
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('video/')) {
      cb(null, true);
    } else {
      cb(new Error('Only video files are allowed'));
    }
  }
});

// Video platform configurations
const VIDEO_PLATFORMS = {
  'instagram-reel': { width: 1080, height: 1920, name: 'Instagram Reel', bitrate: '2M' },
  'instagram-story': { width: 1080, height: 1920, name: 'Instagram Story', bitrate: '2M' },
  'tiktok': { width: 1080, height: 1920, name: 'TikTok', bitrate: '2M' },
  'youtube-1080p': { width: 1920, height: 1080, name: 'YouTube 1080p', bitrate: '5M' },
  'youtube-720p': { width: 1280, height: 720, name: 'YouTube 720p', bitrate: '3M' },
  'youtube-shorts': { width: 1080, height: 1920, name: 'YouTube Shorts', bitrate: '2M' },
  'facebook-feed': { width: 1280, height: 720, name: 'Facebook Feed', bitrate: '3M' },
  'facebook-story': { width: 1080, height: 1920, name: 'Facebook Story', bitrate: '2M' },
  'twitter-post': { width: 1280, height: 720, name: 'Twitter Post', bitrate: '3M' },
  'linkedin-video': { width: 1280, height: 720, name: 'LinkedIn Video', bitrate: '3M' }
};

export function registerVideoRoutes(app: Express) {
  // Video resize/compress endpoint
  app.post('/api/resize-compress-video', videoUpload.single('video'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No video file uploaded' });
      }

      const { platform, customWidth, customHeight, compress, quality } = req.body;
      let config;

      if (platform && VIDEO_PLATFORMS[platform as keyof typeof VIDEO_PLATFORMS]) {
        config = VIDEO_PLATFORMS[platform as keyof typeof VIDEO_PLATFORMS];
      } else if (customWidth && customHeight) {
        config = {
          width: parseInt(customWidth),
          height: parseInt(customHeight),
          name: `Custom ${customWidth}x${customHeight}`,
          bitrate: '3M'
        };
      } else {
        return res.status(400).json({ error: 'Please select a platform or provide custom dimensions' });
      }

      // Create output directory
      const outputDir = path.join(process.cwd(), "uploads", "processed", "videos");
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      const outputFilename = `processed-${nanoid()}.mp4`;
      const outputPath = path.join(outputDir, outputFilename);

      // Build FFmpeg command
      const ffmpegArgs = [
        '-i', req.file.path,
        '-vf', `scale=${config.width}:${config.height}:force_original_aspect_ratio=decrease,pad=${config.width}:${config.height}:(ow-iw)/2:(oh-ih)/2`,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', quality || '23',
        '-b:v', config.bitrate,
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        '-y', // Overwrite output file
        outputPath
      ];

      // Add compression settings if requested
      if (compress === 'true') {
        ffmpegArgs.splice(-2, 0, '-crf', '28'); // Higher CRF for more compression
      }

      // Execute FFmpeg
      const ffmpeg = spawn('ffmpeg', ffmpegArgs);
      
      let stderr = '';
      ffmpeg.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      ffmpeg.on('close', (code) => {
        if (code === 0) {
          // Success - get file stats
          const stats = fs.statSync(outputPath);
          const originalStats = fs.statSync(req.file.path);
          const compressionRatio = ((originalStats.size - stats.size) / originalStats.size * 100).toFixed(1);

          // Clean up original file
          fs.unlinkSync(req.file.path);

          res.json({
            success: true,
            filename: outputFilename,
            platform: config.name,
            dimensions: { width: config.width, height: config.height },
            originalSize: originalStats.size,
            processedSize: stats.size,
            compressionRatio: `${compressionRatio}%`,
            downloadUrl: `/api/download/videos/${outputFilename}`
          });
        } else {
          console.error('FFmpeg error:', stderr);
          // Clean up files on error
          if (fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
          if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
          
          res.status(500).json({ error: 'Failed to process video' });
        }
      });

      ffmpeg.on('error', (error) => {
        console.error('FFmpeg spawn error:', error);
        // Clean up files on error
        if (fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
        if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);

        if (!res.headersSent) {
          res.status(500).json({
            error: 'FFmpeg is not installed. Please install FFmpeg to process videos.'
          });
        }
      });

    } catch (error) {
      console.error('Video processing error:', error);
      res.status(500).json({ error: 'Failed to process video' });
    }
  });

  // Download processed video
  app.get('/api/download/videos/:filename', (req, res) => {
    const filename = req.params.filename;
    const filePath = path.join(process.cwd(), "uploads", "processed", "videos", filename);
    
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'File not found' });
    }

    res.download(filePath, (err) => {
      if (err) {
        console.error('Download error:', err);
        res.status(500).json({ error: 'Failed to download file' });
      }
    });
  });

  // Get video platform configurations
  app.get('/api/video-platforms', (req, res) => {
    res.json(VIDEO_PLATFORMS);
  });
}
