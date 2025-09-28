import { useState, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { 
    Dialog, 
    DialogContent, 
    DialogHeader, 
    DialogTitle, 
    DialogTrigger,
    DialogFooter
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Settings, Trash2, Edit, FolderOpen } from "lucide-react";
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface Namespace {
    name: string;
    document_count: number;
    is_default: boolean;
}

interface NamespaceSelectorProps {
    selectedNamespace: string;
    onNamespaceChange: (namespace: string) => void;
    showManagement?: boolean;
}

export function NamespaceSelector({ 
    selectedNamespace, 
    onNamespaceChange, 
    showManagement = true 
}: NamespaceSelectorProps) {
    const [namespaces, setNamespaces] = useState<Namespace[]>([]);
    const [error, setError] = useState<string | null>(null);
    
    // Dialog states
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    const [isManageDialogOpen, setIsManageDialogOpen] = useState(false);
    const [newNamespaceName, setNewNamespaceName] = useState('');
    const [isCreating, setIsCreating] = useState(false);
    
    // Rename/delete states
    const [editingNamespace, setEditingNamespace] = useState<string | null>(null);
    const [editingName, setEditingName] = useState('');
    const [isDeleting, setIsDeleting] = useState<string | null>(null);

    const loadNamespaces = async () => {
        setError(null);
        try {
            const response = await axios.get(`${API_BASE_URL}/namespaces`);
            setNamespaces(response.data.namespaces);
        } catch (err) {
            setError('Failed to load namespaces');
            console.error('Error loading namespaces:', err);
        }
    };

    useEffect(() => {
        loadNamespaces();
    }, []);

    const handleCreateNamespace = async () => {
        if (!newNamespaceName.trim()) return;
        
        setIsCreating(true);
        try {
            const formData = new FormData();
            formData.append('name', newNamespaceName.trim());
            
            await axios.post(`${API_BASE_URL}/namespaces`, formData);
            
            setNewNamespaceName('');
            setIsCreateDialogOpen(false);
            await loadNamespaces();
            onNamespaceChange(newNamespaceName.trim());
        } catch (err: any) {
            console.error('Error creating namespace:', err);
            if (err.response?.status === 409) {
                setError('Namespace already exists');
            } else if (err.response?.status === 400) {
                setError('Invalid namespace name. Use only letters, numbers, underscores, and hyphens.');
            } else {
                setError('Failed to create namespace');
            }
        } finally {
            setIsCreating(false);
        }
    };

    const handleRenameNamespace = async (oldName: string) => {
        if (!editingName.trim() || editingName === oldName) {
            setEditingNamespace(null);
            setEditingName('');
            return;
        }
        
        try {
            const formData = new FormData();
            formData.append('new_name', editingName.trim());
            
            await axios.put(`${API_BASE_URL}/namespaces/${oldName}/rename`, formData);
            
            setEditingNamespace(null);
            setEditingName('');
            await loadNamespaces();
            
            // Update selected namespace if it was renamed
            if (selectedNamespace === oldName) {
                onNamespaceChange(editingName.trim());
            }
        } catch (err: any) {
            console.error('Error renaming namespace:', err);
            if (err.response?.status === 409) {
                setError('Namespace name already exists');
            } else if (err.response?.status === 400) {
                setError('Cannot rename default namespace or invalid name');
            } else {
                setError('Failed to rename namespace');
            }
        }
    };

    const handleDeleteNamespace = async (name: string) => {
        if (name === 'default') {
            setError('Cannot delete the default namespace');
            return;
        }
        
        if (!window.confirm(`Are you sure you want to delete namespace "${name}"? This will permanently delete all documents in this namespace.`)) {
            return;
        }
        
        setIsDeleting(name);
        try {
            await axios.delete(`${API_BASE_URL}/namespaces/${name}`);
            await loadNamespaces();
            
            // Switch to default if current namespace was deleted
            if (selectedNamespace === name) {
                onNamespaceChange('default');
            }
        } catch (err) {
            console.error('Error deleting namespace:', err);
            setError('Failed to delete namespace');
        } finally {
            setIsDeleting(null);
        }
    };

    const selectedNamespaceData = namespaces.find(ns => ns.name === selectedNamespace);

    return (
        <div className="flex items-center gap-2">
            {/* Namespace Selector */}
            <div className="flex items-center gap-2">
                <FolderOpen className="w-4 h-4 text-muted-foreground" />
                <Select value={selectedNamespace} onValueChange={onNamespaceChange}>
                    <SelectTrigger className="w-48">
                        <SelectValue placeholder="Select namespace" />
                    </SelectTrigger>
                    <SelectContent>
                        {namespaces.map((namespace) => (
                            <SelectItem key={namespace.name} value={namespace.name}>
                                <div className="flex items-center justify-between w-full">
                                    <span>{namespace.name}</span>
                                    <div className="flex items-center gap-1">
                                        {namespace.is_default && (
                                            <Badge variant="secondary" className="text-xs">Default</Badge>
                                        )}
                                        <Badge variant="outline" className="text-xs">
                                            {namespace.document_count}
                                        </Badge>
                                    </div>
                                </div>
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                
                {selectedNamespaceData && (
                    <Badge variant="outline" className="text-xs">
                        {selectedNamespaceData.document_count} docs
                    </Badge>
                )}
            </div>

            {/* Management Buttons */}
            {showManagement && (
                <div className="flex items-center gap-1">
                    {/* Create Namespace Button */}
                    <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                        <DialogTrigger asChild>
                            <Button variant="outline" size="sm" title="Create New Namespace">
                                <Plus className="w-4 h-4" />
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Create New Namespace</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2">
                                    <Label htmlFor="namespace-name">Namespace Name</Label>
                                    <Input
                                        id="namespace-name"
                                        value={newNamespaceName}
                                        onChange={(e) => setNewNamespaceName(e.target.value)}
                                        placeholder="e.g., project-name, research-docs"
                                        disabled={isCreating}
                                    />
                                    <p className="text-sm text-muted-foreground">
                                        Use letters, numbers, underscores, and hyphens only.
                                    </p>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button 
                                    variant="outline" 
                                    onClick={() => setIsCreateDialogOpen(false)}
                                    disabled={isCreating}
                                >
                                    Cancel
                                </Button>
                                <Button 
                                    onClick={handleCreateNamespace}
                                    disabled={!newNamespaceName.trim() || isCreating}
                                >
                                    {isCreating ? 'Creating...' : 'Create'}
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>

                    {/* Manage Namespaces Button */}
                    <Dialog open={isManageDialogOpen} onOpenChange={setIsManageDialogOpen}>
                        <DialogTrigger asChild>
                            <Button variant="outline" size="sm" title="Manage Namespaces">
                                <Settings className="w-4 h-4" />
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                            <DialogHeader>
                                <DialogTitle>Manage Namespaces</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4 py-4 max-h-96 overflow-y-auto">
                                {namespaces.map((namespace) => (
                                    <Card key={namespace.name}>
                                        <CardContent className="p-4">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    {editingNamespace === namespace.name ? (
                                                        <Input
                                                            value={editingName}
                                                            onChange={(e) => setEditingName(e.target.value)}
                                                            onBlur={() => handleRenameNamespace(namespace.name)}
                                                            onKeyDown={(e) => {
                                                                if (e.key === 'Enter') {
                                                                    handleRenameNamespace(namespace.name);
                                                                } else if (e.key === 'Escape') {
                                                                    setEditingNamespace(null);
                                                                    setEditingName('');
                                                                }
                                                            }}
                                                            className="w-48"
                                                            autoFocus
                                                        />
                                                    ) : (
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-medium">{namespace.name}</span>
                                                            {namespace.is_default && (
                                                                <Badge variant="secondary">Default</Badge>
                                                            )}
                                                        </div>
                                                    )}
                                                    <Badge variant="outline">
                                                        {namespace.document_count} documents
                                                    </Badge>
                                                </div>
                                                
                                                <div className="flex items-center gap-1">
                                                    {!namespace.is_default && (
                                                        <>
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() => {
                                                                    setEditingNamespace(namespace.name);
                                                                    setEditingName(namespace.name);
                                                                }}
                                                                title="Rename namespace"
                                                            >
                                                                <Edit className="w-4 h-4" />
                                                            </Button>
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() => handleDeleteNamespace(namespace.name)}
                                                                disabled={isDeleting === namespace.name}
                                                                title="Delete namespace"
                                                                className="text-red-500 hover:text-red-700"
                                                            >
                                                                <Trash2 className="w-4 h-4" />
                                                            </Button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
            )}

            {/* Error Display */}
            {error && (
                <div className="text-sm text-red-600 bg-red-50 px-2 py-1 rounded">
                    {error}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setError(null)}
                        className="ml-2 h-auto p-0 text-red-600"
                    >
                        ×
                    </Button>
                </div>
            )}
        </div>
    );
}