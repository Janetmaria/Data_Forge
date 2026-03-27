import { cn } from '@/lib/utils';

interface PreviewPanelProps {
  data: any[];
  columns: string[];
  selectedColumn: string | null;
  onSelectColumn: (col: string) => void;
  loading?: boolean;
}

export function PreviewPanel({ data, columns, selectedColumn, onSelectColumn, loading }: PreviewPanelProps) {
  // If loading, show spinner
  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full bg-[#1e1e1e] text-gray-500 text-xs">
        <div className="w-6 h-6 border-2 border-t-teal-500 border-gray-700 rounded-full animate-spin mb-2"></div>
        <div>Updating preview...</div>
      </div>
    );
  }

  // Ensure data is an array
  const safeData = Array.isArray(data) ? data : [];
  // Ensure columns is an array
  const safeColumns = Array.isArray(columns) ? columns : [];

  if (safeData.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full bg-[#1e1e1e] text-gray-500">
        <div className="text-lg font-semibold mb-2">No Data Loaded</div>
        <div className="text-xs text-gray-600">Import a file or reset pipeline</div>
      </div>
    );
  }

  const formatCellValue = (val: any) => {
    if (val === null || val === undefined) return null;
    if (typeof val === 'object') {
      try {
        return JSON.stringify(val);
      } catch (e) {
        return String(val);
      }
    }
    return String(val);
  };

  return (
    <div className="flex-1 overflow-auto bg-[#1e1e1e] relative h-full w-full">
      <div className="min-w-max h-full">
        <table className="w-full text-xs border-collapse text-left">
          <thead className="bg-[#252526] sticky top-0 z-10 shadow-sm border-b border-black">
            <tr>
              <th className="p-2 text-center font-mono text-[10px] text-gray-500 w-10 border-r border-black/50 bg-[#252526] sticky left-0 z-20">#</th>
              {safeColumns.map((col) => (
                <th
                  key={col}
                  onClick={() => onSelectColumn(selectedColumn === col ? null : col)}
                  className={cn(
                    "p-2 font-medium border-r border-black/50 min-w-[120px] cursor-pointer hover:bg-[#333333] transition-colors select-none group text-gray-300 bg-[#252526]",
                    selectedColumn === col && "bg-[#094771] text-white"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="truncate">{col}</span>
                    {selectedColumn === col && <div className="h-1 w-1 rounded-full bg-white/50" />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {safeData.map((row, i) => (
              <tr key={i} className="group hover:bg-[#2a2d2e] border-b border-black/20">
                <td className="p-1 border-r border-black/20 font-mono text-[10px] text-gray-600 text-center bg-[#252526] sticky left-0 z-10 shadow-[1px_0_0_black]">
                  {i + 1}
                </td>
                {safeColumns.map((col) => (
                  <td
                    key={col}
                    className={cn(
                      "p-1.5 border-r border-black/20 truncate max-w-[200px] text-gray-400 font-mono",
                      selectedColumn === col && "bg-[#094771]/20 text-gray-200"
                    )}
                    title={formatCellValue(row[col]) || ""}
                  >
                    {row[col] === null ? (
                      <span className="text-gray-700 italic text-[10px]">null</span>
                    ) : (
                      formatCellValue(row[col])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
