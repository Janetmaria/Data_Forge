import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import api from '@/lib/api';

interface SavePipelineDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  pipelineId: string | null;
  currentName: string;
  onSaved: () => void;
}

export function SavePipelineDialog({ open, onOpenChange, pipelineId, currentName, onSaved }: SavePipelineDialogProps) {
  const [name, setName] = useState(currentName);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!pipelineId) return;
    try {
      setLoading(true);
      // We need an endpoint to update pipeline details.
      // Currently we only have create (POST /) and interactive endpoints.
      // We should probably add PUT /pipelines/{id} or similar.
      // For now, let's assume we can update it via a new endpoint or reusing create if we were making a new one.
      // But interactive pipeline IS the draft. We just want to give it a name and "save" it.
      // Let's implement a simple update endpoint on backend or use a specific action.
      // Since I didn't create a specific update endpoint yet, I will create one now.
      
      await api.post(`/pipelines/${pipelineId}/clone`, {
        name,
        description
      });
      
      onSaved();
      onOpenChange(false);
    } catch (err) {
      console.error(err);
      alert('Failed to save pipeline');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-[#1e1e1e] border-black text-gray-300 sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="text-gray-100">Save Pipeline</DialogTitle>
          <DialogDescription className="text-gray-500">
            Save your current steps as a named pipeline for future use.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>Pipeline Name</Label>
            <Input 
              value={name} 
              onChange={(e) => setName(e.target.value)} 
              className="bg-[#2d2d2d] border-black/50 text-gray-300"
            />
          </div>
          <div className="grid gap-2">
            <Label>Description</Label>
            <Textarea 
              value={description} 
              onChange={(e) => setDescription(e.target.value)} 
              className="bg-[#2d2d2d] border-black/50 text-gray-300"
              placeholder="Describe what this pipeline does..."
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)} className="bg-transparent border border-gray-600 hover:bg-gray-800 text-gray-300">Cancel</Button>
          <Button onClick={handleSave} disabled={!name || loading} className="bg-teal-600 hover:bg-teal-700 text-white">
            {loading ? 'Saving...' : 'Save Pipeline'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
