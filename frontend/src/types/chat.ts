export interface ChatMessage {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
    model?: string;
    toolUsed?: string;
    attachments?: FileAttachment[];
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
}

export interface ChatState {
    messages: ChatMessage[];
    isLoading: boolean;
    selectedModel: string;
    availableModels: string[];
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