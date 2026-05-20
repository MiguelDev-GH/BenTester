export function shouldShowOpenPorts(scanData) {
    if (!scanData || !Array.isArray(scanData.open_ports)) {
        return false;
    }

    return scanData.open_ports.length > 0 || Boolean(scanData.status || scanData.resolved_target);
}

export function getMarkdownBlocks(markdown = '') {
    const lines = String(markdown).replace(/\r\n/g, '\n').split('\n');
    const blocks = [];
    let paragraph = [];
    let listItems = [];
    let codeLines = [];
    let codeLanguage = '';
    let inCode = false;

    const flushParagraph = () => {
        if (paragraph.length === 0) return;
        blocks.push({ type: 'paragraph', text: paragraph.join(' ') });
        paragraph = [];
    };

    const flushList = () => {
        if (listItems.length === 0) return;
        blocks.push({ type: 'list', items: listItems });
        listItems = [];
    };

    lines.forEach((line) => {
        const codeFence = line.match(/^```(\w+)?\s*$/);
        if (codeFence) {
            if (inCode) {
                blocks.push({
                    type: 'code',
                    language: codeLanguage,
                    text: codeLines.join('\n').trim(),
                });
                codeLines = [];
                codeLanguage = '';
                inCode = false;
                return;
            }

            flushParagraph();
            flushList();
            inCode = true;
            codeLanguage = codeFence[1] || '';
            return;
        }

        if (inCode) {
            codeLines.push(line);
            return;
        }

        if (!line.trim()) {
            flushParagraph();
            flushList();
            return;
        }

        const heading = line.match(/^(#{1,3})\s+(.+)$/);
        if (heading) {
            flushParagraph();
            flushList();
            blocks.push({
                type: 'heading',
                level: heading[1].length,
                text: heading[2].trim(),
            });
            return;
        }

        const listItem = line.match(/^\s*(?:[-*]|\d+\.)\s+(.+)$/);
        if (listItem) {
            flushParagraph();
            listItems.push(listItem[1].trim());
            return;
        }

        flushList();
        paragraph.push(line.trim());
    });

    if (inCode) {
        blocks.push({ type: 'code', language: codeLanguage, text: codeLines.join('\n').trim() });
    }
    flushParagraph();
    flushList();

    return blocks;
}
