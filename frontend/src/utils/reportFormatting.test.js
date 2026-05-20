import test from 'node:test';
import assert from 'node:assert/strict';
import {
    getMarkdownBlocks,
    shouldShowOpenPorts,
} from './reportFormatting.js';

test('hides open ports section when the analysis did not test ports', () => {
    assert.equal(shouldShowOpenPorts({ tipo: 'VIRUSTOTAL', stats: {} }), false);
    assert.equal(shouldShowOpenPorts({ target: 'arquivo.exe' }), false);
});

test('shows open ports section when network scan tested ports even if none are open', () => {
    assert.equal(shouldShowOpenPorts({ target: 'localhost', status: 'up', open_ports: [] }), true);
});

test('shows open ports section when open ports have values', () => {
    const scanData = {
        open_ports: [{ port: 80, protocol: 'tcp', name: 'http' }],
    };

    assert.equal(shouldShowOpenPorts(scanData), true);
});

test('parses markdown patch text into readable blocks', () => {
    const blocks = getMarkdownBlocks(`# Corrigir\n\n- Validar entrada\n- Aplicar patch\n\n\`\`\`js\nconst ok = true;\n\`\`\``);

    assert.deepEqual(blocks, [
        { type: 'heading', level: 1, text: 'Corrigir' },
        { type: 'list', items: ['Validar entrada', 'Aplicar patch'] },
        { type: 'code', language: 'js', text: 'const ok = true;' },
    ]);
});
