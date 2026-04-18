const stats = [
  { value: '99.9%', label: 'Platform Uptime', description: 'SLA-backed reliability' },
  { value: '<2s', label: 'Avg. Processing Latency', description: 'From upload to report' },
  { value: '99.4%', label: 'Moderation Accuracy', description: 'Validated on benchmark datasets' },
  { value: '6', label: 'Specialized AI Agents', description: 'LangGraph-orchestrated pipeline' },
  { value: '3', label: 'Ingestion Channels', description: 'Upload, Live, API submission' },
  { value: '∞', label: 'Horizontal Scale', description: 'GKE auto-scaling' },
];

export function Stats() {
  return (
    <section className="bg-slate-900 border-y border-slate-800/60 py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl sm:text-4xl font-extrabold text-white mb-1">
                {stat.value}
              </div>
              <div className="text-blue-400 font-semibold text-sm mb-1">{stat.label}</div>
              <div className="text-slate-500 text-xs">{stat.description}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
