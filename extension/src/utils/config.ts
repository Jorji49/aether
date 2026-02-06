/**
 * Aether — Configuration Utilities
 *
 * Typed accessors for `aether.*` settings.
 * 100% local mode — no external API keys needed.
 *
 * @module config
 */

import * as vscode from "vscode";

const SECTION = "aether";

export function getConfig<T>(key: string, fallback: T): T {
  return vscode.workspace.getConfiguration(SECTION).get<T>(key, fallback);
}

export const AetherConfig = {
  get brainServerUrl(): string {
    return getConfig("brainServerUrl", "http://127.0.0.1:8420");
  },

  get ollamaModel(): string {
    return getConfig("ollamaModel", "gemma2:2b");
  },

  get maxContextFiles(): number {
    return getConfig("maxContextFiles", 30);
  },

  get autoSendToAgent(): boolean {
    return getConfig("autoSendToAgent", true);
  },
} as const;
