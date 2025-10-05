import { Search, Globe, FileText, Zap } from 'lucide-react';

interface SearchModeSelectorProps {
    selectedMode: 'auto' | 'web' | 'documents' | 'hybrid';
    onModeChange: (mode: 'auto' | 'web' | 'documents' | 'hybrid') => void;
}

export function SearchModeSelector({ selectedMode, onModeChange }: SearchModeSelectorProps) {
    const modes = [
        {
            value: 'auto' as const,
            label: 'Auto',
            icon: Search,
            description: 'Automatically select best search method',
            color: 'text-blue-500'
        },
        {
            value: 'web' as const,
            label: 'Web',
            icon: Globe,
            description: 'Search current web information',
            color: 'text-green-500'
        },
        {
            value: 'documents' as const,
            label: 'Documents',
            icon: FileText,
            description: 'Search uploaded documents only',
            color: 'text-purple-500'
        },
        {
            value: 'hybrid' as const,
            label: 'Hybrid',
            icon: Zap,
            description: 'Combine web and documents',
            color: 'text-orange-500'
        }
    ];

    return (
        <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground mr-1">Search:</span>
            <select
                value={selectedMode}
                onChange={(e) => onModeChange(e.target.value as 'auto' | 'web' | 'documents' | 'hybrid')}
                className="text-sm border rounded px-2 py-1 cursor-pointer hover:border-primary transition-colors"
                title="Select search mode"
                aria-label="Search mode"
            >
                {modes.map((mode) => (
                    <option key={mode.value} value={mode.value}>
                        {mode.label}
                    </option>
                ))}
            </select>
            
            {/* Mode description tooltip */}
            <div className="relative group">
                <Search className="w-4 h-4 text-muted-foreground cursor-help" />
                <div className="absolute bottom-full right-0 mb-2 w-64 p-3 bg-popover text-popover-foreground text-xs rounded-lg shadow-lg border opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                    <div className="font-semibold mb-1">
                        {modes.find(m => m.value === selectedMode)?.label} Mode
                    </div>
                    <div className="text-muted-foreground">
                        {modes.find(m => m.value === selectedMode)?.description}
                    </div>
                </div>
            </div>
        </div>
    );
}
