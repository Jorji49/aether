/**
 * Aether — Brain Client
 * HTTP client for the local Python Brain (FastAPI + Ollama).
 * Health checks use separate connections and never interfere with active requests.
 */

import * as http from "http";

export interface PromptResponse {
  prompt: string;
  context_summary: string;
  model_used: string;
  generation_time_ms: number;
  agent_used: string;
  quality_score: number;
  quality_grade: string;
  security_verdict: string;
  prompt_fingerprint: string;
}

export interface AgentInfo {
  id: string;
  name: string;
}

export interface OllamaModel {
  name: string;
  size_mb: number;
}

export interface ModelsResponse {
  models: OllamaModel[];
  current: string;
  error?: string;
}

export interface CatalogModel {
  name: string;
  desc: string;
  size: string;
  installed: boolean;
}

export interface CatalogResponse {
  catalog: CatalogModel[];
}

export class BrainClient {
  private _baseUrl: string;
  /** Only tracks the main vibe request (for abort). */
  private _vibeRequest: http.ClientRequest | null = null;

  private static readonly TIMEOUT_MS = 300_000;
  private static readonly HEALTH_TIMEOUT_MS = 2_000;

  constructor(baseUrl: string) {
    this._baseUrl = baseUrl.replace(/\/+$/, "");
  }

  /**
   * Health check with port discovery.
   * If the configured port fails, tries ports 8420-8429 to find the Brain.
   */
  public async healthCheck(): Promise<boolean> {
    try {
      const res = await this._fire<{ status: string }>("GET", "/health", undefined, BrainClient.HEALTH_TIMEOUT_MS);
      return res.status === "ok";
    } catch {
      // Port discovery: Brain may have started on an alternate port
      const base = new URL(this._baseUrl);
      const basePort = parseInt(base.port || "8420", 10);
      for (let p = basePort; p < basePort + 10; p++) {
        if (p === basePort) { continue; } // already tried
        const tryUrl = `${base.protocol}//${base.hostname}:${p}`;
        try {
          const res = await this._fire<{ status: string }>("GET", "/health", undefined, BrainClient.HEALTH_TIMEOUT_MS, tryUrl);
          if (res.status === "ok") {
            this._baseUrl = tryUrl;
            return true;
          }
        } catch { /* try next */ }
      }
      return false;
    }
  }

  public async sendVibe(vibe: string, workspacePath: string, agent: string = "auto"): Promise<PromptResponse> {
    return this._fetchTracked<PromptResponse>("POST", "/vibe", { vibe, workspace_path: workspacePath, agent });
  }

  public async listAgents(): Promise<{ agents: AgentInfo[] }> {
    return this._fire<{ agents: AgentInfo[] }>("GET", "/agents", undefined, 5_000);
  }

  public async listModels(): Promise<ModelsResponse> {
    return this._fire<ModelsResponse>("GET", "/models", undefined, 10_000);
  }

  public async setModel(model: string): Promise<{ status: string; model: string }> {
    return this._fire("POST", "/model", { model }, 5_000);
  }

  public async catalogModels(): Promise<CatalogResponse> {
    return this._fire<CatalogResponse>("GET", "/models/available", undefined, 15_000);
  }

  /**
   * Pull (download) a model from Ollama with SSE progress events.
   * Calls onProgress with percentage (0-100) during download.
   * Returns final status when complete.
   */
  public async pullModel(
    model: string,
    onProgress?: (pct: number, status: string) => void
  ): Promise<{ status: string; model?: string; message?: string }> {
    return new Promise((resolve, reject) => {
      const url = new URL(this._baseUrl + "/models/pull");
      const payload = JSON.stringify({ model });

      const options: http.RequestOptions = {
        hostname: url.hostname,
        port: url.port || 8420,
        path: url.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          "Content-Length": Buffer.byteLength(payload).toString(),
        },
        timeout: 600_000,
      };

      const req = http.request(options, (res) => {
        let lastStatus = "";
        let buffer = "";

        res.on("data", (chunk: Buffer) => {
          buffer += chunk.toString();
          // Parse SSE lines
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";
          for (const block of lines) {
            const line = block.trim();
            if (!line.startsWith("data: ")) { continue; }
            try {
              const data = JSON.parse(line.slice(6));
              lastStatus = data.status || "";
              if (onProgress && typeof data.pct === "number") {
                onProgress(data.pct, lastStatus);
              }
            } catch { /* ignore parse errors */ }
          }
        });

        res.on("end", () => {
          if (lastStatus === "done" || lastStatus === "success") {
            resolve({ status: "ok", model });
          } else if (lastStatus === "error") {
            resolve({ status: "error", message: "Pull failed" });
          } else {
            resolve({ status: "ok", model });
          }
        });
      });

      req.on("error", (err) => reject(err));
      req.on("timeout", () => { req.destroy(); reject(new Error("Pull timeout")); });
      req.write(payload);
      req.end();
    });
  }

  /** Abort the active vibe request only. */
  public abort(): void {
    if (this._vibeRequest) {
      this._vibeRequest.destroy();
      this._vibeRequest = null;
    }
  }

  /**
   * Tracked fetch — used for vibe requests only.
   * Stored in _vibeRequest so abort() can cancel it.
   */
  private _fetchTracked<T>(method: string, path: string, body?: unknown): Promise<T> {
    return new Promise((resolve, reject) => {
      const req = this._makeRequest<T>(method, path, body, BrainClient.TIMEOUT_MS, resolve, reject);
      this._vibeRequest = req;
    });
  }

  /**
   * Fire-and-forget fetch — used for health checks, model ops, etc.
   * Does NOT touch _vibeRequest, so it never interferes with ongoing vibes.
   */
  private _fire<T>(method: string, path: string, body?: unknown, timeoutMs: number = BrainClient.TIMEOUT_MS, baseOverride?: string): Promise<T> {
    return new Promise((resolve, reject) => {
      this._makeRequest<T>(method, path, body, timeoutMs, resolve, reject, baseOverride);
    });
  }

  private _makeRequest<T>(
    method: string,
    path: string,
    body: unknown | undefined,
    timeoutMs: number,
    resolve: (value: T) => void,
    reject: (reason: Error) => void,
    baseOverride?: string
  ): http.ClientRequest {
    const url = new URL((baseOverride || this._baseUrl) + path);
    const payload = body ? JSON.stringify(body) : undefined;

    const options: http.RequestOptions = {
      hostname: url.hostname,
      port: url.port || 8420,
      path: url.pathname,
      method,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(payload ? { "Content-Length": Buffer.byteLength(payload).toString() } : {}),
      },
      timeout: timeoutMs,
    };

    const req = http.request(options, (res) => {
      let data = "";
      res.on("data", (chunk: string) => (data += chunk));
      res.on("end", () => {
        if (this._vibeRequest === req) { this._vibeRequest = null; }
        const status = res.statusCode ?? 0;
        if (status >= 400) {
          let detail = data.slice(0, 300);
          try { const p = JSON.parse(data); if (p.detail) { detail = p.detail; } } catch { /* */ }
          reject(new Error(`Brain HTTP ${status}: ${detail}`));
          return;
        }
        try { resolve(JSON.parse(data) as T); } catch { reject(new Error(`Invalid JSON: ${data.slice(0, 200)}`)); }
      });
    });

    req.on("error", (err) => {
      if (this._vibeRequest === req) { this._vibeRequest = null; }
      reject(err);
    });
    req.on("timeout", () => {
      if (this._vibeRequest === req) { this._vibeRequest = null; }
      req.destroy();
      reject(new Error(`Timeout (${Math.round(timeoutMs / 1000)}s)`));
    });

    if (payload) { req.write(payload); }
    req.end();
    return req;
  }
}
