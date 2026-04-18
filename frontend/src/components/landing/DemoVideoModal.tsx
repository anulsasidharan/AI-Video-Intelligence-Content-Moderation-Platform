'use client';

import { useEffect, useRef, useState } from 'react';
import {
  X,
  ChevronLeft,
  ChevronRight,
  Shield,
  Upload,
  Cpu,
  FileCheck,
  Bell,
  BarChart3,
} from 'lucide-react';

interface DemoVideoModalProps {
  open: boolean;
  onClose: () => void;
}

// ── Slide: Dashboard ─────────────────────────────────────────────────────────

function SlideDashboard() {
  const [counts, setCounts] = useState({ videos: 0, violations: 0, accuracy: 0, latency: 0 });

  useEffect(() => {
    const targets = { videos: 24891, violations: 1247, accuracy: 994, latency: 18 };
    const steps = 40;
    let step = 0;
    const timer = setInterval(() => {
      step++;
      const ease = 1 - Math.pow(1 - step / steps, 3);
      setCounts({
        videos: Math.round(targets.videos * ease),
        violations: Math.round(targets.violations * ease),
        accuracy: Math.round(targets.accuracy * ease),
        latency: Math.round(targets.latency * ease),
      });
      if (step >= steps) clearInterval(timer);
    }, 30);
    return () => clearInterval(timer);
  }, []);

  const bars = [40, 65, 45, 80, 60, 90, 75, 55, 85, 70, 95, 60];

  return (
    <div className="h-full flex flex-col gap-4 p-6 overflow-auto">
      <div className="flex items-center gap-3">
        <Shield size={18} className="text-blue-400" />
        <span className="text-white font-semibold text-sm">Platform Overview — Live Dashboard</span>
        <span className="ml-auto flex items-center gap-1.5 text-xs text-green-400 font-medium">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse inline-block" />
          All systems operational
        </span>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Videos Processed', value: counts.videos.toLocaleString(), color: 'text-blue-400' },
          { label: 'Violations Detected', value: counts.violations.toLocaleString(), color: 'text-red-400' },
          { label: 'Accuracy Rate', value: `${(counts.accuracy / 10).toFixed(1)}%`, color: 'text-green-400' },
          { label: 'Avg Latency', value: `${(counts.latency / 10).toFixed(1)}s`, color: 'text-yellow-400' },
        ].map((s) => (
          <div key={s.label} className="bg-slate-800 border border-slate-700/50 rounded-xl p-3">
            <div className={`text-xl font-bold ${s.color} mb-0.5`}>{s.value}</div>
            <div className="text-slate-400 text-xs">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-3 flex-1 min-h-0">
        <div className="col-span-2 bg-slate-800 border border-slate-700/50 rounded-xl p-4 flex flex-col min-h-0">
          <span className="text-slate-400 text-xs font-medium mb-2">Processing Activity (24h)</span>
          <div className="flex items-end gap-1 flex-1">
            {bars.map((h, i) => (
              <div key={i} className="flex-1 bg-blue-600/70 rounded-t" style={{ height: `${h}%` }} />
            ))}
          </div>
        </div>
        <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4">
          <span className="text-slate-400 text-xs font-medium">Violation Breakdown</span>
          <div className="mt-3 space-y-2.5">
            {[
              { label: 'Violence', pct: 34, color: 'bg-red-500' },
              { label: 'Explicit Content', pct: 28, color: 'bg-orange-500' },
              { label: 'Hate Speech', pct: 22, color: 'bg-yellow-500' },
              { label: 'Other', pct: 16, color: 'bg-slate-500' },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">{item.label}</span>
                  <span className="text-slate-300 font-medium">{item.pct}%</span>
                </div>
                <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div className={`h-full ${item.color} rounded-full`} style={{ width: `${item.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-3">
        <span className="text-slate-400 text-xs font-medium block mb-2">Recent Activity</span>
        <div className="space-y-1.5">
          {[
            { name: 'product-demo-v2.mp4', status: 'APPROVED', badge: 'bg-green-900/60 text-green-400 border-green-700/50', time: '2s ago' },
            { name: 'user-upload-4821.mp4', status: 'FLAGGED', badge: 'bg-red-900/60 text-red-400 border-red-700/50', time: '14s ago' },
            { name: 'livestream-ch7.m3u8', status: 'PROCESSING', badge: 'bg-blue-900/60 text-blue-400 border-blue-700/50', time: '31s ago' },
          ].map((row) => (
            <div key={row.name} className="flex items-center gap-3 text-xs">
              <span className="text-slate-300 flex-1 truncate">{row.name}</span>
              <span className={`px-2 py-0.5 rounded-full border text-xs font-medium ${row.badge}`}>{row.status}</span>
              <span className="text-slate-500 flex-shrink-0">{row.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Slide: Upload ─────────────────────────────────────────────────────────────

function SlideUpload() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setStage(1), 600),
      setTimeout(() => setStage(2), 1500),
      setTimeout(() => setStage(3), 2400),
      setTimeout(() => setStage(4), 3200),
      setTimeout(() => setStage(5), 4000),
    ];
    return () => timers.forEach(clearTimeout);
  }, []);

  const stages = [
    'Uploading to GCS...',
    'Extracting frames (FFmpeg)',
    'Transcribing audio (Whisper)',
    'Dispatching AI agents',
    'Analysis complete',
  ];

  return (
    <div className="h-full flex flex-col gap-4 p-6 overflow-auto">
      <div className="flex items-center gap-3">
        <Upload size={18} className="text-blue-400" />
        <span className="text-white font-semibold text-sm">Video Upload &amp; Processing Pipeline</span>
      </div>

      <div className={`border-2 border-dashed rounded-2xl p-6 flex flex-col items-center justify-center gap-3 transition-all duration-500 ${stage >= 1 ? 'border-blue-500 bg-blue-600/10' : 'border-slate-600 bg-slate-800/40'}`}>
        <Upload size={32} className={stage >= 1 ? 'text-blue-400' : 'text-slate-500'} />
        {stage === 0 ? (
          <p className="text-slate-300 font-medium text-sm">Drag &amp; drop your video here</p>
        ) : (
          <div className="text-center">
            <p className="text-blue-300 font-semibold text-sm">policy-violation-sample.mp4</p>
            <p className="text-slate-400 text-xs mt-0.5">847 MB · 4K · 00:12:34</p>
          </div>
        )}
      </div>

      {stage >= 1 && (
        <div className="flex-1 bg-slate-800 border border-slate-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-300 text-sm font-medium">AI Processing Pipeline</span>
            {stage >= 5 && <span className="text-green-400 text-xs font-medium bg-green-900/40 border border-green-700/50 px-2 py-0.5 rounded-full">Complete in 8.5s</span>}
          </div>

          <div className="mb-4">
            <div className="flex justify-between text-xs mb-1.5">
              <span className="text-slate-400">Overall Progress</span>
              <span className="text-slate-300">{Math.min(stage * 20, 100)}%</span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-blue-600 rounded-full transition-all duration-700" style={{ width: `${Math.min(stage * 20, 100)}%` }} />
            </div>
          </div>

          <div className="space-y-3">
            {stages.map((label, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300 ${i < stage ? 'bg-green-600' : i === stage ? 'bg-blue-600 animate-pulse' : 'bg-slate-700'}`}>
                  {i < stage ? (
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <span className="text-xs text-slate-400">{i + 1}</span>
                  )}
                </div>
                <span className={`text-sm ${i < stage ? 'text-green-400' : i === stage ? 'text-blue-300' : 'text-slate-500'}`}>
                  {label}{i < stage && ' ✓'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Slide: Agent Log ──────────────────────────────────────────────────────────

const LOG_LINES = [
  { delay: 0,    text: '[00:00.312] OrchestratorAgent  » Dispatching 5 specialist agents', color: 'text-blue-300' },
  { delay: 350,  text: '[00:00.418] ContentAnalyzer    » Sampling 84 frames @ 7fps', color: 'text-slate-300' },
  { delay: 700,  text: '[00:01.204] AudioTranscriber   » Whisper-large-v3 loaded', color: 'text-slate-300' },
  { delay: 1050, text: '[00:02.891] ContentAnalyzer    » Frame 00:42 — VIOLENCE: 0.91 ⚠', color: 'text-red-400' },
  { delay: 1400, text: '[00:03.112] SafetyChecker      » Policy match: violence_threshold exceeded', color: 'text-orange-400' },
  { delay: 1750, text: '[00:04.780] MetadataExtractor  » Entities: [weapon, person, outdoor]', color: 'text-slate-300' },
  { delay: 2100, text: '[00:05.340] SceneClassifier    » Scene: confrontation · outdoor · daytime', color: 'text-slate-300' },
  { delay: 2450, text: '[00:05.901] AudioTranscriber   » Threatening language (0.96) at 00:42–00:48', color: 'text-red-400' },
  { delay: 2800, text: '[00:06.001] OCRTool            » Text detected: "EXIT" (frame 00:51)', color: 'text-slate-300' },
  { delay: 3150, text: '[00:07.230] ReportGenerator    » Compiling report — 3 violations', color: 'text-yellow-400' },
  { delay: 3500, text: '[00:08.544] OrchestratorAgent  » ✅ Analysis complete — FLAGGED 94.2%', color: 'text-green-400' },
];

function SlideAgentLog() {
  const [visible, setVisible] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timers = LOG_LINES.map((line, i) =>
      setTimeout(() => {
        setVisible(i + 1);
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, line.delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="h-full flex flex-col gap-4 p-6 overflow-auto">
      <div className="flex items-center gap-3">
        <Cpu size={18} className="text-blue-400" />
        <span className="text-white font-semibold text-sm">AI Agent Pipeline — Live Activity</span>
        <span className="ml-auto text-xs text-slate-400 font-mono">LangGraph · GPT-4o · Whisper</span>
      </div>

      <div className="flex-1 bg-slate-950 border border-slate-700/50 rounded-xl p-4 font-mono text-xs overflow-y-auto min-h-0">
        {LOG_LINES.slice(0, visible).map((line, i) => (
          <div key={i} className={`${line.color} mb-1.5 leading-relaxed`}>{line.text}</div>
        ))}
        {visible < LOG_LINES.length && <span className="text-slate-500 animate-pulse">█</span>}
        <div ref={bottomRef} />
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Agents Active', value: '5', color: 'text-blue-400' },
          { label: 'Frames Analyzed', value: '84', color: 'text-slate-300' },
          { label: 'Violations Found', value: '3', color: 'text-red-400' },
        ].map((s) => (
          <div key={s.label} className="bg-slate-800 border border-slate-700/50 rounded-xl p-3 text-center">
            <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-slate-500 text-xs mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Slide: Moderation Report ──────────────────────────────────────────────────

function SlideModerationReport() {
  const [show, setShow] = useState(false);
  useEffect(() => { const t = setTimeout(() => setShow(true), 200); return () => clearTimeout(t); }, []);

  const violations = [
    { category: 'Violence', severity: 'HIGH', confidence: 91, info: '14 frames affected', badge: 'bg-red-900/50 border-red-700/50 text-red-400', bar: 'bg-red-500' },
    { category: 'Threatening Language', severity: 'HIGH', confidence: 96, info: 'Source: Audio', badge: 'bg-red-900/50 border-red-700/50 text-red-400', bar: 'bg-red-500' },
    { category: 'Weapon Detection', severity: 'MEDIUM', confidence: 88, info: '7 frames affected', badge: 'bg-yellow-900/50 border-yellow-700/50 text-yellow-400', bar: 'bg-yellow-500' },
  ];

  return (
    <div className="h-full flex flex-col gap-4 p-6 overflow-auto">
      <div className="flex items-center gap-3">
        <FileCheck size={18} className="text-blue-400" />
        <span className="text-white font-semibold text-sm">Moderation Report</span>
      </div>

      <div className={`bg-slate-800 border border-red-500/30 bg-red-950/10 rounded-xl p-4 flex items-center gap-4 transition-all duration-500 ${show ? 'opacity-100' : 'opacity-0'}`}>
        <div className="w-12 h-8 bg-slate-700 rounded flex items-center justify-center flex-shrink-0">
          <span className="text-slate-500 text-xs">▶</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-slate-200 text-sm font-medium">policy-violation-sample.mp4</p>
          <p className="text-slate-500 text-xs">Analyzed in 8.5s · Policy: Enterprise v2.3</p>
        </div>
        <div className="text-right flex-shrink-0">
          <span className="px-3 py-1 rounded-full bg-red-900/60 border border-red-700/50 text-red-400 text-xs font-bold">FLAGGED</span>
          <p className="text-slate-500 text-xs mt-1">Confidence 94.2%</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {violations.map((v, i) => (
          <div
            key={v.category}
            className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 transition-all duration-500"
            style={{ transitionDelay: `${i * 150 + 300}ms`, opacity: show ? 1 : 0, transform: show ? 'translateY(0)' : 'translateY(8px)' }}
          >
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${v.badge}`}>{v.severity}</span>
            <p className="text-slate-200 text-sm font-medium mt-2 mb-1">{v.category}</p>
            <div className="mb-2">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-500">Confidence</span>
                <span className="font-semibold">{v.confidence}%</span>
              </div>
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div className={`h-full ${v.bar} rounded-full transition-all duration-1000`} style={{ width: show ? `${v.confidence}%` : '0%', transitionDelay: `${i * 150 + 500}ms` }} />
              </div>
            </div>
            <p className="text-slate-500 text-xs">{v.info}</p>
          </div>
        ))}
      </div>

      <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4">
        <p className="text-slate-400 text-xs font-medium mb-3">Violation Timeline</p>
        <div className="relative h-5 flex items-center">
          <div className="absolute inset-x-0 h-2 rounded-full bg-slate-700" />
          {[{ pos: '56%', label: '00:42' }, { pos: '76%', label: '01:17' }, { pos: '88%', label: '02:05' }].map((m) => (
            <div key={m.pos} className="absolute flex flex-col items-center" style={{ left: m.pos, transform: 'translateX(-50%)' }}>
              <div className="w-3.5 h-3.5 rounded-full bg-red-500 border-2 border-red-300" />
              <span className="text-red-400 text-xs mt-0.5 whitespace-nowrap">{m.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Slide: Notifications & Audit ──────────────────────────────────────────────

function SlideNotifications() {
  const [show, setShow] = useState(false);
  useEffect(() => { const t = setTimeout(() => setShow(true), 100); return () => clearTimeout(t); }, []);

  return (
    <div className="h-full flex flex-col gap-4 p-6 overflow-auto">
      <div className="flex items-center gap-3">
        <Bell size={18} className="text-blue-400" />
        <span className="text-white font-semibold text-sm">Multi-Channel Alerts &amp; Audit Trail</span>
      </div>

      <div className="grid grid-cols-2 gap-4 flex-1 min-h-0">
        <div className="flex flex-col gap-3">
          <p className="text-slate-400 text-xs font-medium">Alert Channels</p>
          {[
            { icon: '📧', name: 'Email (SendGrid)', desc: 'security@acme.com', color: 'text-green-400' },
            { icon: '💬', name: 'WhatsApp (Twilio)', desc: '+1 (555) 000-0001', color: 'text-green-400' },
            { icon: '🔔', name: 'In-App Alerts', desc: 'All severities', color: 'text-blue-400' },
          ].map((ch, i) => (
            <div
              key={ch.name}
              className="bg-slate-800 border border-slate-700/50 rounded-xl p-3 flex items-center gap-3 transition-all duration-500"
              style={{ transitionDelay: `${i * 120}ms`, opacity: show ? 1 : 0, transform: show ? 'translateX(0)' : 'translateX(-10px)' }}
            >
              <span className="text-lg">{ch.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="text-slate-200 text-sm font-medium">{ch.name}</p>
                <p className="text-slate-500 text-xs truncate">{ch.desc}</p>
              </div>
              <div className={`w-1.5 h-1.5 rounded-full ${ch.color === 'text-green-400' ? 'bg-green-400' : 'bg-blue-400'}`} />
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-3">
          <p className="text-slate-400 text-xs font-medium">Audit Trail</p>
          <div className="flex-1 bg-slate-950 border border-slate-700/50 rounded-xl p-3 overflow-hidden min-h-0">
            <div className="space-y-1.5">
              {[
                { time: '14:32:01', actor: 'AI Agent', action: 'FLAGGED', detail: 'Violence 91%', color: 'text-red-400' },
                { time: '14:32:02', actor: 'System', action: 'QUARANTINE', detail: 'Auto-policy', color: 'text-orange-400' },
                { time: '14:32:03', actor: 'System', action: 'NOTIFIED', detail: 'Email + WhatsApp', color: 'text-blue-400' },
                { time: '14:31:55', actor: 'admin@acme', action: 'API_KEY', detail: 'prod-wh01 created', color: 'text-slate-400' },
                { time: '14:28:12', actor: 'AI Agent', action: 'APPROVED', detail: 'Clean 98.2%', color: 'text-green-400' },
              ].map((row, i) => (
                <div key={i} className="text-xs font-mono transition-all duration-500" style={{ transitionDelay: `${i * 80 + 200}ms`, opacity: show ? 1 : 0 }}>
                  <span className="text-slate-600">{row.time} </span>
                  <span className="text-slate-500">{row.actor} </span>
                  <span className={`font-bold ${row.color}`}>{row.action} </span>
                  <span className="text-slate-600">{row.detail}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-3">
            <p className="text-slate-400 text-xs font-medium mb-2">Compliance Score</p>
            <div className="flex items-center gap-3">
              <div className="text-xl font-bold text-green-400">98.4%</div>
              <div className="flex-1">
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full transition-all duration-1000" style={{ width: show ? '98.4%' : '0%' }} />
                </div>
                <p className="text-slate-500 text-xs mt-1">GDPR · SOC 2 · CSAM Ready</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Slide registry ────────────────────────────────────────────────────────────

const SLIDES = [
  { id: 'dashboard', icon: BarChart3, label: 'Dashboard',       component: SlideDashboard },
  { id: 'upload',    icon: Upload,    label: 'Upload & Process', component: SlideUpload },
  { id: 'agents',   icon: Cpu,       label: 'AI Agents',        component: SlideAgentLog },
  { id: 'report',   icon: FileCheck, label: 'Report',           component: SlideModerationReport },
  { id: 'alerts',   icon: Bell,      label: 'Alerts & Audit',   component: SlideNotifications },
];

const SLIDE_DURATION = 8000;

// ── Modal ─────────────────────────────────────────────────────────────────────

export function DemoVideoModal({ open, onClose }: DemoVideoModalProps) {
  const [current, setCurrent] = useState(0);
  const [paused, setPaused] = useState(false);
  const [progress, setProgress] = useState(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const goTo = (index: number) => { setCurrent(index); setProgress(0); };
  const prev = () => goTo((current - 1 + SLIDES.length) % SLIDES.length);
  const next = () => goTo((current + 1) % SLIDES.length);

  useEffect(() => {
    if (!open) return;
    setCurrent(0); setProgress(0); setPaused(false);
  }, [open]);

  useEffect(() => {
    if (!open || paused) {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (tickRef.current) clearInterval(tickRef.current);
      return;
    }
    setProgress(0);
    const tick = 60;
    tickRef.current = setInterval(() => {
      setProgress((p) => Math.min(p + (tick / SLIDE_DURATION) * 100, 100));
    }, tick);
    timerRef.current = setTimeout(() => {
      setCurrent((c) => (c + 1) % SLIDES.length);
      setProgress(0);
    }, SLIDE_DURATION);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (tickRef.current) clearInterval(tickRef.current);
    };
  }, [open, current, paused]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!open) return;
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft') prev();
      if (e.key === 'ArrowRight') next();
      if (e.key === ' ') { e.preventDefault(); setPaused((p) => !p); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, current]);

  if (!open) return null;

  const SlideComponent = SLIDES[current].component;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />

      {/* Panel */}
      <div
        className="relative z-10 w-full max-w-5xl bg-slate-900 border border-slate-700/60 rounded-2xl shadow-2xl shadow-black/60 flex flex-col overflow-hidden"
        style={{ height: 'min(88vh, 620px)' }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-3.5 border-b border-slate-700/60 bg-slate-900/90 flex-shrink-0">
          <Shield size={16} className="text-blue-400 flex-shrink-0" />
          <span className="text-white font-semibold text-sm">VidShield AI — Platform Demo</span>

          <div className="flex items-center gap-1 ml-3 overflow-x-auto flex-1">
            {SLIDES.map((slide, i) => {
              const Icon = slide.icon;
              return (
                <button
                  key={slide.id}
                  type="button"
                  onClick={() => goTo(i)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors flex-shrink-0 ${
                    i === current ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <Icon size={11} />
                  {slide.label}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              type="button"
              onClick={() => setPaused((p) => !p)}
              className="text-slate-400 hover:text-slate-200 text-xs px-2 py-1 rounded-md hover:bg-slate-800 transition-colors"
            >
              {paused ? '▶ Resume' : '⏸ Pause'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="text-slate-400 hover:text-white transition-colors p-1 rounded-md hover:bg-slate-800"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-0.5 bg-slate-800 flex-shrink-0">
          <div className="h-full bg-blue-500 transition-none" style={{ width: `${progress}%` }} />
        </div>

        {/* Slide */}
        <div className="flex-1 overflow-hidden min-h-0">
          <SlideComponent key={current} />
        </div>

        {/* Footer nav */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-slate-700/60 bg-slate-900/60 flex-shrink-0">
          <button type="button" onClick={prev} className="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors px-3 py-1.5 rounded-lg hover:bg-slate-800">
            <ChevronLeft size={15} /> Previous
          </button>
          <div className="flex items-center gap-2">
            {SLIDES.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => goTo(i)}
                className={`rounded-full transition-all duration-200 ${i === current ? 'w-5 h-2 bg-blue-500' : 'w-2 h-2 bg-slate-600 hover:bg-slate-400'}`}
              />
            ))}
          </div>
          <button type="button" onClick={next} className="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors px-3 py-1.5 rounded-lg hover:bg-slate-800">
            Next <ChevronRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
