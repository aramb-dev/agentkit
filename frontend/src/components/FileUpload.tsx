import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { FileAttachment } from "@/types/chat";
import { Upload, X, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileUploadProps {
    onFilesAdded: (files: FileAttachment[]) => void;
    onFileRemoved: (fileId: string) => void;
    uploadedFiles: FileAttachment[];
    maxFiles?: number;
    acceptedTypes?: string[];
}

export function FileUpload({
    onFilesAdded,
    onFileRemoved,
    uploadedFiles,
    maxFiles = 5,
    acceptedTypes = ['.pdf', '.txt', '.docx', '.md', '.json']
}: FileUploadProps) {

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const newFiles: FileAttachment[] = acceptedFiles.map(file => ({
            id: crypto.randomUUID(),
            name: file.name,
            size: file.size,
            type: file.type,
            uploadProgress: 0,
            file: file, // Store the actual File object
            uploaded: false
        }));

        onFilesAdded(newFiles);
    }, [onFilesAdded]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/plain': ['.txt'],
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'text/markdown': ['.md'],
            'application/json': ['.json']
        },
        maxFiles,
        maxSize: 10 * 1024 * 1024, // 10MB
        disabled: uploadedFiles.length >= maxFiles
    });

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const getFileIcon = (fileName: string) => {
        const ext = fileName.split('.').pop()?.toLowerCase();
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
        <div className="space-y-3">
            {/* Dropzone */}
            <Card
                {...getRootProps()}
                className={cn(
                    "border-2 border-dashed cursor-pointer transition-colors",
                    isDragActive
                        ? "border-blue-500 bg-blue-50"
                        : "border-muted-foreground/25 hover:border-muted-foreground/50",
                    uploadedFiles.length >= maxFiles && "opacity-50 cursor-not-allowed"
                )}
            >
                <CardContent className="p-6 text-center">
                    <input {...getInputProps()} />
                    <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground mb-1">
                        {isDragActive
                            ? "Drop the files here..."
                            : "Click to upload or drag and drop"
                        }
                    </p>
                    <p className="text-xs text-muted-foreground">
                        Supports: {acceptedTypes.join(', ')} (max {maxFiles} files, 10MB each)
                    </p>
                    {uploadedFiles.length >= maxFiles && (
                        <p className="text-xs text-red-500 mt-1">
                            Maximum number of files reached
                        </p>
                    )}
                </CardContent>
            </Card>

            {/* Uploaded files list */}
            {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                    <h4 className="text-sm font-medium">Uploaded Files ({uploadedFiles.length}/{maxFiles})</h4>
                    {uploadedFiles.map((file) => (
                        <Card key={file.id} className="p-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                    <span className="text-lg">{getFileIcon(file.name)}</span>
                                    <div className="min-w-0 flex-1">
                                        <p className="text-sm font-medium truncate">{file.name}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {formatFileSize(file.size)}
                                        </p>
                                    </div>

                                    {/* Upload status */}
                                    {file.uploadProgress !== undefined && (
                                        <div className="flex items-center gap-1">
                                            {file.uploadProgress === 100 ? (
                                                <CheckCircle className="w-4 h-4 text-green-500" />
                                            ) : file.uploadProgress === -1 ? (
                                                <AlertCircle className="w-4 h-4 text-red-500" />
                                            ) : (
                                                <Badge variant="secondary" className="text-xs">
                                                    {file.uploadProgress}%
                                                </Badge>
                                            )}
                                        </div>
                                    )}
                                </div>

                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => onFileRemoved(file.id)}
                                    className="ml-2 h-8 w-8 p-0"
                                >
                                    <X className="w-4 h-4" />
                                </Button>
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}