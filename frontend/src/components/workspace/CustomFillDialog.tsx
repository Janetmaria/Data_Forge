import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface CustomFillDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onApply: (params: { method: string; value: string }) => void;
    selectedColumn: string | null;
}

export function CustomFillDialog({ open, onOpenChange, onApply, selectedColumn }: CustomFillDialogProps) {
    const [fillValue, setFillValue] = useState<string>("");

    const handleApply = () => {
        if (!fillValue.trim()) {
            alert("Please enter a value.");
            return;
        }

        // Let the backend decide whether to cast this to an int, float, or keep as string
        onApply({ method: 'constant', value: fillValue });
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="bg-[#1e1e1e] border-black text-gray-300 sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="text-gray-100">Custom Fill: {selectedColumn}</DialogTitle>
                    <DialogDescription className="text-gray-500">
                        Replace all missing (NaN) values in this column with a specific number or text.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label>Replacement Value</Label>
                        <Input
                            type="text"
                            placeholder="e.g. 0, Unknown, Not Applicable"
                            value={fillValue}
                            onChange={(e) => setFillValue(e.target.value)}
                            className="bg-[#2d2d2d] border-black/50 text-gray-300"
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="secondary" onClick={() => onOpenChange(false)} className="bg-transparent border border-gray-600 hover:bg-gray-800 text-gray-300">Cancel</Button>
                    <Button onClick={handleApply} className="bg-teal-600 hover:bg-teal-700 text-white">
                        Apply Fill
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
