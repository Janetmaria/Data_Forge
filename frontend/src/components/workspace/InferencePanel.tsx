import { useQuery } from '@tanstack/react-query';
import { X, Sparkles, AlertTriangle, Info, Lightbulb, CheckCircle2, AlertCircle, TerminalSquare } from 'lucide-react';
import api from '@/lib/api';

// --- Interfaces matching Pydantic schemas ---
interface DomainResult {
  domain: 'hr' | 'finance' | 'healthcare' | 'ecommerce' | 'iot_sensor' | 'generic';
  confidence: number;
  evidence: string[];
}

interface Inference {
  id: string;
  severity: 'critical' | 'warning' | 'info' | 'suggestion';
  category: 'data_quality' | 'ml_readiness' | 'structure' | 'statistics' | 'consistency';
  title: string;
  detail: string;
  affected_columns: string[];
  suggested_action: string;
  auto_fixable: boolean;
  fix_operation?: string;
}

interface InferenceReport {
  domain_detection: DomainResult;
  general_inferences: Inference[];
  domain_inferences: Inference[];
  all_inferences: Inference[];
  critical_count: number;
  warning_count: number;
  info_count: number;
  suggestion_count: number;
  ml_readiness_score: number;
  ml_readiness_label: 'Not Ready' | 'Needs Work' | 'Almost Ready' | 'Ready';
  top_actions: string[];
}

interface InferencePanelProps {
  datasetId: string;
  onClose: () => void;
  onApplyFix?: (operation: string, columns: string[]) => void;
}

export default function InferencePanel({ datasetId, onClose, onApplyFix }: InferencePanelProps) {
  const { data: report, isLoading, error } = useQuery<InferenceReport>({
    queryKey: ['inference', datasetId],
    queryFn: async () => {
      const res = await api.get(`/datasets/${datasetId}/infer`);
      return res.data;
    },
    staleTime: 0, // Always refetch when opened to get latest pipeline state
  });

  const getReadinessColor = (score: number) => {
    if (score >= 0.85) return 'text-green-500 bg-green-500';
    if (score >= 0.65) return 'text-lime-500 bg-lime-500';
    if (score >= 0.40) return 'text-amber-500 bg-amber-500';
    return 'text-red-500 bg-red-500';
  };

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'critical':
        return { border: 'border-l-red-500', icon: <AlertCircle className="w-4 h-4 text-red-500" />, bg: 'bg-red-500/5' };
      case 'warning':
        return { border: 'border-l-amber-500', icon: <AlertTriangle className="w-4 h-4 text-amber-500" />, bg: 'bg-amber-500/5' };
      case 'info':
        return { border: 'border-l-blue-500', icon: <Info className="w-4 h-4 text-blue-500" />, bg: 'bg-blue-500/5' };
      case 'suggestion':
        return { border: 'border-l-teal-500', icon: <Lightbulb className="w-4 h-4 text-teal-500" />, bg: 'bg-teal-500/5' };
      default:
        return { border: 'border-l-gray-500', icon: <Info className="w-4 h-4 text-gray-500" />, bg: 'bg-gray-500/5' };
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#1e1e1e] border border-gray-700 shadow-2xl rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
        
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
              {/* Top Summary Row */}
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

                {/* Readiness Score */}
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
                    {report.ml_readiness_score >= 0.85 ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : <AlertTriangle className="w-4 h-4 text-amber-500" />}
                    <span className={`text-sm font-semibold ${getReadinessColor(report.ml_readiness_score).split(' ')[0]}`}>{report.ml_readiness_label}</span>
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
                        <span className="bg-teal-900/50 text-teal-300 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">{i + 1}</span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Inferences List */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-2 border-b border-gray-800 pb-2">Detailed Findings ({report.all_inferences.length})</h3>
                
                {report.all_inferences.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 border border-dashed border-gray-700 rounded-lg">
                    No issues found! Your dataset looks very clean.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {report.all_inferences.map((inf) => {
                      const styles = getSeverityStyles(inf.severity);
                      return (
                        <div key={inf.id} className={`p-4 rounded-lg border ${styles.border} ${styles.bg} border-t-gray-800 border-r-gray-800 border-b-gray-800 border-l-4 shadow-sm`}>
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-2 flex-1">
                              <div className="flex items-center gap-2">
                                {styles.icon}
                                <span className="font-bold text-gray-200 text-sm">{inf.title}</span>
                                <span className="text-[10px] font-mono uppercase bg-black/40 px-2 py-0.5 rounded text-gray-400 ml-2">
                                  {inf.category.replace('_', ' ')}
                                </span>
                              </div>
                              <p className="text-sm text-gray-400 leading-relaxed">{inf.detail}</p>
                              
                              <div className="flex flex-wrap gap-2 pt-1">
                                {inf.affected_columns.map(c => (
                                  <span key={c} className="text-[10px] font-mono bg-white/5 text-gray-300 px-2 py-1 rounded border border-white/10">
                                    {c}
                                  </span>
                                ))}
                              </div>
                              
                              <div className="text-sm text-gray-300 italic pt-2 border-t border-white/5 mt-2">
                                <span className="text-gray-500 not-italic font-bold mr-2">Action:</span>
                                {inf.suggested_action}
                              </div>
                            </div>

                            {/* Auto-fix button if supported */}
                            {inf.auto_fixable && inf.fix_operation && onApplyFix && (
                              <button 
                                onClick={() => {
                                  onApplyFix(inf.fix_operation!, inf.affected_columns.filter(c => c !== '(entire dataset)'));
                                  onClose();
                                }}
                                className="shrink-0 bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold px-3 py-1.5 rounded transition-colors shadow-sm"
                              >
                                Fix Now
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          ) : null}
          
        </div>
      </div>
    </div>
  );
}
