import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, jsonb, timestamp, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const uploadJobs = pgTable("upload_jobs", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  originalFileName: text("original_file_name").notNull(),
  fileSize: integer("file_size").notNull(),
  mimeType: text("mime_type").notNull(),
  platforms: jsonb("platforms").notNull().$type<string[]>(),
  status: text("status").notNull().default("uploading"), // uploading, processing, completed, failed
  progress: integer("progress").notNull().default(0),
  results: jsonb("results").$type<ProcessedResult[]>(),
  error: text("error"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export const insertUploadJobSchema = createInsertSchema(uploadJobs).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export type InsertUploadJob = z.infer<typeof insertUploadJobSchema>;
export type UploadJob = typeof uploadJobs.$inferSelect;

// Type definitions for processed results
export interface ProcessedResult {
  platform: string;
  format: string;
  dimensions: {
    width: number;
    height: number;
  };
  fileSize: number;
  filePath: string;
  optimized: boolean;
}

export interface PlatformConfig {
  id: string;
  name: string;
  icon: string;
  formats: Array<{
    name: string;
    dimensions: {
      width: number;
      height: number;
    };
    aspectRatio: string;
  }>;
  color: string;
}

// Platform configurations
export const PLATFORM_CONFIGS: PlatformConfig[] = [
  {
    id: "instagram",
    name: "Instagram",
    icon: "instagram",
    color: "from-pink-500 to-orange-500",
    formats: [
      { name: "Square", dimensions: { width: 1080, height: 1080 }, aspectRatio: "1:1" },
      { name: "Story", dimensions: { width: 1080, height: 1920 }, aspectRatio: "9:16" },
      { name: "Reel", dimensions: { width: 1080, height: 1920 }, aspectRatio: "9:16" },
    ]
  },
  {
    id: "tiktok",
    name: "TikTok",
    icon: "tiktok",
    color: "bg-black",
    formats: [
      { name: "Video", dimensions: { width: 1080, height: 1920 }, aspectRatio: "9:16" },
    ]
  },
  {
    id: "youtube",
    name: "YouTube",
    icon: "youtube",
    color: "bg-red-600",
    formats: [
      { name: "Video", dimensions: { width: 1920, height: 1080 }, aspectRatio: "16:9" },
      { name: "Thumbnail", dimensions: { width: 1280, height: 720 }, aspectRatio: "16:9" },
    ]
  },
  {
    id: "facebook",
    name: "Facebook",
    icon: "facebook",
    color: "bg-blue-600",
    formats: [
      { name: "Feed", dimensions: { width: 1200, height: 1500 }, aspectRatio: "4:5" },
      { name: "Story", dimensions: { width: 1080, height: 1920 }, aspectRatio: "9:16" },
      { name: "Video", dimensions: { width: 1920, height: 1080 }, aspectRatio: "16:9" },
    ]
  },
  {
    id: "linkedin",
    name: "LinkedIn",
    icon: "linkedin",
    color: "bg-blue-700",
    formats: [
      { name: "Post", dimensions: { width: 1200, height: 628 }, aspectRatio: "1.91:1" },
      { name: "Video", dimensions: { width: 1920, height: 1080 }, aspectRatio: "16:9" },
    ]
  },
  {
    id: "pinterest",
    name: "Pinterest",
    icon: "pinterest",
    color: "bg-red-500",
    formats: [
      { name: "Pin", dimensions: { width: 1000, height: 1500 }, aspectRatio: "2:3" },
      { name: "Idea Pin", dimensions: { width: 1080, height: 1920 }, aspectRatio: "9:16" },
    ]
  },
  {
    id: "twitter",
    name: "X/Twitter",
    icon: "twitter",
    color: "bg-black",
    formats: [
      { name: "Post", dimensions: { width: 1920, height: 1080 }, aspectRatio: "16:9" },
      { name: "Header", dimensions: { width: 1500, height: 500 }, aspectRatio: "3:1" },
    ]
  },
  {
    id: "website",
    name: "Website",
    icon: "monitor",
    color: "bg-gray-600",
    formats: [
      { name: "Banner", dimensions: { width: 2560, height: 1080 }, aspectRatio: "21:9" },
      { name: "Hero", dimensions: { width: 1920, height: 1080 }, aspectRatio: "16:9" },
    ]
  }
];
