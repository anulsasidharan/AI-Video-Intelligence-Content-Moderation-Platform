import Link from 'next/link';
import { Webhook, Shield, Zap, CheckCircle, AlertTriangle, Code2, ChevronRight } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

const WEBHOOK_EVENTS = [
  { event: 'video.processed', desc: 'Fired when a video has finished AI analysis' },
  { event: 'video.rejected', desc: 'Fired when a video is rejected by the moderation pipeline' },
  { event: 'video.flagged', desc: 'Fired when a video is flagged for human review' },
  { event: 'moderation.decision', desc: 'Fired for every AI moderation decision' },
  { event: 'live.violation', desc: 'Fired when a live stream violation is detected in real time' },
  { event: 'alert.triggered', desc: 'Fired when a configurable alert threshold is crossed' },
];

const SETUP_STEPS = [
  {
    step: '1',
    title: 'Create a webhook endpoint',
    desc: 'In your VidShield dashboard, navigate to Settings → Webhooks → Add Endpoint. Enter the HTTPS URL of your server that will receive events.',
  },
  {
    step: '2',
    title: 'Select events to subscribe to',
    desc: 'Choose which events to receive. You can subscribe to individual events or use a wildcard (*) to receive all events.',
  },
  {
    step: '3',
    title: 'Copy your signing secret',
    desc: 'VidShield generates a unique signing secret per endpoint. Store it securely — you will use it to verify webhook signatures.',
  },
  {
    step: '4',
    title: 'Verify the signature',
    desc: 'For every incoming request, verify the X-VidShield-Signature header using HMAC-SHA256 with your signing secret.',
  },
  {
    step: '5',
    title: 'Respond with 200 OK',
    desc: 'Return a 2xx status within 10 seconds. If your endpoint is unavailable, VidShield retries with exponential back-off up to 72 hours.',
  },
];

export default function WebhooksGuidePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      <section className="pt-32 pb-14 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
            <Webhook size={14} className="text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">Webhooks Guide</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-4">Setting up Webhooks</h1>
          <p className="text-slate-400 text-lg">
            Webhooks let your application react to VidShield events in real time — no polling required.
            When an event occurs, we send an HTTP POST request to your registered endpoint.
          </p>
        </div>
      </section>

      <section className="pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto space-y-6">

          {/* Setup steps */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-6">
              <Zap size={15} className="text-blue-400" />
              <span className="text-white font-semibold text-lg">Setup walkthrough</span>
            </div>
            <div className="space-y-6">
              {SETUP_STEPS.map((s) => (
                <div key={s.step} className="flex gap-4">
                  <div className="w-8 h-8 bg-blue-600/20 border border-blue-500/30 rounded-full flex items-center justify-center text-blue-400 font-bold text-sm shrink-0">
                    {s.step}
                  </div>
                  <div>
                    <div className="text-white font-semibold text-sm mb-1">{s.title}</div>
                    <div className="text-slate-400 text-sm leading-relaxed">{s.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Event types */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Code2 size={15} className="text-purple-400" />
              <span className="text-white font-semibold">Available events</span>
            </div>
            <div className="space-y-2">
              {WEBHOOK_EVENTS.map((e) => (
                <div key={e.event} className="flex items-center gap-3 bg-slate-800/50 rounded-xl px-4 py-3">
                  <code className="text-blue-400 text-sm shrink-0">{e.event}</code>
                  <span className="text-slate-500 text-sm hidden sm:block">— {e.desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sample payload */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Code2 size={15} className="text-emerald-400" />
              <span className="text-white font-semibold">Sample payload — video.processed</span>
            </div>
            <div className="bg-slate-800 border border-slate-700/60 rounded-xl p-4 overflow-x-auto">
              <pre className="text-xs text-slate-300">{`POST https://your-server.com/webhooks/vidshield
X-VidShield-Signature: sha256=<hmac_hex>
Content-Type: application/json

{
  "id": "evt_01j8kzxy...",
  "type": "video.processed",
  "created_at": "2026-03-26T10:00:00Z",
  "data": {
    "video_id": "vid_abc123",
    "title": "Product Demo v2",
    "status": "completed",
    "moderation_status": "approved",
    "confidence": 0.97,
    "duration_seconds": 182,
    "violations": []
  }
}`}</pre>
            </div>
          </div>

          {/* Signature verification */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Shield size={15} className="text-amber-400" />
              <span className="text-white font-semibold">Verifying signatures</span>
            </div>
            <p className="text-slate-400 text-sm mb-4">
              Every webhook request includes a{' '}
              <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded">X-VidShield-Signature</code>{' '}
              header. Verify it to ensure the request is from VidShield and hasn&apos;t been tampered with.
            </p>
            <div className="bg-slate-800 border border-slate-700/60 rounded-xl p-4 overflow-x-auto">
              <pre className="text-xs text-slate-300">{`import hmac, hashlib

def verify_signature(payload_body: bytes, secret: str, signature: str) -> bool:
    expected = hmac.new(
        secret.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)`}</pre>
            </div>
          </div>

          {/* Retry policy */}
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={15} className="text-amber-400" />
              <span className="text-amber-400 font-semibold">Retry policy</span>
            </div>
            <p className="text-slate-300 text-sm">
              If your endpoint returns a non-2xx response or times out (10 s), VidShield retries
              with exponential back-off: 5 min → 30 min → 2 h → 8 h → 24 h. After 5 failed
              attempts over 72 hours, the event is marked as failed and an alert is sent to
              your account email.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link href="/dashboard/settings" className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors">
              Configure webhooks in dashboard
            </Link>
            <Link href="/docs/api-reference" className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors">
              API Reference <ChevronRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
