import { Code2, Webhook, Zap, RefreshCw } from 'lucide-react';

const webhookEvents = [
  { event: 'moderation.completed', description: 'Fired when full analysis is done' },
  { event: 'violation.detected', description: 'Fired on each policy violation found' },
  { event: 'alert.triggered', description: 'Fired on queue backlog or pipeline failure' },
  { event: 'stream.status', description: 'Live stream started, stopped, or errored' },
];

const codeSnippet = `// Register a video for moderation
const response = await fetch('/api/v1/videos', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'User Upload #4821',
    source_url: 'https://cdn.example.com/vid.mp4',
    policy_id: 'pol_standard_v2'
  })
});

const { data } = await response.json();
// { "video_id": "vid_abc123", "status": "queued" }`;

export function Integrations() {
  return (
    <section id="integrations" className="bg-slate-950 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-4">
            <span className="text-blue-400 text-sm font-medium">Integrations & API</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Integrate in minutes, not weeks
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            A clean REST API, HMAC-signed webhooks, and WebSocket support — everything you need to embed
            VidShield AI into your existing platform.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {/* Left: Code snippet */}
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <Code2 className="text-blue-400" size={22} />
              <h3 className="text-white font-bold text-xl">REST API</h3>
              <span className="text-xs px-2.5 py-1 bg-green-600/15 text-green-400 rounded-full border border-green-500/20 font-medium">
                /api/v1/
              </span>
            </div>

            {/* Code block */}
            <div className="bg-slate-900 border border-slate-800/60 rounded-xl overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2.5 bg-slate-800/60 border-b border-slate-700/60">
                <div className="w-2.5 h-2.5 rounded-full bg-red-400/60" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-400/60" />
                <div className="w-2.5 h-2.5 rounded-full bg-green-400/60" />
                <span className="ml-2 text-slate-400 text-xs">register-video.js</span>
              </div>
              <pre className="p-5 text-sm text-slate-300 overflow-x-auto leading-relaxed font-mono">
                <code>{codeSnippet}</code>
              </pre>
            </div>

            {/* API features */}
            <div className="grid grid-cols-2 gap-4">
              {[
                { icon: Zap, label: 'Rate Limiting', desc: 'Per API key throttling' },
                { icon: RefreshCw, label: 'Pagination', desc: 'Cursor-based pagination' },
              ].map(({ icon: Icon, label, desc }) => (
                <div
                  key={label}
                  className="bg-slate-900/60 border border-slate-800/60 rounded-xl p-4 flex items-start gap-3"
                >
                  <Icon size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="text-white text-sm font-medium">{label}</div>
                    <div className="text-slate-500 text-xs">{desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Webhooks */}
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <Webhook className="text-violet-400" size={22} />
              <h3 className="text-white font-bold text-xl">Outbound Webhooks</h3>
            </div>

            <p className="text-slate-400 text-sm leading-relaxed">
              Register your endpoint and receive HMAC-signed payloads for every event. Automatic retries
              with exponential backoff ensure no event is lost.
            </p>

            {/* Webhook events */}
            <div className="space-y-3">
              {webhookEvents.map((ev) => (
                <div
                  key={ev.event}
                  className="bg-slate-900/60 border border-slate-800/60 rounded-xl p-4 flex items-center gap-4"
                >
                  <div className="w-2 h-2 rounded-full bg-violet-400 flex-shrink-0 animate-pulse" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-mono text-violet-300 truncate">{ev.event}</div>
                    <div className="text-slate-500 text-xs">{ev.description}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Webhook features */}
            <div className="bg-slate-900/60 border border-slate-800/60 rounded-xl p-5">
              <div className="text-white font-semibold text-sm mb-3">Security & Reliability</div>
              <ul className="space-y-2">
                {[
                  'HMAC-SHA256 signature verification',
                  'Automatic retries with backoff',
                  'Configurable secret per endpoint',
                  'Delivery logs and replay support',
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" />
                    <span className="text-slate-400 text-sm">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* WebSocket callout */}
        <div className="mt-10 bg-gradient-to-r from-blue-900/30 to-indigo-900/20 border border-blue-800/40 rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="w-10 h-10 bg-blue-600/20 border border-blue-500/30 rounded-xl flex items-center justify-center flex-shrink-0">
            <Zap size={20} className="text-blue-400" />
          </div>
          <div className="flex-1">
            <div className="text-white font-semibold mb-1">Real-Time WebSocket Support</div>
            <div className="text-slate-400 text-sm">
              Subscribe to live stream status and moderation queue updates via{' '}
              <code className="text-blue-300 font-mono text-xs bg-blue-900/30 px-1.5 py-0.5 rounded">
                wss://www.orionvexa.ca/ws/live/&#123;stream_id&#125;
              </code>{' '}
              for sub-second latency notifications.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
