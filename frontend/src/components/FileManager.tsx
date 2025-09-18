import { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash2, RefreshCw, FolderOpen } from "lucide-react";
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

export function FileManager() {
    const [files, setFiles] = useState<StoredFile[]>([]);
    const [stats, setStats] = useState<StorageStats | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

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

    const deleteFile = async (fileId: string) => {
        try {
            await axios.delete(`${API_BASE_URL}/files/${fileId}`);
            await loadFiles(); // Refresh the list
        } catch (err) {
            setError('Failed to delete file');
            console.error('Error deleting file:', err);
        }
    };

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
    }, []);

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

            <CardContent className="space-y-4">
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

                {/* Files List */}
                <div>
                    <h3 className="text-lg font-semibold mb-3">Uploaded Files ({files.length})</h3>

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
        </Card>
    );
}