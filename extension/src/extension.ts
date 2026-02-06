/**
 * Aether — Main Extension Entry Point
 *
 * Multi-IDE support: Cursor, Claude Code, Windsurf/Antigravity, GitHub Copilot.
 * Resilient health check with 3-failure threshold.
 */

import * as vscode from "vscode";
import { SidebarProvider } from "./providers/SidebarProvider";
import { BrainClient } from "./services/BrainClient";

let brainClient: BrainClient;

export function activate(context: vscode.ExtensionContext): void {
  const config = vscode.workspace.getConfiguration("aether");
  const brainUrl = config.get<string>("brainServerUrl", "http://127.0.0.1:8420");

  brainClient = new BrainClient(brainUrl);
  const sidebarProvider = new SidebarProvider(context.extensionUri, brainClient, context);

  // ── Register Sidebar ──────────────────────────────────────────────
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      "aether.vibePanel",
      sidebarProvider,
      { webviewOptions: { retainContextWhenHidden: true } }
    )
  );

  // ── Commands ──────────────────────────────────────────────────────
  context.subscriptions.push(
    vscode.commands.registerCommand("aether.sendVibe", async () => {
      const input = await vscode.window.showInputBox({
        prompt: "Enter your vibe...",
        placeHolder: "e.g. login sayfası yap, dark mode ekle",
      });
      if (input) { await sidebarProvider.handleVibe(input); }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("aether.startBrain", () => {
      const terminal = vscode.window.createTerminal("Aether Brain");
      terminal.show();
      terminal.sendText("cd brain && python sslm_engine.py");
      vscode.window.showInformationMessage("Aether Brain starting on :8420...");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("aether.sendToAgent", async (prompt: string) => {
      await sendPromptToAgent(prompt);
    })
  );

  // ── Resilient Health Check ────────────────────────────────────────
  // Requires 3 consecutive failures before showing offline.
  // Recovers immediately on first success.
  let failCount = 0;
  let wasOnline = false;
  const MAX_FAILS = 3;

  async function doHealthCheck(): Promise<void> {
    const ok = await brainClient.healthCheck();
    if (ok) {
      failCount = 0;
      if (!wasOnline) {
        wasOnline = true;
        sidebarProvider.updateBrainStatus(true);
      }
    } else {
      failCount++;
      if (failCount >= MAX_FAILS && wasOnline) {
        wasOnline = false;
        sidebarProvider.updateBrainStatus(false);
      }
    }
  }

  // Initial check
  doHealthCheck().then(() => {
    if (!wasOnline) {
      sidebarProvider.updateBrainStatus(false);
      vscode.window.showWarningMessage("Aether Brain offline. Run 'Aether: Start Brain Server'.");
    }
  });

  // Periodic check — every 10 seconds
  const healthInterval = setInterval(doHealthCheck, 10_000);
  context.subscriptions.push({ dispose: () => clearInterval(healthInterval) });

  console.log("[Aether] Activated — 100% local mode.");
}

async function sendPromptToAgent(prompt: string): Promise<void> {
  await vscode.env.clipboard.writeText(prompt);

  // Detect which IDE we're running in and use the best strategy
  const ide = await detectIDE();

  try {
    switch (ide) {
      case "cursor":
        await sendToCursor(prompt);
        return;
      case "windsurf":
        await sendToWindsurf(prompt);
        return;
      case "claude-code":
        await sendToClaudeCode(prompt);
        return;
      case "copilot":
        await sendToCopilot(prompt);
        return;
      default:
        await sendToGenericChat(prompt);
        return;
    }
  } catch {
    // All IDE-specific strategies failed, use clipboard fallback
    vscode.window.showInformationMessage(
      `Prompt copied to clipboard! Paste it in your AI agent. (Detected IDE: ${ide})`
    );
  }
}

/**
 * Detect which AI IDE/editor we're running in.
 * Checks appName first, then probes for IDE-specific commands.
 */
async function detectIDE(): Promise<"cursor" | "windsurf" | "claude-code" | "copilot" | "vscode"> {
  const appName = vscode.env.appName.toLowerCase();

  // Direct name detection
  if (appName.includes("cursor")) { return "cursor"; }
  if (appName.includes("windsurf") || appName.includes("codeium") || appName.includes("antigravity")) { return "windsurf"; }
  if (appName.includes("claude")) { return "claude-code"; }

  // Probe for IDE-specific commands
  const commands = await vscode.commands.getCommands(true);
  const cmdSet = new Set(commands);

  if (cmdSet.has("composerMode.agent") || cmdSet.has("cursor.newComposer")) { return "cursor"; }
  if (cmdSet.has("codeium.openChat") || cmdSet.has("windsurf.openChat")) { return "windsurf"; }
  if (cmdSet.has("claude.newConversation") || cmdSet.has("claudeCode.startTask")) { return "claude-code"; }
  if (cmdSet.has("github.copilot.chat.open") || cmdSet.has("workbench.action.chat.open")) { return "copilot"; }

  return "vscode";
}

async function sendToCursor(prompt: string): Promise<void> {
  // Cursor: Open composer in agent mode and paste
  try {
    await vscode.commands.executeCommand("composerMode.agent");
    await delay(300);
    await vscode.commands.executeCommand("editor.action.clipboardPasteAction");
  } catch {
    // Fallback: Try Cursor's newer command API
    try {
      await vscode.commands.executeCommand("cursor.newComposer", prompt);
    } catch {
      await vscode.commands.executeCommand("workbench.action.chat.open", { query: prompt });
    }
  }
}

async function sendToWindsurf(prompt: string): Promise<void> {
  // Windsurf/Antigravity/Codeium: Open chat panel and paste
  try {
    await vscode.commands.executeCommand("codeium.openChat");
    await delay(400);
    await vscode.commands.executeCommand("editor.action.clipboardPasteAction");
  } catch {
    try {
      await vscode.commands.executeCommand("windsurf.openChat");
      await delay(400);
      await vscode.commands.executeCommand("editor.action.clipboardPasteAction");
    } catch {
      await vscode.commands.executeCommand("workbench.action.chat.open", { query: prompt });
    }
  }
}

async function sendToClaudeCode(prompt: string): Promise<void> {
  // Claude Code (Anthropic's IDE): Use task/conversation API
  try {
    await vscode.commands.executeCommand("claude.newConversation", prompt);
  } catch {
    try {
      await vscode.commands.executeCommand("claudeCode.startTask", prompt);
    } catch {
      // Claude Code may also support standard VS Code chat
      await vscode.commands.executeCommand("workbench.action.chat.open", { query: prompt });
    }
  }
}

async function sendToCopilot(prompt: string): Promise<void> {
  // GitHub Copilot Chat (VS Code native)
  try {
    await vscode.commands.executeCommand("workbench.action.chat.open", { query: prompt });
  } catch {
    try {
      await vscode.commands.executeCommand("github.copilot.chat.open", { query: prompt });
    } catch {
      throw new Error("Copilot chat not available");
    }
  }
}

async function sendToGenericChat(prompt: string): Promise<void> {
  // Generic fallback: try any available chat panel
  try {
    await vscode.commands.executeCommand("workbench.action.chat.open", { query: prompt });
  } catch {
    vscode.window.showInformationMessage("Prompt copied to clipboard! Paste it in your AI agent.");
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export function deactivate(): void {
  brainClient?.abort();
  console.log("[Aether] Deactivated.");
}
