import Link from 'next/link';
import { ArrowRight, Shield } from 'lucide-react';

export function CTASection() {
  return (
    <section className="bg-slate-950 py-24">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Glow */}
        <div className="relative">
          <div className="absolute inset-0 bg-blue-600/10 blur-3xl rounded-full" />
          <div className="relative bg-gradient-to-br from-slate-900 to-slate-900/80 border border-slate-800/60 rounded-3xl p-12 sm:p-16">
            {/* Icon */}
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600/15 border border-blue-500/30 rounded-2xl mb-8">
              <Shield size={32} className="text-blue-400" />
            </div>

            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-5 leading-tight">
              Ready to automate your{' '}
              <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                content moderation?
              </span>
            </h2>

            <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-10">
              Join platforms using VidShield AI to moderate content at scale — fully
              autonomous, policy-driven, and enterprise-ready.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
              <Link
                href="/register"
                className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-base px-8 py-4 rounded-xl transition-all duration-200 shadow-lg shadow-blue-600/30"
              >
                Start Free 14-Day Trial
                <ArrowRight size={18} />
              </Link>
              <Link
                href="/register"
                className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-base px-8 py-4 rounded-xl transition-all duration-200"
              >
                Contact Sales
              </Link>
            </div>

            <p className="text-slate-500 text-sm">
              No credit card required · Cancel anytime · Full Growth features during trial
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
