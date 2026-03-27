import { useMemo } from 'react';

interface ColumnStatsPanelProps {
    column: string;
    columnType: string | null;
    data: any[]; // the live preview rows
}

function isNumeric(v: any) {
    return v !== null && v !== undefined && v !== '' && !isNaN(Number(v));
}

// Column name patterns where charts are meaningless regardless of cardinality
const ID_LIKE_PATTERNS = [
    'phone', 'email', 'mail', 'ip', 'address', 'url', 'website', 'credit',
    'card', 'aadhaar', 'ssn', 'passport', 'employee_id', 'emp_id', 'user_id',
    'order_id', 'transaction', 'uuid', 'guid', 'token', 'hash', 'code',
];

function isIdLikeColumn(colName: string): boolean {
    const lower = colName.toLowerCase();
    return ID_LIKE_PATTERNS.some(p => lower.includes(p));
}

/** Clip values to IQR fences to remove extreme outliers before histogram binning */
function clipToIQR(sorted: number[]): number[] {
    const n = sorted.length;
    if (n < 4) return sorted;
    const q1 = sorted[Math.floor(n * 0.25)];
    const q3 = sorted[Math.floor(n * 0.75)];
    const iqr = q3 - q1;
    if (iqr === 0) return sorted; // all same value, let caller handle it
    const lo = q1 - 1.5 * iqr;
    const hi = q3 + 1.5 * iqr;
    return sorted.filter(v => v >= lo && v <= hi);
}

function computeStats(numericValues: number[]) {
    const n = numericValues.length;
    if (n === 0) return { min: 0, max: 0, mean: 0, median: 0, stdDev: 0, skewness: 0, kurtosis: 0 };

    const sorted = [...numericValues].sort((a, b) => a - b);
    const min = sorted[0];
    const max = sorted[n - 1];
    const mean = numericValues.reduce((a, b) => a + b, 0) / n;

    const median = n % 2 === 0
        ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2
        : sorted[Math.floor(n / 2)];

    const variance = numericValues.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / n;
    const stdDev = Math.sqrt(variance);

    let skewness = 0;
    let kurtosis = 0;
    if (stdDev > 0 && n >= 3) {
        skewness = (numericValues.reduce((sum, v) => sum + Math.pow((v - mean) / stdDev, 3), 0) / n);
        kurtosis = (numericValues.reduce((sum, v) => sum + Math.pow((v - mean) / stdDev, 4), 0) / n) - 3;
    }

    return { min, max, mean, median, stdDev, skewness, kurtosis };
}

function MiniHistogram({ values }: { values: number[] }) {
    const BINS = 10;
    const W = 200;
    const H = 50;
    const PAD = 2;

    // Clip outliers using IQR before binning so sentinel values (-9999, 9999999) don't ruin the axis
    const sorted = [...values].sort((a, b) => a - b);
    const clipped = clipToIQR(sorted);
    if (clipped.length < 2) return null;

    const min = clipped[0];
    const max = clipped[clipped.length - 1];
    if (min === max) return null;

    const binSize = (max - min) / BINS;
    const bins = Array(BINS).fill(0);
    clipped.forEach(v => {
        const idx = Math.min(Math.floor((v - min) / binSize), BINS - 1);
        bins[idx]++;
    });

    const maxCount = Math.max(...bins);
    const barW = (W - PAD * 2) / BINS;
    const clippedCount = values.length - clipped.length;

    return (
        <div>
            <svg width={W} height={H} className="mt-1" aria-label="Histogram">
                {bins.map((count, i) => {
                    const barH = maxCount > 0 ? ((count / maxCount) * (H - 8)) : 0;
                    const x = PAD + i * barW;
                    const y = H - barH - 4;
                    return (
                        <g key={i}>
                            <rect
                                x={x + 0.5}
                                y={y}
                                width={Math.max(barW - 1.5, 1)}
                                height={barH}
                                fill="#14b8a6"
                                opacity={0.75}
                                rx={1}
                            />
                        </g>
                    );
                })}
                {/* X-axis line */}
                <line x1={PAD} y1={H - 4} x2={W - PAD} y2={H - 4} stroke="#374151" strokeWidth={0.5} />
                <text x={PAD} y={H} fontSize={8} fill="#6b7280">{fmtAxisVal(min)}</text>
                <text x={W - PAD} y={H} fontSize={8} fill="#6b7280" textAnchor="end">{fmtAxisVal(max)}</text>
            </svg>
            {clippedCount > 0 && (
                <p className="text-[8px] text-gray-700 mt-0.5">{clippedCount} outlier{clippedCount !== 1 ? 's' : ''} excluded from view</p>
            )}
        </div>
    );
}

function MiniBarChart({ items }: { items: { label: string; count: number }[] }) {
    const W = 200;
    const barH = 12;
    const GAP = 4;
    const LabelW = 80;
    const H = items.length * (barH + GAP);
    const maxCount = Math.max(...items.map(i => i.count), 1);

    return (
        <svg width={W} height={H} className="mt-1" aria-label="Bar chart">
            {items.map((item, i) => {
                const y = i * (barH + GAP);
                const barWidth = ((item.count / maxCount) * (W - LabelW - 6));
                const label = item.label.length > 12 ? item.label.slice(0, 11) + '…' : item.label;
                return (
                    <g key={i}>
                        <text x={0} y={y + barH - 2} fontSize={8} fill="#9ca3af" textAnchor="start">{label}</text>
                        <rect x={LabelW} y={y + 1} width={Math.max(barWidth, 1)} height={barH - 2} fill="#0d9488" opacity={0.7} rx={1.5} />
                        <text x={LabelW + barWidth + 3} y={y + barH - 2} fontSize={8} fill="#6b7280">{item.count}</text>
                    </g>
                );
            })}
        </svg>
    );
}

function fmt(n: number, digits = 3) {
    if (!isFinite(n)) return 'N/A';
    return n.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
}

/** Compact axis label: 50000 → 50K, 1500000 → 1.5M */
function fmtAxisVal(n: number): string {
    if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (Math.abs(n) >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, '') + 'K';
    return n.toFixed(1);
}

export function ColumnStatsPanel({ column, columnType, data }: ColumnStatsPanelProps) {
    const stats = useMemo(() => {
        if (!column || !data || data.length === 0) return null;

        const values = data.map(row => row[column]);
        const total = values.length;
        const nulls = values.filter(v => v === null || v === undefined || v === '').length;
        const nonNullValues = values.filter(v => v !== null && v !== undefined && v !== '');
        const uniqueCount = new Set(nonNullValues.map(v => String(v))).size;
        const nullPct = total > 0 ? ((nulls / total) * 100).toFixed(1) : '0.0';

        const numericValues = nonNullValues.filter(isNumeric).map(Number);
        const isNum = numericValues.length > 0 && numericValues.length >= nonNullValues.length * 0.5;

        let numStats: ReturnType<typeof computeStats> | null = null;
        if (isNum && numericValues.length > 0) {
            numStats = computeStats(numericValues);
        }

        // Top values for categorical chart
        const freqMap: Record<string, number> = {};
        nonNullValues.forEach(v => {
            const k = String(v);
            freqMap[k] = (freqMap[k] || 0) + 1;
        });
        const topItems = Object.entries(freqMap)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([label, count]) => ({ label, count }));

        return { total, nulls, nullPct, uniqueCount, isNum, numStats, numericValues, topItems };
    }, [column, data]);

    if (!stats) return null;

    const { numStats } = stats;

    const rows: { label: string; value: string | number }[] = [
        { label: 'Type', value: columnType || 'Unknown' },
        { label: 'Total Rows', value: stats.total.toLocaleString() },
        { label: 'Null Count', value: `${stats.nulls.toLocaleString()} (${stats.nullPct}%)` },
        { label: 'Unique', value: stats.uniqueCount.toLocaleString() }
    ];

    // Only show numeric statistics for columns that actually represent measures, not identifiers
    if (stats.isNum && numStats && !isIdLikeColumn(column)) {
        rows.push(
            { label: 'Min', value: fmt(numStats.min) },
            { label: 'Max', value: fmt(numStats.max) },
            { label: 'Mean', value: fmt(numStats.mean) },
            { label: 'Median', value: fmt(numStats.median) },
            { label: 'Std Dev', value: fmt(numStats.stdDev) },
            { label: 'Skewness', value: fmt(numStats.skewness) },
            { label: 'Kurtosis', value: fmt(numStats.kurtosis) },
        );
    }

    return (
        <div className="mx-2 mb-3 rounded border border-teal-900/40 bg-[#0d1f1f] overflow-hidden">
            <div className="px-2 py-1 bg-teal-900/30 border-b border-teal-900/40">
                <p className="text-[10px] font-bold text-teal-400 uppercase tracking-widest truncate">
                    ⓘ {column}
                </p>
            </div>
            <table className="w-full text-[10px]">
                <tbody>
                    {rows.map(({ label, value }) => (
                        <tr key={label} className="border-b border-teal-900/20 last:border-0">
                            <td className="px-2 py-[3px] text-gray-500 w-[44%] font-medium">{label}</td>
                            <td className="px-2 py-[3px] text-gray-200 font-mono break-all">{value}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {/* Mini Histogram: only for numeric columns with some repetition, and not ID-like by name */}
            {stats.isNum && stats.numericValues.length > 1 && stats.uniqueCount < stats.total * 0.95 && !isIdLikeColumn(column) && (
                <div className="px-2 pb-2 pt-1 border-t border-teal-900/20">
                    <p className="text-[9px] text-gray-600 uppercase tracking-widest mb-0.5">Distribution</p>
                    <MiniHistogram values={stats.numericValues} />
                </div>
            )}

            {/* Mini Bar Chart: only for low-cardinality columns — suppress for phone, email, ID-like names or fields */}
            {!stats.isNum && stats.topItems.length > 0 && stats.uniqueCount <= 20 && stats.uniqueCount < stats.total * 0.6 && !isIdLikeColumn(column) && (
                <div className="px-2 pb-2 pt-1 border-t border-teal-900/20">
                    <p className="text-[9px] text-gray-600 uppercase tracking-widest mb-0.5">Top Values</p>
                    <MiniBarChart items={stats.topItems} />
                </div>
            )}
        </div>
    );
}
