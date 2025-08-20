import type { Express } from "express";
import fs from "fs";
import path from "path";

export function setupCleanupRoutes(app: Express) {
  // Cleanup endpoint for processed files
  app.post('/api/cleanup', async (req, res) => {
    try {
      const { files } = req.body;
      
      if (!files || !Array.isArray(files)) {
        return res.status(400).json({ error: 'Invalid files array' });
      }

      let cleanedCount = 0;
      const errors: string[] = [];

      for (const file of files) {
        try {
          let filePath: string;
          
          // Determine file path based on type
          switch (file.type) {
            case 'optimize':
              filePath = path.join(process.cwd(), 'public', 'optimized', file.filename);
              break;
            case 'images':
              filePath = path.join(process.cwd(), 'public', 'resized', file.filename);
              break;
            case 'videos':
              filePath = path.join(process.cwd(), 'public', 'videos', file.filename);
              break;
            default:
              errors.push(`Unknown file type: ${file.type}`);
              continue;
          }

          // Check if file exists and delete it
          if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
            cleanedCount++;
            console.log(`Cleaned up file: ${file.filename}`);
          } else {
            console.log(`File not found for cleanup: ${file.filename}`);
          }
          
        } catch (error) {
          const errorMsg = `Failed to cleanup ${file.filename}: ${error instanceof Error ? error.message : 'Unknown error'}`;
          errors.push(errorMsg);
          console.error(errorMsg);
        }
      }

      // Also cleanup any temporary upload files older than 1 hour
      try {
        const uploadDirs = [
          path.join(process.cwd(), 'uploads', 'images'),
          path.join(process.cwd(), 'uploads', 'videos'),
          path.join(process.cwd(), 'uploads', 'optimize')
        ];

        for (const uploadDir of uploadDirs) {
          if (fs.existsSync(uploadDir)) {
            const files = fs.readdirSync(uploadDir);
            const oneHourAgo = Date.now() - (60 * 60 * 1000); // 1 hour ago

            for (const file of files) {
              const filePath = path.join(uploadDir, file);
              const stats = fs.statSync(filePath);
              
              if (stats.mtime.getTime() < oneHourAgo) {
                fs.unlinkSync(filePath);
                console.log(`Cleaned up old upload file: ${file}`);
              }
            }
          }
        }
      } catch (error) {
        console.error('Error cleaning up old uploads:', error);
      }

      res.json({
        success: true,
        cleanedCount,
        errors: errors.length > 0 ? errors : undefined
      });

    } catch (error) {
      console.error('Cleanup error:', error);
      res.status(500).json({ 
        error: 'Cleanup failed',
        details: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });
}
