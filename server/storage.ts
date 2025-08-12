import { type UploadJob, type InsertUploadJob } from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  getUploadJob(id: string): Promise<UploadJob | undefined>;
  createUploadJob(job: InsertUploadJob): Promise<UploadJob>;
  updateUploadJob(id: string, updates: Partial<UploadJob>): Promise<UploadJob | undefined>;
  getAllUploadJobs(): Promise<UploadJob[]>;
}

export class MemStorage implements IStorage {
  private uploadJobs: Map<string, UploadJob>;

  constructor() {
    this.uploadJobs = new Map();
  }

  async getUploadJob(id: string): Promise<UploadJob | undefined> {
    return this.uploadJobs.get(id);
  }

  async createUploadJob(insertJob: InsertUploadJob): Promise<UploadJob> {
    const id = randomUUID();
    const now = new Date();
    const job: UploadJob = {
      ...insertJob,
      id,
      status: insertJob.status || "uploading",
      progress: insertJob.progress ?? 0,
      error: insertJob.error ?? null,
      results: insertJob.results ?? null,
      createdAt: now,
      updatedAt: now,
    };
    this.uploadJobs.set(id, job);
    return job;
  }

  async updateUploadJob(id: string, updates: Partial<UploadJob>): Promise<UploadJob | undefined> {
    const existingJob = this.uploadJobs.get(id);
    if (!existingJob) {
      return undefined;
    }
    
    const updatedJob: UploadJob = {
      ...existingJob,
      ...updates,
      updatedAt: new Date(),
    };
    
    this.uploadJobs.set(id, updatedJob);
    return updatedJob;
  }

  async getAllUploadJobs(): Promise<UploadJob[]> {
    return Array.from(this.uploadJobs.values()).sort(
      (a, b) => b.createdAt.getTime() - a.createdAt.getTime()
    );
  }
}

export const storage = new MemStorage();
