import Link from 'next/link';
import { Package, Terminal, Code2, ChevronRight, CheckCircle } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

const sdks = [
  {
    lang: 'Python',
    package: 'vidshield-ai',
    install: 'pip install vidshield-ai',
    status: 'stable',
    statusColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    example: `from vidshield import VidShieldClient

client = VidShieldClient(api_key="vs_live_...")

# Upload and analyze a video
video = client.videos.upload(
    file_path="./demo.mp4",
    title="Product Demo",
    wait_for_analysis=True,
)

print(video.moderation_status)   # "approved"
print(video.violations)          # []`,
  },
  {
    lang: 'Node.js / TypeScript',
    package: '@vidshield/sdk',
    install: 'npm install @vidshield/sdk',
    status: 'stable',
    statusColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    example: `import { VidShieldClient } from '@vidshield/sdk';

const client = new VidShieldClient({ apiKey: 'vs_live_...' });

// List recent moderation decisions
const queue = await client.moderation.list({
  status: 'pending',
  pageSize: 20,
});

console.log(queue.items);`,
  },
  {
    lang: 'Go',
    package: 'github.com/vidshield-ai/go-sdk',
    install: 'go get github.com/vidshield-ai/go-sdk',
    status: 'beta',
    statusColor: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    example: `package main

import (
    "fmt"
    "github.com/vidshield-ai/go-sdk/vidshield"
)

func main() {
    client := vidshield.NewClient("vs_live_...")
    videos, _ := client.Videos.List(ctx, nil)
    fmt.Println(videos.Total)
}`,
  },
  {
    lang: 'Java / Kotlin',
    package: 'ai.vidshield:vidshield-sdk',
    install: 'implementation "ai.vidshield:vidshield-sdk:1.0.0"',
    status: 'coming soon',
    statusColor: 'text-slate-400 bg-slate-700/30 border-slate-700/40',
    example: `// Java SDK is in active development.
// Star the GitHub repo to be notified on release.`,
  },
];

const features = [
  'Automatic token refresh and retry logic',
  'Full TypeScript type safety across all SDK methods',
  'Streaming support for large video uploads',
  'Built-in webhook signature verification helpers',
  'Pagination iterators for large result sets',
  'Async/await and Promise support for all operations',
];

export default function SdkDocumentationPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      <section className="pt-32 pb-14 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
            <Package size={14} className="text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">SDK Documentation</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-4">Official SDKs</h1>
          <p className="text-slate-400 text-lg">
            Client libraries that wrap the VidShield REST API for your language of choice.
            All SDKs are open-source and published to their respective package registries.
          </p>
        </div>
      </section>

      <section className="pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto space-y-6">

          {/* Features */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Code2 size={15} className="text-blue-400" />
              <span className="text-white font-semibold">What&apos;s included in every SDK</span>
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              {features.map((f) => (
                <div key={f} className="flex items-start gap-2">
                  <CheckCircle size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                  <span className="text-slate-400 text-sm">{f}</span>
                </div>
              ))}
            </div>
          </div>

          {/* SDK cards */}
          {sdks.map((sdk) => (
            <div key={sdk.lang} className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-slate-800 border border-slate-700/60 rounded-lg flex items-center justify-center">
                    <Package size={14} className="text-slate-400" />
                  </div>
                  <span className="text-white font-semibold">{sdk.lang}</span>
                </div>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${sdk.statusColor}`}>
                  {sdk.status}
                </span>
              </div>

              <div className="flex items-center gap-2 mb-4">
                <Terminal size={13} className="text-slate-500" />
                <div className="flex-1 bg-slate-800 border border-slate-700/60 rounded-lg px-3 py-2">
                  <code className="text-sm text-emerald-400">{sdk.install}</code>
                </div>
              </div>

              <div className="bg-slate-800 border border-slate-700/60 rounded-xl p-4 overflow-x-auto">
                <pre className="text-xs text-slate-300">{sdk.example}</pre>
              </div>

              <div className="mt-3 text-slate-500 text-xs">
                Package: <code className="text-slate-400">{sdk.package}</code>
              </div>
            </div>
          ))}

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Link href="/docs/api-reference" className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors">
              Full API Reference
            </Link>
            <Link href="/docs/developer-portal" className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors">
              Developer Portal <ChevronRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
