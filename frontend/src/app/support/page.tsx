'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Headphones,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
  MessageSquare,
  Zap,
  Shield,
} from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';
import { getBrowserApiV1Root } from '@/lib/apiOrigin';

const SLA_TIERS = [
  { plan: 'Free', response: '5 business days', badge: 'bg-slate-700 text-slate-300' },
  { plan: 'Business', response: '< 4 hours', badge: 'bg-blue-500/20 text-blue-300' },
  { plan: 'Enterprise', response: '< 1 hour', badge: 'bg-purple-500/20 text-purple-300' },
];

interface FormState {
  name: string;
  email: string;
  phone: string;
  subject: string;
  message: string;
}

const INITIAL_FORM: FormState = { name: '', email: '', phone: '', subject: '', message: '' };

export default function SupportPage() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const set = (field: keyof FormState) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch(`${getBrowserApiV1Root()}/support-tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name.trim(),
          email: form.email.trim(),
          phone: form.phone.trim() || null,
          subject: form.subject.trim(),
          message: form.message.trim(),
        }),
      });
      if (!res.ok) {
        const json = await res.json().catch(() => ({})) as { error?: { message?: string } };
        throw new Error(json?.error?.message ?? 'Failed to submit ticket. Please try again.');
      }
      const json = await res.json() as { data?: { id?: string }; id?: string };
      const id = json?.data?.id ?? json?.id ?? null;
      setTicketId(id);
      setSuccess(true);
      setForm(INITIAL_FORM);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-14 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
            <Headphones size={14} className="text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">Support Center</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
            How can we help?
          </h1>
          <p className="text-slate-400 text-lg">
            Submit a support ticket and our team will get back to you based on your plan SLA.
            For urgent issues, call our 24/7 hotline at{' '}
            <span className="text-white font-medium">1-888-843-4357</span>.
          </p>
        </div>
      </section>

      {/* SLA tiers */}
      <section className="pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="flex flex-wrap justify-center gap-3">
            {SLA_TIERS.map((tier) => (
              <div key={tier.plan} className={`flex items-center gap-2 px-4 py-2 rounded-full border border-slate-800/60 bg-slate-900 text-sm`}>
                <Clock size={13} className="text-slate-500" />
                <span className="text-slate-400">{tier.plan}:</span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${tier.badge}`}>
                  {tier.response}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Main content */}
      <section className="pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8">

          {/* Sidebar info */}
          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Zap size={15} className="text-blue-400" />
                <span className="text-white font-semibold text-sm">Before you submit</span>
              </div>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li>• Check our{' '}
                  <Link href="/#faq" className="text-blue-400 hover:text-blue-300">FAQ section</Link>
                  {' '}for instant answers
                </li>
                <li>• Review the{' '}
                  <Link href="/docs/api-reference" className="text-blue-400 hover:text-blue-300">API docs</Link>
                  {' '}for integration issues
                </li>
                <li>• Include your Organization ID for faster lookup</li>
                <li>• Attach screenshots or logs if available</li>
              </ul>
            </div>

            <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Shield size={15} className="text-purple-400" />
                <span className="text-white font-semibold text-sm">Enterprise support</span>
              </div>
              <p className="text-slate-400 text-sm mb-3">
                Enterprise customers get a dedicated Slack channel and named CSM.
              </p>
              <Link
                href="/contact"
                className="text-blue-400 text-sm hover:text-blue-300 transition-colors"
              >
                Contact enterprise sales →
              </Link>
            </div>

            <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <MessageSquare size={15} className="text-emerald-400" />
                <span className="text-white font-semibold text-sm">Other channels</span>
              </div>
              <div className="space-y-1.5 text-sm">
                <div className="text-slate-400">Email: <a href="mailto:support@orionvexa.ca" className="text-blue-400">support@orionvexa.ca</a></div>
                <div className="text-slate-400">Phone: <span className="text-white">1-888-843-4357</span></div>
              </div>
            </div>
          </div>

          {/* Form */}
          <div className="md:col-span-2">
            {success ? (
              <div className="bg-slate-900 border border-emerald-500/30 rounded-2xl p-10 text-center">
                <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/30 rounded-full flex items-center justify-center mx-auto mb-5">
                  <CheckCircle2 size={28} className="text-emerald-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Ticket submitted!</h2>
                {ticketId && (
                  <div className="text-slate-500 text-sm mb-2">
                    Ticket ID: <span className="text-slate-300 font-mono">{ticketId}</span>
                  </div>
                )}
                <p className="text-slate-400 text-sm mb-6">
                  We&apos;ve received your request and will respond to your email within the SLA window
                  for your plan. Keep an eye on your inbox.
                </p>
                <button
                  onClick={() => { setSuccess(false); setTicketId(null); }}
                  className="text-blue-400 text-sm hover:text-blue-300 transition-colors"
                >
                  Submit another ticket
                </button>
              </div>
            ) : (
              <form
                onSubmit={handleSubmit}
                className="bg-slate-900 border border-slate-800/60 rounded-2xl p-8 space-y-5"
              >
                <h2 className="text-xl font-bold text-white mb-1">Submit a support ticket</h2>
                <p className="text-slate-500 text-sm">
                  All fields marked <span className="text-red-400">*</span> are required.
                </p>

                {error && (
                  <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm">
                    <AlertCircle size={15} />
                    {error}
                  </div>
                )}

                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-slate-300 text-sm font-medium mb-1.5">
                      Full name <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={form.name}
                      onChange={set('name')}
                      placeholder="Jane Smith"
                      className="w-full bg-slate-800 border border-slate-700/60 text-white placeholder-slate-500 text-sm px-4 py-2.5 rounded-xl outline-none focus:border-blue-500/60 transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-300 text-sm font-medium mb-1.5">
                      Email address <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="email"
                      required
                      value={form.email}
                      onChange={set('email')}
                      placeholder="jane@company.com"
                      className="w-full bg-slate-800 border border-slate-700/60 text-white placeholder-slate-500 text-sm px-4 py-2.5 rounded-xl outline-none focus:border-blue-500/60 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-1.5">
                    Phone number <span className="text-slate-600">(optional)</span>
                  </label>
                  <input
                    type="tel"
                    value={form.phone}
                    onChange={set('phone')}
                    placeholder="+1 (555) 000-0000"
                    className="w-full bg-slate-800 border border-slate-700/60 text-white placeholder-slate-500 text-sm px-4 py-2.5 rounded-xl outline-none focus:border-blue-500/60 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-1.5">
                    Subject <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={form.subject}
                    onChange={set('subject')}
                    placeholder="Brief description of your issue"
                    className="w-full bg-slate-800 border border-slate-700/60 text-white placeholder-slate-500 text-sm px-4 py-2.5 rounded-xl outline-none focus:border-blue-500/60 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-1.5">
                    Message <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    required
                    rows={6}
                    value={form.message}
                    onChange={set('message')}
                    placeholder="Please describe your issue in detail. Include steps to reproduce, error messages, your Organization ID, and any relevant context."
                    className="w-full bg-slate-800 border border-slate-700/60 text-white placeholder-slate-500 text-sm px-4 py-2.5 rounded-xl outline-none focus:border-blue-500/60 transition-colors resize-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors"
                >
                  {submitting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Submitting…
                    </>
                  ) : (
                    <>
                      <MessageSquare size={16} />
                      Submit ticket
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
