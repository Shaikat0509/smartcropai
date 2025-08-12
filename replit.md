# Overview

MediaResize AI is a full-stack web application that uses AI to automatically resize and optimize media files for multiple social media platforms. Users can upload images or videos, select target platforms (Instagram, Facebook, TikTok, etc.), and receive optimized versions formatted for each platform's specific requirements. The application handles the entire workflow from upload to processing to download, with real-time status updates throughout the process.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **React + TypeScript**: Modern React application with TypeScript for type safety
- **Vite**: Build tool and development server for fast development experience
- **Wouter**: Lightweight routing library for client-side navigation
- **TanStack Query**: Data fetching, caching, and synchronization with the backend
- **Tailwind CSS + shadcn/ui**: Utility-first CSS framework with pre-built component library
- **React Hook Form + Zod**: Form handling with schema validation

## Backend Architecture
- **Express.js**: Node.js web server framework handling API routes and middleware
- **TypeScript**: End-to-end type safety with shared schema definitions
- **File Upload System**: Multer middleware for handling multipart file uploads with size limits (500MB)
- **Image Processing**: Sharp library for image manipulation and optimization
- **AI Integration**: OpenAI GPT-4o for intelligent content analysis and optimization decisions
- **RESTful API**: Clean API design with proper error handling and logging

## Data Storage
- **PostgreSQL**: Primary database using Neon serverless PostgreSQL
- **Drizzle ORM**: Type-safe database operations with schema-first approach
- **In-Memory Fallback**: MemStorage class provides fallback storage for development
- **File System**: Local file storage for uploaded and processed media files
- **Session Management**: PostgreSQL-backed session storage with connect-pg-simple

## External Dependencies
- **Neon Database**: Serverless PostgreSQL hosting for production data storage
- **OpenAI API**: GPT-4o model integration for AI-powered media optimization
- **Sharp**: High-performance image processing library for resizing and format conversion
- **Multer**: Express middleware for handling file uploads
- **React Dropzone**: File drag-and-drop interface component
- **Radix UI**: Accessible component primitives for the UI system
- **shadcn/ui**: Pre-built component library built on Radix UI primitives