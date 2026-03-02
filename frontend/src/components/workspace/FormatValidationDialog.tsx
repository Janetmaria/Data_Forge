import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface FormatValidationDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onApply: (params: { format_type: string; action: string; pattern?: string }) => void;
    selectedColumn: string | null;
}

export function FormatValidationDialog({ open, onOpenChange, onApply, selectedColumn }: FormatValidationDialogProps) {
    const [formatType, setFormatType] = useState<string>("email");
    const [action, setAction] = useState<string>("drop_invalid");
    const [customPattern, setCustomPattern] = useState<string>("");

    const handleApply = () => {
        const params: any = { format_type: formatType, action: action };
        if (formatType === "custom") {
            if (!customPattern.trim()) {
                alert("Please enter a valid regular expression.");
                return;
            }
            params.pattern = customPattern;
        }
        onApply(params);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="bg-[#1e1e1e] border-black text-gray-300 sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="text-gray-100">Validate Format: {selectedColumn}</DialogTitle>
                    <DialogDescription className="text-gray-500">
                        Check if the values in this column match an industry-standard format.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label>Expected Format</Label>
                        <Select value={formatType} onValueChange={setFormatType}>
                            <SelectTrigger className="bg-[#2d2d2d] border-black/50 text-gray-300">
                                <SelectValue placeholder="Select format..." />
                            </SelectTrigger>
                            <SelectContent className="bg-[#2d2d2d] border-black/50 text-gray-300">
                                <SelectItem value="email">Email Address</SelectItem>
                                <SelectItem value="phone">Phone Number</SelectItem>
                                <SelectItem value="url">Website URL</SelectItem>
                                <SelectItem value="ip_address">IP Address</SelectItem>
                                <SelectItem value="credit_card">Credit Card Number</SelectItem>
                                <SelectItem value="aadhaar">Aadhaar Card Number</SelectItem>
                                <SelectItem value="custom">Custom Regex Pattern</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {formatType === "custom" && (
                        <div className="grid gap-2 mt-2">
                            <Label>Regular Expression</Label>
                            <Input
                                value={customPattern}
                                onChange={(e) => setCustomPattern(e.target.value)}
                                placeholder="e.g. ^[A-Z]{3}-\d{4}$"
                                className="bg-[#2d2d2d] border-black/50 text-gray-300"
                            />
                        </div>
                    )}

                    <div className="grid gap-2 mt-2">
                        <Label>Action for Invalid Rows</Label>
                        <Select value={action} onValueChange={setAction}>
                            <SelectTrigger className="bg-[#2d2d2d] border-black/50 text-gray-300">
                                <SelectValue placeholder="Select action..." />
                            </SelectTrigger>
                            <SelectContent className="bg-[#2d2d2d] border-black/50 text-gray-300">
                                <SelectItem value="drop_invalid">Drop Entire Row</SelectItem>
                                <SelectItem value="set_null">Keep Row, Set Cell to Missing (NaN)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="secondary" onClick={() => onOpenChange(false)} className="bg-transparent border border-gray-600 hover:bg-gray-800 text-gray-300">Cancel</Button>
                    <Button onClick={handleApply} className="bg-teal-600 hover:bg-teal-700 text-white">
                        Apply Validation
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
