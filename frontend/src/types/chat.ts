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
}