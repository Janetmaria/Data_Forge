import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight, Type, Wand2, Database, GitMerge } from 'lucide-react';
import { cn } from '@/lib/utils';
import { MergeDialog } from './MergeDialog';
import { ScaleDialog } from './ScaleDialog';

interface SidebarProps {
  selectedColumn: string | null;
  columnType: string | null;
  onAddStep: (operation: string, params: any) => void;
  currentDatasetId: string;
  currentDatasetColumns: any[];
}

interface OperationGroup {
  title: string;
  icon: any;
  operations: Operation[];
}

interface Operation {
  id: string;
  label: string;
  description?: string;
  validTypes?: string[]; // 'Numeric', 'String', 'Date', 'Boolean', 'All'
  requiresColumn?: boolean;
  params?: any; // Default params
  isCustomAction?: boolean; // If true, opens a dialog instead of direct action
}

export function Sidebar({ selectedColumn, columnType, onAddStep, currentDatasetId, currentDatasetColumns }: SidebarProps) {
  const [openGroups, setOpenGroups] = useState<string[]>(['cleaning', 'standardization', 'advanced', 'data integration']);
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
  const [scaleDialogOpen, setScaleDialogOpen] = useState(false);

  const toggleGroup = (id: string) => {
    setOpenGroups(prev =>
      prev.includes(id) ? prev.filter(g => g !== id) : [...prev, id]
    );
  };

  const operations: OperationGroup[] = [
    {
      title: 'Data Integration',
      icon: GitMerge,
      operations: [
        { id: 'merge_datasets', label: 'Merge / Join Datasets', validTypes: ['All'], isCustomAction: true },
      ]
    },
    {
      title: 'Data Cleaning',
      icon: Database,
      operations: [
        { id: 'drop_duplicates', label: 'Remove Duplicates', validTypes: ['All'] },
        { id: 'drop_columns', label: 'Drop Column', requiresColumn: true, validTypes: ['All'] },
        { id: 'drop_missing', label: 'Drop Missing Rows', validTypes: ['All'] },
        { id: 'fill_missing', label: 'Fill Missing (Mean)', requiresColumn: true, validTypes: ['Numeric'], params: { method: 'mean' } },
        { id: 'fill_missing_mode', label: 'Fill Missing (Mode)', requiresColumn: true, validTypes: ['All'], params: { method: 'mode' } },
      ]
    },
    {
      title: 'Standardization',
      icon: Type,
      operations: [
        { id: 'text_case_upper', label: 'To Uppercase', requiresColumn: true, validTypes: ['String', 'Text', 'Categorical'], params: { case: 'upper' } },
        { id: 'text_case_lower', label: 'To Lowercase', requiresColumn: true, validTypes: ['String', 'Text', 'Categorical'], params: { case: 'lower' } },
        { id: 'text_case_title', label: 'To Title Case', requiresColumn: true, validTypes: ['String', 'Text', 'Categorical'], params: { case: 'title' } },
        { id: 'convert_type_numeric', label: 'Convert to Numeric', requiresColumn: true, validTypes: ['All'], params: { type: 'numeric' } },
        { id: 'convert_type_string', label: 'Convert to String', requiresColumn: true, validTypes: ['All'], params: { type: 'string' } },
        { id: 'convert_type_text_to_numeric', label: 'Mixed → Numbers (20, thirty → 20, 30)', requiresColumn: true, validTypes: ['All'], params: { type: 'text_to_numeric' } },
        { id: 'convert_type_numeric_to_text', label: 'Mixed → Words (20, thirty → twenty, thirty)', requiresColumn: true, validTypes: ['All'], params: { type: 'numeric_to_text' } },
      ]
    },
    {
      title: 'Advanced',
      icon: Wand2,
      operations: [
        { id: 'knn_impute', label: 'KNN Imputation', validTypes: ['Numeric'], params: { n_neighbors: 5 } },
        { id: 'normalize', label: 'Min-Max Scaling', requiresColumn: true, validTypes: ['Numeric'], isCustomAction: true },
      ]
    }
  ];

  const handleOperationClick = (op: Operation) => {
    if (op.isCustomAction) {
      if (op.id === 'merge_datasets') {
        setMergeDialogOpen(true);
      } else if (op.id === 'normalize') {
        if (!selectedColumn) return;
        setScaleDialogOpen(true);
      }
      return;
    }

    let params = op.params || {};
    let opName = op.id;

    // Normalize operation names mapping to backend
    if (op.id.startsWith('text_case')) opName = 'text_case';
    if (op.id.startsWith('convert_type')) opName = 'convert_type';
    if (op.id === 'fill_missing_mode') opName = 'fill_missing';

    if (op.requiresColumn) {
      if (!selectedColumn) return; // Should be disabled anyway
      params = { ...params, columns: [selectedColumn] };
    }

    // Special handling for global operations that might take columns optionally
    if (op.id === 'drop_duplicates' && selectedColumn) {
      // If a column is selected, maybe we want to drop dupes based on that column?
      // For now, let's keep drop_duplicates global unless we implement a specific UI for it.
      // But the requirement says "Remove Duplicates" in "Data Cleaning".
    }

    if (op.id === 'knn_impute') {
      // KNN usually applies to all numeric columns or specific ones. 
      // For simplicity, let's apply to all numeric columns if no specific selection logic (backend handles filtering)
      // Or if a column is selected and it's numeric, we could restrict it, but KNN is multivariate.
      // Let's send empty columns to imply "all valid".
    }

    onAddStep(opName, params);
  };

  const isOperationValid = (op: Operation) => {
    // If operation DOES NOT require a column, it is always valid (Global operation)
    if (!op.requiresColumn) return true;

    // If it requires a column, we must have one selected
    if (!selectedColumn) return false;

    // If types are specified, check them
    if (op.validTypes) {
      if (op.validTypes.includes('All')) return true;

      // Strict type checking against backend types
      if (!columnType) return false;

      // Backend types: 'Numeric', 'Date', 'Boolean', 'Categorical', 'Text'
      // Frontend map: 'String' matches 'Text' or 'Categorical'
      if (op.validTypes.includes(columnType)) return true;

      if (op.validTypes.includes('String') && (columnType === 'Text' || columnType === 'Categorical')) return true;

      return false;
    }

    return true;
  };

  return (
    <div className="w-64 bg-[#1e1e1e] border-r border-black flex flex-col h-full text-xs">
      <div className="p-3 bg-[#252526] border-b border-black">
        <h2 className="font-bold text-gray-300 uppercase tracking-wider text-[10px] mb-1">Control Panel</h2>
        <div className="text-[10px] text-gray-500 truncate">
          {selectedColumn ? (
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              {selectedColumn} ({columnType})
            </span>
          ) : (
            <span className="italic">No column selected</span>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-4">
        {operations.map((group, idx) => (
          <div key={idx} className="space-y-1">
            <button
              onClick={() => toggleGroup(group.title.toLowerCase())}
              className="flex items-center w-full px-2 py-1 text-[11px] font-bold text-gray-400 uppercase tracking-wide hover:text-white transition-colors bg-black/20 rounded-sm mb-1"
            >
              {openGroups.includes(group.title.toLowerCase()) ?
                <ChevronDown className="h-3 w-3 mr-1" /> :
                <ChevronRight className="h-3 w-3 mr-1" />
              }
              {group.title}
            </button>

            {openGroups.includes(group.title.toLowerCase()) && (
              <div className="grid gap-1 pl-1">
                {group.operations.map(op => {
                  const isValid = isOperationValid(op);
                  return (
                    <Button
                      key={op.id}
                      variant="secondary"
                      size="sm"
                      className={cn(
                        "w-full justify-start text-left h-7 text-[11px] bg-[#2d2d2d] hover:bg-[#3e3e3e] text-gray-300 border border-black/50 shadow-sm",
                        !isValid && "opacity-40 cursor-not-allowed bg-transparent border-transparent hover:bg-transparent"
                      )}
                      disabled={!isValid}
                      onClick={() => handleOperationClick(op)}
                    >
                      <div className="w-1 h-full bg-gray-600 mr-2 rounded-full opacity-50"></div>
                      {op.label}
                    </Button>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      <MergeDialog
        open={mergeDialogOpen}
        onOpenChange={setMergeDialogOpen}
        currentDatasetId={currentDatasetId}
        currentDatasetColumns={currentDatasetColumns}
        onMerge={(params) => onAddStep('merge', params)}
      />

      <ScaleDialog
        open={scaleDialogOpen}
        onOpenChange={setScaleDialogOpen}
        onApply={(params) => {
          if (selectedColumn) {
            onAddStep('normalize', { ...params, columns: [selectedColumn] });
          }
        }}
      />
    </div>
  );
}
