import { useMemo } from 'react';
import { X, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BeforeAfterModalProps {
    column: string;
    columnType: string | null;
    beforeData: any[];
    afterData: any[];
    onClose: () => void;
}

function isNumeric(v: any) {
    return v !== null && v !== undefined && v !== '' && !isNaN(Number(v));
}

function colStats(data: any[], column: string) {
    const values = data.map(r => r[column]);
    const total = values.length;
    const nullCount = values.filter(v => v === null || v === undefined || v === '').length;
    const nonNull = values.filter(v => v !== null && v !== undefined && v !== '');
    const unique = new Set(nonNull.map(v => String(v))).size;
    const nums = nonNull.filter(isNumeric).map(Number);
    const mean = nums.length > 0 ? nums.reduce((a, b) => a + b, 0) / nums.length : null;
    return { total, nullCount, unique, mean };
}

function DiffBadge({ before, after, lower = false }: { before: number | null; after: number | null; lower?: boolean }) {
    if (before === null || after === null) return null;
    const delta = after - before;
    if (Math.abs(delta) < 0.0001) return <Minus className="h-3 w-3 text-gray-500 inline ml-1" />;
    const improved = lower ? delta < 0 : delta > 0;
    return (
        <span className={cn("inline-flex items-center gap-0.5 text-[9px] font-bold ml-1", improved ? 'text-green-400' : 'text-red-400')}>
            {improved ? <TrendingUp className="h-2.5 w-2.5" /> : <TrendingDown className="h-2.5 w-2.5" />}
            {delta > 0 ? '+' : ''}{typeof before === 'number' ? delta.toLocaleString(undefined, { maximumFractionDigits: 2 }) : delta}
        </span>
    );
}

export function BeforeAfterModal({ column, columnType, beforeData, afterData, onClose }: BeforeAfterModalProps) {
    const before = useMemo(() => colStats(beforeData, column), [beforeData, column]);
    const after = useMemo(() => colStats(afterData, column), [afterData, column]);

    // Sample rows — show first 15 non-null before and their corresponding after
    const SAMPLE = 15;
    const sampleRows = useMemo(() => {
        return beforeData.slice(0, SAMPLE).map((row, i) => ({
            before: row[column],
            after: afterData[i]?.[column] ?? null,
        }));
    }, [beforeData, afterData, column]);

    const fmtVal = (v: any) => {
        if (v === null || v === undefined || v === '') return <span className="text-gray-700 italic text-[9px]">null</span>;
        return <span>{String(v)}</span>;
    };

    const statsRows: { label: string; bv: string; av: string; delta: React.ReactNode }[] = [
        {
            label: 'Null Count',
            bv: before.nullCount.toLocaleString(),
            av: after.nullCount.toLocaleString(),
            delta: <DiffBadge before={before.nullCount} after={after.nullCount} lower={true} />,
        },
        {
            label: 'Unique Values',
            bv: before.unique.toLocaleString(),
            av: after.unique.toLocaleString(),
            delta: <DiffBadge before={before.unique} after={after.unique} />,
        },
        ...(before.mean !== null || after.mean !== null ? [{
            label: 'Mean',
            bv: before.mean !== null ? before.mean.toLocaleString(undefined, { maximumFractionDigits: 3 }) : '—',
            av: after.mean !== null ? after.mean.toLocaleString(undefined, { maximumFractionDigits: 3 }) : '—',
            delta: <DiffBadge before={before.mean} after={after.mean} />,
        }] : []),
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
            <div
                className="bg-[#141414] border border-teal-900/40 rounded-lg shadow-2xl w-[700px] max-w-[95vw] max-h-[85vh] flex flex-col overflow-hidden"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 bg-[#1a2f2f] border-b border-teal-900/40 shrink-0">
                    <div>
                        <h2 className="text-sm font-bold text-gray-100">Before / After: <span className="font-mono text-teal-400">{column}</span></h2>
                        <p className="text-[10px] text-gray-500 mt-0.5">Type: {columnType || 'Unknown'} · {before.total.toLocaleString()} rows</p>
                    </div>
                    <button onClick={onClose} className="text-gray-600 hover:text-gray-300 transition-colors">
                        <X className="h-4 w-4" />
                    </button>
                </div>

                {/* Stats diff */}
                <div className="px-4 py-3 border-b border-teal-900/30 shrink-0 bg-[#0e1e1e]">
                    <p className="text-[9px] text-gray-600 uppercase tracking-widest mb-2">Impact Summary</p>
                    <div className="grid grid-cols-3 gap-2">
                        {statsRows.map(({ label, bv, av, delta }) => (
                            <div key={label} className="bg-[#0a1515] rounded border border-teal-900/30 p-2">
                                <p className="text-[9px] text-gray-600 uppercase tracking-widest mb-1">{label}</p>
                                <div className="flex items-center gap-1.5">
                                    <span className="text-[11px] text-gray-500 line-through">{bv}</span>
                                    <span className="text-[10px] text-gray-500">→</span>
                                    <span className="text-[12px] font-bold text-gray-100">{av}</span>
                                    {delta}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Side-by-side sample rows */}
                <div className="flex-1 overflow-y-auto">
                    <div className="grid grid-cols-2 h-full divide-x divide-teal-900/30">
                        {/* Before column */}
                        <div>
                            <div className="px-3 py-2 bg-[#1a1a1a] border-b border-teal-900/20 sticky top-0 z-10">
                                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Before</p>
                            </div>
                            {sampleRows.map((row, i) => (
                                <div key={i} className={cn(
                                    "px-3 py-1.5 border-b border-teal-900/10 text-[11px] font-mono",
                                    String(row.before) !== String(row.after) ? 'bg-red-900/10 text-red-300' : 'text-gray-400'
                                )}>
                                    {fmtVal(row.before)}
                                </div>
                            ))}
                            {beforeData.length > SAMPLE && (
                                <div className="px-3 py-2 text-[10px] text-gray-700 italic">…and {(beforeData.length - SAMPLE).toLocaleString()} more rows</div>
                            )}
                        </div>

                        {/* After column */}
                        <div>
                            <div className="px-3 py-2 bg-[#1a2020] border-b border-teal-900/20 sticky top-0 z-10">
                                <p className="text-[10px] font-bold text-teal-500 uppercase tracking-widest">After</p>
                            </div>
                            {sampleRows.map((row, i) => (
                                <div key={i} className={cn(
                                    "px-3 py-1.5 border-b border-teal-900/10 text-[11px] font-mono",
                                    String(row.before) !== String(row.after) ? 'bg-green-900/10 text-green-300' : 'text-gray-400'
                                )}>
                                    {fmtVal(row.after)}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-4 py-2 border-t border-teal-900/40 bg-[#0a1515] text-[9px] text-gray-600 shrink-0">
                    Showing first {Math.min(SAMPLE, sampleRows.length)} rows · Changed cells highlighted
                </div>
            </div>
        </div>
    );
}
