import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { GitBranch, Eye, ShieldCheck, Tag, Film, FileText } from 'lucide-react';

const agents = [
  {
    icon: GitBranch,
    name: 'Orchestrator Agent',
    role: 'Entry Point',
    description:
      'Receives video analysis requests and delegates tasks to specialist agents using LangGraph state machine.',
    color: 'blue',
  },
  {
    icon: Eye,
    name: 'Content Analyzer',
    role: 'Vision Analysis',
    description:
      'GPT-4o vision on sampled frames for deep scene and content understanding — objects, actions, context.',
    color: 'indigo',
  },
  {
    icon: ShieldCheck,
    name: 'Safety Checker',
    role: 'Policy Enforcement',
    description:
      'Policy-aware moderation using configurable rule sets — makes autonomous decisions or escalates to human review.',
    color: 'violet',
  },
  {
    icon: Tag,
    name: 'Metadata Extractor',
    role: 'Entity Extraction',
    description:
      'Pulls entities, topics, brands, and text (OCR) from frames and audio transcript for rich metadata.',
    color: 'green',
  },
  {
    icon: Film,
    name: 'Scene Classifier',
    role: 'Category Detection',
    description:
      'Categorizes scenes into violence, nudity, drugs, hate symbols, graphic content, and custom categories.',
    color: 'orange',
  },
  {
    icon: FileText,
    name: 'Report Generator',
    role: 'Output Synthesis',
    description:
      'Synthesizes all agent outputs into a structured moderation report with violation timeline and recommendations.',
    color: 'teal',
  },
];

const colorMap: Record<string, { bg: string; border: string; icon: string; badge: string }> = {
  blue: {
    bg: 'bg-blue-600/10',
    border: 'border-blue-500/30',
    icon: 'text-blue-400',
    badge: 'bg-blue-600/20 text-blue-300',
  },
  indigo: {
    bg: 'bg-indigo-600/10',
    border: 'border-indigo-500/30',
    icon: 'text-indigo-400',
    badge: 'bg-indigo-600/20 text-indigo-300',
  },
  violet: {
    bg: 'bg-violet-600/10',
    border: 'border-violet-500/30',
    icon: 'text-violet-400',
    badge: 'bg-violet-600/20 text-violet-300',
  },
  green: {
    bg: 'bg-green-600/10',
    border: 'border-green-500/30',
    icon: 'text-green-400',
    badge: 'bg-green-600/20 text-green-300',
  },
  orange: {
    bg: 'bg-orange-600/10',
    border: 'border-orange-500/30',
    icon: 'text-orange-400',
    badge: 'bg-orange-600/20 text-orange-300',
  },
  teal: {
    bg: 'bg-teal-600/10',
    border: 'border-teal-500/30',
    icon: 'text-teal-400',
    badge: 'bg-teal-600/20 text-teal-300',
  },
};

export function AgentArchitecture() {
  return (
    <section id="ai-agents" className="bg-slate-950 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-4">
            <span className="text-blue-400 text-sm font-medium">AI Agent Architecture</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            6 specialist AI agents working in concert
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Powered by LangGraph multi-agent orchestration — each agent is an expert in its domain,
            collaborating autonomously to produce comprehensive moderation decisions.
          </p>
        </div>

        {/* Flow diagram hint */}
        <div className="flex items-center justify-center gap-2 mb-12 text-slate-500 text-sm">
          <span className="px-3 py-1 bg-slate-800 rounded-full border border-slate-700">Video Input</span>
          <span>→</span>
          <span className="px-3 py-1 bg-blue-900/50 rounded-full border border-blue-700/50 text-blue-300">Orchestrator</span>
          <span>→</span>
          <span className="px-3 py-1 bg-slate-800 rounded-full border border-slate-700">5 Specialists</span>
          <span>→</span>
          <span className="px-3 py-1 bg-slate-800 rounded-full border border-slate-700">Moderation Report</span>
        </div>

        {/* Agent cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => {
            const Icon = agent.icon;
            const colors = colorMap[agent.color];
            return (
              <div
                key={agent.name}
                className="bg-slate-900/60 border border-slate-800/60 rounded-2xl p-6 hover:border-slate-700 transition-all duration-200 group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div
                    className={`w-12 h-12 rounded-xl border ${colors.bg} ${colors.border} flex items-center justify-center`}
                  >
                    <Icon size={22} className={colors.icon} />
                  </div>
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${colors.badge}`}>
                    {agent.role}
                  </span>
                </div>
                <h3 className="text-white font-bold text-base mb-2">{agent.name}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{agent.description}</p>
              </div>
            );
          })}
        </div>

        {/* Tech stack note */}
        <div className="mt-12 flex flex-wrap gap-3 justify-center mb-10">
          {['LangGraph', 'GPT-4o Vision', 'GPT-4o-mini', 'OpenAI Whisper', 'LangChain 0.2+', 'Pinecone Vectors'].map((tech) => (
            <span
              key={tech}
              className="text-xs px-3 py-1.5 bg-slate-800 border border-slate-700/60 text-slate-300 rounded-full font-medium"
            >
              {tech}
            </span>
          ))}
        </div>

        {/* Section CTA */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors shadow-lg shadow-blue-600/20"
          >
            Try the AI Pipeline
            <ArrowRight size={16} />
          </Link>
          <a
            href="#integrations"
            className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors"
          >
            Explore API Docs
          </a>
        </div>
      </div>
    </section>
  );
}
