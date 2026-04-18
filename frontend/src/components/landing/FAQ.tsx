'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

const faqs = [
  {
    question: 'How long does it take to process a video?',
    answer:
      'Average end-to-end processing time is under 2 seconds for standard video segments. Full reports for longer videos depend on duration and policy complexity, but the Celery async pipeline ensures your platform is never blocked — you receive a webhook or can poll the API when the report is ready.',
  },
  {
    question: 'What content categories can VidShield AI detect?',
    answer:
      'Out of the box: violence, graphic content, nudity/explicit material, drug use, hate symbols and speech, and dangerous activities. You can define custom categories via the Policy Editor using natural language rules — no code changes required.',
  },
  {
    question: 'Does VidShield AI support live stream moderation?',
    answer:
      'Yes. Register a live stream via the API and VidShield AI will perform near-real-time analysis of stream segments, sending alerts via WebSocket or webhook as violations are detected. The dashboard includes a live stream monitor with AlertBanner for operator visibility.',
  },
  {
    question: 'How does the 6-agent AI pipeline work?',
    answer:
      'The LangGraph Orchestrator receives your video analysis request and fans out work to 5 specialist agents: Content Analyzer (GPT-4o vision on frames), Safety Checker (policy evaluation), Metadata Extractor (entities, OCR, topics), Scene Classifier (category detection), and Report Generator (synthesizes all outputs into a structured moderation report).',
  },
  {
    question: 'Is human review supported?',
    answer:
      'Yes. Human review is optional and configurable per policy. You can set escalation thresholds so that borderline confidence scores route items to the moderation queue for human operator review, override, or approval — with a full audit trail for every decision.',
  },
  {
    question: 'How do webhooks work and are they secure?',
    answer:
      'VidShield AI sends HMAC-SHA256 signed payloads to your registered endpoint for events like moderation.completed, violation.detected, alert.triggered, and stream.status. Each webhook includes a signature header you verify server-side. Automatic retries with exponential backoff ensure delivery even through transient failures.',
  },
  {
    question: 'Is VidShield AI GDPR compliant?',
    answer:
      'The platform is designed GDPR-aware from the ground up — PII detection and masking in transcripts, data export, deletion requests, and configurable retention periods are all built in. Production deployments on GCP use encrypted Cloud Storage, VPC isolation, and GCP Secret Manager for credential management.',
  },
  {
    question: 'What infrastructure does VidShield AI run on?',
    answer:
      'VidShield AI is deployed on GKE (auto-scaling Kubernetes containers), Cloud SQL PostgreSQL 16 (HA in production), Cloud Memorystore Redis 7 (cache + Celery broker), Google Cloud Storage (video + artifact storage), and Cloud CDN. Infrastructure is fully managed via Terraform with dev/staging/prod environment configs.',
  },
  {
    question: 'Can I integrate VidShield AI into my existing platform?',
    answer:
      'Absolutely. The REST API (`/api/v1/`) provides full programmatic access — submit videos, poll results, manage policies, and receive events. The API uses standard JSON, supports API key and JWT authentication, and has rate limiting per key. Integration typically takes hours, not weeks.',
  },
  {
    question: 'What happens during my free trial?',
    answer:
      'You get full access to all Growth-tier features for 14 days — no credit card required. You can process real videos, configure policies, test webhooks, and evaluate the platform against your actual content before committing.',
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section id="faq" className="bg-slate-900 py-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-4">
            <span className="text-blue-400 text-sm font-medium">FAQ</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Frequently asked questions
          </h2>
          <p className="text-slate-400 text-lg">
            Everything you need to know about VidShield AI.
          </p>
        </div>

        {/* FAQ list */}
        <div className="space-y-3">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-slate-950/60 border border-slate-800/60 rounded-xl overflow-hidden"
            >
              <button
                className="w-full flex items-center justify-between px-6 py-5 text-left gap-4 hover:bg-slate-800/30 transition-colors"
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                aria-expanded={openIndex === index}
              >
                <span className="text-white font-medium text-sm">{faq.question}</span>
                <ChevronDown
                  size={18}
                  className={`text-slate-400 flex-shrink-0 transition-transform duration-200 ${
                    openIndex === index ? 'rotate-180' : ''
                  }`}
                />
              </button>
              {openIndex === index && (
                <div className="px-6 pb-5">
                  <p className="text-slate-400 text-sm leading-relaxed">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
