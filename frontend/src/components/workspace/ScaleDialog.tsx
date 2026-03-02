import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface ScaleDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onApply: (params: { feature_min: number; feature_max: number }) => void;
}

export function ScaleDialog({ open, onOpenChange, onApply }: ScaleDialogProps) {
    const [featureMin, setFeatureMin] = useState<string>("0");
    const [featureMax, setFeatureMax] = useState<string>("1");

    const handleApply = () => {
        const minVal = parseFloat(featureMin);
        const maxVal = parseFloat(featureMax);

        // Basic validation
        if (isNaN(minVal) || isNaN(maxVal)) {
            alert("Please enter valid numbers for min and max bounds.");
            return;
        }

        if (minVal >= maxVal) {
            alert("Feature Min must be strictly less than Feature Max.");
            return;
        }

        onApply({ feature_min: minVal, feature_max: maxVal });
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="bg-[#1e1e1e] border-black text-gray-300 sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="text-gray-100">Min-Max Scaling</DialogTitle>
                    <DialogDescription className="text-gray-500">
                        Choose the target range for your normalized data.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <Label>Feature Min</Label>
                            <Input
                                type="number"
                                value={featureMin}
                                onChange={(e) => setFeatureMin(e.target.value)}
                                className="bg-[#2d2d2d] border-black/50 text-gray-300"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label>Feature Max</Label>
                            <Input
                                type="number"
                                value={featureMax}
                                onChange={(e) => setFeatureMax(e.target.value)}
                                className="bg-[#2d2d2d] border-black/50 text-gray-300"
                            />
                        </div>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="secondary" onClick={() => onOpenChange(false)} className="bg-transparent border border-gray-600 hover:bg-gray-800 text-gray-300">Cancel</Button>
                    <Button onClick={handleApply} className="bg-teal-600 hover:bg-teal-700 text-white">
                        Apply Scaling
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
