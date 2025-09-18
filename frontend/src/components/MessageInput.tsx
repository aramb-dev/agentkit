import { useState, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { FileAttachment } from "@/types/chat";
import { Send, Paperclip, X, Loader2 } from "lucide-react";
import { FileUpload } from "./FileUpload";

interface MessageInputProps {
    onSendMessage: (message: string, attachments: FileAttachment[]) => void;
    isLoading: boolean;
    selectedModel: string;
}

export function MessageInput({ onSendMessage, isLoading, selectedModel }: MessageInputProps) {
    const [message, setMessage] = useState('');
    const [attachedFiles, setAttachedFiles] = useState<FileAttachment[]>([]);
    const [showFileUpload, setShowFileUpload] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSend = () => {
        if (message.trim() || attachedFiles.length > 0) {
            onSendMessage(message.trim(), attachedFiles);
            setMessage('');
            setAttachedFiles([]);
            setShowFileUpload(false);
        }
    };

    const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleFilesAdded = (newFiles: FileAttachment[]) => {
        setAttachedFiles(prev => [...prev, ...newFiles]);
    };

    const handleFileRemoved = (fileId: string) => {
        setAttachedFiles(prev => prev.filter(file => file.id !== fileId));
    };

    return (
        <div className="space-y-3">
            {/* Model indicator */}
            <div className="flex items-center justify-between">
                <Badge variant="outline" className="text-xs">
                    Model: {selectedModel}
                </Badge>
                {attachedFiles.length > 0 && (
                    <Badge variant="secondary" className="text-xs">
                        {attachedFiles.length} file{attachedFiles.length > 1 ? 's' : ''} attached
                    </Badge>
                )}
            </div>

            {/* File upload section */}
            {showFileUpload && (
                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-3">
                            <h4 className="text-sm font-medium">Attach Documents</h4>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowFileUpload(false)}
                                className="h-8 w-8 p-0"
                            >
                                <X className="w-4 h-4" />
                            </Button>
                        </div>
                        <FileUpload
                            onFilesAdded={handleFilesAdded}
                            onFileRemoved={handleFileRemoved}
                            uploadedFiles={attachedFiles}
                        />
                    </CardContent>
                </Card>
            )}

            {/* Attached files preview */}
            {attachedFiles.length > 0 && !showFileUpload && (
                <div className="flex flex-wrap gap-2">
                    {attachedFiles.map((file) => (
                        <Badge key={file.id} variant="secondary" className="text-xs pr-1">
                            📄 {file.name}
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleFileRemoved(file.id)}
                                className="ml-1 h-4 w-4 p-0 hover:bg-transparent"
                            >
                                <X className="w-3 h-3" />
                            </Button>
                        </Badge>
                    ))}
                </div>
            )}

            {/* Message input */}
            <div className="flex gap-2">
                <div className="flex-1 relative">
                    <Textarea
                        ref={textareaRef}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyPress}
                        placeholder="Type your message... (Shift+Enter for new line)"
                        className="min-h-[60px] max-h-[200px] resize-none pr-10"
                        disabled={isLoading}
                    />
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowFileUpload(!showFileUpload)}
                        className="absolute right-2 top-2 h-8 w-8 p-0"
                        disabled={isLoading}
                    >
                        <Paperclip className="w-4 h-4" />
                    </Button>
                </div>

                <Button
                    onClick={handleSend}
                    disabled={isLoading || (!message.trim() && attachedFiles.length === 0)}
                    className="min-w-[60px]"
                >
                    {isLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        <Send className="w-4 h-4" />
                    )}
                </Button>
            </div>

            <p className="text-xs text-muted-foreground">
                Press Enter to send, Shift+Enter for new line
            </p>
        </div>
    );
}