import type MarkdownIt from 'markdown-it/index.js';

export function markdownBlockHover(md: MarkdownIt) {
    md.core.ruler.push('wrap_hover_blocks', state => {
        const tokens = state.tokens;
        const newTokens: any[] = [];

        const srcLines = state.src.split('\n');

        let i = 0;
        while (i < tokens.length) {
            const token = tokens[i];

            if (token.type === 'hr') {
                if (newTokens[newTokens.length - 1]?.type !== 'hr') {
                    newTokens.push(token);
                }

                const buffer: any[] = [];
                let startLine: number | null = null;
                let endLine: number | null = null;
                i++;

                while (i < tokens.length && tokens[i].type !== 'hr') {
                    const t = tokens[i];
                    buffer.push(t);

                    // Запоминаем диапазон строк, если он есть
                    if (t.map) {
                        if (startLine === null) startLine = t.map[0];
                        endLine = t.map[1]; // Всегда обновляем — последний token определит конец
                    }

                    i++;
                }

                if (i < tokens.length && tokens[i].type === 'hr') {
                    const lines = (startLine !== null && endLine !== null)
                        ? srcLines.slice(startLine, endLine).join('\n')
                        : '';

                    const openDiv = new state.Token('html_block', '', 0);
                    openDiv.content = `<app-hover-block originalContent="${escapeHtml(lines)}">`;

                    const closeDiv = new state.Token('html_block', '', 0);
                    closeDiv.content = '</app-hover-block>';

                    newTokens.push(openDiv);
                    newTokens.push(...buffer);
                    newTokens.push(closeDiv);
                    newTokens.push(tokens[i]);
                } else {
                    newTokens.push(...buffer);
                }
            } else {
                newTokens.push(token);
                i++;
            }
        }

        state.tokens = newTokens;
    });
}

// Простая HTML-экранизация
function escapeHtml(str: string): string {
    return str
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

export function sourceListPlugin(md: MarkdownIt) {
    const pattern = /^\.{3}\s*sources:\[(.+?)\]\((.+?)\)(?:SEPARATOR\[(.+?)\]\((.+?)\))*$/gm;

    md.core.ruler.push('source_list', (state) => {
        const tokens = state.tokens;
        for (let i = 0; i < tokens.length; i++) {
            const token = tokens[i];

            if (token.type === 'inline' && token.content.startsWith('sources:')) {
                const raw = token.content;
                const sources: { title: string; url: string }[] = [];

                const parts = raw.replace(/^\.{3}\s*sources:/, '').split(/SEPARATOR/);
                for (const part of parts) {
                    const match = part.match(/\[([^\]]+)\]\(([^)]+)\)/);
                    if (match) {
                        sources.push({ title: match[1], url: match[2] });
                    }
                }

                const json = JSON.stringify(sources);

                const openToken = new state.Token('html_block', '', 0);
                openToken.content = `<app-source-list sources='${
                    json.replace(/'/g, '&apos;')
                }'></app-source-list>`;

                tokens.splice(i, 1, openToken);
            }
        }
    });
};
