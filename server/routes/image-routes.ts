import type { Express } from "express";
import multer from "multer";
import sharp from "sharp";
import path from "path";
import fs from "fs";
import { nanoid } from "nanoid";
import archiver from "archiver";
import { spawn } from "child_process";

// Configure multer for image uploads
const imageStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(process.cwd(), "uploads", "images");
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

const imageUpload = multer({
  storage: imageStorage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit per file
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'));
    }
  }
});

// Platform dimensions configuration
const PLATFORM_DIMENSIONS = {
  'instagram-post': { width: 1080, height: 1080, name: 'Instagram Post (Square)' },
  'instagram-story': { width: 1080, height: 1920, name: 'Instagram Story' },
  'instagram-reel': { width: 1080, height: 1920, name: 'Instagram Reel' },
  'facebook-post': { width: 1200, height: 630, name: 'Facebook Post' },
  'facebook-cover': { width: 1200, height: 315, name: 'Facebook Cover' },
  'facebook-story': { width: 1080, height: 1920, name: 'Facebook Story' },
  'youtube-thumbnail': { width: 1280, height: 720, name: 'YouTube Thumbnail' },
  'youtube-banner': { width: 2560, height: 1440, name: 'YouTube Channel Banner' },
  'twitter-post': { width: 1200, height: 675, name: 'Twitter Post' },
  'twitter-header': { width: 1500, height: 500, name: 'Twitter Header' },
  'linkedin-post': { width: 1200, height: 628, name: 'LinkedIn Post' },
  'linkedin-banner': { width: 1584, height: 396, name: 'LinkedIn Banner' },
  'pinterest-pin': { width: 1000, height: 1500, name: 'Pinterest Pin' },
  'tiktok-video': { width: 1080, height: 1920, name: 'TikTok Video' },
  'website-banner': { width: 1920, height: 600, name: 'Website Banner' },
  'website-hero': { width: 1920, height: 1080, name: 'Website Hero' }
};

export function registerImageRoutes(app: Express) {
  // Image resize endpoint
  app.post('/api/resize-image', imageUpload.single('image'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No image file uploaded' });
      }

      const { platform, customWidth, customHeight } = req.body;
      let dimensions;

      if (platform && PLATFORM_DIMENSIONS[platform as keyof typeof PLATFORM_DIMENSIONS]) {
        dimensions = PLATFORM_DIMENSIONS[platform as keyof typeof PLATFORM_DIMENSIONS];
      } else if (customWidth && customHeight) {
        dimensions = {
          width: parseInt(customWidth),
          height: parseInt(customHeight),
          name: `Custom ${customWidth}x${customHeight}`
        };
      } else {
        return res.status(400).json({ error: 'Please select a platform or provide custom dimensions' });
      }

      // Create output directory
      const outputDir = path.join(process.cwd(), "uploads", "processed", "images");
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      const outputFilename = `resized-${nanoid()}.jpg`;
      const outputPath = path.join(outputDir, outputFilename);

      // Use advanced AI-powered smart cropping
      let pythonOutput = '';
      let aiProcessingUsed = false;

      try {
        // Try to use advanced Python AI processing first
        const pythonProcess = spawn('python3', [
          path.join(process.cwd(), 'server', 'advanced_media_processor.py'),
          req.file.path,
          outputPath,
          dimensions.width.toString(),
          dimensions.height.toString()
        ]);

        pythonProcess.stdout.on('data', (data) => {
          pythonOutput += data.toString();
        });

        await new Promise((resolve, reject) => {
          pythonProcess.on('close', (code) => {
            if (code === 0) {
              aiProcessingUsed = true;
              // Log AI detection results
              try {
                const detectionResults = JSON.parse(pythonOutput);
                console.log('AI Detection Results:', {
                  mainSubject: detectionResults.main_subject,
                  confidence: detectionResults.confidence,
                  facesDetected: detectionResults.faces?.length || 0,
                  objectsDetected: detectionResults.objects?.length || 0
                });
              } catch (e) {
                console.log('AI processing completed successfully');
              }
              resolve(code);
            } else {
              reject(new Error('AI processing failed'));
            }
          });
          pythonProcess.on('error', reject);
        });
      } catch (error) {
        console.log('AI smart cropping failed, using Sharp fallback:', error.message);

        // Fallback to Sharp with attention-based smart cropping
        await sharp(req.file.path)
          .resize(dimensions.width, dimensions.height, {
            fit: 'cover',
            position: sharp.strategy.attention // Smart cropping
          })
          .jpeg({ quality: 90, progressive: true })
          .toFile(outputPath);
      }

      // Get file stats
      const stats = fs.statSync(outputPath);
      const originalStats = fs.statSync(req.file.path);

      // Clean up original file
      fs.unlinkSync(req.file.path);

      // Include AI processing results if available
      let aiProcessing = undefined;
      if (aiProcessingUsed) {
        try {
          if (pythonOutput) {
            const detectionResults = JSON.parse(pythonOutput);
            aiProcessing = {
              method: detectionResults.main_subject || 'Smart cropping applied',
              detectionsFound: (detectionResults.faces?.length || 0) +
                             (detectionResults.objects?.length || 0) +
                             (detectionResults.poses?.length || 0),
              confidence: detectionResults.confidence || 0,
              cropMethod: detectionResults.bounding_box ? 'ai_detected' : 'center_fallback'
            };
          }
        } catch (e) {
          // If parsing fails, still indicate AI processing was attempted
          aiProcessing = {
            method: 'AI processing applied',
            detectionsFound: 0,
            confidence: 0.5,
            cropMethod: 'smart_fallback'
          };
        }
      } else {
        // Sharp fallback was used
        aiProcessing = {
          method: 'Sharp attention-based cropping',
          detectionsFound: 0,
          confidence: 0.7,
          cropMethod: 'sharp_attention'
        };
      }

      res.json({
        success: true,
        filename: outputFilename,
        dimensions: dimensions,
        originalSize: originalStats.size,
        processedSize: stats.size,
        downloadUrl: `/api/download/images/${outputFilename}`,
        aiProcessing: aiProcessing
      });

    } catch (error) {
      console.error('Image resize error:', error);
      res.status(500).json({ error: 'Failed to process image' });
    }
  });

  // Download processed image
  app.get('/api/download/images/:filename', (req, res) => {
    const filename = req.params.filename;
    const filePath = path.join(process.cwd(), "uploads", "processed", "images", filename);

    console.log('Download request for:', filename);
    console.log('Looking for file at:', filePath);
    console.log('File exists:', fs.existsSync(filePath));

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

  // Get platform dimensions
  app.get('/api/platform-dimensions', (req, res) => {
    res.json(PLATFORM_DIMENSIONS);
  });

  // Create ZIP file from multiple images
  app.post('/api/create-zip', async (req, res) => {
    try {
      const { urls } = req.body;

      if (!urls || !Array.isArray(urls) || urls.length === 0) {
        return res.status(400).json({ error: 'No URLs provided' });
      }

      const zipFilename = `resized-images-${nanoid()}.zip`;
      const zipPath = path.join(process.cwd(), "uploads", "processed", "zips", zipFilename);

      // Create zips directory if it doesn't exist
      const zipDir = path.dirname(zipPath);
      if (!fs.existsSync(zipDir)) {
        fs.mkdirSync(zipDir, { recursive: true });
      }

      const output = fs.createWriteStream(zipPath);
      const archive = archiver('zip', { zlib: { level: 9 } });

      output.on('close', () => {
        res.json({
          success: true,
          filename: zipFilename,
          downloadUrl: `/api/download/zips/${zipFilename}`,
          size: archive.pointer()
        });
      });

      archive.on('error', (err) => {
        console.error('Archive error:', err);
        res.status(500).json({ error: 'Failed to create ZIP file' });
      });

      archive.pipe(output);

      // Add files to archive
      for (const url of urls) {
        try {
          // Extract filename from URL
          const urlPath = new URL(url, `http://localhost:${process.env.PORT || 3000}`).pathname;
          const filename = path.basename(urlPath);
          const filePath = path.join(process.cwd(), "uploads", "processed", "images", filename);

          if (fs.existsSync(filePath)) {
            archive.file(filePath, { name: filename });
          }
        } catch (error) {
          console.error('Error adding file to ZIP:', error);
        }
      }

      await archive.finalize();

    } catch (error) {
      console.error('ZIP creation error:', error);
      res.status(500).json({ error: 'Failed to create ZIP file' });
    }
  });

  // Download ZIP file
  app.get('/api/download/zips/:filename', (req, res) => {
    const filename = req.params.filename;
    const filePath = path.join(process.cwd(), "uploads", "processed", "zips", filename);

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'ZIP file not found' });
    }

    res.download(filePath, (err) => {
      if (err) {
        console.error('ZIP download error:', err);
        res.status(500).json({ error: 'Failed to download ZIP file' });
      } else {
        // Clean up ZIP file after download
        setTimeout(() => {
          if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
          }
        }, 5000);
      }
    });
  });
}
