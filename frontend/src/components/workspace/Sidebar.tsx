import { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronRight, Type, Wand2, Database, GitMerge, ChevronUp } from 'lucide-react';
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

// ─── Types ───────────────────────────────────────────────────────────────────

interface SubOption {
  label: string;
  operation: string;
  params?: any;
  isCustomAction?: string; // dialog key
}

interface ControlButton {
  id: string;
  label: string;
  icon?: string;
  /** If set, clicking opens a sub-menu with these choices */
  subOptions?: SubOption[];
  /** If set, clicking fires directly */
  operation?: string;
  params?: any;
  isCustomAction?: string;
  requiresColumn?: boolean;
  validTypes?: string[];
}

interface ControlGroup {
  title: string;
  icon: any;
  buttons: ControlButton[];
}

// ─── Sub-menu Popover ────────────────────────────────────────────────────────

function SubMenu({
  options,
  onSelect,
  onClose,
}: {
  options: SubOption[];
  onSelect: (o: SubOption) => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  return (
    <div
      ref={ref}
      className="absolute left-full top-0 ml-1 z-50 bg-[#2a2a2a] border border-gray-700 rounded-lg shadow-2xl min-w-[160px] py-1 overflow-hidden"
    >
      {options.map((opt, i) => (
        <button
          key={i}
          className="w-full text-left px-3 py-1.5 text-[11px] text-gray-300 hover:bg-teal-600/20 hover:text-teal-300 transition-colors"
          onClick={() => { onSelect(opt); onClose(); }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// ─── Single control button ────────────────────────────────────────────────────

function CtrlButton({
  btn,
  isValid,
  onDirect,
  onSubSelect,
}: {
  btn: ControlButton;
  isValid: boolean;
  onDirect: (btn: ControlButton) => void;
  onSubSelect: (btn: ControlButton, opt: SubOption) => void;
}) {
  const [open, setOpen] = useState(false);
  const hasMenu = !!btn.subOptions?.length;

  return (
    <div className="relative">
      <button
        disabled={!isValid}
        onClick={() => {
          if (!isValid) return;
          if (hasMenu) { setOpen(v => !v); }
          else { onDirect(btn); }
        }}
        className={cn(
          'w-full flex items-center justify-between text-left px-2 py-1 rounded text-[11px] font-medium transition-colors border',
          isValid
            ? 'bg-[#2d2d2d] border-black/50 text-gray-300 hover:bg-[#3a3a3a] hover:text-white'
            : 'opacity-30 cursor-not-allowed bg-transparent border-transparent text-gray-500',
        )}
      >
        <span className="flex items-center gap-1.5 truncate">
          <span className="w-1 h-3 bg-gray-600 rounded-full opacity-40 shrink-0" />
          {btn.label}
        </span>
        {hasMenu && isValid && (
          open
            ? <ChevronUp className="w-3 h-3 shrink-0 text-gray-400" />
            : <ChevronDown className="w-3 h-3 shrink-0 text-gray-400" />
        )}
      </button>

      {hasMenu && open && isValid && (
        <SubMenu
          options={btn.subOptions!}
          onSelect={(opt) => onSubSelect(btn, opt)}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
}

// ─── Main Sidebar ─────────────────────────────────────────────────────────────

export function Sidebar({
  selectedColumn,
  columnType,
  onAddStep,
  currentDatasetId,
  currentDatasetColumns,
  previewData,
}: SidebarProps) {
  const [openGroups, setOpenGroups] = useState<string[]>([
    'data cleaning', 'type conversion', 'feature engineering',
    'advanced ml prep', 'data integration',
  ]);
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
  const [scaleDialogOpen, setScaleDialogOpen] = useState(false);
  const [formatDialogOpen, setFormatDialogOpen] = useState(false);
  const [customFillDialogOpen, setCustomFillDialogOpen] = useState(false);
  const [mlEncodeDialogOpen, setMlEncodeDialogOpen] = useState(false);

  const toggleGroup = (id: string) =>
    setOpenGroups(prev => prev.includes(id) ? prev.filter(g => g !== id) : [...prev, id]);

  const groups: ControlGroup[] = [
    {
      title: 'Data Cleaning',
      icon: Database,
      buttons: [
        {
          id: 'fill_missing_group',
          label: 'Fill Missing',
          requiresColumn: true,
          validTypes: ['All'],
          subOptions: [
            { label: 'Mean',         operation: 'fill_missing', params: { method: 'mean' } },
            { label: 'Median',       operation: 'fill_missing', params: { method: 'median' } },
            { label: 'Mode',         operation: 'fill_missing', params: { method: 'mode' } },
            { label: 'Custom Value', operation: 'fill_missing', isCustomAction: 'fill_custom' },
            { label: 'KNN (k=5)',    operation: 'knn_impute',   params: { n_neighbors: 5 } },
          ],
        },
        {
          id: 'drop_rows_group',
          label: 'Drop Rows',
          validTypes: ['All'],
          subOptions: [
            { label: 'Duplicates',          operation: 'drop_duplicates', params: {} },
            { label: 'Any Null',            operation: 'drop_missing',    params: {} },
            { label: 'Null (This Col)',      operation: 'drop_missing',    params: { _useCol: true } },
          ],
        },
        {
          id: 'outliers_group',
          label: 'Outliers',
          requiresColumn: true,
          validTypes: ['Numeric'],
          subOptions: [
            { label: 'Cap (IQR)',  operation: 'handle_outliers',    params: { method: 'iqr', fold: 1.5, strategy: 'cap' } },
            { label: 'Drop (IQR)', operation: 'remove_outliers_iqr', params: { multiplier: 1.5 } },
          ],
        },
        {
          id: 'drop_columns',
          label: 'Drop Column',
          operation: 'drop_columns',
          requiresColumn: true,
          validTypes: ['All'],
        },
        {
          id: 'validate_format',
          label: 'Format Validate',
          isCustomAction: 'format_dialog',
          requiresColumn: true,
          validTypes: ['Text', 'Categorical', 'Numeric', 'Date'],
        },
      ],
    },
    {
      title: 'Type Conversion',
      icon: Type,
      buttons: [
        {
          id: 'convert_type_group',
          label: 'Convert Type',
          requiresColumn: true,
          validTypes: ['All'],
          subOptions: [
            { label: 'To Numeric',     operation: 'convert_type', params: { type: 'numeric' } },
            { label: 'To String',      operation: 'convert_type', params: { type: 'string' } },
            { label: 'To Date',        operation: 'convert_type', params: { type: 'date' } },
            { label: 'Text → Numbers', operation: 'convert_type', params: { type: 'text_to_numeric' } },
            { label: 'Numbers → Text', operation: 'convert_type', params: { type: 'numeric_to_text' } },
          ],
        },
        {
          id: 'extract_numeric_group',
          label: 'Extract Numeric',
          requiresColumn: true,
          validTypes: ['Text', 'Categorical'],
          subOptions: [
            { label: 'Null invalid',  operation: 'extract_numeric', params: { on_invalid: 'null' } },
            { label: 'Drop invalid',  operation: 'extract_numeric', params: { on_invalid: 'drop' } },
          ],
        },
        {
          id: 'text_case_group',
          label: 'Text Case',
          requiresColumn: true,
          validTypes: ['String', 'Text', 'Categorical'],
          subOptions: [
            { label: 'UPPERCASE', operation: 'text_case', params: { case: 'upper' } },
            { label: 'lowercase', operation: 'text_case', params: { case: 'lower' } },
            { label: 'Title Case', operation: 'text_case', params: { case: 'title' } },
          ],
        },
      ],
    },
    {
      title: 'Feature Engineering',
      icon: Database,
      buttons: [
        {
          id: 'scale_group',
          label: 'Scale / Normalise',
          requiresColumn: true,
          validTypes: ['Numeric'],
          subOptions: [
            { label: 'Z-Score (Standard)', operation: 'standard_scale', params: {} },
            { label: 'Min-Max',            operation: 'normalize',       isCustomAction: 'scale_dialog' },
          ],
        },
        {
          id: 'timeseries_fill_group',
          label: 'Time-Series Fill',
          requiresColumn: true,
          validTypes: ['All'],
          subOptions: [
            { label: 'Forward Fill',  operation: 'time_series_fill', params: { method: 'ffill' } },
            { label: 'Backward Fill', operation: 'time_series_fill', params: { method: 'bfill' } },
          ],
        },
        {
          id: 'bin_column',
          label: 'Bin Column',
          operation: 'bin_column',
          requiresColumn: true,
          validTypes: ['Numeric'],
          params: { strategy: 'equal_frequency', n_bins: 5 },
        },
        {
          id: 'extract_datetime_components',
          label: 'Extract Date Parts',
          operation: 'extract_datetime_components',
          requiresColumn: true,
          validTypes: ['Date'],
          params: { components: ['year', 'month', 'day'] },
        },
      ],
    },
    {
      title: 'Advanced ML Prep',
      icon: Wand2,
      buttons: [
        {
          id: 'encode_categorical',
          label: 'Encode Categorical',
          isCustomAction: 'encode_dialog',
          requiresColumn: true,
          validTypes: ['Categorical'],
        },
        {
          id: 'handle_imbalance',
          label: 'Handle Imbalance',
          operation: 'handle_imbalance',
          requiresColumn: true,
          validTypes: ['Categorical', 'Numeric'],
          params: {
            strategy: 'smote',
            target_column: selectedColumn,
            feature_columns: currentDatasetColumns
              ?.filter(c => c.detected_type === 'Numeric')
              .map(c => c.name) || [],
          },
        },
        {
          id: 'add_missingness_indicator',
          label: 'Missingness Flag',
          operation: 'add_missingness_indicator',
          requiresColumn: true,
          validTypes: ['All'],
        },
      ],
    },
    {
      title: 'Data Integration',
      icon: GitMerge,
      buttons: [
        {
          id: 'merge_datasets',
          label: 'Merge / Join',
          isCustomAction: 'merge_dialog',
          validTypes: ['All'],
        },
      ],
    },
  ];

  // ── Validity check ─────────────────────────────────────────────────────────
  const isButtonValid = (btn: ControlButton): boolean => {
    if (!btn.requiresColumn) {
      // Global ops: valid only when no column is selected, EXCEPT merge
      if (selectedColumn && btn.id !== 'merge_datasets') return false;
      return true;
    }
    if (!selectedColumn) return false;
    if (!btn.validTypes || btn.validTypes.includes('All')) return true;
    if (!columnType) return false;
    if (btn.validTypes.includes(columnType)) return true;
    if (btn.validTypes.includes('String') && (columnType === 'Text' || columnType === 'Categorical')) return true;
    return false;
  };

  // ── Direct button click handler ────────────────────────────────────────────
  const handleDirect = (btn: ControlButton) => {
    if (btn.isCustomAction) {
      if (btn.isCustomAction === 'merge_dialog')  { setMergeDialogOpen(true);  return; }
      if (btn.isCustomAction === 'scale_dialog')  { if (selectedColumn) setScaleDialogOpen(true);  return; }
      if (btn.isCustomAction === 'format_dialog') { if (selectedColumn) setFormatDialogOpen(true); return; }
      if (btn.isCustomAction === 'fill_custom')   { if (selectedColumn) setCustomFillDialogOpen(true); return; }
      if (btn.isCustomAction === 'encode_dialog') { if (selectedColumn) setMlEncodeDialogOpen(true);  return; }
      return;
    }
    if (!btn.operation) return;
    let params = btn.params || {};
    if (btn.requiresColumn && selectedColumn) {
      const colOps = ['bin_column', 'encode_categorical', 'extract_datetime_components'];
      if (colOps.includes(btn.id)) params = { ...params, column: selectedColumn };
      else if (btn.id === 'handle_imbalance') params = { ...params, target_column: selectedColumn };
      else params = { ...params, columns: [selectedColumn] };
    }
    onAddStep(btn.operation, params);
  };

  // ── Sub-option click handler ───────────────────────────────────────────────
  const handleSubSelect = (btn: ControlButton, opt: SubOption) => {
    if (opt.isCustomAction) {
      if (opt.isCustomAction === 'fill_custom')  { if (selectedColumn) setCustomFillDialogOpen(true); return; }
      if (opt.isCustomAction === 'scale_dialog') { if (selectedColumn) setScaleDialogOpen(true);      return; }
      return;
    }
    let params = opt.params ? { ...opt.params } : {};
    // _useCol flag = requires the currently selected column
    const needsCol = params._useCol || btn.requiresColumn;
    delete params._useCol;

    if (needsCol && selectedColumn) {
      const colOps = ['bin_column', 'encode_categorical', 'extract_datetime_components', 'knn_impute'];
      if (colOps.includes(opt.operation)) params = { ...params, column: selectedColumn };
      else params = { ...params, columns: [selectedColumn] };
    }
    onAddStep(opt.operation, params);
  };

  return (
    <div className="w-52 min-w-[180px] max-w-[280px] resize-x overflow-y-auto overflow-x-visible bg-[#1e1e1e] border-r border-black flex flex-col h-full text-xs">
      {/* Header */}
      <div className="p-3 bg-[#252526] border-b border-black shrink-0">
        <h2 className="font-bold text-gray-300 uppercase tracking-wider text-[10px] mb-1">Control Panel</h2>
        <div className="text-[10px] text-gray-500 truncate">
          {selectedColumn ? (
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              {selectedColumn} <span className="text-gray-600">({columnType})</span>
            </span>
          ) : (
            <span className="italic">No column selected</span>
          )}
        </div>
      </div>

      {/* Scrollable body */}
      <div className="px-2 pb-4 overflow-y-auto overflow-x-visible flex-1">
        {selectedColumn && previewData && previewData.length > 0 && (
          <ColumnStatsPanel column={selectedColumn} columnType={columnType} data={previewData} />
        )}

        {groups.map((group, gi) => (
          <div key={gi} className="mt-2">
            {/* Group header */}
            <button
              onClick={() => toggleGroup(group.title.toLowerCase())}
              className="flex items-center w-full px-2 py-1 text-[10px] font-bold text-gray-500 uppercase tracking-wider hover:text-white transition-colors bg-black/20 rounded-sm mb-1"
            >
              {openGroups.includes(group.title.toLowerCase())
                ? <ChevronDown className="h-3 w-3 mr-1 shrink-0" />
                : <ChevronRight className="h-3 w-3 mr-1 shrink-0" />}
              {group.title}
            </button>

            {openGroups.includes(group.title.toLowerCase()) && (
              <div className="flex flex-col gap-0.5 pl-1 relative">
                {group.buttons.map(btn => (
                  <CtrlButton
                    key={btn.id}
                    btn={btn}
                    isValid={isButtonValid(btn)}
                    onDirect={handleDirect}
                    onSubSelect={handleSubSelect}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* ── Dialogs ─────────────────────────────────────────────────────────── */}
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
          if (selectedColumn) onAddStep('normalize', { ...params, columns: [selectedColumn] });
        }}
      />
      <FormatValidationDialog
        open={formatDialogOpen}
        onOpenChange={setFormatDialogOpen}
        selectedColumn={selectedColumn}
        onApply={(params) => {
          if (selectedColumn) onAddStep('validate_format', { ...params, columns: [selectedColumn] });
        }}
      />
      <CustomFillDialog
        open={customFillDialogOpen}
        onOpenChange={setCustomFillDialogOpen}
        selectedColumn={selectedColumn}
        onApply={(params) => {
          if (selectedColumn) onAddStep('fill_missing', { ...params, columns: [selectedColumn] });
        }}
      />
      <MLEncodeDialog
        open={mlEncodeDialogOpen}
        onOpenChange={setMlEncodeDialogOpen}
        selectedColumn={selectedColumn}
        onApply={(params) => {
          if (selectedColumn) onAddStep('encode_categorical', { ...params, column: selectedColumn });
        }}
      />
    </div>
  );
}
