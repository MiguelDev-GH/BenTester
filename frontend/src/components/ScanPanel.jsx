import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Globe, Folder, FileText, Zap, AlertTriangle, ChevronDown } from 'lucide-react';
import axios from 'axios';

const MODES = { NETWORK: 'network', FILE: 'file' };

const GEMINI_MODELS = [
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
    { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
    { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
    { value: 'gemini-2.0-flash-lite', label: 'Gemini 2.0 Flash Lite' },
    { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite' },
];

const OPENAI_MODELS = [
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'gpt-4.1', label: 'GPT-4.1' },
    { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini' },
    { value: 'gpt-4.1-nano', label: 'GPT-4.1 Nano' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'o3-mini', label: 'o3-mini' },
    { value: 'o4-mini', label: 'o4-mini' },
];

export default function ScanPanel({ onScanComplete, onProviderChange }) {
    const [mode, setMode] = useState(MODES.NETWORK);
    const [target, setTarget] = useState('172.17.0.2');
    const [file, setFile] = useState(null);
    const [provider, setProvider] = useState('gemini');
    const [model, setModel] = useState('gemini-2.5-flash');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [modelFlashing, setModelFlashing] = useState(false);
    const fileInputRef = useRef(null);
    const flashTimerRef = useRef(null);

    useEffect(() => () => { if (flashTimerRef.current) clearTimeout(flashTimerRef.current); }, []);

    const triggerModelFlash = useCallback(() => {
        setModelFlashing(false);
        // Force reflow so removing + re-adding the class re-triggers animation
        if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
        requestAnimationFrame(() => {
            setModelFlashing(true);
            flashTimerRef.current = setTimeout(() => setModelFlashing(false), 560);
        });
    }, []);

    const handleProviderChange = (newProvider) => {
        setProvider(newProvider);
        onProviderChange?.(newProvider);
        const nextModel = newProvider === 'gemini' ? GEMINI_MODELS[0].value : OPENAI_MODELS[0].value;
        setModel(nextModel);
        triggerModelFlash();
    };

    const handleScanSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            let response;

            if (mode === MODES.FILE) {
                if (!file) {
                    setError('Selecione um arquivo para análise.');
                    setLoading(false);
                    return;
                }
                const formData = new FormData();
                formData.append('file', file);
                formData.append('model', model);
                response = await axios.post('http://localhost:8000/analyze-file', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
            } else {
                response = await axios.post(
                    `http://localhost:8000/analyze?target=${encodeURIComponent(target)}&model=${encodeURIComponent(model)}`
                );
            }

            if (response.data.status === 'sucesso') {
                onScanComplete(response.data);
            } else {
                setError(response.data.error || 'Ação bloqueada pelas regras de confinamento seguro.');
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Erro intrusivo na conexão com back-end.');
        } finally {
            setLoading(false);
        }
    };

    const handleModeSwitch = (newMode) => {
        setMode(newMode);
        setError(null);
        setFile(null);
    };

    const currentModels = provider === 'openai' ? OPENAI_MODELS : GEMINI_MODELS;

    return (
        <div className="scan-panel-outer slide-up">

            {/* ── Abas no topo sobrepostas à borda do card ── */}
            <div className="mode-tabs">
                <button
                    id="mode-network-btn"
                    type="button"
                    className={`mode-tab ${mode === MODES.NETWORK ? 'active' : ''}`}
                    onClick={() => handleModeSwitch(MODES.NETWORK)}
                >
                    <Globe size={15} className="mode-tab-icon" />
                    Modo Link
                </button>
                <button
                    id="mode-file-btn"
                    type="button"
                    className={`mode-tab ${mode === MODES.FILE ? 'active' : ''}`}
                    onClick={() => handleModeSwitch(MODES.FILE)}
                >
                    <Folder size={15} className="mode-tab-icon" />
                    Modo Arquivo
                </button>
            </div>

            {/* ── Card principal ── */}
            <div className="scan-panel">
                <form onSubmit={handleScanSubmit} className="scan-form-inner">

                    {/* Input central */}
                    <div className="central-input-wrapper fade-in" key={mode}>
                        {mode === MODES.NETWORK ? (
                            <input
                                id="target-input"
                                type="text"
                                className="central-input"
                                value={target}
                                onChange={(e) => setTarget(e.target.value)}
                                placeholder="IP ou Host — ex: 172.17.0.2, localhost:3000"
                                autoComplete="off"
                            />
                        ) : (
                            <div
                                className={`file-drop-area ${file ? 'has-file' : ''}`}
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    style={{ display: 'none' }}
                                    onChange={(e) => setFile(e.target.files[0])}
                                />
                                <FileText className="file-drop-icon" size={24} />
                                <span className="file-drop-text">
                                    {file ? file.name : 'Clique para selecionar um arquivo (qualquer tipo)'}
                                </span>
                                {file && (
                                    <span className="file-drop-size">
                                        {(file.size / 1024).toFixed(1)} KB
                                    </span>
                                )}
                            </div>
                        )}
                    </div>

                    {/* ── Linha inferior: provedor + modelo + executar ── */}
                    <div className="scan-bottom-row">

                        {/* Toggle de provedor inline estilo texto */}
                        <div className="provider-inline">
                            <button
                                id="provider-gemini-btn"
                                type="button"
                                className={`provider-text-btn ${provider === 'gemini' ? 'active' : ''}`}
                                onClick={() => handleProviderChange('gemini')}
                            >
                                Gemini
                            </button>
                            <span className="provider-sep">/</span>
                            <button
                                id="provider-openai-btn"
                                type="button"
                                className={`provider-text-btn ${provider === 'openai' ? 'active' : ''}`}
                                onClick={() => handleProviderChange('openai')}
                            >
                                OpenAI
                            </button>
                        </div>

                        {/* Seletor de modelo */}
                        <div className="model-select-wrapper">
                            <select
                                id="model-select"
                                className={`model-select-minimal${modelFlashing ? ' model-flash model-changed' : ''}`}
                                value={model}
                                onChange={(e) => { setModel(e.target.value); triggerModelFlash(); }}
                            >
                                {currentModels.map(m => (
                                    <option key={m.value} value={m.value}>{m.label}</option>
                                ))}

                            </select>
                            <ChevronDown size={13} className="select-chevron" />
                        </div>

                        {/* Botão executar compacto */}
                        <button id="execute-btn" type="submit" className="execute-button" disabled={loading}>
                            {loading ? (
                                <span className="btn-loading">
                                    <span className="spinner" />
                                    {mode === MODES.FILE ? 'Analisando...' : 'Infiltrando...'}
                                </span>
                            ) : (
                                <><Zap size={13} style={{ marginRight: '6px' }} />Executar</>
                            )}
                        </button>
                    </div>

                    {error && (
                        <div className="error-alert">
                            <AlertTriangle size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                            <strong>Alerta:</strong> {error}
                        </div>
                    )}
                </form>
            </div>
        </div>
    );
}
