import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import multer from "multer";
import sharp from "sharp";
import path from "path";
import fs from "fs";
import { insertUploadJobSchema, PLATFORM_CONFIGS, type ProcessedResult } from "@shared/schema";
import OpenAI from "openai";

// Polyfills for Node.js < 18
if (!globalThis.fetch) {
  const { default: fetch, Headers, Request, Response } = await import('node-fetch');
  globalThis.fetch = fetch as any;
  globalThis.Headers = Headers as any;
  globalThis.Request = Request as any;
  globalThis.Response = Response as any;
}

// Add Blob polyfill for OpenAI
if (!globalThis.Blob) {
  const { Blob } = await import('buffer');
  globalThis.Blob = Blob as any;
}

// Add FormData polyfill if needed
if (!globalThis.FormData) {
  const { FormData } = await import('formdata-node');
  globalThis.FormData = FormData as any;
}

// Create uploads directory if it doesn't exist
const uploadsDir = path.join(process.cwd(), "uploads");
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Configure multer for file uploads
const upload = multer({
  dest: uploadsDir,
  limits: {
    fileSize: 500 * 1024 * 1024, // 500MB limit
  },
  fileFilter: (req, file, cb) => {
    const allowedMimes = ['image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'video/mov', 'video/quicktime'];
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Unsupported file type. Please upload JPG, PNG, MP4, or MOV files.'));
    }
  }
});

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || process.env.OPENAI_KEY || ""
});

// the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
const OPENAI_MODEL = "gpt-4o";

export async function registerRoutes(app: Express): Promise<Server> {

  // Serve the landing page
  app.get("/", (req, res) => {
    res.sendFile(path.join(process.cwd(), "templates", "index.html"));
  });

  // Serve individual tool pages
  app.get("/resize-image", (req, res) => {
    res.sendFile(path.join(process.cwd(), "templates", "resize-image.html"));
  });

  app.get("/optimize-convert", (req, res) => {
    res.sendFile(path.join(process.cwd(), "templates", "optimize-convert.html"));
  });

  app.get("/resize-compress-video", (req, res) => {
    res.sendFile(path.join(process.cwd(), "templates", "resize-compress-video.html"));
  });

  // Legacy route for the original smart crop tool
  app.get("/smart-crop", (req, res) => {
    res.sendFile(path.join(process.cwd(), "client", "simple.html"));
  });

  // Get all upload jobs
  app.get("/api/jobs", async (req, res) => {
    try {
      const jobs = await storage.getAllUploadJobs();
      res.json(jobs);
    } catch (error) {
      console.error("Error fetching jobs:", error);
      res.status(500).json({ message: "Failed to fetch jobs" });
    }
  });

  // Get specific upload job
  app.get("/api/jobs/:id", async (req, res) => {
    try {
      const job = await storage.getUploadJob(req.params.id);
      if (!job) {
        return res.status(404).json({ message: "Job not found" });
      }
      res.json(job);
    } catch (error) {
      console.error("Error fetching job:", error);
      res.status(500).json({ message: "Failed to fetch job" });
    }
  });

  // Upload and process media
  app.post("/api/upload", upload.single('file'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ message: "No file uploaded" });
      }

      // Handle both old format (platforms array) and new format (selectedFormats object)
      let selectedFormats: Record<string, string[]> = {};

      if (req.body.selectedFormats) {
        selectedFormats = JSON.parse(req.body.selectedFormats || '{}');
      } else if (req.body.platforms) {
        // Fallback for old format - select all formats for each platform
        const platforms = JSON.parse(req.body.platforms || '[]');
        platforms.forEach((platformId: string) => {
          const platform = PLATFORM_CONFIGS.find(p => p.id === platformId);
          if (platform) {
            selectedFormats[platformId] = platform.formats.map(f => f.name);
          }
        });
      }

      if (Object.keys(selectedFormats).length === 0) {
        return res.status(400).json({ message: "At least one format must be selected" });
      }

      // Validate the upload job data
      const jobData = insertUploadJobSchema.parse({
        originalFileName: req.file.originalname,
        fileSize: req.file.size,
        mimeType: req.file.mimetype,
        platforms: Object.keys(selectedFormats),
        status: "processing",
        progress: 0,
        results: null,
        error: null,
      });

      // Create upload job
      const job = await storage.createUploadJob(jobData);

      // Start processing asynchronously
      processMediaAsync(job.id, req.file.path, req.file.mimetype, selectedFormats);

      res.json(job);
    } catch (error) {
      console.error("Error creating upload job:", error);
      res.status(500).json({ message: "Failed to create upload job" });
    }
  });

  // Download processed file
  app.get("/api/download/:jobId/:filename", async (req, res) => {
    try {
      const { jobId, filename } = req.params;
      const job = await storage.getUploadJob(jobId);
      
      if (!job || !job.results) {
        return res.status(404).json({ message: "File not found" });
      }

      // Find the file in results
      const result = job.results.find(r => r.filePath.includes(filename));
      if (!result || !fs.existsSync(result.filePath)) {
        return res.status(404).json({ message: "File not found" });
      }

      res.download(result.filePath, filename);
    } catch (error) {
      console.error("Error downloading file:", error);
      res.status(500).json({ message: "Failed to download file" });
    }
  });

  // Download all processed files as zip
  app.get("/api/download-all/:jobId", async (req, res) => {
    try {
      const job = await storage.getUploadJob(req.params.jobId);
      
      if (!job || !job.results || job.results.length === 0) {
        return res.status(404).json({ message: "No processed files found" });
      }

      // For now, return the list of files - in production you'd create a zip
      res.json({
        files: job.results.map(r => ({
          platform: r.platform,
          format: r.format,
          filename: path.basename(r.filePath),
          downloadUrl: `/api/download/${job.id}/${path.basename(r.filePath)}`
        }))
      });
    } catch (error) {
      console.error("Error preparing download:", error);
      res.status(500).json({ message: "Failed to prepare download" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}

// Async processing function
async function processMediaAsync(jobId: string, filePath: string, mimeType: string, selectedFormats: Record<string, string[]>) {
  try {
    // Update status to processing
    await storage.updateUploadJob(jobId, { 
      status: "processing", 
      progress: 10 
    });

    let subjectAnalysis = null;
    
    // Analyze image content with OpenAI Vision API for smart cropping
    if (mimeType.startsWith('image/')) {
      try {
        const imageBuffer = fs.readFileSync(filePath);
        const base64Image = imageBuffer.toString('base64');
        
        const visionResponse = await openai.chat.completions.create({
          model: OPENAI_MODEL,
          messages: [
            {
              role: "user",
              content: [
                {
                  type: "text",
                  text: "Analyze this image and identify the main subject(s) and their location. Provide the bounding box coordinates as percentages of the image dimensions. Respond with JSON in this format: { 'main_subject': 'description', 'bounding_box': { 'x': number, 'y': number, 'width': number, 'height': number }, 'focal_points': [{'x': number, 'y': number}] }"
                },
                {
                  type: "image_url",
                  image_url: {
                    url: `data:${mimeType};base64,${base64Image}`
                  }
                }
              ],
            },
          ],
          response_format: { type: "json_object" },
          max_tokens: 500,
        });

        subjectAnalysis = JSON.parse(visionResponse.choices[0].message.content || '{}');
        console.log("Subject analysis:", subjectAnalysis);
      } catch (error) {
        console.error("Error analyzing image with OpenAI:", error);
        // Continue processing without AI analysis
      }
    }

    // Update progress
    await storage.updateUploadJob(jobId, { progress: 30 });

    const results: ProcessedResult[] = [];

    // Calculate total formats to process
    const totalFormats = Object.entries(selectedFormats).reduce((acc, [platformId, formatNames]) => {
      return acc + formatNames.length;
    }, 0);

    let processedFormats = 0;

    // Process for each platform and selected formats
    for (const [platformId, formatNames] of Object.entries(selectedFormats)) {
      const platform = PLATFORM_CONFIGS.find(p => p.id === platformId);
      if (!platform) continue;

      for (const formatName of formatNames) {
        const format = platform.formats.find(f => f.name === formatName);
        if (!format) continue;

        try {
          const outputPath = await processMedia(
            filePath,
            mimeType,
            format.dimensions,
            platformId,
            format.name,
            subjectAnalysis
          );

          const stats = fs.statSync(outputPath);
          results.push({
            platform: platform.name,
            format: format.name,
            dimensions: format.dimensions,
            fileSize: stats.size,
            filePath: outputPath,
            optimized: true
          });

          processedFormats++;
          const progress = 30 + Math.round((processedFormats / totalFormats) * 60);
          await storage.updateUploadJob(jobId, { progress });

        } catch (error) {
          console.error(`Error processing ${platformId} ${format.name}:`, error);
        }
      }
    }

    // Update job as completed
    await storage.updateUploadJob(jobId, {
      status: "completed",
      progress: 100,
      results
    });

    // Clean up original uploaded file
    fs.unlinkSync(filePath);

  } catch (error) {
    console.error("Error processing media:", error);
    await storage.updateUploadJob(jobId, {
      status: "failed",
      error: error instanceof Error ? error.message : "Unknown error occurred"
    });
  }
}

// Process media for specific dimensions using advanced Python tools
async function processMedia(
  inputPath: string, 
  mimeType: string, 
  dimensions: { width: number; height: number }, 
  platform: string, 
  format: string,
  subjectAnalysis: any
): Promise<string> {
  const outputDir = path.join(process.cwd(), "uploads", "processed");
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const timestamp = Date.now();
  const mediaType = mimeType.startsWith('image/') ? 'image' : 'video';

  // Preserve original format for images, use mp4 for videos
  let extension = 'jpg'; // default
  if (mediaType === 'image') {
    if (mimeType === 'image/png') {
      extension = 'png';
    } else if (mimeType === 'image/jpeg' || mimeType === 'image/jpg') {
      extension = 'jpg';
    } else if (mimeType === 'image/webp') {
      extension = 'webp';
    } else if (mimeType === 'image/gif') {
      extension = 'gif';
    }
  } else {
    extension = 'mp4';
  }

  const outputPath = path.join(outputDir, `${platform}-${format}-${timestamp}.${extension}`);

  try {
    // Use Python script for advanced processing
    const { spawn } = await import('child_process');
    
    const args = [
      path.join(process.cwd(), 'server', 'media_processor.py'),
      inputPath,
      outputPath,
      dimensions.width.toString(),
      dimensions.height.toString(),
      mediaType
    ];

    // Add subject analysis if available
    if (subjectAnalysis) {
      args.push(JSON.stringify(subjectAnalysis));
    }

    return new Promise((resolve, reject) => {
      const python = spawn('python3', args);
      
      let stdout = '';
      let stderr = '';
      
      python.stdout.on('data', (data: Buffer) => {
        stdout += data.toString();
      });
      
      python.stderr.on('data', (data: Buffer) => {
        stderr += data.toString();
      });
      
      python.on('close', (code: number) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout.trim());
            if (result.success) {
              console.log(`Successfully processed ${mediaType} with advanced tools`);
              resolve(result.output_path);
            } else {
              console.error('Python processing failed:', result.error);
              reject(new Error(result.error || 'Python processing failed'));
            }
          } catch (parseError) {
            console.error('Failed to parse Python output:', stdout, stderr);
            reject(new Error('Failed to parse processing result'));
          }
        } else {
          console.error(`Python script exited with code ${code}:`, stderr);
          reject(new Error(`Processing failed with code ${code}`));
        }
      });
      
      python.on('error', (error: Error) => {
        console.error('Failed to start Python script:', error);
        reject(error);
      });
    });

  } catch (error) {
    console.error('Error in advanced media processing:', error);
    
    // Fallback to Sharp for images if Python processing fails
    if (mimeType.startsWith('image/')) {
      console.log('Falling back to Sharp processing for image');
      const fallbackPath = path.join(outputDir, `${platform}-${format}-fallback-${timestamp}.jpg`);
      
      await sharp(inputPath)
        .resize(dimensions.width, dimensions.height, {
          fit: 'cover',
          position: 'center'
        })
        .jpeg({ 
          quality: 85,
          progressive: true
        })
        .toFile(fallbackPath);
      
      return fallbackPath;
    } else {
      // For videos, create a placeholder if FFmpeg fails
      const placeholderPath = path.join(outputDir, `${platform}-${format}-placeholder-${timestamp}.jpg`);
      
      await sharp({
        create: {
          width: dimensions.width,
          height: dimensions.height,
          channels: 3,
          background: { r: 100, g: 100, b: 100 }
        }
      })
      .jpeg({ quality: 85 })
      .toFile(placeholderPath);
      
      return placeholderPath;
    }
  }
}
