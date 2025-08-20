import { ImagePool } from '@squoosh/lib';
import fs from 'fs';
import path from 'path';

interface OptimizationResult {
  success: boolean;
  originalSize: number;
  optimizedSize: number;
  compressionRatio: number;
  format: string;
  qualityUsed: string | number;
  error?: string;
}

export class SquooshOptimizer {
  private imagePool: ImagePool;

  constructor() {
    this.imagePool = new ImagePool();
  }

  async optimizeImage(
    inputPath: string,
    outputPath: string,
    targetFormat: string,
    reduceDimensions: boolean = false,
    reductionPercentage: number = 80
  ): Promise<OptimizationResult> {
    try {
      // Read input file
      const inputBuffer = fs.readFileSync(inputPath);
      const originalSize = inputBuffer.length;

      // Ingest the image
      const image = this.imagePool.ingestImage(inputBuffer);

      // Get original dimensions
      const { bitmap } = await image.decoded;
      const originalWidth = bitmap.width;
      const originalHeight = bitmap.height;

      // Calculate new dimensions if reduction is requested
      let newWidth = originalWidth;
      let newHeight = originalHeight;
      
      if (reduceDimensions) {
        const scale = reductionPercentage / 100;
        newWidth = Math.round(originalWidth * scale);
        newHeight = Math.round(originalHeight * scale);
      }

      // Resize if needed
      if (newWidth !== originalWidth || newHeight !== originalHeight) {
        await image.preprocess({
          resize: {
            enabled: true,
            width: newWidth,
            height: newHeight,
          },
        });
      }

      // Determine optimal encoding options based on format
      const encodingOptions = this.getOptimalEncodingOptions(targetFormat, originalSize);

      // Encode the image
      await image.encode(encodingOptions);

      // Get the encoded result
      const encodedImage = await image.encodedWith[targetFormat];
      
      if (!encodedImage) {
        throw new Error(`Failed to encode image as ${targetFormat}`);
      }

      const optimizedBuffer = encodedImage.binary;
      const optimizedSize = optimizedBuffer.length;

      // Write output file
      fs.writeFileSync(outputPath, optimizedBuffer);

      // Calculate compression ratio
      const compressionRatio = ((originalSize - optimizedSize) / originalSize) * 100;

      // Clean up
      image.close();

      return {
        success: true,
        originalSize,
        optimizedSize,
        compressionRatio: Math.round(compressionRatio * 10) / 10,
        format: targetFormat.toUpperCase(),
        qualityUsed: encodingOptions[targetFormat]?.quality || 'auto',
      };

    } catch (error) {
      console.error('Squoosh optimization error:', error);
      return {
        success: false,
        originalSize: 0,
        optimizedSize: 0,
        compressionRatio: 0,
        format: targetFormat.toUpperCase(),
        qualityUsed: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  private getOptimalEncodingOptions(format: string, originalSize: number): any {
    switch (format.toLowerCase()) {
      case 'jpeg':
        // Adaptive quality based on file size
        let jpegQuality = 85;
        if (originalSize > 2 * 1024 * 1024) { // > 2MB
          jpegQuality = 75;
        } else if (originalSize > 5 * 1024 * 1024) { // > 5MB
          jpegQuality = 70;
        }
        
        return {
          mozjpeg: {
            quality: jpegQuality,
            baseline: false,
            arithmetic: false,
            progressive: true,
            optimize_coding: true,
            smoothing: 0,
            color_space: 3,
            quant_table: 3,
            trellis_multipass: false,
            trellis_opt_zero: false,
            trellis_opt_table: false,
            trellis_loops: 1,
            auto_subsample: true,
            chroma_subsample: 2,
            separate_chroma_quality: false,
            chroma_quality: jpegQuality,
          },
        };

      case 'webp':
        // High-quality WebP with optimal settings
        let webpQuality = 85;
        if (originalSize > 2 * 1024 * 1024) { // > 2MB
          webpQuality = 80;
        } else if (originalSize > 5 * 1024 * 1024) { // > 5MB
          webpQuality = 75;
        }

        return {
          webp: {
            quality: webpQuality,
            target_size: 0,
            target_PSNR: 0,
            method: 6, // Maximum compression effort
            sns_strength: 50,
            filter_strength: 60,
            filter_sharpness: 0,
            filter_type: 1,
            partitions: 0,
            segments: 4,
            pass: 1,
            show_compressed: 0,
            preprocessing: 0,
            autofilter: 0,
            partition_limit: 0,
            alpha_compression: 1,
            alpha_filtering: 1,
            alpha_quality: 100,
            lossless: 0,
            exact: 0,
            image_hint: 0,
            emulate_jpeg_size: 0,
            thread_level: 0,
            low_memory: 0,
            near_lossless: 100,
            use_delta_palette: 0,
            use_sharp_yuv: 0,
          },
        };

      case 'png':
        // Optimal PNG compression
        return {
          oxipng: {
            level: 6, // Maximum compression
            interlace: false,
          },
        };

      case 'avif':
        // High-quality AVIF
        let avifQuality = 80;
        if (originalSize > 2 * 1024 * 1024) { // > 2MB
          avifQuality = 75;
        } else if (originalSize > 5 * 1024 * 1024) { // > 5MB
          avifQuality = 70;
        }

        return {
          avif: {
            cqLevel: 100 - avifQuality, // AVIF uses cqLevel (lower = better quality)
            cqAlphaLevel: -1,
            denoiseLevel: 0,
            tileColsLog2: 0,
            tileRowsLog2: 0,
            speed: 6, // Slower but better compression
            subsample: 1,
            chromaDeltaQ: false,
            sharpness: 0,
            tune: 0,
          },
        };

      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  async close(): Promise<void> {
    await this.imagePool.close();
  }
}

// Export a singleton instance
export const squooshOptimizer = new SquooshOptimizer();
