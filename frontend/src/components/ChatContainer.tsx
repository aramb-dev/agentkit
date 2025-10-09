import { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import type { ChatMessage, ChatState, FileAttachment, AgentResponse, DocumentIngestResponse } from "@/types/chat";
import { ChatMessage as ChatMessageComponent } from "./ChatMessage";
import { MessageInput } from "./MessageInput";
import { NamespaceSelector } from "./NamespaceSelector";
import { SearchModeSelector } from "./SearchModeSelector";
import { Trash2, Bot, Loader2 } from "lucide-react";
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Retry utility with exponential backoff
async function retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxAttempts: number = 3,
    initialDelay: number = 1000,
    shouldRetry: (error: any) => boolean = () => true
): Promise<T> {
    let lastError: any;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;
            
            // Check if we should retry this error
            if (!shouldRetry(error) || attempt === maxAttempts) {
                throw error;
            }
            
            // Calculate exponential backoff delay
            const delay = initialDelay * Math.pow(2, attempt - 1);
            console.log(`Retry attempt ${attempt}/${maxAttempts} after ${delay}ms delay`);
            
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    
    throw lastError;
}

// Determine if an error is retryable
function isRetryableError(error: any): boolean {
    if (axios.isAxiosError(error)) {
        // Network errors are retryable
        if (error.code === 'NETWORK_ERROR' || error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED') {
            return true;
        }
        
        // 5xx server errors are retryable
        if (error.response?.status && error.response.status >= 500) {
            return true;
        }
        
        // 429 rate limit errors are retryable
        if (error.response?.status === 429) {
            return true;
        }
    }
    
    return false;
}

export function ChatContainer() {
    // const { addToast } = useToast();
    const [chatState, setChatState] = useState<ChatState>({
        messages: [],
        isLoading: false,
        selectedModel: 'gemini-1.5-flash',
        availableModels: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash'],
        namespace: 'default',
        sessionId: crypto.randomUUID(),
        searchMode: 'auto',
        error: undefined
    });

    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chatState.messages]);

    // Load available models on component mount
    useEffect(() => {
        const loadModels = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/models`);
                setChatState(prev => ({
                    ...prev,
                    availableModels: response.data.available_models,
                    selectedModel: response.data.default_model
                }));
            } catch (error) {
                console.error('Failed to load models:', error);
                // Fallback to default models
                const defaultModels = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash'];
                setChatState(prev => ({
                    ...prev,
                    availableModels: defaultModels,
                    selectedModel: defaultModels[0]
                }));
            }
        };

        loadModels();
    }, []);

    // Function to ingest PDF documents for RAG with enhanced progress tracking
    const ingestDocument = async (file: File, onProgressUpdate?: (stage: "uploading" | "processing" | "embedding" | "complete" | "error", progress: number) => void): Promise<boolean> => {
        try {
            onProgressUpdate?.('uploading', 10);
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('namespace', chatState.namespace);
            formData.append('session_id', chatState.sessionId);

            onProgressUpdate?.('processing', 30);

            // Use retry logic for document ingestion
            const response = await retryWithBackoff(
                () => axios.post<DocumentIngestResponse>(`${API_BASE_URL}/docs/ingest`, formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                    onUploadProgress: (progressEvent) => {
                        if (progressEvent.total) {
                            const uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                            onProgressUpdate?.('uploading', Math.min(uploadProgress, 25));
                        }
                    }
                }),
                3, // max attempts
                1000, // initial delay 1s
                isRetryableError
            );

            onProgressUpdate?.('embedding', 70);

            if (response.data.status === 'success') {
                onProgressUpdate?.('complete', 100);
                
                // Show toast notification for success
                // addToast({
                //     type: 'success',
                //     title: '🎉 Document processed successfully!',
                //     description: `${file.name} is ready for RAG queries (${response.data.chunks} chunks created)`,
                //     duration: 4000
                // });
                
                // Show enhanced success message with more details
                const ingestMessage: ChatMessage = {
                    id: crypto.randomUUID(),
                    content: `✅ **Successfully processed ${file.name}!**

📊 **Processing Results:**
• **Chunks created:** ${response.data.chunks}
• **Document ID:** ${response.data.doc_id?.substring(0, 8)}...
• **Namespace:** ${response.data.namespace}
• **File size:** ${(file.size / 1024 / 1024).toFixed(2)} MB

🚀 **Ready for RAG retrieval!** You can now ask questions about this document and I'll retrieve relevant information from it.`,
                    role: 'assistant',
                    timestamp: new Date(),
                    toolUsed: 'rag'
                };

                setChatState(prev => ({
                    ...prev,
                    messages: [...prev.messages, ingestMessage]
                }));

                return true;
            }
            return false;
        } catch (error) {
            console.error('Document ingestion failed:', error);
            
            onProgressUpdate?.('error', 0);

            // Show toast notification for error
            // let errorTitle = 'Document processing failed';
            // let errorDescription = `Failed to process ${file.name}`;
            
            // if (axios.isAxiosError(error)) {
            //     if (error.response?.status === 413) {
            //         errorTitle = 'File too large';
            //         errorDescription = 'Maximum file size is 10MB';
            //     } else if (error.response?.status === 400) {
            //         errorTitle = 'Unsupported format';
            //         errorDescription = 'Only PDF files are supported';
            //     } else if (error.code === 'NETWORK_ERROR') {
            //         errorTitle = 'Network error';
            //         errorDescription = 'Check your internet connection';
            //     }
            // }
            
            // addToast({
            //     type: 'error',
            //     title: errorTitle,
            //     description: errorDescription,
            //     duration: 6000
            // });

            // Enhanced error message with better categorization
            let errorDetails = '';
            let retryAfter: number | undefined;
            
            if (axios.isAxiosError(error)) {
                // Check for standardized error response
                if (error.response?.data?.error) {
                    const errorData = error.response.data.error;
                    errorDetails = `\n**Reason:** ${errorData.message}`;
                    retryAfter = errorData.retry_after;
                    
                    if (errorData.details?.file_size_mb) {
                        errorDetails += `\n**File size:** ${errorData.details.file_size_mb}MB`;
                    }
                } else {
                    // Fallback to legacy error handling
                    if (error.response?.status === 413) {
                        errorDetails = '\n**Reason:** File size too large (max 50MB allowed)';
                    } else if (error.response?.status === 400) {
                        errorDetails = '\n**Reason:** Unsupported file format (supported: PDF, DOCX, TXT, MD, JSON)';
                    } else if (error.code === 'NETWORK_ERROR' || error.code === 'ERR_NETWORK') {
                        errorDetails = '\n**Reason:** Network connection issue';
                    } else {
                        errorDetails = '\n**Reason:** Server processing error';
                    }
                }
            }

            const errorMessage: ChatMessage = {
                id: crypto.randomUUID(),
                content: `❌ **Failed to process ${file.name}**${errorDetails}

🔧 **What you can try:**
• Check file format (supported: PDF, DOCX, TXT, MD, JSON)
• Ensure file size is under 50MB
• Check your internet connection
• Try uploading again${retryAfter ? `\n• Wait ${retryAfter} seconds before retrying` : ''}

💡 **Note:** You can still attach the file for immediate processing, but it won't be available for future document retrieval.`,
                role: 'assistant',
                timestamp: new Date(),
                error: true
            };

            setChatState(prev => ({
                ...prev,
                messages: [...prev.messages, errorMessage]
            }));

            return false;
        }
    };

    const handleSendMessage = async (content: string, attachments: FileAttachment[]) => {
        if (!content.trim() && attachments.length === 0) return;

        const userMessage: ChatMessage = {
            id: crypto.randomUUID(),
            content,
            role: 'user',
            timestamp: new Date(),
            attachments: attachments.length > 0 ? attachments : undefined
        };

        setChatState(prev => ({
            ...prev,
            messages: [...prev.messages, userMessage],
            isLoading: true,
            error: undefined
        }));

        // Process PDF attachments for RAG ingestion with enhanced progress tracking
        const updatedAttachments = [...attachments];
        for (let i = 0; i < attachments.length; i++) {
            const attachment = attachments[i];
            if (attachment.file && attachment.type === 'application/pdf') {
                // Initialize processing state
                updatedAttachments[i] = { 
                    ...attachment, 
                    ingestProgress: 0,
                    ingestStage: 'uploading',
                    processingStartTime: new Date()
                };

                // Create progress update callback
                const updateProgress = (stage: 'uploading' | 'processing' | 'embedding' | 'complete' | 'error', progress: number) => {
                    setChatState(prev => ({
                        ...prev,
                        messages: prev.messages.map(msg =>
                            msg.id === userMessage.id && msg.attachments
                                ? {
                                    ...msg,
                                    attachments: msg.attachments.map(att =>
                                        att.id === attachment.id
                                            ? { 
                                                ...att, 
                                                ingestProgress: progress,
                                                ingestStage: stage,
                                                ...(stage === 'error' && { ingestError: 'Processing failed' })
                                            }
                                            : att
                                    )
                                }
                                : msg
                        )
                    }));
                };

                try {
                    const ingested = await ingestDocument(attachment.file, updateProgress);
                    
                    // Final state update
                    updatedAttachments[i] = {
                        ...updatedAttachments[i],
                        ingested,
                        ingestProgress: ingested ? 100 : 0,
                        ingestStage: ingested ? 'complete' : 'error',
                        ...(ingested && { chunksCreated: 0 }) // This would be populated from response
                    };
                } catch (error) {
                    updatedAttachments[i] = {
                        ...updatedAttachments[i],
                        ingested: false,
                        ingestProgress: 0,
                        ingestStage: 'error',
                        ingestError: 'Processing failed'
                    };
                }
            }
        }

        try {
            // Prepare form data for file uploads
            const formData = new FormData();
            formData.append('message', content);
            formData.append('model', chatState.selectedModel);
            formData.append('namespace', chatState.namespace);
            formData.append('session_id', chatState.sessionId);
            formData.append('search_mode', chatState.searchMode);

            // Add conversation history (last 10 messages for context)
            const historyForContext = chatState.messages.slice(-10).map(msg => ({
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp.toISOString()
            }));
            formData.append('history', JSON.stringify(historyForContext));

            // Add files to form data
            for (const attachment of attachments) {
                if (attachment.file) {
                    // Send the actual File object
                    formData.append('files', attachment.file, attachment.name);
                }
            }

            // Use retry logic for the chat request
            const response = await retryWithBackoff(
                () => axios.post<AgentResponse>(`${API_BASE_URL}/chat`, formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                }),
                3, // max attempts
                1000, // initial delay 1s
                isRetryableError
            );

            const assistantMessage: ChatMessage = {
                id: crypto.randomUUID(),
                content: response.data.answer,
                role: 'assistant',
                timestamp: new Date(),
                model: response.data.model,
                toolUsed: response.data.tool_used
            };

            // Update attachment file IDs with server response
            if (response.data.stored_files) {
                const finalAttachments = updatedAttachments.map(attachment => {
                    const storedFile = response.data.stored_files?.find(
                        sf => sf.original_filename === attachment.name
                    );
                    if (storedFile) {
                        return {
                            ...attachment,
                            fileId: storedFile.file_id,
                            uploaded: true,
                            uploadProgress: 100
                        };
                    }
                    return attachment;
                });

                // Update the user message with the file IDs
                setChatState(prev => ({
                    ...prev,
                    messages: prev.messages.map(msg =>
                        msg.id === userMessage.id
                            ? { ...msg, attachments: finalAttachments }
                            : msg
                    ),
                    isLoading: false
                }));
            }

            setChatState(prev => ({
                ...prev,
                messages: [...prev.messages, assistantMessage],
                isLoading: false
            }));

        } catch (error) {
            console.error('Failed to send message:', error);

            // Create a retry function for this specific message
            const retryMessage = () => {
                // Remove the error message and retry
                setChatState(prev => ({
                    ...prev,
                    messages: prev.messages.filter(msg => msg.id !== errorMessageId),
                    error: undefined
                }));
                // Retry the original request
                handleSendMessage(content, attachments);
            };

            const errorMessageId = crypto.randomUUID();
            const errorMessage: ChatMessage = {
                id: errorMessageId,
                content: `Sorry, I encountered an error while processing your message. This might be due to network issues or API limits.`,
                role: 'assistant',
                timestamp: new Date(),
                error: true,
                retryHandler: retryMessage
            };

            setChatState(prev => ({
                ...prev,
                messages: [...prev.messages, errorMessage],
                isLoading: false,
                error: 'Failed to send message. You can try again or check your network connection.'
            }));
        }
    };

    const handleClearChat = () => {
        setChatState(prev => ({
            ...prev,
            messages: [],
            error: undefined
        }));
    };

    const handleModelChange = (model: string) => {
        setChatState(prev => ({
            ...prev,
            selectedModel: model
        }));
    };

    const handleNamespaceChange = (namespace: string) => {
        setChatState(prev => ({
            ...prev,
            namespace
        }));
    };

    const handleSearchModeChange = (searchMode: 'auto' | 'web' | 'documents' | 'hybrid') => {
        setChatState(prev => ({
            ...prev,
            searchMode
        }));
    };

    return (
        <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
            <Card className="flex-1 flex flex-col">
                {/* Header */}
                <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
                    <div className="flex items-center gap-2">
                        <Bot className="w-6 h-6 text-emerald-500" />
                        <CardTitle className="text-xl">AgentKit Chat</CardTitle>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Search Mode Selector */}
                        <SearchModeSelector
                            selectedMode={chatState.searchMode}
                            onModeChange={handleSearchModeChange}
                        />

                        {/* Namespace Selector */}
                        <NamespaceSelector
                            selectedNamespace={chatState.namespace}
                            onNamespaceChange={handleNamespaceChange}
                        />

                        <div className="flex items-center gap-2">
                            {/* Model selector */}
                            <select
                                value={chatState.selectedModel}
                                onChange={(e) => handleModelChange(e.target.value)}
                                className="text-sm border rounded px-2 py-1"
                                disabled={chatState.isLoading}
                                title="Select AI Model"
                                aria-label="Select AI Model"
                            >
                                {chatState.availableModels.map((model) => (
                                    <option key={model} value={model}>
                                        {model}
                                    </option>
                                ))}
                            </select>

                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleClearChat}
                                disabled={chatState.isLoading || chatState.messages.length === 0}
                            >
                                <Trash2 className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </CardHeader>

                {/* Messages */}
                <CardContent className="flex-1 flex flex-col p-0">
                    <ScrollArea className="flex-1 px-4">
                        <div className="space-y-4 py-4">
                            {chatState.messages.length === 0 ? (
                                <div className="text-center text-muted-foreground py-8">
                                    <Bot className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                                    <p className="text-lg font-medium mb-2">Welcome to AgentKit!</p>
                                    <p className="text-sm">
                                        I can help you with web search, document analysis, and more.
                                        Start by typing a message or uploading a document.
                                    </p>
                                </div>
                            ) : (
                                chatState.messages.map((message) => (
                                    <ChatMessageComponent key={message.id} message={message} />
                                ))
                            )}

                            {chatState.isLoading && (
                                <div className="flex items-center gap-3 text-muted-foreground py-4">
                                    <div className="flex items-center gap-2">
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        <span className="text-sm">AgentKit is thinking...</span>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>
                    </ScrollArea>

                    {/* Error display */}
                    {chatState.error && (
                        <div className="px-4 py-2 bg-red-50 border-t border-red-200">
                            <p className="text-sm text-red-600">{chatState.error}</p>
                        </div>
                    )}

                    {/* Message input */}
                    <div className="border-t p-4">
                        <MessageInput
                            onSendMessage={handleSendMessage}
                            isLoading={chatState.isLoading}
                            selectedModel={chatState.selectedModel}
                        />
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}