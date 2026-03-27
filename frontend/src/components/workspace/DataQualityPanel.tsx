import { useState, useMemo } from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QualityAlert {
    entity: string;
    type: string;
    missing_pct: number;
    recommended_action: string;
}

interface DataQualityPanelProps {
    alerts: QualityAlert[];
    onClose: () => void;
}

const ALERT_META: Record<string, { label: string; color: string; icon: string; severity: 'high' | 'medium' | 'low' }> = {
    missing_values:          { label: 'Missing Values',          color: 'text-orange-400', icon: '⚠',  severity: 'medium' },
    placeholder_values:      { label: 'Placeholder / Sentinel',  color: 'text-orange-400', icon: '⚠',  severity: 'medium' },
    mixed_type_numeric:      { label: 'Mixed Numeric Types',     color: 'text-yellow-400', icon: '⚡', severity: 'low'    },
    mixed_type_worded:       { label: 'Mixed Text/Number Types', color: 'text-yellow-400', icon: '⚡', severity: 'low'    },
    invalid_numeric_format:  { label: 'Invalid Numeric Format',  color: 'text-red-400',    icon: '✖',  severity: 'high'   },
    invalid_date_format:     { label: 'Invalid Date Format',     color: 'text-red-400',    icon: '✖',  severity: 'high'   },
    duplicate_rows:          { label: 'Duplicate Rows',          color: 'text-red-400',    icon: '✖',  severity: 'high'   },
    outliers:                { label: 'Outliers Detected',       color: 'text-amber-400',  icon: '⚠',  severity: 'medium' },
    class_imbalance:         { label: 'Class Imbalance',         color: 'text-purple-400', icon: '⚡', severity: 'medium' },
    skewed_distribution:     { label: 'Skewed Distribution',     color: 'text-yellow-400', icon: '⚡', severity: 'low'    },
    constant_column:         { label: 'Constant Column',         color: 'text-gray-400',   icon: '—',  severity: 'low'    },
    high_cardinality:        { label: 'High Cardinality',        color: 'text-yellow-400', icon: '⚡', severity: 'low'    },
};

function severity(type: string): number {
    const s = ALERT_META[type]?.severity;
    return s === 'high' ? 0 : s === 'medium' ? 1 : 2;
}

export function DataQualityPanel({ alerts, onClose }: DataQualityPanelProps) {
    const [expandedCols, setExpandedCols] = useState<Set<string>>(new Set());

    const grouped = useMemo(() => {
        const map: Record<string, QualityAlert[]> = {};
        alerts.forEach(a => {
            if (!map[a.entity]) map[a.entity] = [];
            map[a.entity].push(a);
        });
        return Object.entries(map)
            .sort(([, a], [, b]) =>
                Math.min(...a.map(x => severity(x.type))) - Math.min(...b.map(x => severity(x.type)))
            );
    }, [alerts]);

    const toggleCol = (col: string) => {
        setExpandedCols(prev => {
            const next = new Set(prev);
            next.has(col) ? next.delete(col) : next.add(col);
            return next;
        });
    };

    const highCount = alerts.filter(a => ALERT_META[a.type]?.severity === 'high').length;
    const medCount  = alerts.filter(a => ALERT_META[a.type]?.severity === 'medium').length;

    return (
        <div className="flex flex-col h-full bg-[#0e1a1a] border-l border-teal-900/40 text-xs">
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-1.5 bg-[#152020] border-b border-teal-900/40 shrink-0">
                <div className="flex items-center gap-2">
                    <AlertTriangle className="h-3.5 w-3.5 text-orange-400 shrink-0" />
                    <span className="font-bold text-gray-200 text-[11px] uppercase tracking-wider">Data Quality</span>
                </div>
                <div className="flex items-center gap-1.5">
                    {highCount > 0 && (
                        <span className="px-1.5 py-0.5 rounded bg-red-900/40 text-red-400 font-bold text-[10px]">{highCount} HIGH</span>
                    )}
                    {medCount > 0 && (
                        <span className="px-1.5 py-0.5 rounded bg-orange-900/30 text-orange-400 font-bold text-[10px]">{medCount} MED</span>
                    )}
                    <button onClick={onClose} className="text-gray-600 hover:text-gray-300 transition-colors ml-1">
                        <X className="h-3.5 w-3.5" />
                    </button>
                </div>
            </div>

            {alerts.length === 0 ? (
                <div className="flex flex-col items-center justify-center flex-1 gap-1.5 text-gray-600 p-4">
                    <span className="text-xl">✅</span>
                    <p className="text-[11px]">No quality issues detected!</p>
                </div>
            ) : (
                <div className="flex-1 overflow-y-auto divide-y divide-teal-900/20">
                    {grouped.map(([col, colAlerts]) => {
                        const isOpen = expandedCols.has(col);
                        const topSeverity = colAlerts.some(a => ALERT_META[a.type]?.severity === 'high')
                            ? 'high' : colAlerts.some(a => ALERT_META[a.type]?.severity === 'medium')
                                ? 'medium' : 'low';
                        const severityColor = topSeverity === 'high' ? 'text-red-400' : topSeverity === 'medium' ? 'text-orange-400' : 'text-yellow-400';
                        const severityBg    = topSeverity === 'high' ? 'bg-red-900/20'  : topSeverity === 'medium' ? 'bg-orange-900/15' : 'bg-yellow-900/10';

                        return (
                            <div key={col}>
                                {/* Column row */}
                                <button
                                    onClick={() => toggleCol(col)}
                                    className={cn("w-full flex items-center gap-2 px-3 py-1.5 hover:bg-white/5 transition-colors text-left", severityBg)}
                                >
                                    {isOpen
                                        ? <ChevronDown  className={cn("h-3 w-3 shrink-0", severityColor)} />
                                        : <ChevronRight className={cn("h-3 w-3 shrink-0", severityColor)} />
                                    }
                                    <span className="font-mono font-semibold text-gray-200 truncate flex-1">{col}</span>
                                    <span className={cn("text-[9px] font-bold uppercase px-1.5 py-0.5 rounded shrink-0",
                                        topSeverity === 'high'   ? 'text-red-400 bg-red-900/30' :
                                        topSeverity === 'medium' ? 'text-orange-400 bg-orange-900/30' :
                                                                   'text-yellow-400 bg-yellow-900/30'
                                    )}>
                                        {colAlerts.length} {colAlerts.length === 1 ? 'issue' : 'issues'}
                                    </span>
                                </button>

                                {/* Expanded alert list */}
                                {isOpen && (
                                    <div className="bg-[#0a1515] border-t border-teal-900/20 divide-y divide-teal-900/10">
                                        {colAlerts.map((alert, i) => {
                                            const meta = ALERT_META[alert.type];
                                            return (
                                                <div key={i} className="flex items-start gap-2 px-4 py-1.5">
                                                    <span className={cn("text-[11px] shrink-0 mt-px", meta?.color || 'text-gray-400')}>
                                                        {meta?.icon || '•'}
                                                    </span>
                                                    <div className="flex-1 min-w-0">
                                                        <p className={cn("font-semibold text-[10px]", meta?.color || 'text-gray-400')}>
                                                            {meta?.label || alert.type}
                                                            {alert.missing_pct > 0 && (
                                                                <span className="text-gray-500 font-normal"> — {alert.missing_pct.toFixed(1)}% of rows</span>
                                                            )}
                                                        </p>
                                                        <p className="text-gray-600 text-[9px] mt-0.5 italic">{alert.recommended_action}</p>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Footer */}
            <div className="px-3 py-1 border-t border-teal-900/40 bg-[#0a1515] shrink-0">
                <p className="text-[9px] text-gray-600">
                    {alerts.length} issue{alerts.length !== 1 ? 's' : ''} across {grouped.length} column{grouped.length !== 1 ? 's' : ''}
                </p>
            </div>
        </div>
    );
}
