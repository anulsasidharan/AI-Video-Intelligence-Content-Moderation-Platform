import Link from 'next/link';
import {
  Mail,
  Phone,
  MapPin,
  Clock,
  MessageSquare,
  Shield,
  Headphones,
  Building2,
} from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

const contactMethods = [
  {
    icon: Phone,
    title: 'Toll-Free Sales',
    value: '1-800-VID-SAFE',
    sub: '1-800-843-7233',
    note: 'Mon–Fri, 9 AM – 6 PM PST',
    color: 'blue',
  },
  {
    icon: Headphones,
    title: '24/7 Technical Support',
    value: '1-888-VID-HELP',
    sub: '1-888-843-4357',
    note: 'Available around the clock',
    color: 'purple',
  },
  {
    icon: Mail,
    title: 'General Inquiries',
    value: 'hello@orionvexa.ca',
    sub: undefined,
    note: 'We respond within 1 business day',
    color: 'emerald',
  },
  {
    icon: MessageSquare,
    title: 'Enterprise Sales',
    value: 'enterprise@orionvexa.ca',
    sub: undefined,
    note: 'Custom pricing & SLAs',
    color: 'amber',
  },
];

const offices = [
  {
    city: 'San Francisco (HQ)',
    address: '123 Innovation Drive, Suite 400',
    cityState: 'San Francisco, CA 94105',
    country: 'United States',
    phone: '+1 (415) 555-0192',
  },
  {
    city: 'New York',
    address: '350 Fifth Avenue, Floor 21',
    cityState: 'New York, NY 10118',
    country: 'United States',
    phone: '+1 (212) 555-0148',
  },
  {
    city: 'London',
    address: '1 Canada Square, Level 40',
    cityState: 'London E14 5AB',
    country: 'United Kingdom',
    phone: '+44 20 7946 0391',
  },
];

const colorMap: Record<string, string> = {
  blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
  purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
  emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
  amber: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
};

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
            <Building2 size={14} className="text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">Contact VidShield AI</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
            Let&apos;s talk
          </h1>
          <p className="text-slate-400 text-lg">
            Whether you&apos;re evaluating VidShield, need technical support, or want to discuss an
            enterprise agreement — our team is here to help.
          </p>
        </div>
      </section>

      {/* Contact methods */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {contactMethods.map((m) => (
              <div
                key={m.title}
                className="bg-slate-900 border border-slate-800/60 rounded-2xl p-5 hover:border-slate-700/60 transition-colors"
              >
                <div className={`w-10 h-10 border rounded-xl flex items-center justify-center mb-4 ${colorMap[m.color]}`}>
                  <m.icon size={18} />
                </div>
                <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1">
                  {m.title}
                </div>
                <div className="text-white font-semibold text-sm mb-0.5">{m.value}</div>
                {m.sub && (
                  <div className="text-slate-500 text-xs mb-1">{m.sub}</div>
                )}
                <div className="flex items-center gap-1 mt-2">
                  <Clock size={11} className="text-slate-600" />
                  <span className="text-slate-600 text-xs">{m.note}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Company info + support CTA */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">

          {/* Company card */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                <Shield size={18} className="text-white" />
              </div>
              <div>
                <div className="text-white font-bold text-lg leading-tight">VidShield AI, Inc.</div>
                <div className="text-slate-500 text-xs">EIN: 88-1234567</div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <MapPin size={16} className="text-blue-400 mt-0.5 shrink-0" />
                <div>
                  <div className="text-white text-sm font-medium">Registered Address</div>
                  <div className="text-slate-400 text-sm">123 Innovation Drive, Suite 400</div>
                  <div className="text-slate-400 text-sm">San Francisco, CA 94105</div>
                  <div className="text-slate-400 text-sm">United States</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Phone size={16} className="text-blue-400 shrink-0" />
                <div>
                  <div className="text-white text-sm font-medium">Main Line</div>
                  <div className="text-slate-400 text-sm">+1 (415) 555-0100</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Mail size={16} className="text-blue-400 shrink-0" />
                <div>
                  <div className="text-white text-sm font-medium">Corporate Email</div>
                  <div className="text-slate-400 text-sm">info@orionvexa.ca</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Clock size={16} className="text-blue-400 shrink-0" />
                <div>
                  <div className="text-white text-sm font-medium">Business Hours</div>
                  <div className="text-slate-400 text-sm">Mon – Fri, 9:00 AM – 6:00 PM PST</div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick actions */}
          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
              <h3 className="text-white font-semibold text-lg mb-2">Need technical support?</h3>
              <p className="text-slate-400 text-sm mb-4">
                Open a support ticket and our engineering team will respond within 4 hours for
                Business plans and 1 hour for Enterprise plans.
              </p>
              <Link
                href="/support"
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors"
              >
                <MessageSquare size={15} />
                Open a support ticket
              </Link>
            </div>

            <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
              <h3 className="text-white font-semibold text-lg mb-2">Media inquiries</h3>
              <p className="text-slate-400 text-sm mb-2">
                Press kit, product screenshots, executive interviews, and logo assets:
              </p>
              <a
                href="mailto:press@orionvexa.ca"
                className="text-blue-400 text-sm hover:text-blue-300 transition-colors"
              >
                press@orionvexa.ca
              </a>
            </div>

            <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
              <h3 className="text-white font-semibold text-lg mb-2">Partnership &amp; integrations</h3>
              <p className="text-slate-400 text-sm mb-2">
                Interested in becoming a technology or reseller partner?
              </p>
              <a
                href="mailto:partners@orionvexa.ca"
                className="text-blue-400 text-sm hover:text-blue-300 transition-colors"
              >
                partners@orionvexa.ca
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Offices */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-slate-900/30">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">Our offices</h2>
          <div className="grid sm:grid-cols-3 gap-5">
            {offices.map((o) => (
              <div
                key={o.city}
                className="bg-slate-900 border border-slate-800/60 rounded-2xl p-5"
              >
                <div className="flex items-center gap-2 mb-3">
                  <MapPin size={15} className="text-blue-400" />
                  <span className="text-white font-semibold text-sm">{o.city}</span>
                </div>
                <div className="text-slate-400 text-sm">{o.address}</div>
                <div className="text-slate-400 text-sm">{o.cityState}</div>
                <div className="text-slate-400 text-sm mb-3">{o.country}</div>
                <div className="flex items-center gap-2">
                  <Phone size={12} className="text-slate-600" />
                  <span className="text-slate-500 text-xs">{o.phone}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
