export interface ChatMessage {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
    model?: string;
    toolUsed?: string;
    attachments?: FileAttachment[];
    error?: boolean;
    retryHandler?: () => void;
    citations?: Citation[]; // Source citations for the response
}

export interface Citation {
    source: string;
    chunk?: number;
    relevance?: number;
    type: 'document' | 'web';
}

export interface FileAttachment {
    id: string;
    name: string;
    size: number;
    type: string;
    url?: string;
    uploadProgress?: number;
    file?: File; // Original browser File object
    fileId?: string; // Server-side stored file ID
    uploaded?: boolean; // Whether file has been uploaded to server
    ingested?: boolean; // Whether file has been processed for RAG
    ingestProgress?: number; // RAG ingestion progress
    ingestStage?: 'uploading' | 'processing' | 'embedding' | 'complete' | 'error'; // Current processing stage
    ingestError?: string; // Error message if ingestion fails
    processingStartTime?: Date; // When processing started
    chunksCreated?: number; // Number of chunks created during processing
}

export interface ChatState {
    messages: ChatMessage[];
    isLoading: boolean;
    selectedModel: string;
    availableModels: string[];
    namespace: string; // RAG namespace for document isolation
    sessionId: string; // Session ID for conversation context
    searchMode: 'auto' | 'web' | 'documents' | 'hybrid'; // Search mode preference
    error?: string;
}

export interface AgentResponse {
    answer: string;
    tool_used: string;
    tool_output: string;
    model: string;
    context: string;
    summary: string;
    stored_files?: Array<{
        file_id: string;
        original_filename: string;
        file_size: number;
        content_type: string;
    }>;
}

export interface DocumentIngestResponse {
    status: string;
    message: string;
    chunks: number;
    namespace: string;
    filename: string;
    doc_id: string;
}