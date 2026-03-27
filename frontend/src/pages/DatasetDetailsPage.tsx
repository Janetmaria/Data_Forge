import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Download, AlertTriangle, Save, Upload, GitCompare } from 'lucide-react';
import { WorkspaceLayout } from '@/layouts/WorkspaceLayout';
import { Sidebar } from '@/components/workspace/Sidebar';
import { PreviewPanel } from '@/components/workspace/PreviewPanel';
import { LogPanel } from '@/components/workspace/LogPanel';
import { SavePipelineDialog } from '@/components/workspace/SavePipelineDialog';
import { ApplyTemplateDialog } from '@/components/workspace/ApplyTemplateDialog';
import { DataQualityPanel } from '@/components/workspace/DataQualityPanel';
import { BeforeAfterModal } from '@/components/workspace/BeforeAfterModal';
import InferencePanel from '@/components/workspace/InferencePanel';

interface QualityAlert {
  entity: string;
  type: string;
  missing_pct: number;
  recommended_action: string;
}

interface DatasetColumn {
  id: string;
  name: string;
  detected_type: string;
}

interface Dataset {
  id: string;
  original_filename: string;
  row_count: number;
  col_count: number;
  file_format: string;
  domain?: string | null;
  columns: DatasetColumn[];
  quality_alerts: QualityAlert[];
}

export default function DatasetDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [previewColumns, setPreviewColumns] = useState<string[]>([]);
  const [steps, setSteps] = useState<any[]>([]);
  const [pipelineId, setPipelineId] = useState<string | null>(null);
  const [pipelineName] = useState<string>('Draft Pipeline');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [applyTemplateDialogOpen, setApplyTemplateDialogOpen] = useState(false);

  // Feature 2: Quality panel
  const [qualityPanelOpen, setQualityPanelOpen] = useState(false);

  // Feature 3: Before/After tracking
  const beforeSnapshotRef = useRef<any[]>([]);
  const [compareData, setCompareData] = useState<{ before: any[]; after: any[]; column: string } | null>(null);

  // Feature 4: Expert Inference Modal
  const [inferenceDialogOpen, setInferenceDialogOpen] = useState(false);

  useEffect(() => {
    if (id) {
      initializeWorkspace();
    }
  }, [id]);

  const initializeWorkspace = async () => {
    try {
      setLoading(true);
      const dsRes = await api.get(`/datasets/${id}`);
      const datasetData = dsRes.data;

      const pipeRes = await api.get(`/pipelines/interactive/${id}`);
      setSteps(pipeRes.data.steps);
      setPreviewData(pipeRes.data.preview);
      setPreviewColumns(pipeRes.data.columns || []);
      setPipelineId(pipeRes.data.pipeline_id);

      setDataset({
        ...datasetData,
        quality_alerts: pipeRes.data.quality_alerts || datasetData.quality_alerts
      });
    } catch (err: any) {
      console.error("Failed to init workspace", err);
      const detailedError = err.response?.data?.detail || err.message || String(err);
      setErrorMsg(`Failed to load workspace: ${detailedError}`);
    } finally {
      setLoading(false);
    }
  };

  const updateState = (res: any) => {
    setSteps(res.data.steps);
    setPreviewData([...(res.data.preview || [])]);
    setPreviewColumns(res.data.columns || []);

    if (dataset) {
      setDataset({
        ...dataset,
        quality_alerts: res.data.quality_alerts ? [...res.data.quality_alerts] : dataset.quality_alerts,
        columns: res.data.column_schemas ? [...res.data.column_schemas] : dataset.columns,
        row_count: res.data.row_count !== undefined ? res.data.row_count : dataset.row_count,
        col_count: res.data.col_count !== undefined ? res.data.col_count : dataset.col_count
      });
    }
  };

  const handleSelectColumn = useCallback((col: string) => {
    // Snapshot current data BEFORE any step is applied when user selects a column
    setSelectedColumn(col);
    beforeSnapshotRef.current = previewData;
  }, [previewData]);

  const handleAddStep = async (operation: string, params: any) => {
    if (!id) return;
    // Capture before snapshot for compare (keyed to currently selected column)
    const snapshotBefore = [...previewData];
    const colForCompare = selectedColumn;

    try {
      setProcessing(true);
      const res = await api.post(`/pipelines/interactive/${id}/steps`, {
        operation,
        params
      });

      const afterRows = res.data.preview || [];
      updateState(res);

      // Feature 3: Auto-open comparison if a column was selected and it was affected
      const affectedCols: string[] = params.columns || [];
      if (colForCompare && (affectedCols.length === 0 || affectedCols.includes(colForCompare))) {
        setCompareData({ before: snapshotBefore, after: afterRows, column: colForCompare });
      }
    } catch (err: any) {
      console.error("Failed to add step", err);
      const errorMsg = err.response?.data?.detail || err.message || "Operation failed";
      alert(`Error: ${errorMsg}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleRemoveStep = async (index: number) => {
    if (!id) return;
    try {
      setProcessing(true);
      const res = await api.delete(`/pipelines/interactive/${id}/steps/${index}`);
      updateState(res);
    } catch (err: any) {
      console.error("Failed to remove step", err);
      const errorMsg = err.response?.data?.detail || err.message || "Undo operation failed";
      alert(`Error: ${errorMsg}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleReset = async () => {
    if (!id) return;
    if (!confirm("Are you sure you want to reset all transformations?")) return;
    try {
      setProcessing(true);
      const res = await api.post(`/pipelines/interactive/${id}/reset`);
      updateState(res);
      setCompareData(null);
    } catch (err) {
      console.error("Failed to reset", err);
    } finally {
      setProcessing(false);
    }
  };

  const handleCommand = async (cmd: string) => {
    if (!id) return;
    const snapshotBefore = [...previewData];
    const colForCompare = selectedColumn;
    try {
      setProcessing(true);
      const res = await api.post(`/pipelines/interactive/${id}/command`, { text: cmd });
      const afterRows = res.data.preview || [];
      updateState(res);

      if (colForCompare) {
        setCompareData({ before: snapshotBefore, after: afterRows, column: colForCompare });
      }
    } catch (err: any) {
      console.error("Command failed", err);
      const errorMsg = err.response?.data?.detail || err.message || "Command failed";
      alert(`Error: ${errorMsg}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleExport = async (format: string) => {
    if (!id) return;
    try {
      const pipelineSteps = steps.map(({ operation, params }) => ({ operation, params }));
      const response = await api.post(`/datasets/${id}/export`, pipelineSteps, {
        params: { export_format: format }
      });
      const downloadUrl = response.data.download_url;
      window.open(`http://127.0.0.1:8000${downloadUrl}`, '_blank');
    } catch (err) {
      console.error(err);
      alert('Export failed');
    }
  };

  const selectedColumnType = useMemo(() => {
    if (!dataset || !selectedColumn) return null;
    const col = dataset.columns.find(c => c.name === selectedColumn);
    return col ? col.detected_type : null;
  }, [dataset, selectedColumn]);

  const alertCount = dataset?.quality_alerts?.length ?? 0;

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#121212]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-teal-600 border-t-transparent"></div>
          <p className="text-gray-400">Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#121212]">
        <div className="flex flex-col items-center justify-center p-8 text-red-400 bg-[#1e1e1e] border border-red-900/50 rounded-xl shadow-lg max-w-lg text-center">
          <AlertTriangle className="h-12 w-12 mb-4 text-red-500" />
          <h2 className="text-xl font-bold mb-2 text-red-400">Error Loading Dataset</h2>
          <p className="font-mono text-sm bg-[#121212] p-4 rounded text-red-300 w-full overflow-auto break-all text-left">{errorMsg}</p>
          <Button variant="outline" className="mt-6 border-red-500 text-red-400 hover:bg-red-500/10" onClick={() => window.location.href = "/"}>Return to Dashboard</Button>
        </div>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#121212]">
        <div className="flex h-full items-center justify-center p-8 text-red-400">Dataset not found</div>
      </div>
    );
  }

  return (
    <>
      {/* Feature 4: Expert Inference Modal */}
      {inferenceDialogOpen && (
        <InferencePanel
          datasetId={id!}
          onClose={() => setInferenceDialogOpen(false)}
          onApplyFix={(operation, columns) => handleAddStep(operation, { columns })}
        />
      )}
      {/* Feature 3: Before/After Modal */}
      {compareData && (
        <BeforeAfterModal
          column={compareData.column}
          columnType={selectedColumnType}
          beforeData={compareData.before}
          afterData={compareData.after}
          onClose={() => setCompareData(null)}
        />
      )}

      <div className="flex h-screen w-full overflow-hidden">
        {/* Feature 2: Quality panel slides in from right */}
        {qualityPanelOpen && (
          <div className="w-72 shrink-0 overflow-hidden z-20 shadow-xl border-l border-teal-900/40 flex flex-col" style={{ order: 2 }}>
            <DataQualityPanel
              alerts={dataset.quality_alerts || []}
              onAddStep={handleAddStep}
              onClose={() => setQualityPanelOpen(false)}
            />
          </div>
        )}

        <div className="flex-1 min-w-0 overflow-hidden" style={{ order: 1 }}>
          <WorkspaceLayout
            header={
              <div className="flex w-full items-center justify-between overflow-hidden">
                <div className="flex items-center gap-4 min-w-0 flex-1">
                  <Link to="/">
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-white hover:bg-white/10 shrink-0">
                      <ArrowLeft className="h-4 w-4" />
                    </Button>
                  </Link>
                  <div className="min-w-0 flex-1">
                    <h1 className="text-sm font-bold text-gray-200 tracking-wide uppercase truncate">Automated Multi-Format Data Preprocessing System</h1>
                    <div className="flex items-center gap-2 text-[10px] text-gray-500 truncate">
                      <span className="truncate max-w-[200px]" title={dataset.original_filename}>FILE: {dataset.original_filename}</span>
                      <span className="shrink-0">• {dataset.row_count.toLocaleString()} ROWS</span>
                      <span className="shrink-0">• {dataset.col_count} COLS</span>
                      {dataset.domain && (
                        <span className="shrink-0 text-teal-400 font-bold bg-teal-900/40 px-1.5 py-0.5 rounded border border-teal-800 ml-2">
                          DOMAIN: {dataset.domain.toUpperCase()}
                        </span>
                      )}
                      <button
                        onClick={() => setInferenceDialogOpen(true)}
                        className="flex items-center gap-1 ml-1 text-teal-300 font-bold shrink-0 hover:text-white px-1.5 py-0.5 rounded hover:bg-teal-800 transition-colors bg-teal-900/60 shadow-sm border border-teal-700/50"
                      >
                        <span className="text-[10px]">✨</span> INFERENCE
                      </button>
                      {alertCount > 0 && (
                        <button
                          onClick={() => setQualityPanelOpen(p => !p)}
                          className={`flex items-center gap-1 ml-2 font-bold shrink-0 px-1.5 py-0.5 rounded transition-colors ${qualityPanelOpen ? 'bg-orange-500/20 text-orange-300' : 'text-red-400 hover:text-orange-300'}`}
                        >
                          <AlertTriangle className="h-3 w-3" />
                          {alertCount} ALERTS
                        </button>
                      )}
                      {/* Feature 3 trigger: show compare button if we have snapshot data */}
                      {compareData && (
                        <button
                          onClick={() => setCompareData(compareData)}
                          className="flex items-center gap-1 ml-1 text-teal-400 font-bold shrink-0 hover:text-teal-300 px-1.5 py-0.5 rounded hover:bg-teal-900/20 transition-colors"
                        >
                          <GitCompare className="h-3 w-3" />
                          VIEW DIFF
                        </button>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0 ml-4">
                  <Button variant="secondary" size="sm" onClick={() => setApplyTemplateDialogOpen(true)} className="h-7 text-xs bg-[#3e3e42] hover:bg-[#4e4e52] text-gray-200 border border-black/50 shadow-sm whitespace-nowrap">
                    <Upload className="mr-2 h-3 w-3" /> Apply Template
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => setSaveDialogOpen(true)} className="h-7 text-xs bg-[#3e3e42] hover:bg-[#4e4e52] text-gray-200 border border-black/50 shadow-sm whitespace-nowrap">
                    <Save className="mr-2 h-3 w-3" /> Save Pipeline
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleExport('csv')} className="h-7 text-xs bg-[#3e3e42] hover:bg-[#4e4e52] text-gray-200 border border-black/50 shadow-sm whitespace-nowrap">
                    <Download className="mr-2 h-3 w-3" /> Export CSV
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => handleExport('xlsx')} className="h-7 text-xs bg-[#3e3e42] hover:bg-[#4e4e52] text-gray-200 border border-black/50 shadow-sm whitespace-nowrap">
                    <Download className="mr-2 h-3 w-3" /> Export Excel
                  </Button>
                </div>
              </div>
            }
            sidebar={
              <Sidebar
                selectedColumn={selectedColumn}
                columnType={selectedColumnType}
                onAddStep={handleAddStep}
                currentDatasetId={id!}
                currentDatasetColumns={dataset.columns}
                previewData={previewData}
              />
            }
            preview={
              <PreviewPanel
                data={previewData}
                columns={previewColumns.length > 0 ? previewColumns : dataset.columns.map(c => c.name)}
                selectedColumn={selectedColumn}
                onSelectColumn={handleSelectColumn}
                loading={processing}
              />
            }
            log={
              <>
                <LogPanel
                  steps={steps}
                  onRemoveStep={handleRemoveStep}
                  onReset={handleReset}
                  onCommand={handleCommand}
                />
                <SavePipelineDialog
                  open={saveDialogOpen}
                  onOpenChange={setSaveDialogOpen}
                  pipelineId={pipelineId}
                  currentName={pipelineName}
                  onSaved={() => {
                    alert("Pipeline saved successfully!");
                  }}
                />
                <ApplyTemplateDialog
                  open={applyTemplateDialogOpen}
                  onOpenChange={setApplyTemplateDialogOpen}
                  datasetId={id!}
                  onApplied={() => {
                    initializeWorkspace();
                    setApplyTemplateDialogOpen(false);
                  }}
                />
              </>
            }
          />
        </div>
      </div>
    </>
  );
}
