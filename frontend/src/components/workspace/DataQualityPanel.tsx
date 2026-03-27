import { useState, useMemo } from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, X, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface QualityAlert {
    entity: string;
    type: string;
    missing_pct: number;
    recommended_action: string;
}

interface DataQualityPanelProps {
    alerts: QualityAlert[];
    onAddStep: (operation: string, params: any) => Promise<void>;
    onClose: () => void;
}

const ALERT_META: Record<string, { label: string; color: string; icon: string; severity: 'high' | 'medium' | 'low' }> = {
    missing_values: { label: 'Missing Values', color: 'text-orange-400', icon: '⚠', severity: 'medium' },
    mixed_type_numeric: { label: 'Mixed Numeric Types', color: 'text-yellow-400', icon: '⚡', severity: 'low' },
    mixed_type_worded: { label: 'Mixed Text/Number Types', color: 'text-yellow-400', icon: '⚡', severity: 'low' },
    invalid_numeric_format: { label: 'Invalid Numeric Format', color: 'text-red-400', icon: '✖', severity: 'high' },
    invalid_date_format: { label: 'Invalid Date Format', color: 'text-red-400', icon: '✖', severity: 'high' },
};

function getQuickFix(alert: QualityAlert): { label: string; op: string; params: any } | null {
    switch (alert.type) {
        // missing_values intentionally has no quick-fix — the right strategy (drop, fill mean/median/mode/constant)
        // depends heavily on the column's domain and semantics. Offering a generic fix would be misleading.
        case 'mixed_type_numeric':
        case 'mixed_type_worded':
            return { label: 'Convert to Numeric', op: 'convert_type', params: { columns: [alert.entity], type: 'text_to_numeric' } };
        case 'invalid_numeric_format':
            return { label: 'Convert to Numeric', op: 'convert_type', params: { columns: [alert.entity], type: 'numeric' } };
        case 'invalid_date_format':
            return { label: 'Convert to Date', op: 'convert_type', params: { columns: [alert.entity], type: 'date' } };
        default:
            return null;
    }
}

function severity(type: string): number {
    const s = ALERT_META[type]?.severity;
    return s === 'high' ? 0 : s === 'medium' ? 1 : 2;
}

export function DataQualityPanel({ alerts, onAddStep, onClose }: DataQualityPanelProps) {
    const [expandedCols, setExpandedCols] = useState<Set<string>>(new Set());

    // Group alerts by entity (column)
    const grouped = useMemo(() => {
        const map: Record<string, QualityAlert[]> = {};
        alerts.forEach(a => {
            if (!map[a.entity]) map[a.entity] = [];
            map[a.entity].push(a);
        });
        // Sort each group by severity
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
    const medCount = alerts.filter(a => ALERT_META[a.type]?.severity === 'medium').length;

    return (
        <div className="flex flex-col h-full bg-[#0e1a1a] border-l border-teal-900/40 text-xs">
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2 bg-[#152020] border-b border-teal-900/40 shrink-0">
                <div className="flex items-center gap-2">
                    <AlertTriangle className="h-3.5 w-3.5 text-orange-400 shrink-0" />
                    <span className="font-bold text-gray-200 text-[11px] uppercase tracking-wider">Data Quality Report</span>
                </div>
                <div className="flex items-center gap-2">
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
                <div className="flex flex-col items-center justify-center flex-1 gap-2 text-gray-600 p-4">
                    <span className="text-2xl">✅</span>
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
                        const severityBg = topSeverity === 'high' ? 'bg-red-900/20' : topSeverity === 'medium' ? 'bg-orange-900/15' : 'bg-yellow-900/10';

                        return (
                            <div key={col}>
                                {/* Column row */}
                                <button
                                    onClick={() => toggleCol(col)}
                                    className={cn("w-full flex items-center gap-2 px-3 py-2 hover:bg-white/5 transition-colors text-left", severityBg)}
                                >
                                    {isOpen
                                        ? <ChevronDown className={cn("h-3 w-3 shrink-0", severityColor)} />
                                        : <ChevronRight className={cn("h-3 w-3 shrink-0", severityColor)} />
                                    }
                                    <span className="font-mono font-semibold text-gray-200 truncate flex-1">{col}</span>
                                    <span className={cn("text-[9px] font-bold uppercase px-1.5 py-0.5 rounded shrink-0",
                                        topSeverity === 'high' ? 'text-red-400 bg-red-900/30' :
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
                                            const fix = getQuickFix(alert);
                                            return (
                                                <div key={i} className="px-4 py-2">
                                                    <div className="flex items-start gap-2">
                                                        <span className={cn("text-[11px] shrink-0 mt-px", meta?.color || 'text-gray-400')}>
                                                            {meta?.icon || '•'}
                                                        </span>
                                                        <div className="flex-1 min-w-0">
                                                            <p className={cn("font-semibold text-[10px]", meta?.color || 'text-gray-400')}>
                                                                {meta?.label || alert.type}
                                                            </p>
                                                            {alert.missing_pct > 0 && (
                                                                <p className="text-gray-500 text-[10px] mt-0.5">
                                                                    Affects {alert.missing_pct.toFixed(1)}% of rows
                                                                </p>
                                                            )}
                                                            <p className="text-gray-600 text-[9px] mt-0.5 italic">{alert.recommended_action}</p>
                                                        </div>
                                                    </div>
                                                    {fix && (
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="mt-1.5 h-5 text-[9px] px-2 text-teal-400 border border-teal-900/50 hover:bg-teal-900/20 hover:text-teal-300 gap-1"
                                                            onClick={() => onAddStep(fix.op, fix.params)}
                                                        >
                                                            <Zap className="h-2.5 w-2.5" /> {fix.label}
                                                        </Button>
                                                    )}
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

            {/* Footer summary */}
            <div className="px-3 py-1.5 border-t border-teal-900/40 bg-[#0a1515] shrink-0">
                <p className="text-[9px] text-gray-600">
                    {alerts.length} issue{alerts.length !== 1 ? 's' : ''} across {grouped.length} column{grouped.length !== 1 ? 's' : ''}
                </p>
            </div>
        </div>
    );
}
