import Link from 'next/link';
import { Upload, Cpu, FileCheck, ArrowRight, BookOpen } from 'lucide-react';

const steps = [
  {
    number: '01',
    icon: Upload,
    title: 'Ingest Video',
    description:
      'Submit video via upload (S3 presigned URL), live stream registration, or REST API. The platform queues it for async processing immediately.',
    details: ['Direct file upload', 'Live stream RTMP/HLS', 'API URL submission', 'Celery async queue'],
  },
  {
    number: '02',
    icon: Cpu,
    title: 'AI Pipeline Analyzes',
    description:
      'The LangGraph Orchestrator delegates to 6 specialist AI agents — analyzing frames with GPT-4o vision, transcribing audio with Whisper, and extracting metadata.',
    details: ['Frame extraction (FFmpeg)', 'GPT-4o vision analysis', 'Whisper transcription', 'OCR + object detection'],
  },
  {
    number: '03',
    icon: FileCheck,
    title: 'Receive Moderation Report',
    description:
      'Get a structured moderation report with violations, timestamps, confidence scores, and recommended actions — via webhook, API poll, or real-time WebSocket.',
    details: ['Violation timestamps', 'Confidence scores', 'Policy-based decisions', 'Webhook notification'],
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-slate-900 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-4">
            <span className="text-blue-400 text-sm font-medium">How It Works</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            From upload to moderation report in seconds
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            A fully automated pipeline — no manual configuration required for standard moderation workflows.
          </p>
        </div>

        {/* Steps */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={step.number} className="relative">
                {/* Arrow between steps (mobile) */}
                {index < steps.length - 1 && (
                  <div className="md:hidden flex justify-center my-4">
                    <ArrowRight className="text-slate-600 rotate-90" size={20} />
                  </div>
                )}

                <div className="bg-slate-950/60 border border-slate-800/60 rounded-2xl p-6 h-full">
                  {/* Step number + icon */}
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-blue-600/15 border border-blue-500/30 rounded-xl flex items-center justify-center">
                      <Icon size={22} className="text-blue-400" />
                    </div>
                    <span className="text-4xl font-black text-slate-800">{step.number}</span>
                  </div>

                  <h3 className="text-white font-bold text-xl mb-3">{step.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed mb-4">{step.description}</p>

                  {/* Detail pills */}
                  <ul className="space-y-2">
                    {step.details.map((detail) => (
                      <li key={detail} className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0" />
                        <span className="text-slate-400 text-xs">{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom note */}
        <div className="mt-12 text-center">
          <p className="text-slate-500 text-sm mb-6">
            Average end-to-end processing time:{' '}
            <span className="text-blue-400 font-semibold">under 2 seconds</span> for standard video segments
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors"
            >
              Get Started
              <ArrowRight size={16} />
            </Link>
            <a
              href="#integrations"
              className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors"
            >
              <BookOpen size={15} className="text-blue-400" />
              View Documentation
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
