import React from 'react';
import { ShieldAlert, Terminal, Activity } from 'lucide-react';
import DiagramRenderer from './DiagramRenderer';
import { getMarkdownBlocks, shouldShowOpenPorts } from '../utils/reportFormatting';

function renderInlineMarkdown(text) {
    return String(text).split(/(`[^`]+`|\*\*[^*]+\*\*)/g).map((part, index) => {
        if (part.startsWith('`') && part.endsWith('`')) {
            return <code key={index}>{part.slice(1, -1)}</code>;
        }

        if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={index}>{part.slice(2, -2)}</strong>;
        }

        return part;
    });
}

function MarkdownPatch({ value }) {
    const blocks = getMarkdownBlocks(value);

    if (blocks.length === 0) {
        return <p className="markdown-empty">Nenhuma solução causal foi retornada pela IA.</p>;
    }

    return (
        <div className="markdown-patch">
            {blocks.map((block, index) => {
                if (block.type === 'heading') {
                    const HeadingTag = `h${Math.min(block.level + 4, 6)}`;
                    return <HeadingTag key={index}>{renderInlineMarkdown(block.text)}</HeadingTag>;
                }

                if (block.type === 'list') {
                    return (
                        <ul key={index}>
                            {block.items.map((item, itemIndex) => (
                                <li key={itemIndex}>{renderInlineMarkdown(item)}</li>
                            ))}
                        </ul>
                    );
                }

                if (block.type === 'code') {
                    return (
                        <pre key={index}>
                            <code>{block.text}</code>
                        </pre>
                    );
                }

                return <p key={index}>{renderInlineMarkdown(block.text)}</p>;
            })}
        </div>
    );
}

export default function ReportViewer({ scanData, aiAnalysis }) {
    const openPortsWereTested = shouldShowOpenPorts(scanData);
    const openPorts = Array.isArray(scanData?.open_ports) ? scanData.open_ports : [];

    return (
        <div className="report-viewer">
            <h2>Diagnóstico da Base de Dados & Laboratório</h2>

            <div className="telemetry-box slide-up">
                <h3><Terminal size={18} style={{ marginRight: '8px', verticalAlign: 'middle' }} /> Dados de Telemetria Esgotados</h3>
                <p><strong>Alvo Base Isolado:</strong> {scanData?.target || "N/A"}</p>
                <p><strong>Status Laboratório:</strong> <span className={scanData?.status === 'up' ? 'status-up' : 'status-down'}>{scanData?.status || "Ausente"}</span></p>
                {openPortsWereTested && (
                    <div className="open-ports-logs">
                        <h4>Portas de Entrada Analisadas (Abertas):</h4>
                        {openPorts.length > 0 ? (
                            <ul>
                                {openPorts.map((port, i) => (
                                    <li key={i}>
                                        Porta <code>{port.port}</code> / {port.protocol.toUpperCase()} — {port.name}
                                        {port.product && <span> ({port.product} {port.version})</span>}
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="open-ports-empty">Nenhuma porta aberta foi identificada nesta varredura.</p>
                        )}
                    </div>
                )}
            </div>

            <div className="ai-analysis-box slide-up" style={{ animationDelay: '0.1s' }}>
                <h3><Activity size={18} style={{ marginRight: '8px', verticalAlign: 'middle' }} /> Insights da Camada Cognitiva (Google Gemini LLM)</h3>
                {!aiAnalysis?.vulnerabilidades || aiAnalysis.vulnerabilidades.length === 0 ? (
                    <p>Submeta a análise para gerar relatórios de anomalia.</p>
                ) : (
                    aiAnalysis.vulnerabilidades.map((vuln, index) => (
                        <div key={index} className="vuln-entry">
                            <h4 className="vuln-title">
                                <ShieldAlert size={20} style={{ color: '#f87171', marginRight: '10px', verticalAlign: 'bottom' }} />
                                {vuln.titulo}
                            </h4>

                            <div className="vuln-section text-block">
                                <h5>Prova Documentacional Causal:</h5>
                                {/* Renderiza as tags HTML enviadas pela IA com segurança */}
                                <div dangerouslySetInnerHTML={{ __html: vuln.explicacao }}></div>
                            </div>

                            <div className="vuln-section diagram-block">
                                <h5>Mapeamento do Exploit (Topologia de Fluxo):</h5>
                                <DiagramRenderer chartCode={vuln.mermaid} />
                            </div>

                            <div className="vuln-section code-block">
                                <h5>Solução / Patch Causal:</h5>
                                <MarkdownPatch value={vuln.patch} />
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
