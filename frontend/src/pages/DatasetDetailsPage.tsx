import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Download, AlertTriangle, Save, Upload } from 'lucide-react';
import { WorkspaceLayout } from '@/layouts/WorkspaceLayout';
import { Sidebar } from '@/components/workspace/Sidebar';
import { PreviewPanel } from '@/components/workspace/PreviewPanel';
import { LogPanel } from '@/components/workspace/LogPanel';
import { SavePipelineDialog } from '@/components/workspace/SavePipelineDialog';
import { ApplyTemplateDialog } from '@/components/workspace/ApplyTemplateDialog';

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

  useEffect(() => {
    if (id) {
      initializeWorkspace();
    }
  }, [id]);

  const initializeWorkspace = async () => {
    try {
      setLoading(true);
      // 1. Fetch Dataset Metadata
      const dsRes = await api.get(`/datasets/${id}`);
      const datasetData = dsRes.data;

      // 2. Fetch Interactive Pipeline State
      const pipeRes = await api.get(`/pipelines/interactive/${id}`);
      setSteps(pipeRes.data.steps);
      setPreviewData(pipeRes.data.preview);
      setPreviewColumns(pipeRes.data.columns || []);
      setPipelineId(pipeRes.data.pipeline_id);

      // 3. Update dataset with pipeline alerts (this has the current transformed data alerts)
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
    console.log("UpdateState called with:", res.data);
    console.log("Preview data sample:", res.data.preview?.slice(0, 3));
    console.log("Steps:", res.data.steps);

    setSteps(res.data.steps);
    // Create a new array reference to ensure React re-render
    setPreviewData([...(res.data.preview || [])]);
    setPreviewColumns(res.data.columns || []);

    // Update quality alerts dynamically - ensure new object reference for React re-render
    if (dataset) {
      setDataset({
        ...dataset,
        quality_alerts: res.data.quality_alerts ? [...res.data.quality_alerts] : dataset.quality_alerts,
        columns: res.data.column_schemas ? [...res.data.column_schemas] : dataset.columns
      });
    }
  };

  const handleAddStep = async (operation: string, params: any) => {
    if (!id) return;
    try {
      setProcessing(true);
      console.log("Sending API request:", { operation, params });
      const res = await api.post(`/pipelines/interactive/${id}/steps`, {
        operation,
        params
      });
      console.log("API response received:", res);
      console.log("API response data:", res.data);
      updateState(res);
    } catch (err: any) {
      console.error("Failed to add step", err);
      // Enhanced error handling
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
    } catch (err) {
      console.error("Failed to reset", err);
    } finally {
      setProcessing(false);
    }
  };

  const handleCommand = async (cmd: string) => {
    if (!id) return;
    try {
      setProcessing(true);
      const res = await api.post(`/pipelines/interactive/${id}/command`, { text: cmd });

      updateState(res);

      // Optionally show a toast or message about the action taken
      if (res.data.added_step) {
        console.log("Executed command:", res.data.added_step);
      }
    } catch (err) {
      console.error("Command failed", err);
      alert("Could not understand or execute command");
    } finally {
      setProcessing(false);
    }
  };

  const handleExport = async (format: string) => {
    if (!id) return;
    try {
      // We can pass the current steps from state to ensure we export exactly what we see
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

  // Determine selected column type
  const selectedColumnType = useMemo(() => {
    if (!dataset || !selectedColumn) return null;
    const col = dataset.columns.find(c => c.name === selectedColumn);
    return col ? col.detected_type : null;
  }, [dataset, selectedColumn]);

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
                {dataset.quality_alerts?.length > 0 && (
                  <span className="text-red-400 flex items-center gap-1 ml-2 font-bold shrink-0">
                    <AlertTriangle className="h-3 w-3" /> {dataset.quality_alerts.length} ALERTS
                  </span>
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
          onSelectColumn={setSelectedColumn}
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
  );
}
