import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight, Type, Wand2, Database, GitMerge } from 'lucide-react';
import { cn } from '@/lib/utils';
import { MergeDialog } from './MergeDialog';
import { ScaleDialog } from './ScaleDialog';
import { FormatValidationDialog } from './FormatValidationDialog';
import { CustomFillDialog } from './CustomFillDialog';
import { ColumnStatsPanel } from './ColumnStatsPanel';
import { MLEncodeDialog } from './MLEncodeDialog';

interface DatasetColumn {
  id: string;
  name: string;
  detected_type: string;
}

interface SidebarProps {
  selectedColumn: string | null;
  columnType: string | null;
  onAddStep: (operation: string, params: any) => Promise<void>;
  currentDatasetId: string;
  currentDatasetColumns?: DatasetColumn[];
  previewData?: any[];
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

export function Sidebar({ selectedColumn, columnType, onAddStep, currentDatasetId, currentDatasetColumns, previewData }: SidebarProps) {
  const [openGroups, setOpenGroups] = useState<string[]>(['data cleaning', 'feature engineering', 'advanced ml preparation', 'type conversion', 'formatting & standardization', 'data integration']);
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
  const [scaleDialogOpen, setScaleDialogOpen] = useState(false);
  const [formatDialogOpen, setFormatDialogOpen] = useState(false);
  const [customFillDialogOpen, setCustomFillDialogOpen] = useState(false);
  const [mlEncodeDialogOpen, setMlEncodeDialogOpen] = useState(false);

  const toggleGroup = (id: string) => {
    setOpenGroups(prev =>
      prev.includes(id) ? prev.filter(g => g !== id) : [...prev, id]
    );
  };

  const operations: OperationGroup[] = [
    {
      title: 'Data Cleaning',
      icon: Database,
      operations: [
        { id: 'drop_duplicates', label: 'Remove Duplicates', validTypes: ['All'] },
        { id: 'drop_missing', label: 'Drop Missing Rows (Any Column)', validTypes: ['All'] },
        { id: 'drop_missing_specific', label: 'Drop Missing Rows (This Column)', requiresColumn: true, validTypes: ['All'] },
        { id: 'drop_columns', label: 'Drop Selected Column', requiresColumn: true, validTypes: ['All'] },
        { id: 'fill_missing', label: 'Fill Missing (Mean)', requiresColumn: true, validTypes: ['Numeric'], params: { method: 'mean' } },
        { id: 'fill_missing_mode', label: 'Fill Missing (Mode)', requiresColumn: true, validTypes: ['All'], params: { method: 'mode' } },
        { id: 'fill_missing_custom', label: 'Fill Missing (Custom Value)', requiresColumn: true, validTypes: ['All'], isCustomAction: true },
        { id: 'knn_impute', label: 'KNN Imputation', requiresColumn: true, validTypes: ['Numeric'], params: { n_neighbors: 5 } },
        { id: 'remove_outliers_iqr', label: 'Remove Outliers (Drop via IQR)', requiresColumn: true, validTypes: ['Numeric'], params: { multiplier: 1.5 } },
        { id: 'handle_outliers', label: 'Handle Outliers (Cap via IQR)', requiresColumn: true, validTypes: ['Numeric'], params: { method: 'iqr', fold: 1.5, strategy: 'cap' } },
        { id: 'validate_format', label: 'Format Validation (Email, Links, IP...)', requiresColumn: true, validTypes: ['Text', 'Categorical', 'Numeric', 'Date'], isCustomAction: true },
      ]
    },
    {
      title: 'Type Conversion',
      icon: Type,
      operations: [
        { id: 'convert_type_numeric', label: 'Convert to Numeric', requiresColumn: true, validTypes: ['All'], params: { type: 'numeric' } },
        { id: 'convert_type_string', label: 'Convert to String', requiresColumn: true, validTypes: ['All'], params: { type: 'string' } },
        { id: 'convert_type_text_to_numeric', label: 'Mixed → Numbers (20, thirty → 20, 30)', requiresColumn: true, validTypes: ['All'], params: { type: 'text_to_numeric' } },
        { id: 'convert_type_numeric_to_text', label: 'Mixed → Words (20, thirty → twenty, thirty)', requiresColumn: true, validTypes: ['All'], params: { type: 'numeric_to_text' } },
        { id: 'extract_numeric_null', label: 'Extract Numeric (Smart Parse → null invalid)', requiresColumn: true, validTypes: ['Text', 'Categorical'], params: { on_invalid: 'null' } },
        { id: 'extract_numeric_drop', label: 'Extract Numeric (Smart Parse → drop invalid rows)', requiresColumn: true, validTypes: ['Text', 'Categorical'], params: { on_invalid: 'drop' } },
      ]
    },
    {
      title: 'Formatting & Standardization',
      icon: Type,
      operations: [
        { id: 'text_case_upper', label: 'To Uppercase', requiresColumn: true, validTypes: ['String', 'Text', 'Categorical'], params: { case: 'upper' } },
        { id: 'text_case_lower', label: 'To Lowercase', requiresColumn: true, validTypes: ['String', 'Text', 'Categorical'], params: { case: 'lower' } },
        { id: 'text_case_title', label: 'To Title Case', requiresColumn: true, validTypes: ['String', 'Text', 'Categorical'], params: { case: 'title' } },
      ]
    },
    {
      title: 'Feature Engineering',
      icon: Database,
      operations: [
        { id: 'extract_datetime_components', label: 'Extract Date Info (Y/M/D)', requiresColumn: true, validTypes: ['Date'], params: { components: ['year', 'month', 'day'] } },
        { id: 'bin_column', label: 'Bin Column (Quantile)', requiresColumn: true, validTypes: ['Numeric'], params: { strategy: 'equal_frequency', n_bins: 5 } },
        { id: 'normalize', label: 'Min-Max Scaling', requiresColumn: true, validTypes: ['Numeric'], isCustomAction: true },
        { id: 'standard_scale', label: 'Standard Scaling (Z-Score)', requiresColumn: true, validTypes: ['Numeric'] },
        { id: 'time_series_fill_ffill', label: 'Time-Series: Forward Fill', requiresColumn: true, validTypes: ['All'], params: { method: 'ffill' } },
        { id: 'time_series_fill_bfill', label: 'Time-Series: Backward Fill', requiresColumn: true, validTypes: ['All'], params: { method: 'bfill' } },
      ]
    },
    {
      title: 'Data Integration',
      icon: GitMerge,
      operations: [
        { id: 'merge_datasets', label: 'Merge / Join Datasets', validTypes: ['All'], isCustomAction: true },
      ]
    },
    {
      title: 'Advanced ML Preparation',
      icon: Wand2,
      operations: [
        { id: 'add_missingness_indicator', label: 'Add Missingness Indicator', requiresColumn: true, validTypes: ['All'] },
        { id: 'encode_categorical', label: 'Encode Categorical', requiresColumn: true, validTypes: ['Categorical'], isCustomAction: true },
        { id: 'handle_imbalance', label: 'Handle Imbalance (SMOTE)', requiresColumn: true, validTypes: ['Categorical', 'Numeric'], params: { strategy: 'smote', target_column: selectedColumn, feature_columns: currentDatasetColumns?.filter(c => c.detected_type === "Numeric").map(c => c.name) || [] } },
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
      } else if (op.id === 'validate_format') {
        if (!selectedColumn) return;
        setFormatDialogOpen(true);
      } else if (op.id === 'fill_missing_custom') {
        if (!selectedColumn) return;
        setCustomFillDialogOpen(true);
      } else if (op.id === 'encode_categorical') {
        if (!selectedColumn) return;
        setMlEncodeDialogOpen(true);
      }
      return;
    }

    let params = op.params || {};
    let opName = op.id;

    // Normalize operation names mapping to backend
    if (op.id.startsWith('text_case')) opName = 'text_case';
    if (op.id.startsWith('convert_type')) opName = 'convert_type';
    if (op.id.startsWith('fill_missing')) opName = 'fill_missing';
    if (op.id === 'drop_missing_specific') opName = 'drop_missing';
    if (op.id.startsWith('time_series_fill')) opName = 'time_series_fill';
    if (op.id.startsWith('extract_numeric')) opName = 'extract_numeric';

    if (op.requiresColumn) {
      if (!selectedColumn) return; // Should be disabled anyway
      if (op.id === 'encode_categorical' || op.id === 'bin_column' || op.id === 'extract_datetime_components' || op.id === 'create_lag_features' || op.id === 'create_rolling_features') {
        params = { ...params, column: selectedColumn };
      } else if (op.id === 'handle_imbalance') {
        // Special case for SMOTE
        params = { ...params, target_column: selectedColumn };
      } else {
        params = { ...params, columns: [selectedColumn] };
      }
    }

    onAddStep(opName, params);
  };

  const isOperationValid = (op: Operation) => {
    // If operation DOES NOT require a column, it is a global operation
    if (!op.requiresColumn) {
      // It is only valid if NO specific column is selected
      if (selectedColumn) return false;
      return true;
    }

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
    <div className="w-64 min-w-[200px] max-w-[500px] resize-x overflow-y-auto overflow-x-hidden bg-[#1e1e1e] border-r border-black flex flex-col h-full text-xs">
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

      <div className="px-2 pb-2 overflow-y-auto w-full">
        {/* Column Statistics Panel */}
        {selectedColumn && previewData && previewData.length > 0 && (
          <ColumnStatsPanel
            column={selectedColumn}
            columnType={columnType}
            data={previewData}
          />
        )}

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
        currentDatasetColumns={currentDatasetColumns || []}
        onMerge={(params) => {
          if (params.how === 'concat') {
            const { how, ...restParams } = params;
            onAddStep('concat', restParams);
          } else {
            onAddStep('merge', params);
          }
        }}
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

      <FormatValidationDialog
        open={formatDialogOpen}
        onOpenChange={setFormatDialogOpen}
        selectedColumn={selectedColumn}
        onApply={(params) => {
          if (selectedColumn) {
            onAddStep('validate_format', { ...params, columns: [selectedColumn] });
          }
        }}
      />

      <CustomFillDialog
        open={customFillDialogOpen}
        onOpenChange={setCustomFillDialogOpen}
        selectedColumn={selectedColumn}
        onApply={(params) => {
          if (selectedColumn) {
            onAddStep('fill_missing', { ...params, columns: [selectedColumn] });
          }
        }}
      />

      <MLEncodeDialog
        open={mlEncodeDialogOpen}
        onOpenChange={setMlEncodeDialogOpen}
        selectedColumn={selectedColumn}
        onApply={(params) => {
          if (selectedColumn) {
            onAddStep('encode_categorical', { ...params, column: selectedColumn });
          }
        }}
      />
    </div>
  );
}
