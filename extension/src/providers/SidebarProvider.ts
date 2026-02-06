/**
 * Aether — Sidebar Provider (Production v2.0)
 * Ollama-style UI with custom agent selector panel.
 * All event handlers use delegation — fully CSP-compliant.
 */

import * as vscode from "vscode";
import { BrainClient, PromptResponse } from "../services/BrainClient";

export class SidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "aether.vibePanel";
  private _view?: vscode.WebviewView;
  private _selectedAgent = "auto";   // agent id
  private _selectedFamily = "auto";  // family key for brain

  constructor(
    private readonly _extUri: vscode.Uri,
    private readonly _brain: BrainClient,
    private readonly _ctx: vscode.ExtensionContext
  ) {
    this._selectedAgent = this._ctx.globalState.get<string>("aether.agent", "auto");
    this._selectedFamily = this._ctx.globalState.get<string>("aether.family", "auto");
  }

  public resolveWebviewView(view: vscode.WebviewView): void {
    this._view = view;
    view.webview.options = { enableScripts: true, localResourceRoots: [this._extUri] };
    view.webview.html = this._html(view.webview);

    const setupDone = this._ctx.globalState.get<boolean>("aether.setupDone", false);
    this._brain.healthCheck().then(ok => {
      this._post({ command: "status", online: ok });
      this._post({ command: "setAgent", agentId: this._selectedAgent, family: this._selectedFamily });
      if (!setupDone || !ok) {
        this._post({ command: "showSetup" });
        if (ok) { this._loadAll(); }
      }
    });

    const saved = this._ctx.globalState.get<string[]>("aether.h", []);
    if (saved.length) { this._post({ command: "restore", h: saved }); }

    view.webview.onDidReceiveMessage(async (m) => {
      switch (m.command) {
        case "vibe": await this.handleVibe(m.text); break;
        case "stop": this._brain.abort(); this._post({ command: "stopped" }); break;
        case "copy":
          await vscode.env.clipboard.writeText(m.prompt);
          this._post({ command: "copied" });
          break;
        case "agent":
          await vscode.commands.executeCommand("aether.sendToAgent", m.prompt);
          this._post({ command: "agentSent" });
          break;
        case "save": await this._ctx.globalState.update("aether.h", m.h); break;
        case "settings": vscode.commands.executeCommand("workbench.action.openSettings", "aether"); break;
        case "loadModels": await this._loadAll(); break;
        case "selectModel": await this._selectModel(m.model); break;
        case "pullModel": await this._pullModel(m.model); break;
        case "finishSetup":
          await this._ctx.globalState.update("aether.setupDone", true);
          break;
        case "openSetup":
          this._post({ command: "showSetup" });
          this._loadAll();
          break;
        case "selectAgent":
          this._selectedAgent = m.agentId || "auto";
          this._selectedFamily = m.family || "auto";
          await this._ctx.globalState.update("aether.agent", this._selectedAgent);
          await this._ctx.globalState.update("aether.family", this._selectedFamily);
          break;
        case "startBrain":
          await vscode.commands.executeCommand("aether.startBrain");
          break;
      }
    });
  }

  public updateBrainStatus(online: boolean, starting: boolean = false): void {
    this._post({ command: "status", online, starting });
  }

  public async handleVibe(vibe: string): Promise<void> {
    const ws = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? "";
    this._post({ command: "loading", on: true });
    try {
      const r: PromptResponse = await this._brain.sendVibe(vibe, ws, this._selectedFamily);
      this._post({
        command: "result",
        prompt: r.prompt,
        ms: r.generation_time_ms,
        model: r.model_used,
        agent: r.agent_used,
        quality: r.quality_score ?? 0,
        grade: r.quality_grade ?? "",
        security: r.security_verdict ?? "PASS",
      });
      const autoSend = vscode.workspace.getConfiguration("aether").get<boolean>("autoSendToAgent", false);
      if (autoSend) {
        await vscode.commands.executeCommand("aether.sendToAgent", r.prompt);
      }
    } catch (e: unknown) {
      this._post({ command: "err", msg: e instanceof Error ? e.message : String(e) });
    } finally {
      this._post({ command: "loading", on: false });
    }
  }

  // Static catalog — used as fallback when Brain is offline
  private static readonly FALLBACK_CATALOG = [
    { name: "gemma3:4b", desc: "\u2B50 Best Pick \u2014 Great quality/speed balance.", size: "3.3 GB", installed: false },
    { name: "gemma2:2b", desc: "\u26A1 Fast \u2014 Quick prompt generation, low RAM.", size: "1.6 GB", installed: false },
    { name: "gemma3:1b", desc: "\u26A1 Ultra fast \u2014 Minimal RAM. Quick iterations.", size: "815 MB", installed: false },
    { name: "qwen2.5:1.5b", desc: "Efficient multilingual. Turkish/English.", size: "986 MB", installed: false },
    { name: "llama3.2:3b", desc: "Good speed/quality balance.", size: "2.0 GB", installed: false },
    { name: "llama3.2:1b", desc: "Tiny, instant responses. Simple prompts.", size: "1.3 GB", installed: false },
    { name: "codegemma:2b", desc: "Code specialist. Tech-aware prompts.", size: "1.6 GB", installed: false },
    { name: "deepseek-r1:1.5b", desc: "Reasoning-focused. Logic-heavy prompts.", size: "1.1 GB", installed: false },
    { name: "gemma2", desc: "Strong 7B. High quality, moderate speed.", size: "5.4 GB", installed: false },
    { name: "phi4", desc: "Best reasoning. Top quality, needs 12GB+ RAM.", size: "9.1 GB", installed: false },
    { name: "llama3.1:8b", desc: "Powerful 8B. Excellent quality, needs 8GB+ RAM.", size: "4.7 GB", installed: false },
    { name: "mistral", desc: "Versatile 7B. Reliable quality.", size: "4.1 GB", installed: false },
    { name: "qwen2.5:7b", desc: "Strong multilingual 7B. Non-English prompts.", size: "4.7 GB", installed: false },
    { name: "deepseek-r1:7b", desc: "Advanced reasoning. Complex architectures.", size: "4.7 GB", installed: false },
    { name: "codellama:7b", desc: "Code specialist 7B. Deep understanding.", size: "3.8 GB", installed: false },
  ];

  private async _loadAll(): Promise<void> {
    try {
      const [installed, catalog] = await Promise.all([
        this._brain.listModels().catch(() => ({ models: [], current: "" })),
        this._brain.catalogModels().catch(() => ({ catalog: [] as { name: string; desc: string; size: string; installed: boolean }[] })),
      ]);
      const cat = catalog.catalog?.length ? catalog.catalog : SidebarProvider.FALLBACK_CATALOG;
      this._post({ command: "allModels", installed: installed.models, current: installed.current, catalog: cat });
    } catch {
      this._post({ command: "allModels", installed: [], current: "", catalog: SidebarProvider.FALLBACK_CATALOG });
    }
  }

  private async _selectModel(model: string): Promise<void> {
    try {
      await this._brain.setModel(model);
      await vscode.workspace.getConfiguration("aether").update("ollamaModel", model, vscode.ConfigurationTarget.Global);
      this._post({ command: "modelSet", model });
    } catch (e: unknown) {
      this._post({ command: "err", msg: e instanceof Error ? e.message : String(e) });
    }
  }

  private async _pullModel(model: string): Promise<void> {
    this._post({ command: "pullStart", model });
    try {
      const res = await this._brain.pullModel(model, (pct, status) => {
        this._post({ command: "pullProgress", model, pct, status });
      });
      if (res.status === "ok") {
        this._post({ command: "pullDone", model });
        this._loadAll();
      } else {
        this._post({ command: "pullFail", model, msg: res.message ?? "Unknown error" });
      }
    } catch (e: unknown) {
      this._post({ command: "pullFail", model, msg: e instanceof Error ? e.message : String(e) });
    }
  }

  private _post(m: Record<string, unknown>): void { this._view?.webview.postMessage(m); }

  private static readonly LLAMA = `<svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M35 85V55C35 40 40 30 50 25C60 30 65 40 65 55V85" stroke="currentColor" stroke-width="3" fill="none"/><path d="M39 35V15C39 10 42 8 44 12L43 30" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><path d="M61 35V15C61 10 58 8 56 12L57 30" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><circle cx="43" cy="45" r="3.5" fill="currentColor"/><circle cx="57" cy="45" r="3.5" fill="currentColor"/><ellipse cx="50" cy="58" rx="5" ry="3.5" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="48" cy="57" r="1" fill="currentColor"/><circle cx="52" cy="57" r="1" fill="currentColor"/><path d="M47 63Q50 66 53 63" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/></svg>`;

  private _html(wv: vscode.Webview): string {
    const n = Array.from({ length: 32 }, () => "abcdefghijklmnopqrstuvwxyz0123456789"[Math.random() * 36 | 0]).join("");
    const L = SidebarProvider.LLAMA;
    const L20 = L.replace('viewBox=', 'style="width:20px;height:20px" viewBox=');
    const L40 = L.replace('viewBox=', 'style="width:40px;height:40px" viewBox=');
    const L56 = L.replace('viewBox=', 'style="width:56px;height:56px" viewBox=');

    return /*html*/ `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${wv.cspSource} 'unsafe-inline'; script-src 'nonce-${n}';">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#000;--s1:#0a0a0a;--s2:#111;--s3:#1a1a1a;--border:#1a1a1a;--border2:#2a2a2a;--t:#fff;--t2:#b0b0b0;--t3:#666;--t4:#444;--ok:#22c55e;--err:#ef4444;--blue:#3b82f6;--r:10px;--f:-apple-system,'Segoe UI',system-ui,sans-serif;--m:'SF Mono','Cascadia Code','Fira Code',Consolas,monospace}
html,body{height:100%;overflow:hidden}
body{font-family:var(--f);background:var(--bg);color:var(--t);display:flex;flex-direction:column;font-size:13px;-webkit-font-smoothing:antialiased}

/* ── Header ─────────────────────────── */
.hdr{padding:12px 16px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border)}
.hdr-logo{display:flex;align-items:center;gap:7px;flex:1}
.hdr-logo span{font-size:14px;font-weight:700;letter-spacing:-.3px}
.hdr-st{display:flex;align-items:center;gap:5px;font-size:10px;color:var(--t3);font-weight:500}
.dot{width:6px;height:6px;border-radius:50%;transition:.3s}.dot.on{background:var(--ok)}.dot.off{background:var(--err)}
.ib{width:28px;height:28px;border-radius:8px;border:none;background:transparent;color:var(--t4);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.15s}
.ib:hover{background:var(--s2);color:var(--t)}
.ib svg{width:14px;height:14px}

/* ── Agent Selector ─────────────────── */
.aw{position:relative;z-index:100}
.ab{padding:8px 16px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border);cursor:pointer;transition:background .1s;user-select:none}
.ab:hover{background:var(--s1)}
.ab-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;transition:background .2s}
.ab-name{flex:1;font-size:11px;font-weight:600;color:var(--t2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ab-arrow{width:10px;height:10px;color:var(--t4);transition:transform .2s;flex-shrink:0}
.ab.open .ab-arrow{transform:rotate(180deg)}

.ap{position:absolute;top:100%;left:0;right:0;background:var(--s1);border:1px solid var(--border2);border-top:none;max-height:0;opacity:0;overflow:hidden;transition:max-height .2s ease,opacity .15s ease;box-shadow:0 12px 40px rgba(0,0,0,.6)}
.ap.open{max-height:65vh;opacity:1;overflow-y:auto}
.ap::-webkit-scrollbar{width:3px}.ap::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}

.ap-auto{padding:9px 14px;display:flex;align-items:center;gap:8px;cursor:pointer;transition:background .1s;border-bottom:1px solid var(--border)}
.ap-auto:hover{background:var(--s2)}
.ap-auto.sel{background:var(--s2)}
.ap-auto .ap-ck{width:14px;height:14px;border-radius:50%;border:1.5px solid var(--border2);display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.15s}
.ap-auto.sel .ap-ck{border-color:var(--ok);background:var(--ok)}
.ap-auto.sel .ap-ck::after{content:'';width:5px;height:5px;border-radius:50%;background:#fff}
.ap-auto-n{font-size:11px;font-weight:500;flex:1;color:var(--t2)}

.ag-hdr{padding:10px 14px 5px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--t4);display:flex;align-items:center;gap:6px}
.ag-dot{width:5px;height:5px;border-radius:50%;flex-shrink:0}

.ag-i{padding:7px 14px 7px 22px;display:flex;align-items:center;gap:8px;cursor:pointer;transition:background .1s}
.ag-i:hover{background:var(--s2)}
.ag-i.sel{background:var(--s2)}
.ag-i-n{flex:1;font-size:11.5px;font-weight:500;color:var(--t2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ag-i-d{font-size:9px;color:var(--t4);flex-shrink:0;max-width:90px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ag-i-ck{width:13px;height:13px;border-radius:50%;border:1.5px solid var(--border2);display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.15s}
.ag-i.sel .ag-i-ck{border-color:var(--ok);background:var(--ok)}
.ag-i.sel .ag-i-ck::after{content:'';width:4.5px;height:4.5px;border-radius:50%;background:#fff}

.ag-sep{height:1px;background:var(--border);margin:4px 14px}

/* ── Views ──────────────────────────── */
.view{display:none;flex-direction:column;flex:1;overflow:hidden}.view.active{display:flex}

/* ── Setup ──────────────────────────── */
.setup{padding:24px 20px;overflow-y:auto;flex:1}
.setup::-webkit-scrollbar{width:3px}.setup::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.setup-logo{text-align:center;margin-bottom:16px}
.setup h2{font-size:18px;font-weight:700;text-align:center;margin-bottom:4px;letter-spacing:-.3px}
.setup .sub{font-size:12px;color:var(--t3);text-align:center;margin-bottom:20px;line-height:1.6}
.tabs{display:flex;gap:0;margin-bottom:14px;border:1px solid var(--border);border-radius:8px;overflow:hidden}
.tab{flex:1;padding:8px;font-size:11px;font-weight:600;text-align:center;cursor:pointer;background:var(--s1);color:var(--t3);border:none;transition:.15s}
.tab.active{background:var(--s2);color:var(--t)}
.tab:not(:last-child){border-right:1px solid var(--border)}
.tab-panel{display:none}.tab-panel.active{display:block}
.model-list{display:flex;flex-direction:column;gap:5px}
.mi{padding:10px 12px;background:var(--s1);border:1px solid var(--border);border-radius:var(--r);cursor:pointer;display:flex;align-items:center;gap:10px;transition:.15s}
.mi:hover{background:var(--s2);border-color:var(--border2)}
.mi.selected{border-color:var(--t3)}
.mi-info{flex:1;min-width:0}
.mi-name{font-size:12px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mi-desc{font-size:9px;color:var(--t3);margin-top:2px;line-height:1.4}
.mi-size{font-size:9px;color:var(--t4);font-family:var(--m);flex-shrink:0}
.mi-check{width:16px;height:16px;border-radius:50%;border:1.5px solid var(--border2);flex-shrink:0;display:flex;align-items:center;justify-content:center;transition:.15s}
.mi.selected .mi-check{border-color:var(--ok);background:var(--ok)}
.mi.selected .mi-check::after{content:'';width:6px;height:6px;border-radius:50%;background:#fff}
.mi-action{flex-shrink:0}
.dl-btn{padding:5px 10px;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--t2);font-size:9px;font-weight:600;cursor:pointer;transition:.15s;font-family:var(--f)}
.dl-btn:hover{background:var(--s2);border-color:var(--border2);color:var(--t)}
.dl-btn.pulling{color:var(--blue);border-color:rgba(59,130,246,.2);pointer-events:none;min-width:90px;text-align:center;position:relative;overflow:hidden}
.dl-btn.pulling .dl-bar{position:absolute;left:0;top:0;bottom:0;background:rgba(59,130,246,.12);transition:width .3s;border-radius:6px}
.dl-btn.pulling .dl-txt{position:relative;z-index:1}
.dl-btn.done{color:var(--ok);border-color:rgba(34,197,94,.15);pointer-events:none}
.dl-btn.fail{color:var(--err);border-color:rgba(239,68,68,.15)}
.setup-msg{text-align:center;padding:16px;color:var(--t3);font-size:12px}
.setup-btn{width:100%;padding:12px;border-radius:var(--r);border:none;background:var(--t);color:var(--bg);font-size:13px;font-weight:600;cursor:pointer;transition:.15s;margin-top:14px}
.setup-btn:hover{opacity:.85}
.setup-btn:disabled{opacity:.2;cursor:default}
.setup-tip{font-size:9px;color:var(--t4);text-align:center;margin-top:10px;line-height:1.6}

/* ── Feed / Chat ────────────────────── */
.feed{flex:1;overflow-y:auto;padding:0}.feed::-webkit-scrollbar{width:3px}.feed::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:10px;padding:40px 24px;text-align:center}
.empty h3{font-size:15px;font-weight:600;letter-spacing:-.2px}
.empty p{font-size:11px;line-height:1.7;color:var(--t3);max-width:230px}
.msg{padding:16px 18px;border-bottom:1px solid var(--border);animation:fi .15s ease}
@keyframes fi{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
.msg-u{background:var(--bg)}.msg-u .from{font-size:10px;font-weight:700;color:var(--t3);margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px}.msg-u .body{font-size:13px;line-height:1.6;color:var(--t2)}
.msg-a{background:var(--s1)}.msg-a .from{font-size:10px;font-weight:700;color:var(--t3);margin-bottom:8px;display:flex;justify-content:space-between;text-transform:uppercase;letter-spacing:.5px}.msg-a .from .time{font-weight:500;color:var(--t4);font-size:9px;text-transform:none;letter-spacing:0}

.po{background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:14px 16px;margin-bottom:10px;font-family:var(--m);font-size:11px;line-height:1.9;color:var(--t2);white-space:pre-wrap;word-break:break-word;max-height:400px;overflow-y:auto;user-select:text}
.po::-webkit-scrollbar{width:2px}.po::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.po .h{color:var(--t);font-weight:700}
.meta{display:flex;gap:5px;margin-bottom:10px;flex-wrap:wrap}
.tag{padding:2px 8px;border-radius:6px;font-size:9px;font-weight:500;color:var(--t3);background:var(--s3);font-family:var(--m)}
.acts{display:flex;gap:6px}
.btn{padding:7px 14px;border-radius:8px;font-size:11px;font-weight:600;cursor:pointer;transition:.15s;font-family:var(--f);border:none}
.btn-w{background:var(--t);color:var(--bg)}.btn-w:hover{opacity:.85}
.btn-o{background:transparent;color:var(--t2);border:1px solid var(--border)}.btn-o:hover{background:var(--s2);color:var(--t)}
.btn-ok{background:transparent;color:var(--ok);border:1px solid rgba(34,197,94,.15);pointer-events:none}
.qbadge{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:6px;font-size:9px;font-weight:600;font-family:var(--m)}
.qbadge.a{background:rgba(34,197,94,.12);color:#22c55e}
.qbadge.b{background:rgba(59,130,246,.12);color:#3b82f6}
.qbadge.c{background:rgba(234,179,8,.12);color:#eab308}
.qbadge.d{background:rgba(239,68,68,.12);color:#ef4444}
.sbadge{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:6px;font-size:9px;font-weight:600;font-family:var(--m)}
.sbadge.pass{background:rgba(34,197,94,.08);color:#22c55e}
.sbadge.warn{background:rgba(234,179,8,.12);color:#eab308}
.sbadge.fail{background:rgba(239,68,68,.12);color:#ef4444}
.msg-e{padding:14px 18px;border-bottom:1px solid var(--border)}
.msg-e .el{font-size:10px;font-weight:600;color:var(--err);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.msg-e .et{font-size:12px;color:var(--t3);line-height:1.5}

/* ── Loader ─────────────────────────── */
.loader{display:none;padding:16px 18px;align-items:center;gap:12px;border-bottom:1px solid var(--border);background:var(--s1)}
.loader.on{display:flex}
.spinner{width:16px;height:16px;border:2px solid var(--border2);border-top-color:var(--t2);border-radius:50%;animation:sp .6s linear infinite;flex-shrink:0}
@keyframes sp{to{transform:rotate(360deg)}}
.load-t{font-size:11px;color:var(--t2);font-weight:500}.load-s{font-size:9px;color:var(--t4);font-family:var(--m);margin-top:2px}
.stop{width:24px;height:24px;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--t3);cursor:pointer;display:flex;align-items:center;justify-content:center}
.stop:hover{background:var(--s2);color:var(--t)}.stop svg{width:10px;height:10px}

/* ── Input ──────────────────────────── */
.input-area{padding:12px 16px;border-top:1px solid var(--border);background:var(--bg)}
.input-wrap{display:flex;gap:8px;align-items:flex-end}
textarea{flex:1;background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:10px 14px;color:var(--t);font-size:13px;font-family:var(--f);resize:none;outline:none;min-height:40px;max-height:140px;line-height:1.5;transition:.15s}
textarea:focus{border-color:var(--border2)}textarea::placeholder{color:var(--t4)}textarea:disabled{opacity:.3}
.send{width:34px;height:34px;border-radius:50%;border:none;background:var(--t);color:var(--bg);cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.15s}
.send:hover:not(:disabled){opacity:.85}.send:disabled{opacity:.1;cursor:default}
.send svg{width:14px;height:14px}

/* ── Footer ─────────────────────────── */
.foot{padding:5px 16px 7px;font-size:9px;color:var(--t4);display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--border)}
.foot-model{font-family:var(--m);cursor:pointer;padding:2px 6px;border-radius:4px;transition:.15s}
.foot-model:hover{background:var(--s2);color:var(--t3)}

/* ── Offline Banner ─────────────────── */
.offline-banner{display:none;padding:16px 20px;background:linear-gradient(135deg,var(--s1),var(--s2));border-bottom:1px solid var(--border);text-align:center;animation:fi .2s ease}
.offline-banner.show{display:block}
.offline-banner .ob-icon{margin-bottom:8px;color:var(--t4)}
.offline-banner .ob-title{font-size:13px;font-weight:600;color:var(--t);margin-bottom:4px}
.offline-banner .ob-desc{font-size:11px;color:var(--t3);line-height:1.5;margin-bottom:12px}
.start-brain-btn{width:100%;padding:10px 16px;border-radius:var(--r);border:none;background:var(--ok);color:#000;font-size:12px;font-weight:700;cursor:pointer;transition:.15s;font-family:var(--f);display:flex;align-items:center;justify-content:center;gap:8px}
.start-brain-btn:hover{opacity:.85}
.start-brain-btn:disabled{opacity:.4;cursor:default}
.start-brain-btn.starting{background:var(--blue);color:#fff}
.start-brain-btn svg{width:14px;height:14px}
</style>
</head>
<body>

<!-- Header -->
<div class="hdr">
  <div class="hdr-logo">${L20}<span>Aether</span></div>
  <div class="hdr-st"><span class="dot off" id="D"></span><span id="SL">Offline</span></div>
  <button class="ib" id="bSet" title="Settings"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg></button>
  <button class="ib" id="bClr" title="Clear chat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg></button>
</div>

<!-- Agent Selector -->
<div class="aw" id="AW">
  <div class="ab" id="AB">
    <span class="ab-dot" id="abDot" style="background:#666"></span>
    <span class="ab-name" id="abName">Auto — Universal</span>
    <svg class="ab-arrow" viewBox="0 0 10 6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M1 1l4 4 4-4"/></svg>
  </div>
  <div class="ap" id="AP"></div>
</div>

<!-- Setup View -->
<div class="view" id="V_SETUP">
  <div class="setup">
    <div class="setup-logo">${L56}</div>
    <h2>Welcome to Aether</h2>
    <p class="sub">Local AI prompt optimizer powered by Ollama.<br/>Select a model below — smaller models are faster, larger models produce better prompts.</p>
    <div class="tabs">
      <button class="tab active" data-tab="installed">Installed</button>
      <button class="tab" data-tab="available">Available</button>
    </div>
    <div class="tab-panel active" id="P_INSTALLED">
      <div class="model-list" id="ML_INST"><div class="setup-msg">Loading...</div></div>
    </div>
    <div class="tab-panel" id="P_AVAILABLE">
      <div class="model-list" id="ML_AVAIL"><div class="setup-msg">Loading...</div></div>
    </div>
    <button class="setup-btn" id="setupDone" disabled>Get Started</button>
    <p class="setup-tip">Ollama must be running. Models are stored locally.</p>
  </div>
</div>

<!-- Offline Banner -->
<div class="offline-banner" id="OB">
  <div class="ob-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg></div>
  <div class="ob-title">Brain Server Offline</div>
  <div class="ob-desc">Aether Brain server is not running.<br/>Click below to start it.</div>
  <button class="start-brain-btn" id="bStartBrain">
    <svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
    <span id="bStartTxt">Start Brain Server</span>
  </button>
</div>

<!-- Chat View -->
<div class="view active" id="V_CHAT">
  <div class="feed" id="F">
    <div class="empty" id="E">
      ${L40}
      <h3>What do you want to build?</h3>
      <p>Describe your idea. Aether turns it into a perfect prompt for your AI agent.</p>
    </div>
  </div>
  <div class="loader" id="LDR">
    <div class="spinner"></div>
    <div style="flex:1"><div class="load-t">Generating prompt...</div><div class="load-s" id="LTM">0s</div></div>
    <button class="stop" id="bStop"><svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1"/></svg></button>
  </div>
  <div class="input-area">
    <div class="input-wrap">
      <textarea id="I" rows="1" placeholder="Message Aether..."></textarea>
      <button class="send" id="G"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg></button>
    </div>
  </div>
</div>

<div class="foot">
  <span>100% Local</span>
  <span class="foot-model" id="FM" title="Change model">ollama</span>
</div>

<script nonce="${n}">
(function(){
  var vs=acquireVsCodeApi();
  function $(id){return document.getElementById(id)}
  var F=$('F'),E=$('E'),I=$('I'),G=$('G'),LDR=$('LDR'),LTM=$('LTM'),D=$('D'),SL=$('SL'),FM=$('FM');
  var VS=$('V_SETUP'),VC=$('V_CHAT'),OB=$('OB');
  var AB=$('AB'),AP=$('AP'),AW=$('AW');
  var brainStarting=false;
  var busy=0,ti=null,t0=0,hist=[],selModel='';
  var curAgent='auto',curFamily='auto',panelOpen=false;

  /* ── Agent data (matches Cursor's model list exactly) ── */
  var AG=[
    {l:'Anthropic',c:'#cc785c',a:[
      {i:'claude-opus-4.6',n:'Claude Opus 4.6',d:'Best reasoning',f:'claude'},
      {i:'claude-opus-4.5',n:'Claude Opus 4.5',d:'Deep analysis',f:'claude'},
      {i:'claude-sonnet-4.5',n:'Claude Sonnet 4.5',d:'Fast & smart',f:'claude'},
      {i:'claude-sonnet-4',n:'Claude Sonnet 4',d:'Balanced',f:'claude'},
      {i:'claude-haiku-4.5',n:'Claude Haiku 4.5',d:'Ultra fast',f:'claude'}
    ]},
    {l:'OpenAI',c:'#10a37f',a:[
      {i:'gpt-5.2-codex',n:'GPT-5.2-Codex',d:'Latest code',f:'gpt-codex'},
      {i:'gpt-5.2',n:'GPT-5.2',d:'Latest general',f:'gpt'},
      {i:'gpt-5.1-codex-max',n:'GPT-5.1-Codex-Max',d:'Max performance',f:'gpt-codex'},
      {i:'gpt-5.1-codex',n:'GPT-5.1-Codex',d:'Code specialist',f:'gpt-codex'},
      {i:'gpt-5.1-codex-mini',n:'GPT-5.1-Codex-Mini',d:'Fast code',f:'gpt-codex'},
      {i:'gpt-5.1',n:'GPT-5.1',d:'Strong general',f:'gpt'},
      {i:'gpt-5-codex',n:'GPT-5-Codex',d:'Code focused',f:'gpt-codex'},
      {i:'gpt-5',n:'GPT-5',d:'General purpose',f:'gpt'},
      {i:'gpt-5-mini',n:'GPT-5 mini',d:'Lightweight',f:'gpt'},
      {i:'gpt-4o',n:'GPT-4o',d:'Multimodal',f:'gpt'},
      {i:'gpt-4.1',n:'GPT-4.1',d:'Stable',f:'gpt'}
    ]},
    {l:'Google',c:'#4285f4',a:[
      {i:'gemini-3-pro',n:'Gemini 3 Pro',d:'Most capable',f:'gemini'},
      {i:'gemini-3-flash',n:'Gemini 3 Flash',d:'Fast & efficient',f:'gemini'},
      {i:'gemini-2.5-pro',n:'Gemini 2.5 Pro',d:'Long context',f:'gemini'}
    ]},
    {l:'Other',c:'#a0a0a0',a:[
      {i:'grok-code-fast-1',n:'Grok Code Fast 1',d:'Speed optimized',f:'grok'},
      {i:'raptor-mini',n:'Raptor mini',d:'Preview',f:'auto'}
    ]}
  ];

  /* ── Agent panel rendering ── */
  function renderPanel(){
    var h='<div class="ap-auto'+(curAgent==='auto'?' sel':'')+'" data-aid="auto" data-fam="auto">';
    h+='<div class="ap-ck"></div><div class="ap-auto-n">Auto — Universal</div></div>';
    for(var gi=0;gi<AG.length;gi++){
      var g=AG[gi];
      if(gi>0)h+='<div class="ag-sep"></div>';
      h+='<div class="ag-hdr"><span class="ag-dot" style="background:'+g.c+'"></span>'+g.l+'</div>';
      for(var ai=0;ai<g.a.length;ai++){
        var a=g.a[ai];
        h+='<div class="ag-i'+(curAgent===a.i?' sel':'')+'" data-aid="'+escAttr(a.i)+'" data-fam="'+escAttr(a.f)+'">';
        h+='<div class="ag-i-ck"></div>';
        h+='<div class="ag-i-n">'+esc(a.n)+'</div>';
        h+='<div class="ag-i-d">'+esc(a.d)+'</div>';
        h+='</div>';
      }
    }
    AP.innerHTML=h;
  }

  function findAgent(id){
    if(id==='auto')return{n:'Auto — Universal',c:'#666',f:'auto'};
    for(var gi=0;gi<AG.length;gi++){
      var g=AG[gi];
      for(var ai=0;ai<g.a.length;ai++){
        if(g.a[ai].i===id)return{n:g.a[ai].n,c:g.c,f:g.a[ai].f};
      }
    }
    return{n:'Auto — Universal',c:'#666',f:'auto'};
  }

  function updateBar(){
    var info=findAgent(curAgent);
    $('abName').textContent=info.n;
    $('abDot').style.background=info.c;
  }

  function openPanel(){panelOpen=true;AB.classList.add('open');AP.classList.add('open');renderPanel()}
  function closePanel(){panelOpen=false;AB.classList.remove('open');AP.classList.remove('open')}

  AB.addEventListener('click',function(e){
    e.stopPropagation();
    if(panelOpen)closePanel();else openPanel();
  });

  AP.addEventListener('click',function(e){
    var item=e.target.closest('[data-aid]');
    if(!item)return;
    curAgent=item.getAttribute('data-aid');
    curFamily=item.getAttribute('data-fam');
    updateBar();closePanel();
    vs.postMessage({command:'selectAgent',agentId:curAgent,family:curFamily});
  });

  document.addEventListener('click',function(e){
    if(panelOpen&&!e.target.closest('.aw'))closePanel();
  });

  /* ── Tabs (setup) ── */
  document.querySelectorAll('.tab').forEach(function(t){
    t.addEventListener('click',function(){
      document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('active')});
      document.querySelectorAll('.tab-panel').forEach(function(x){x.classList.remove('active')});
      t.classList.add('active');
      $(t.dataset.tab==='installed'?'P_INSTALLED':'P_AVAILABLE').classList.add('active');
    });
  });

  /* ── Input & send ── */
  I.addEventListener('input',function(){I.style.height='auto';I.style.height=Math.min(I.scrollHeight,140)+'px'});
  I.addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();go()}});
  G.addEventListener('click',go);
  $('bStop').addEventListener('click',function(){vs.postMessage({command:'stop'})});
  $('bSet').addEventListener('click',function(){vs.postMessage({command:'settings'})});
  $('bStartBrain').addEventListener('click',function(){
    if(brainStarting)return;
    brainStarting=true;
    var btn=$('bStartBrain');
    btn.classList.add('starting');
    $('bStartTxt').textContent='Starting...';
    btn.disabled=true;
    vs.postMessage({command:'startBrain'});
  });
  $('bClr').addEventListener('click',function(){
    F.innerHTML='';F.appendChild(E);E.style.display='flex';hist=[];
    vs.postMessage({command:'save',h:[]});
  });
  FM.addEventListener('click',function(){vs.postMessage({command:'openSetup'})});
  $('setupDone').addEventListener('click',function(){
    if(!selModel)return;
    vs.postMessage({command:'selectModel',model:selModel});
    vs.postMessage({command:'finishSetup'});
    showView('chat');
  });

  function showView(v){VS.classList.toggle('active',v==='setup');VC.classList.toggle('active',v==='chat')}

  function go(){
    var t=I.value.trim();if(!t||busy)return;
    E.style.display='none';addU(t);lock();
    vs.postMessage({command:'vibe',text:t});
    I.value='';I.style.height='auto';
  }
  function lock(){busy=1;I.disabled=true;G.disabled=true;LDR.classList.add('on');t0=Date.now();ti=setInterval(function(){LTM.textContent=((Date.now()-t0)/1000|0)+'s'},300)}
  function unlock(){busy=0;I.disabled=false;G.disabled=false;LDR.classList.remove('on');if(ti){clearInterval(ti);ti=null}LTM.textContent='0s';I.focus()}
  function esc(s){var d=document.createElement('div');d.textContent=s||'';return d.innerHTML}
  function escAttr(s){return esc(s).replace(/"/g,'&quot;').replace(/'/g,'&#39;')}
  function sb(){requestAnimationFrame(function(){F.scrollTop=F.scrollHeight})}
  function hl(t){var h=esc(t);h=h.replace(/^(##? .+)$/gm,'<span class="h">$1</span>');return h}

  function addU(t){
    var d=document.createElement('div');d.className='msg msg-u';
    d.innerHTML='<div class="from">You</div><div class="body">'+esc(t)+'</div>';
    F.appendChild(d);sb();hist.push(JSON.stringify({r:'u',t:t}));save();
  }

  function addP(prompt,ms,model,agent,quality,grade,security){
    var d=document.createElement('div');d.className='msg msg-a';d.setAttribute('data-prompt',prompt);
    var now=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
    var info=findAgent(curAgent);
    var h='<div class="from"><span>Aether</span><span class="time">'+now+'</span></div>';
    h+='<div class="po">'+hl(prompt)+'</div>';
    h+='<div class="meta">';
    if(curAgent!=='auto')h+='<span class="tag">'+esc(info.n)+'</span>';
    if(model)h+='<span class="tag">'+esc(model)+'</span>';
    if(ms)h+='<span class="tag">'+(ms/1000).toFixed(1)+'s</span>';
    if(grade){var gc=grade.startsWith('A')?'a':grade==='B'?'b':grade==='C'?'c':'d';h+='<span class="qbadge '+gc+'">'+esc(grade)+' ('+Math.round(quality||0)+')</span>'}
    if(security&&security!=='PASS'){var sc=security==='WARN'?'warn':'fail';h+='<span class="sbadge '+sc+'">\u26a0 '+esc(security)+'</span>'}else if(security==='PASS'){h+='<span class="sbadge pass">\u2713 Secure</span>'}
    h+='</div><div class="acts">';
    h+='<button class="btn btn-w" data-action="agent">Send to Agent</button>';
    h+='<button class="btn btn-o" data-action="copy">Copy</button>';
    h+='</div>';
    d.innerHTML=h;F.appendChild(d);sb();
    hist.push(JSON.stringify({r:'p',t:prompt,ms:ms,m:model,a:curAgent,q:quality,g:grade,s:security}));save();
  }

  function addE(m){
    var d=document.createElement('div');d.className='msg-e';
    d.innerHTML='<div class="el">Error</div><div class="et">'+esc(m)+'</div>';
    F.appendChild(d);sb();
  }

  function save(){vs.postMessage({command:'save',h:hist.slice(-20)})}

  /* ── Event delegation: Copy / Send to Agent ── */
  F.addEventListener('click',function(e){
    var btn=e.target.closest('[data-action]');
    if(!btn)return;
    var msgEl=btn.closest('.msg-a');
    if(!msgEl)return;
    var prompt=msgEl.getAttribute('data-prompt');
    if(!prompt)return;
    var action=btn.getAttribute('data-action');
    if(action==='agent'){
      vs.postMessage({command:'agent',prompt:prompt});
      btn.textContent='\\u2713 Sent';btn.className='btn btn-ok';
    }else if(action==='copy'){
      vs.postMessage({command:'copy',prompt:prompt});
      var orig=btn.textContent;
      btn.textContent='\\u2713 Copied';btn.className='btn btn-ok';
      setTimeout(function(){btn.textContent=orig;btn.className='btn btn-o'},1500);
    }
  });

  /* ── Event delegation: Download models ── */
  $('ML_AVAIL').addEventListener('click',function(e){
    var btn=e.target.closest('[data-pull]');
    if(!btn)return;
    var mn=btn.getAttribute('data-pull');
    vs.postMessage({command:'pullModel',model:mn});
    btn.innerHTML='<span class="dl-bar" style="width:0%"></span><span class="dl-txt">0%</span>';
    btn.className='dl-btn pulling';
    btn.setAttribute('data-pulling',mn);
  });

  /* ── Model list rendering ── */
  function renderInstalled(models,current){
    var c=$('ML_INST');c.innerHTML='';
    if(!models.length){c.innerHTML='<div class="setup-msg">No models installed.<br/>Switch to <b>Available</b> tab to download.</div>';return}
    models.forEach(function(m){
      var el=document.createElement('div');el.className='mi'+(m.name===current?' selected':'');
      var sz=m.size_mb>1024?(m.size_mb/1024).toFixed(1)+' GB':m.size_mb+' MB';
      el.innerHTML='<div class="mi-info"><div class="mi-name">'+esc(m.name)+'</div></div><div class="mi-size">'+sz+'</div><div class="mi-check"></div>';
      el.addEventListener('click',function(){
        document.querySelectorAll('#ML_INST .mi').forEach(function(x){x.classList.remove('selected')});
        el.classList.add('selected');selModel=m.name;$('setupDone').disabled=false;
      });
      if(m.name===current){selModel=m.name;$('setupDone').disabled=false}
      c.appendChild(el);
    });
  }

  function renderCatalog(catalog){
    var c=$('ML_AVAIL');c.innerHTML='';
    if(!catalog||!catalog.length){c.innerHTML='<div class="setup-msg">Could not load model catalog.</div>';return}
    catalog.forEach(function(m){
      var el=document.createElement('div');el.className='mi';
      var act='';
      if(m.installed){act='<div class="mi-action"><span class="dl-btn done">Installed</span></div>'}
      else{act='<div class="mi-action"><button class="dl-btn" data-pull="'+escAttr(m.name)+'">Download</button></div>'}
      el.innerHTML='<div class="mi-info"><div class="mi-name">'+esc(m.name)+'</div><div class="mi-desc">'+esc(m.desc)+'</div></div><div class="mi-size">'+esc(m.size)+'</div>'+act;
      c.appendChild(el);
    });
  }

  /* ── Messages from extension ── */
  window.addEventListener('message',function(e){
    var m=e.data;
    if(m.command==='result'){addP(m.prompt,m.ms,m.model,m.agent,m.quality,m.grade,m.security);unlock()}
    else if(m.command==='err'){addE(m.msg);unlock()}
    else if(m.command==='stopped'){unlock()}
    else if(m.command==='loading'&&!m.on){unlock()}
    else if(m.command==='status'){
      D.className='dot '+(m.online?'on':'off');
      SL.textContent=m.online?'Connected':(m.starting?'Starting...':'Offline');
      if(m.online){
        OB.classList.remove('show');
        brainStarting=false;
        var btn=$('bStartBrain');
        btn.classList.remove('starting');
        btn.disabled=false;
        $('bStartTxt').textContent='Start Brain Server';
      } else if(!m.starting){
        OB.classList.add('show');
      }
    }
    else if(m.command==='showSetup'){showView('setup');vs.postMessage({command:'loadModels'})}
    else if(m.command==='allModels'){
      renderInstalled(m.installed||[],m.current||'');
      renderCatalog(m.catalog||[]);
      if(m.current)FM.textContent=m.current;
    }
    else if(m.command==='modelSet'){FM.textContent=m.model}
    else if(m.command==='setAgent'){
      curAgent=m.agentId||'auto';
      curFamily=m.family||'auto';
      updateBar();
    }
    else if(m.command==='pullProgress'){
      var pb=document.querySelector('[data-pulling="'+m.model+'"]');
      if(pb){
        var bar=pb.querySelector('.dl-bar');
        var txt=pb.querySelector('.dl-txt');
        if(bar)bar.style.width=m.pct+'%';
        if(txt)txt.textContent=m.pct+'%';
      }
    }
    else if(m.command==='pullDone'){
      document.querySelectorAll('.dl-btn.pulling').forEach(function(b){
        b.innerHTML='\\u2713 Done';b.className='dl-btn done';b.removeAttribute('data-pulling');
      });
    }
    else if(m.command==='pullFail'){
      document.querySelectorAll('.dl-btn.pulling').forEach(function(b){
        b.innerHTML='Failed';b.className='dl-btn fail';b.removeAttribute('data-pulling');
      });
    }
    else if(m.command==='restore'&&m.h){
      E.style.display='none';
      m.h.forEach(function(raw){
        try{var o=JSON.parse(raw);if(o.r==='u')addU(o.t);else if(o.r==='p')addP(o.t,o.ms,o.m,o.a,o.q,o.g,o.s)}catch(x){}
      });
    }
  });

  /* Init */
  updateBar();
})();
</script>
</body>
</html>`;
  }
}
