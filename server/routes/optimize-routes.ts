import type { Express } from "express";
import multer from "multer";
import sharp from "sharp";
import path from "path";
import fs from "fs";
import { nanoid } from "nanoid";
import { spawn } from "child_process";
import { squooshOptimizer } from '../squoosh_optimizer';

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
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB limit per file
    files: 20 // Maximum 20 files
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'));
    }
  }
});

export function registerOptimizeRoutes(app: Express) {
  // Image optimize/convert endpoint - supports multiple images (up to 20)
  app.post('/api/optimize-convert', optimizeUpload.array('images', 20), async (req, res) => {
    try {
      if (!req.files || !Array.isArray(req.files) || req.files.length === 0) {
        return res.status(400).json({ error: 'No image files uploaded' });
      }

      const { format, losslessOptimize, reduceDimensions, reduction } = req.body;

      // Process multiple files
      const results = [];
      const files = req.files as Express.Multer.File[];

      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        // Validate format and determine output format for this file
        const allowedFormats = ['jpeg', 'png', 'webp', 'original'];
        let outputFormat = format && allowedFormats.includes(format) ? format : 'original';

        // If 'original' is selected, detect the original format
        if (outputFormat === 'original') {
          const originalExt = path.extname(file.originalname).toLowerCase();
        switch (originalExt) {
          case '.jpg':
          case '.jpeg':
            outputFormat = 'jpeg';
            break;
          case '.png':
            outputFormat = 'png';
            break;
          case '.webp':
            outputFormat = 'webp';
            break;
          default:
            // Default to JPEG for unknown formats
            outputFormat = 'jpeg';
          }
        }

        // Parse settings for this file
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

        // Try Squoosh for maximum optimization, fallback to Sharp if needed
        console.log(`Optimizing file ${i + 1}/${files.length} with Squoosh: ${outputFormat}, reduce: ${shouldReduceDimensions}`);

        let optimizationResult;
        let squooshOptimizationUsed = false;

        try {
          // Set a timeout for Squoosh optimization
          const squooshPromise = squooshOptimizer.optimizeImage(
            file.path,
            outputPath,
            outputFormat,
            shouldReduceDimensions,
            reductionPercent
          );

        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Squoosh timeout')), 15000); // 15 second timeout
        });

        const squooshResult = await Promise.race([squooshPromise, timeoutPromise]) as any;

        if (squooshResult.success) {
          optimizationResult = squooshResult;
          squooshOptimizationUsed = true;
          console.log('Squoosh optimization results:', optimizationResult);
        } else {
          throw new Error(squooshResult.error || 'Squoosh optimization failed');
        }
      } catch (error) {
        console.log('Squoosh optimization failed, using Sharp fallback:', error.message);

          // Fallback to improved Sharp pipeline
          let pipeline = sharp(file.path);

        // Apply dimension reduction if requested
        if (shouldReduceDimensions) {
          const metadata = await pipeline.metadata();
          if (metadata.width && metadata.height) {
            const newWidth = Math.round(metadata.width * (reductionPercent / 100));
            const newHeight = Math.round(metadata.height * (reductionPercent / 100));
            pipeline = pipeline.resize(newWidth, newHeight, { fit: 'inside' });
          }
        }

        // Apply improved format-specific optimization
        switch (outputFormat) {
          case 'jpeg':
            pipeline = pipeline.jpeg({
              quality: isLossless ? 85 : 75,
              progressive: true,
              mozjpeg: true,
              optimiseScans: true,
              optimiseCoding: true,
              trellisQuantisation: true,
              overshootDeringing: true
            });
            break;
          case 'png':
            pipeline = pipeline.png({
              compressionLevel: 9,
              progressive: true,
              palette: !isLossless,
              effort: 10,
              adaptiveFiltering: true
            });
            break;
          case 'webp':
            pipeline = pipeline.webp({
              quality: isLossless ? 90 : 75,
              effort: 6,
              smartSubsample: true,
              nearLossless: isLossless,
              preset: 'photo'
            });
            break;
        }

          // Process with Sharp
          await pipeline.toFile(outputPath);
        }

        // Get file stats
        const stats = fs.statSync(outputPath);
        const originalStats = fs.statSync(file.path);

        // Use Squoosh optimization results if available, otherwise calculate manually
        let compressionRatio, finalFormat, qualityUsed, optimizationMethod;

        if (squooshOptimizationUsed && optimizationResult) {
          compressionRatio = `${optimizationResult.compressionRatio}%`;
          finalFormat = optimizationResult.format;
          qualityUsed = optimizationResult.qualityUsed;
          optimizationMethod = 'Squoosh maximum optimization';
        } else {
          compressionRatio = ((originalStats.size - stats.size) / originalStats.size * 100).toFixed(1) + '%';
          finalFormat = outputFormat.toUpperCase();
          qualityUsed = isLossless ? 'lossless' : 'auto';
          optimizationMethod = 'Sharp-based optimization';
        }

        // Clean up original file
        fs.unlinkSync(file.path);

        // Add result for this file
        results.push({
          success: true,
          filename: outputFilename,
          format: finalFormat,
          losslessOptimized: isLossless,
          dimensionsReduced: shouldReduceDimensions,
          reductionPercent: shouldReduceDimensions ? reductionPercent : 100,
          originalSize: originalStats.size,
          processedSize: stats.size,
          compressionRatio: compressionRatio,
          qualityUsed: qualityUsed,
          optimizationMethod: optimizationMethod,
          squooshOptimization: squooshOptimizationUsed,
          downloadUrl: `/api/download/optimize/${outputFilename}`,
          originalFilename: file.originalname
        });
      }

      // Return results (single result if 1 file, array if multiple)
      if (results.length === 1) {
        res.json(results[0]);
      } else {
        res.json(results);
      }



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
