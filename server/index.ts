import express, { type Request, Response, NextFunction } from "express";
import path from "path";
import { registerRoutes } from "./routes";
import { registerImageRoutes } from "./routes/image-routes";
import { registerVideoRoutes } from "./routes/video-routes";
import { registerOptimizeRoutes } from "./routes/optimize-routes";
import { setupCleanupRoutes } from "./routes/cleanup-routes";
import { setupVite, serveStatic, log } from "./vite";

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

app.use((req, res, next) => {
  const start = Date.now();
  const path = req.path;
  let capturedJsonResponse: Record<string, any> | undefined = undefined;

  const originalResJson = res.json;
  res.json = function (bodyJson, ...args) {
    capturedJsonResponse = bodyJson;
    return originalResJson.apply(res, [bodyJson, ...args]);
  };

  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path.startsWith("/api")) {
      let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
      if (capturedJsonResponse) {
        logLine += ` :: ${JSON.stringify(capturedJsonResponse)}`;
      }

      if (logLine.length > 80) {
        logLine = logLine.slice(0, 79) + "…";
      }

      log(logLine);
    }
  });

  next();
});

(async () => {
  // Register new tool routes first
  registerImageRoutes(app);
  registerVideoRoutes(app);
  registerOptimizeRoutes(app);
  setupCleanupRoutes(app);

  // Then register main routes (which includes template serving)
  const server = await registerRoutes(app);

  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";

    res.status(status).json({ message });
    throw err;
  });

  // Serve the React app - use a simple static approach for Node.js 16 compatibility
  if (app.get("env") === "development") {
    // Serve our custom HTML file for the root route
    app.get("/", (req, res) => {
      res.sendFile(path.resolve(process.cwd(), "client", "simple.html"));
    });

    // Serve static files for other assets
    app.use(express.static("client"));

    // Catch-all for other routes
    app.get("*", (req, res) => {
      if (req.path.startsWith("/api")) {
        return res.status(404).json({ message: "API endpoint not found" });
      }
      res.sendFile(path.resolve(process.cwd(), "client", "simple.html"));
    });
  } else {
    serveStatic(app);
  }

  // ALWAYS serve the app on the port specified in the environment variable PORT
  // Other ports are firewalled. Default to 3000 if not specified.
  // this serves both the API and the client.
  // It is the only port that is not firewalled.
  const port = parseInt(process.env.PORT || '3000', 10);
  server.listen(port, "127.0.0.1", () => {
    log(`serving on port ${port}`);
  });

})();
