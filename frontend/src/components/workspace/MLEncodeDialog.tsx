import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';

interface MLEncodeDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    selectedColumn: string | null;
    onApply: (params: { method: string }) => void;
}

export function MLEncodeDialog({ open, onOpenChange, selectedColumn, onApply }: MLEncodeDialogProps) {
    const [method, setMethod] = useState<string>("one_hot");

    const handleApply = () => {
        onApply({ method });
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="bg-[#1e1e1e] border-black text-gray-300 sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="text-gray-100">Encode Categorical</DialogTitle>
                    <DialogDescription className="text-gray-500">
                        Convert {selectedColumn} to numeric features.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label>Encoding Method</Label>
                        <Select value={method} onValueChange={setMethod}>
                            <SelectTrigger className="w-[180px] bg-[#2d2d2d] border-black/50 text-gray-300">
                                <SelectValue placeholder="Select Method" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#2d2d2d] border-black/50 text-gray-300">
                                <SelectItem value="one_hot">One-Hot</SelectItem>
                                <SelectItem value="ordinal">Ordinal</SelectItem>
                                <SelectItem value="frequency">Frequency</SelectItem>
                                <SelectItem value="target">Target</SelectItem>
                                <SelectItem value="binary">Binary</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="secondary" onClick={() => onOpenChange(false)} className="bg-transparent border border-gray-600 hover:bg-gray-800 text-gray-300">Cancel</Button>
                    <Button onClick={handleApply} className="bg-teal-600 hover:bg-teal-700 text-white">
                        Apply Encoding
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
