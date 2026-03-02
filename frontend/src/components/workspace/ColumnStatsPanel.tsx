import { useMemo } from 'react';

interface ColumnStatsPanelProps {
    column: string;
    columnType: string | null;
    data: any[]; // the live preview rows
}

function isNumeric(v: any) {
    return v !== null && v !== undefined && v !== '' && !isNaN(Number(v));
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

        let min: string | null = null;
        let max: string | null = null;
        let mean: string | null = null;

        if (isNum && numericValues.length > 0) {
            min = Math.min(...numericValues).toLocaleString(undefined, { maximumFractionDigits: 4 });
            max = Math.max(...numericValues).toLocaleString(undefined, { maximumFractionDigits: 4 });
            const sum = numericValues.reduce((a, b) => a + b, 0);
            mean = (sum / numericValues.length).toLocaleString(undefined, { maximumFractionDigits: 4 });
        }

        // Sample values for categorical/text
        const topSamples = [...new Set(nonNullValues.map(v => String(v)))].slice(0, 3);

        return { total, nulls, nullPct, uniqueCount, min, max, mean, isNum, topSamples };
    }, [column, data]);

    if (!stats) return null;

    const rows: { label: string; value: string | number }[] = [
        { label: 'Type', value: columnType || 'Unknown' },
        { label: 'Total Rows', value: stats.total.toLocaleString() },
        { label: 'Null Count', value: stats.nulls.toLocaleString() },
        { label: 'Null %', value: `${stats.nullPct}%` },
        { label: 'Unique', value: stats.uniqueCount.toLocaleString() },
    ];

    if (stats.isNum) {
        rows.push(
            { label: 'Min', value: stats.min! },
            { label: 'Max', value: stats.max! },
            { label: 'Mean', value: stats.mean! },
        );
    } else {
        rows.push({ label: 'Samples', value: stats.topSamples.join(', ') });
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
        </div>
    );
}
