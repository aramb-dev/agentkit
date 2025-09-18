import { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import type { ChatMessage, ChatState, FileAttachment, AgentResponse } from "@/types/chat";
import { ChatMessage as ChatMessageComponent } from "./ChatMessage";
import { MessageInput } from "./MessageInput";
import { Trash2, Bot, Loader2 } from "lucide-react";
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export function ChatContainer() {
    const [chatState, setChatState] = useState<ChatState>({
        messages: [],
        isLoading: false,
        selectedModel: 'gemini-1.5-flash',
        availableModels: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash'],
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

        try {
            // Prepare form data for file uploads
            const formData = new FormData();
            formData.append('message', content);
            formData.append('model', chatState.selectedModel);

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

            const response = await axios.post<AgentResponse>(`${API_BASE_URL}/chat`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

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
                const updatedAttachments = attachments.map(attachment => {
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
                            ? { ...msg, attachments: updatedAttachments }
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

    return (
        <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
            <Card className="flex-1 flex flex-col">
                {/* Header */}
                <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
                    <div className="flex items-center gap-2">
                        <Bot className="w-6 h-6 text-emerald-500" />
                        <CardTitle className="text-xl">AgentKit Chat</CardTitle>
                    </div>

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