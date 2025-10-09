import { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { NamespaceSelector } from "./NamespaceSelector";
import { Trash2, RefreshCw, FolderOpen, File, Search } from "lucide-react";
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface StoredFile {
    file_id: string;
    original_filename: string;
    file_size: number;
    content_type: string;
    upload_timestamp: string;
    user_id?: string;
}

interface StorageStats {
    total_files: number;
    total_size_bytes: number;
    total_size_mb: number;
}

interface NamespaceDocument {
    doc_id: string;
    filename: string;
    namespace: string;
    chunk_count: number;
    session_id: string;
}

interface NamespaceDocumentsResponse {
    namespace: string;
    documents: NamespaceDocument[];
    total_documents: number;
    total_chunks: number;
}

export function FileManager() {
    const [files, setFiles] = useState<StoredFile[]>([]);
    const [stats, setStats] = useState<StorageStats | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Namespace-specific state
    const [selectedNamespace, setSelectedNamespace] = useState('default');
    const [namespaceDocuments, setNamespaceDocuments] = useState<NamespaceDocument[]>([]);
    const [isLoadingDocs, setIsLoadingDocs] = useState(false);
    
    // Document management state
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [documentToDelete, setDocumentToDelete] = useState<NamespaceDocument | null>(null);
    const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);

    const loadFiles = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const [filesResponse, statsResponse] = await Promise.all([
                axios.get(`${API_BASE_URL}/files`),
                axios.get(`${API_BASE_URL}/storage/stats`)
            ]);

            setFiles(filesResponse.data.files);
            setStats(statsResponse.data);
        } catch (err) {
            setError('Failed to load files');
            console.error('Error loading files:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const loadNamespaceDocuments = async (namespace: string) => {
        setIsLoadingDocs(true);
        try {
            const response = await axios.get<NamespaceDocumentsResponse>(`${API_BASE_URL}/namespaces/${namespace}/documents`);
            setNamespaceDocuments(response.data.documents);
        } catch (err) {
            console.error('Error loading namespace documents:', err);
            setNamespaceDocuments([]);
        } finally {
            setIsLoadingDocs(false);
        }
    };

    const handleNamespaceChange = (namespace: string) => {
        setSelectedNamespace(namespace);
        loadNamespaceDocuments(namespace);
        setSelectedDocuments(new Set()); // Clear selection when changing namespace
        setSearchQuery(''); // Clear search
    };

    const deleteFile = async (fileId: string) => {
        try {
            await axios.delete(`${API_BASE_URL}/files/${fileId}`);
            await loadFiles(); // Refresh the list
        } catch (err) {
            setError('Failed to delete file');
            console.error('Error deleting file:', err);
        }
    };

    const deleteDocument = async (doc: NamespaceDocument) => {
        try {
            await axios.delete(`${API_BASE_URL}/namespaces/${doc.namespace}/documents/${doc.doc_id}`);
            await loadNamespaceDocuments(selectedNamespace);
            setSelectedDocuments(new Set()); // Clear selection
            setDeleteDialogOpen(false);
            setDocumentToDelete(null);
        } catch (err) {
            setError('Failed to delete document');
            console.error('Error deleting document:', err);
        }
    };

    const bulkDeleteDocuments = async () => {
        try {
            const deletePromises = Array.from(selectedDocuments).map(docId => 
                axios.delete(`${API_BASE_URL}/namespaces/${selectedNamespace}/documents/${docId}`)
            );
            await Promise.all(deletePromises);
            await loadNamespaceDocuments(selectedNamespace);
            setSelectedDocuments(new Set());
            setBulkDeleteDialogOpen(false);
        } catch (err) {
            setError('Failed to delete selected documents');
            console.error('Error deleting documents:', err);
        }
    };

    const toggleDocumentSelection = (docId: string) => {
        const newSelection = new Set(selectedDocuments);
        if (newSelection.has(docId)) {
            newSelection.delete(docId);
        } else {
            newSelection.add(docId);
        }
        setSelectedDocuments(newSelection);
    };

    const toggleSelectAll = () => {
        if (selectedDocuments.size === filteredDocuments.length) {
            setSelectedDocuments(new Set());
        } else {
            setSelectedDocuments(new Set(filteredDocuments.map(doc => doc.doc_id)));
        }
    };

    const openDeleteDialog = (doc: NamespaceDocument) => {
        setDocumentToDelete(doc);
        setDeleteDialogOpen(true);
    };

    const filteredDocuments = namespaceDocuments.filter(doc =>
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.session_id.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const cleanupOldFiles = async () => {
        try {
            await axios.post(`${API_BASE_URL}/storage/cleanup`);
            await loadFiles(); // Refresh the list
        } catch (err) {
            setError('Failed to cleanup files');
            console.error('Error cleaning up files:', err);
        }
    };

    useEffect(() => {
        loadFiles();
        loadNamespaceDocuments(selectedNamespace);
    }, []);

    useEffect(() => {
        loadNamespaceDocuments(selectedNamespace);
    }, [selectedNamespace]);

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const formatDate = (isoString: string) => {
        return new Date(isoString).toLocaleString();
    };

    const getFileIcon = (filename: string) => {
        const ext = filename.split('.').pop()?.toLowerCase();
        switch (ext) {
            case 'pdf':
                return '📄';
            case 'txt':
            case 'md':
                return '📝';
            case 'docx':
                return '📃';
            case 'json':
                return '🔧';
            default:
                return '📎';
        }
    };

    return (
        <Card className="w-full max-w-4xl">
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
                <div className="flex items-center gap-2">
                    <FolderOpen className="w-5 h-5" />
                    <CardTitle>File Manager</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={loadFiles}
                        disabled={isLoading}
                    >
                        <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={cleanupOldFiles}
                        disabled={isLoading}
                    >
                        Clean Up Old Files
                    </Button>
                </div>
            </CardHeader>

            <CardContent className="space-y-6">
                {/* Namespace Selector */}
                <div className="flex items-center justify-between">
                    <NamespaceSelector
                        selectedNamespace={selectedNamespace}
                        onNamespaceChange={handleNamespaceChange}
                    />
                    <div className="text-sm text-muted-foreground">
                        Documents in namespace: {namespaceDocuments.length}
                    </div>
                </div>
                {/* Storage Stats */}
                {stats && (
                    <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-3 bg-muted rounded-lg">
                            <div className="text-2xl font-bold">{stats.total_files}</div>
                            <div className="text-sm text-muted-foreground">Total Files</div>
                        </div>
                        <div className="text-center p-3 bg-muted rounded-lg">
                            <div className="text-2xl font-bold">{stats.total_size_mb}</div>
                            <div className="text-sm text-muted-foreground">MB Used</div>
                        </div>
                        <div className="text-center p-3 bg-muted rounded-lg">
                            <div className="text-2xl font-bold">{formatFileSize(stats.total_size_bytes)}</div>
                            <div className="text-sm text-muted-foreground">Storage Used</div>
                        </div>
                    </div>
                )}

                {/* Error Display */}
                {error && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                        {error}
                    </div>
                )}

                {/* RAG Documents in Current Namespace */}
                <div>
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold">
                            RAG Documents in "{selectedNamespace}" ({filteredDocuments.length}/{namespaceDocuments.length})
                        </h3>
                        {selectedDocuments.size > 0 && (
                            <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => setBulkDeleteDialogOpen(true)}
                            >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Delete Selected ({selectedDocuments.size})
                            </Button>
                        )}
                    </div>

                    {/* Search Bar */}
                    <div className="relative mb-3">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                            placeholder="Search documents by name or session..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                        />
                    </div>

                    {isLoadingDocs ? (
                        <div className="text-center py-8">Loading documents...</div>
                    ) : namespaceDocuments.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            No documents in this namespace yet
                        </div>
                    ) : filteredDocuments.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            No documents match your search
                        </div>
                    ) : (
                        <>
                            {/* Select All Option */}
                            {filteredDocuments.length > 0 && (
                                <div className="flex items-center gap-2 mb-2 p-2 bg-muted rounded-lg">
                                    <Checkbox
                                        checked={selectedDocuments.size === filteredDocuments.length && filteredDocuments.length > 0}
                                        onCheckedChange={toggleSelectAll}
                                    />
                                    <span className="text-sm font-medium">Select All</span>
                                </div>
                            )}
                            
                            <ScrollArea className="h-64">
                                <div className="space-y-2">
                                    {filteredDocuments.map((doc) => (
                                        <Card key={doc.doc_id} className="p-3">
                                            <div className="flex items-center gap-3">
                                                <Checkbox
                                                    checked={selectedDocuments.has(doc.doc_id)}
                                                    onCheckedChange={() => toggleDocumentSelection(doc.doc_id)}
                                                />
                                                <File className="w-5 h-5 text-blue-500" />
                                                <div className="flex-1 min-w-0">
                                                    <p className="font-medium truncate">{doc.filename}</p>
                                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                        <Badge variant="outline" className="text-xs">
                                                            {doc.chunk_count} chunks
                                                        </Badge>
                                                        <span>Session: {doc.session_id}</span>
                                                    </div>
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => openDeleteDialog(doc)}
                                                    className="h-8 w-8 p-0 text-red-500 hover:text-red-700"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </Card>
                                    ))}
                                </div>
                            </ScrollArea>
                        </>
                    )}
                </div>

                {/* All Uploaded Files */}
                <div>
                    <h3 className="text-lg font-semibold mb-3">All Uploaded Files ({files.length})</h3>

                    {isLoading ? (
                        <div className="text-center py-8">Loading files...</div>
                    ) : files.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            No files uploaded yet
                        </div>
                    ) : (
                        <ScrollArea className="h-96">
                            <div className="space-y-2">
                                {files.map((file) => (
                                    <Card key={file.file_id} className="p-3">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                                <span className="text-lg">
                                                    {getFileIcon(file.original_filename)}
                                                </span>
                                                <div className="min-w-0 flex-1">
                                                    <p className="font-medium truncate">
                                                        {file.original_filename}
                                                    </p>
                                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                        <span>{formatFileSize(file.file_size)}</span>
                                                        <Badge variant="secondary" className="text-xs">
                                                            {file.content_type.split('/')[1]?.toUpperCase()}
                                                        </Badge>
                                                        <span>{formatDate(file.upload_timestamp)}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-1">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => deleteFile(file.file_id)}
                                                    className="h-8 w-8 p-0 text-red-500 hover:text-red-700"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        </ScrollArea>
                    )}
                </div>
            </CardContent>

            {/* Delete Confirmation Dialog */}
            <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Document</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to delete "{documentToDelete?.filename}"?
                            This will remove {documentToDelete?.chunk_count} chunks from the namespace.
                            This action cannot be undone.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setDeleteDialogOpen(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={() => documentToDelete && deleteDocument(documentToDelete)}
                        >
                            Delete
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Bulk Delete Confirmation Dialog */}
            <Dialog open={bulkDeleteDialogOpen} onOpenChange={setBulkDeleteDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Multiple Documents</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to delete {selectedDocuments.size} selected document(s)?
                            This action cannot be undone.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setBulkDeleteDialogOpen(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={bulkDeleteDocuments}
                        >
                            Delete {selectedDocuments.size} Document(s)
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </Card>
    );
}