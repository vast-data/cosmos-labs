import { Injectable } from '@angular/core';
import {
  ChatMessage,
  MessageContentBlock,
  TextContentBlock,
  ToolContentBlock
} from '../../reports/services/session.mapper';

@Injectable({ providedIn: 'root' })
export class PdfExportService {

  extractPlainText(message: ChatMessage): string {
    if (typeof message.content === 'string') return message.content;
    if (!Array.isArray(message.content)) return '';

    return message.content
      .filter((b): b is TextContentBlock => b.type === 'text')
      .map(b => b.text)
      .join('\n\n');
  }

  async exportMessageToPdf(message: ChatMessage, title?: string): Promise<void> {
    const text = this.extractPlainText(message);
    const toolSummaries = this.extractToolSummaries(message);
    const html = this.buildSingleMessageHtml(text, toolSummaries, title);
    await this.renderHtmlToPdf(html, this.sanitizeFilename(title || 'response') + '.pdf');
  }

  async exportConversationToPdf(messages: ChatMessage[], sessionTitle?: string): Promise<void> {
    const html = this.buildConversationHtml(messages, sessionTitle);
    await this.renderHtmlToPdf(html, this.sanitizeFilename(sessionTitle || 'conversation') + '.pdf');
  }

  private extractToolSummaries(message: ChatMessage): string[] {
    if (typeof message.content === 'string' || !Array.isArray(message.content)) return [];

    return message.content
      .filter((b): b is ToolContentBlock => b.type === 'tool')
      .map(b => {
        const name = b.toolName || 'Tool';
        const dur = b.duration != null ? ` (${(b.duration / 1000).toFixed(1)}s)` : '';
        const sources = b.chunks?.length ? ` — ${b.chunks.length} sources` : '';
        return `${name}${dur}${sources}`;
      });
  }

  private buildSingleMessageHtml(text: string, tools: string[], title?: string): string {
    const toolsHtml = tools.length
      ? `<div class="tools">${tools.map(t => `<div class="tool-item">${this.escapeHtml(t)}</div>`).join('')}</div>`
      : '';

    return this.wrapInDocument(`
      ${title ? `<h1>${this.escapeHtml(title)}</h1>` : ''}
      ${toolsHtml}
      <div class="content">${this.markdownToSimpleHtml(text)}</div>
    `);
  }

  private buildConversationHtml(messages: ChatMessage[], sessionTitle?: string): string {
    const blocks = messages.map(msg => {
      const isHuman = msg.role === 'human';
      const label = isHuman ? 'You' : 'Assistant';
      const text = this.extractPlainText(msg);
      const tools = !isHuman ? this.extractToolSummaries(msg) : [];
      const toolsHtml = tools.length
        ? `<div class="tools">${tools.map(t => `<div class="tool-item">${this.escapeHtml(t)}</div>`).join('')}</div>`
        : '';

      return `
        <div class="message ${isHuman ? 'human' : 'assistant'}">
          <div class="role-label">${label}</div>
          ${toolsHtml}
          <div class="content">${isHuman ? this.escapeHtml(text) : this.markdownToSimpleHtml(text)}</div>
        </div>
      `;
    }).join('<hr/>');

    return this.wrapInDocument(`
      <h1>${this.escapeHtml(sessionTitle || 'Conversation')}</h1>
      <div class="meta">Exported on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
      ${blocks}
    `);
  }

  private wrapInDocument(body: string): string {
    return `<!DOCTYPE html><html><head><meta charset="utf-8"/>
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a2e; max-width: 800px; margin: 0 auto; padding: 32px 24px; font-size: 14px; line-height: 1.6; }
      h1 { font-size: 20px; margin-bottom: 4px; color: #0f172a; }
      h2, h3, h4 { margin-top: 18px; margin-bottom: 8px; color: #1e293b; }
      .meta { font-size: 12px; color: #94a3b8; margin-bottom: 24px; }
      hr { border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }
      .message { margin-bottom: 16px; }
      .role-label { font-weight: 600; font-size: 13px; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
      .human .content { background: #f1f5f9; border-radius: 8px; padding: 10px 14px; }
      .assistant .content { padding: 2px 0; }
      .tools { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
      .tool-item { background: #e0f2fe; color: #0369a1; font-size: 11px; padding: 3px 8px; border-radius: 4px; }
      pre { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; overflow-x: auto; font-size: 13px; }
      code { font-family: 'SF Mono', Consolas, monospace; font-size: 13px; }
      p code { background: #f1f5f9; padding: 2px 5px; border-radius: 3px; }
      ul, ol { padding-left: 20px; }
      table { border-collapse: collapse; width: 100%; margin: 12px 0; }
      th, td { border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; font-size: 13px; }
      th { background: #f8fafc; font-weight: 600; }
      strong { font-weight: 600; }
      blockquote { border-left: 3px solid #cbd5e1; margin: 12px 0; padding: 4px 16px; color: #475569; }
    </style></head><body>${body}</body></html>`;
  }

  private async renderHtmlToPdf(html: string, filename: string): Promise<void> {
    const { default: jsPDF } = await import('jspdf');
    const { default: html2canvas } = await import('html2canvas');

    const container = document.createElement('div');
    container.style.cssText = 'position:fixed;left:-9999px;top:0;width:800px;background:#fff;z-index:-1;';
    container.innerHTML = '';

    const iframe = document.createElement('iframe');
    iframe.style.cssText = 'width:800px;height:1px;border:none;visibility:hidden;';
    document.body.appendChild(iframe);

    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!iframeDoc) { document.body.removeChild(iframe); return; }

    iframeDoc.open();
    iframeDoc.write(html);
    iframeDoc.close();

    await new Promise(r => setTimeout(r, 300));

    const body = iframeDoc.body;
    const canvas = await html2canvas(body, { scale: 2, useCORS: true, width: 800, windowWidth: 800 });

    document.body.removeChild(iframe);

    const imgWidth = 190;
    const pageHeight = 277;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    const imgData = canvas.toDataURL('image/png');

    const pdf = new jsPDF('p', 'mm', 'a4');
    let heightLeft = imgHeight;
    let position = 10;

    pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;

    while (heightLeft > 0) {
      position = heightLeft - imgHeight + 10;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }

    pdf.save(filename);
  }

  private markdownToSimpleHtml(md: string): string {
    if (!md) return '';
    let html = this.escapeHtml(md);

    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    html = html.replace(/\n{2,}/g, '</p><p>');
    html = `<p>${html}</p>`;
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>\s*(<h[2-4]>)/g, '$1');
    html = html.replace(/(<\/h[2-4]>)\s*<\/p>/g, '$1');
    html = html.replace(/<p>\s*(<ul>)/g, '$1');
    html = html.replace(/(<\/ul>)\s*<\/p>/g, '$1');
    html = html.replace(/<p>\s*(<pre>)/g, '$1');
    html = html.replace(/(<\/pre>)\s*<\/p>/g, '$1');

    return html;
  }

  private escapeHtml(text: string): string {
    const map: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  private sanitizeFilename(name: string): string {
    return name.replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 50);
  }
}
