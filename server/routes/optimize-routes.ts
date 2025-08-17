import type { Express } from "express";
import multer from "multer";
import sharp from "sharp";
import path from "path";
import fs from "fs";
import { nanoid } from "nanoid";
import { spawn } from "child_process";

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
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit per file
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

      // Validate format and determine output format
      const allowedFormats = ['jpeg', 'png', 'webp', 'original'];
      let outputFormat = format && allowedFormats.includes(format) ? format : 'original';

      // If 'original' is selected, detect the original format
      if (outputFormat === 'original') {
        const originalExt = path.extname(req.file.originalname).toLowerCase();
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

      // Use professional Python optimizer for industry-best results
      let optimizationResult;
      let professionalOptimizationUsed = false;

      try {
        // Prepare optimization options
        const optimizationOptions = {
          format: outputFormat, // Pass format as-is, including 'auto'
          quality: isLossless ? 'auto' : 'auto',
          lossless: isLossless,
          max_width: shouldReduceDimensions ? Math.round(2000 * (reductionPercent / 100)) : null,
          max_height: shouldReduceDimensions ? Math.round(2000 * (reductionPercent / 100)) : null
        };

        // Run professional optimizer
        const pythonProcess = spawn('python3', [
          path.join(process.cwd(), 'server', 'professional_image_optimizer.py'),
          req.file.path,
          outputPath,
          JSON.stringify(optimizationOptions)
        ]);

        let pythonOutput = '';
        let pythonError = '';

        pythonProcess.stdout.on('data', (data) => {
          pythonOutput += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
          pythonError += data.toString();
        });

        await new Promise((resolve, reject) => {
          pythonProcess.on('close', (code) => {
            if (code === 0) {
              try {
                optimizationResult = JSON.parse(pythonOutput);
                professionalOptimizationUsed = true;
                console.log('Professional optimization results:', optimizationResult);
                resolve(code);
              } catch (e) {
                reject(new Error('Failed to parse optimization results'));
              }
            } else {
              reject(new Error(`Professional optimizer failed: ${pythonError}`));
            }
          });
          pythonProcess.on('error', reject);
        });

      } catch (error) {
        console.log('Professional optimization failed, using Sharp fallback:', error.message);

        // Fallback to improved Sharp pipeline
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
      const originalStats = fs.statSync(req.file.path);

      // Use professional optimization results if available, otherwise calculate manually
      let compressionRatio, finalFormat, qualityUsed, optimizationMethod;

      if (professionalOptimizationUsed && optimizationResult) {
        compressionRatio = `${optimizationResult.compression_ratio}%`;
        // Always use the actual output format, not what the optimizer reports
        finalFormat = outputFormat.toUpperCase();
        qualityUsed = optimizationResult.quality_used;
        optimizationMethod = 'Professional AI-powered optimization';
      } else {
        compressionRatio = ((originalStats.size - stats.size) / originalStats.size * 100).toFixed(1) + '%';
        finalFormat = outputFormat.toUpperCase();
        qualityUsed = isLossless ? 'lossless' : 'auto';
        optimizationMethod = 'Sharp-based optimization';
      }

      // Clean up original file
      fs.unlinkSync(req.file.path);

      res.json({
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
        professionalOptimization: professionalOptimizationUsed,
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
