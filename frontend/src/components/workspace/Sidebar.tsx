import { useState } from 'react';
import { ChevronDown, ChevronRight, ChevronUp, Type, Wand2, Database, GitMerge } from 'lucide-react';
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

// ─── Sub option definition ────────────────────────────────────────────────────

interface SubOption {
  label: string;
  operation: string;
  params?: any;
  isCustomAction?: string;
  /**
   * If true, the sub-option is only enabled when a column is selected.
   * If false/undefined, it is always enabled (global op).
   */
  requiresColumn?: boolean;
  /** Column type restriction. 'All' = no restriction. */
  validTypes?: string[];
}

interface ControlButton {
  id: string;
  label: string;
  subOptions?: SubOption[];
  // --- Single-fire button ---
  operation?: string;
  params?: any;
  isCustomAction?: string;
  // --- Validity ---
  requiresColumn?: boolean;
  validTypes?: string[];
}

interface ControlGroup {
  title: string;
  icon: any;
  buttons: ControlButton[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function matchesType(validTypes: string[] | undefined, columnType: string | null): boolean {
  if (!validTypes || validTypes.includes('All')) return true;
  if (!columnType) return false;
  if (validTypes.includes(columnType)) return true;
  if (validTypes.includes('String') && (columnType === 'Text' || columnType === 'Categorical')) return true;
  return false;
}

// ─── Inline sub-option row ────────────────────────────────────────────────────

function SubOptionRow({
  opt,
  selectedColumn,
  columnType,
  onClick,
}: {
  opt: SubOption;
  selectedColumn: string | null;
  columnType: string | null;
  onClick: () => void;
}) {
  const colOK = opt.requiresColumn ? !!selectedColumn : true;
  const typeOK = matchesType(opt.validTypes, columnType);
  const enabled = colOK && typeOK;

  return (
    <button
      disabled={!enabled}
      onClick={onClick}
      className={cn(
        'w-full text-left px-3 py-1 text-[11px] rounded transition-colors',
        enabled
          ? 'text-gray-300 hover:bg-teal-600/20 hover:text-teal-200 cursor-pointer'
          : 'text-gray-600 cursor-not-allowed',
      )}
    >
      {opt.label}
    </button>
  );
}

// ─── Control button (with optional inline accordion) ─────────────────────────

function CtrlButton({
  btn,
  selectedColumn,
  columnType,
  onDirect,
  onSubSelect,
}: {
  btn: ControlButton;
  selectedColumn: string | null;
  columnType: string | null;
  onDirect: (btn: ControlButton) => void;
  onSubSelect: (btn: ControlButton, opt: SubOption) => void;
}) {
  const [open, setOpen] = useState(false);
  const hasMenu = !!btn.subOptions?.length;

  /* ── Validity for the parent trigger ─────────────────────────────────────
     For grouped buttons: enabled if AT LEAST ONE sub-option is usable.
     For single-fire buttons: normal requiresColumn + type check.  */
  let isValid: boolean;
  if (hasMenu) {
    isValid = btn.subOptions!.some(opt => {
      const colOK = opt.requiresColumn ? !!selectedColumn : true;
      const typeOK = matchesType(opt.validTypes, columnType);
      return colOK && typeOK;
    });
  } else {
    if (btn.requiresColumn) {
      isValid = !!selectedColumn && matchesType(btn.validTypes, columnType);
    } else {
      isValid = matchesType(btn.validTypes, columnType);
    }
  }

  return (
    <div>
      {/* Trigger row */}
      <button
        disabled={!isValid}
        onClick={() => {
          if (!isValid) return;
          if (hasMenu) setOpen(v => !v);
          else onDirect(btn);
        }}
        className={cn(
          'w-full flex items-center justify-between text-left px-2 py-1 rounded text-[11px] font-medium transition-colors border',
          isValid
            ? 'bg-[#2d2d2d] border-black/40 text-gray-300 hover:bg-[#3a3a3a] hover:text-white'
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

      {/* Inline accordion — expands downward, no overflow clipping */}
      {hasMenu && open && isValid && (
        <div className="ml-3 mt-0.5 mb-1 flex flex-col border-l border-gray-700/60 pl-1">
          {btn.subOptions!.map((opt, i) => (
            <SubOptionRow
              key={i}
              opt={opt}
              selectedColumn={selectedColumn}
              columnType={columnType}
              onClick={() => {
                onSubSelect(btn, opt);
                setOpen(false);
              }}
            />
          ))}
        </div>
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
          subOptions: [
            { label: 'Mean',         operation: 'fill_missing', params: { method: 'mean' },   requiresColumn: true, validTypes: ['Numeric'] },
            { label: 'Median',       operation: 'fill_missing', params: { method: 'median' }, requiresColumn: true, validTypes: ['Numeric'] },
            { label: 'Mode',         operation: 'fill_missing', params: { method: 'mode' },   requiresColumn: true, validTypes: ['All'] },
            { label: 'Custom Value', operation: 'fill_missing', isCustomAction: 'fill_custom', requiresColumn: true, validTypes: ['All'] },
            { label: 'KNN (k=5)',    operation: 'knn_impute',   params: { n_neighbors: 5 },   requiresColumn: true, validTypes: ['Numeric'] },
          ],
        },
        {
          id: 'drop_rows_group',
          label: 'Drop Rows',
          subOptions: [
            // No requiresColumn → always enabled
            { label: 'Duplicates',      operation: 'drop_duplicates', params: {} },
            { label: 'Null (Any Col)',  operation: 'drop_missing',    params: {} },
            // requiresColumn → only enabled when a column is selected
            { label: 'Null (This Col)', operation: 'drop_missing',    params: { _useCol: true }, requiresColumn: true, validTypes: ['All'] },
          ],
        },
        {
          id: 'outliers_group',
          label: 'Outliers',
          subOptions: [
            { label: 'Cap (IQR)',  operation: 'handle_outliers',     params: { method: 'iqr', fold: 1.5, strategy: 'cap' }, requiresColumn: true, validTypes: ['Numeric'] },
            { label: 'Drop (IQR)', operation: 'remove_outliers_iqr', params: { multiplier: 1.5 },                          requiresColumn: true, validTypes: ['Numeric'] },
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
          subOptions: [
            { label: 'To Numeric',     operation: 'convert_type', params: { type: 'numeric' },         requiresColumn: true, validTypes: ['All'] },
            { label: 'To String',      operation: 'convert_type', params: { type: 'string' },          requiresColumn: true, validTypes: ['All'] },
            { label: 'To Date',        operation: 'convert_type', params: { type: 'date' },            requiresColumn: true, validTypes: ['All'] },
            { label: 'Text → Numbers', operation: 'convert_type', params: { type: 'text_to_numeric' }, requiresColumn: true, validTypes: ['All'] },
            { label: 'Numbers → Text', operation: 'convert_type', params: { type: 'numeric_to_text' }, requiresColumn: true, validTypes: ['All'] },
          ],
        },
        {
          id: 'extract_numeric_group',
          label: 'Extract Numeric',
          subOptions: [
            { label: 'Null invalid',  operation: 'extract_numeric', params: { on_invalid: 'null' }, requiresColumn: true, validTypes: ['Text', 'Categorical'] },
            { label: 'Drop invalid',  operation: 'extract_numeric', params: { on_invalid: 'drop' }, requiresColumn: true, validTypes: ['Text', 'Categorical'] },
          ],
        },
        {
          id: 'text_case_group',
          label: 'Text Case',
          subOptions: [
            { label: 'UPPERCASE', operation: 'text_case', params: { case: 'upper' }, requiresColumn: true, validTypes: ['String', 'Text', 'Categorical'] },
            { label: 'lowercase', operation: 'text_case', params: { case: 'lower' }, requiresColumn: true, validTypes: ['String', 'Text', 'Categorical'] },
            { label: 'Title Case', operation: 'text_case', params: { case: 'title' }, requiresColumn: true, validTypes: ['String', 'Text', 'Categorical'] },
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
          subOptions: [
            { label: 'Z-Score (Standard)', operation: 'standard_scale', params: {},                              requiresColumn: true, validTypes: ['Numeric'] },
            { label: 'Min-Max',            operation: 'normalize',       isCustomAction: 'scale_dialog',         requiresColumn: true, validTypes: ['Numeric'] },
          ],
        },
        {
          id: 'timeseries_fill_group',
          label: 'Time-Series Fill',
          subOptions: [
            { label: 'Forward Fill',  operation: 'time_series_fill', params: { method: 'ffill' }, requiresColumn: true, validTypes: ['All'] },
            { label: 'Backward Fill', operation: 'time_series_fill', params: { method: 'bfill' }, requiresColumn: true, validTypes: ['All'] },
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
        },
      ],
    },
  ];

  // ── Dialog openers ─────────────────────────────────────────────────────────
  const openDialog = (key: string) => {
    if (key === 'merge_dialog')  setMergeDialogOpen(true);
    if (key === 'scale_dialog')  setScaleDialogOpen(true);
    if (key === 'format_dialog') setFormatDialogOpen(true);
    if (key === 'fill_custom')   setCustomFillDialogOpen(true);
    if (key === 'encode_dialog') setMlEncodeDialogOpen(true);
  };

  // ── Build params for a single-fire button ──────────────────────────────────
  const buildParams = (id: string, baseParams: any = {}) => {
    const colOps = ['bin_column', 'encode_categorical', 'extract_datetime_components', 'knn_impute'];
    if (id === 'handle_imbalance') return { ...baseParams, target_column: selectedColumn };
    if (colOps.includes(id))       return { ...baseParams, column: selectedColumn };
    if (selectedColumn)            return { ...baseParams, columns: [selectedColumn] };
    return baseParams;
  };

  // ── Direct single-fire click ───────────────────────────────────────────────
  const handleDirect = (btn: ControlButton) => {
    if (btn.isCustomAction) { openDialog(btn.isCustomAction); return; }
    if (!btn.operation) return;
    onAddStep(btn.operation, buildParams(btn.id, btn.params));
  };

  // ── Sub-option click ───────────────────────────────────────────────────────
  const handleSubSelect = (_btn: ControlButton, opt: SubOption) => {

    if (opt.isCustomAction) { openDialog(opt.isCustomAction); return; }

    let params = opt.params ? { ...opt.params } : {};

    // _useCol: sub-option that needs the selected column as its "columns" param
    const needsCol = params._useCol;
    delete params._useCol;

    const colOps = ['bin_column', 'encode_categorical', 'extract_datetime_components', 'knn_impute'];
    if (needsCol && selectedColumn) {
      params = colOps.includes(opt.operation)
        ? { ...params, column: selectedColumn }
        : { ...params, columns: [selectedColumn] };
    } else if (opt.requiresColumn && selectedColumn && !params.columns && !params.column) {
      params = colOps.includes(opt.operation)
        ? { ...params, column: selectedColumn }
        : { ...params, columns: [selectedColumn] };
    }

    onAddStep(opt.operation, params);
  };

  return (
    <div className="w-52 min-w-[180px] bg-[#1e1e1e] border-r border-black flex flex-col h-full text-xs overflow-hidden">
      {/* Header */}
      <div className="p-3 bg-[#252526] border-b border-black shrink-0">
        <h2 className="font-bold text-gray-300 uppercase tracking-wider text-[10px] mb-1">Control Panel</h2>
        <div className="text-[10px] text-gray-500 truncate">
          {selectedColumn ? (
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-green-500 shrink-0" />
              <span className="truncate">{selectedColumn}</span>
              <span className="text-gray-600 shrink-0">({columnType})</span>
            </span>
          ) : (
            <span className="italic">No column selected</span>
          )}
        </div>
      </div>

      {/* Scrollable body — overflow-y scroll ONLY; sub-menus expand inline */}
      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {selectedColumn && previewData && previewData.length > 0 && (
          <ColumnStatsPanel column={selectedColumn} columnType={columnType} data={previewData} />
        )}

        {groups.map((group, gi) => (
          <div key={gi} className="mt-2">
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
              <div className="flex flex-col gap-0.5 pl-1">
                {group.buttons.map(btn => (
                  <CtrlButton
                    key={btn.id}
                    btn={btn}
                    selectedColumn={selectedColumn}
                    columnType={columnType}
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
            const { how, ...rest } = params;
            onAddStep('concat', rest);
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
