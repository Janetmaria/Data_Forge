import { useQuery } from '@tanstack/react-query';
import { X, Sparkles, AlertTriangle, CheckCircle2, TerminalSquare } from 'lucide-react';
import api from '@/lib/api';

// --- Interfaces matching Pydantic schemas ---
interface DomainResult {
  domain: 'hr' | 'finance' | 'healthcare' | 'ecommerce' | 'iot_sensor' | 'generic';
  confidence: number;
  evidence: string[];
}

interface InferenceReport {
  domain_detection: DomainResult;
  ml_readiness_score: number;
  ml_readiness_label: 'Not Ready' | 'Needs Work' | 'Almost Ready' | 'Ready';
  top_actions: string[];
}

interface InferencePanelProps {
  datasetId: string;
  onClose: () => void;
  onApplyFix?: (operation: string, columns: string[]) => void;
}

export default function InferencePanel({ datasetId, onClose }: InferencePanelProps) {
  const { data: report, isLoading, error } = useQuery<InferenceReport>({
    queryKey: ['inference', datasetId],
    queryFn: async () => {
      const res = await api.get(`/datasets/${datasetId}/infer`);
      return res.data;
    },
    staleTime: 0,
  });

  const getReadinessColor = (score: number) => {
    if (score >= 0.85) return 'text-green-500 bg-green-500';
    if (score >= 0.65) return 'text-lime-500 bg-lime-500';
    if (score >= 0.40) return 'text-amber-500 bg-amber-500';
    return 'text-red-500 bg-red-500';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#1e1e1e] border border-gray-700 shadow-2xl rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-[#252526]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-teal-400" />
            <h2 className="text-lg font-bold text-gray-200 tracking-wide">AI Data Inference Report</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors p-1 rounded hover:bg-white/10">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-[#121212]">

          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
              <div className="w-10 h-10 border-4 border-teal-500/30 border-t-teal-500 rounded-full animate-spin"></div>
              <p className="text-gray-400 font-mono text-sm animate-pulse">Running advanced heuristics...</p>
            </div>
          ) : error ? (
            <div className="text-red-400 p-4 border border-red-500/30 bg-red-500/10 rounded-lg">
              <AlertTriangle className="w-6 h-6 mb-2" />
              Failed to run inference engine. Check console for details.
            </div>
          ) : report ? (
            <>
              {/* Detected Domain + ML Readiness */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* Domain Badge */}
                <div className="bg-[#1e1e1e] p-4 rounded-lg border border-gray-800 shadow-sm">
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 block">Detected Domain</span>
                  <div className="flex items-center gap-3 mb-3">
                    <span className="px-3 py-1 bg-teal-900/40 text-teal-400 border border-teal-800/50 rounded-full text-sm font-bold uppercase tracking-wider">
                      {report.domain_detection.domain}
                    </span>
                    <span className="text-gray-400 text-sm font-mono">
                      {(report.domain_detection.confidence * 100).toFixed(0)}% Confidence
                    </span>
                  </div>
                  <div className="space-y-1">
                    {report.domain_detection.evidence.map((ev, i) => (
                      <p key={i} className="text-xs text-gray-500 flex items-start gap-2">
                        <span className="text-teal-500 opacity-50 mt-0.5">•</span> {ev}
                      </p>
                    ))}
                  </div>
                </div>

                {/* ML Readiness Score */}
                <div className="bg-[#1e1e1e] p-4 rounded-lg border border-gray-800 shadow-sm flex flex-col justify-center">
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">ML Readiness Score</span>
                    <span className={`text-xl font-bold ${getReadinessColor(report.ml_readiness_score).split(' ')[0]}`}>
                      {(report.ml_readiness_score * 100).toFixed(0)} / 100
                    </span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2.5 mb-2 overflow-hidden">
                    <div
                      className={`h-2.5 rounded-full ${getReadinessColor(report.ml_readiness_score).split(' ')[1]}`}
                      style={{ width: `${report.ml_readiness_score * 100}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center gap-2">
                    {report.ml_readiness_score >= 0.85
                      ? <CheckCircle2 className="w-4 h-4 text-green-500" />
                      : <AlertTriangle className="w-4 h-4 text-amber-500" />}
                    <span className={`text-sm font-semibold ${getReadinessColor(report.ml_readiness_score).split(' ')[0]}`}>
                      {report.ml_readiness_label}
                    </span>
                  </div>
                </div>
              </div>

              {/* Recommended Next Steps */}
              {report.top_actions.length > 0 && (
                <div className="bg-teal-900/10 p-5 rounded-lg border border-teal-900/30">
                  <h3 className="text-sm font-bold text-teal-400 mb-3 flex items-center gap-2">
                    <TerminalSquare className="w-4 h-4" />
                    Recommended Next Steps
                  </h3>
                  <ul className="space-y-2">
                    {report.top_actions.map((action, i) => (
                      <li key={i} className="text-sm text-gray-300 flex items-start gap-3">
                        <span className="bg-teal-900/50 text-teal-300 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                          {i + 1}
                        </span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : null}

        </div>
      </div>
    </div>
  );
}
