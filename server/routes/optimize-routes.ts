import type { Express } from "express";
import multer from "multer";
import sharp from "sharp";
import path from "path";
import fs from "fs";
import { nanoid } from "nanoid";

// Configure multer for image uploads
const optimizeStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(process.cwd(), "uploads", "optimize");
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

const optimizeUpload = multer({
  storage: optimizeStorage,
  limits: { fileSize: 50 * 1024 * 1024 }, // 50MB limit
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'));
    }
  }
});

export function registerOptimizeRoutes(app: Express) {
  // Image optimize/convert endpoint
  app.post('/api/optimize-convert', optimizeUpload.single('image'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No image file uploaded' });
      }

      const { format, losslessOptimize, reduceDimensions, reduction } = req.body;

      // Validate format
      const allowedFormats = ['jpeg', 'png', 'webp'];
      const outputFormat = format && allowedFormats.includes(format) ? format : 'jpeg';

      // Parse settings
      const isLossless = losslessOptimize === 'true';
      const shouldReduceDimensions = reduceDimensions === 'true';
      const reductionPercent = shouldReduceDimensions ? Math.max(50, Math.min(95, parseInt(reduction) || 80)) : 100;
      
      // Create output directory
      const outputDir = path.join(process.cwd(), "uploads", "processed", "optimize");
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      const outputFilename = `optimized-${nanoid()}.${outputFormat === 'jpeg' ? 'jpg' : outputFormat}`;
      const outputPath = path.join(outputDir, outputFilename);

      // Start with Sharp pipeline
      let pipeline = sharp(req.file.path);

      // Apply dimension reduction if requested
      if (shouldReduceDimensions) {
        const metadata = await pipeline.metadata();
        if (metadata.width && metadata.height) {
          const newWidth = Math.round(metadata.width * (reductionPercent / 100));
          const newHeight = Math.round(metadata.height * (reductionPercent / 100));
          pipeline = pipeline.resize(newWidth, newHeight, { fit: 'inside' });
        }
      }

      // Apply format-specific options with smart optimization
      if (isLossless) {
        // Smart lossless optimization settings
        switch (outputFormat) {
          case 'jpeg':
            pipeline = pipeline.jpeg({
              quality: 90,
              progressive: true,
              mozjpeg: true,
              optimiseScans: true,
              optimiseCoding: true
            });
            break;
          case 'png':
            pipeline = pipeline.png({
              compressionLevel: 9,
              progressive: true,
              palette: true,
              effort: 10
            });
            break;
          case 'webp':
            pipeline = pipeline.webp({
              quality: 90,
              effort: 6,
              smartSubsample: true
            });
            break;
        }
      } else {
        // Aggressive optimization for smaller files
        switch (outputFormat) {
          case 'jpeg':
            pipeline = pipeline.jpeg({
              quality: 75,
              progressive: true,
              mozjpeg: true,
              optimiseScans: true
            });
            break;
          case 'png':
            pipeline = pipeline.png({
              compressionLevel: 9,
              progressive: true,
              effort: 10
            });
            break;
          case 'webp':
            pipeline = pipeline.webp({
              quality: 80,
              effort: 6
            });
            break;
        }
      }

      // Process the image
      await pipeline.toFile(outputPath);

      // Get file stats
      const stats = fs.statSync(outputPath);
      const originalStats = fs.statSync(req.file.path);
      const compressionRatio = ((originalStats.size - stats.size) / originalStats.size * 100).toFixed(1);

      // Clean up original file
      fs.unlinkSync(req.file.path);

      res.json({
        success: true,
        filename: outputFilename,
        format: outputFormat,
        losslessOptimized: isLossless,
        dimensionsReduced: shouldReduceDimensions,
        reductionPercent: shouldReduceDimensions ? reductionPercent : 100,
        originalSize: originalStats.size,
        processedSize: stats.size,
        compressionRatio: `${compressionRatio}%`,
        downloadUrl: `/api/download/optimize/${outputFilename}`
      });

    } catch (error) {
      console.error('Image optimize error:', error);
      res.status(500).json({ error: 'Failed to process image' });
    }
  });

  // Download optimized image
  app.get('/api/download/optimize/:filename', (req, res) => {
    const filename = req.params.filename;
    const filePath = path.join(process.cwd(), "uploads", "processed", "optimize", filename);

    console.log('Optimize download request for:', filename);
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
}
