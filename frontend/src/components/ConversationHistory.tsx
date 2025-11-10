import { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
    History, 
    Search, 
    Trash2, 
    Download, 
    MessageSquare,
    Clock,
    ChevronRight,
    RefreshCw,
    X
} from "lucide-react";
import type { Conversation, ConversationListResponse } from "@/types/chat";
import axios from 'axios';

// Use environment variable with fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ConversationHistoryProps {
    onSelectConversation: (conversation: Conversation) => void;
    currentSessionId?: string;
    namespace?: string;
}

export function ConversationHistory({ 
    onSelectConversation, 
    currentSessionId,
    namespace 
}: ConversationHistoryProps) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isExpanded, setIsExpanded] = useState(true);

    const loadConversations = async () => {
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams();
            if (namespace) params.append('namespace', namespace);
            if (searchQuery) params.append('search', searchQuery);
            
            const response = await axios.get<ConversationListResponse>(
                `${API_BASE_URL}/conversations?${params.toString()}`
            );
            setConversations(response.data.conversations);
        } catch (err) {
            console.error('Failed to load conversations:', err);
            setError('Failed to load conversations');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadConversations();
    }, [namespace]);

    useEffect(() => {
        // Debounce search
        const timer = setTimeout(() => {
            if (searchQuery !== undefined) {
                loadConversations();
            }
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const handleDeleteConversation = async (conversationId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm('Are you sure you want to delete this conversation?')) {
            return;
        }

        try {
            await axios.delete(`${API_BASE_URL}/conversations/${conversationId}`);
            loadConversations();
        } catch (err) {
            console.error('Failed to delete conversation:', err);
            setError('Failed to delete conversation');
        }
    };

    const handleExportConversation = async (conversationId: string, format: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            const response = await axios.post(
                `${API_BASE_URL}/conversations/${conversationId}/export?format=${format}`
            );
            
            let content: string;
            let filename: string;
            let mimeType: string;
            
            if (format === 'json') {
                content = JSON.stringify(response.data, null, 2);
                filename = `conversation-${conversationId}.json`;
                mimeType = 'application/json';
            } else {
                content = response.data.content;
                filename = `conversation-${conversationId}.${format}`;
                mimeType = format === 'md' ? 'text/markdown' : 'text/plain';
            }
            
            // Create download
            const blob = new Blob([content], { type: mimeType });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Failed to export conversation:', err);
            setError('Failed to export conversation');
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    if (!isExpanded) {
        return (
            <div className="w-12 border-r bg-background">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsExpanded(true)}
                    className="w-full h-12"
                >
                    <ChevronRight className="w-4 h-4" />
                </Button>
            </div>
        );
    }

    return (
        <Card className="w-80 border-r rounded-none h-full flex flex-col">
            <CardHeader className="pb-3 border-b">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <History className="w-5 h-5" />
                        <CardTitle className="text-lg">History</CardTitle>
                    </div>
                    <div className="flex gap-1">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={loadConversations}
                            disabled={loading}
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setIsExpanded(false)}
                        >
                            <X className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
                <div className="relative mt-2">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search conversations..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-8"
                    />
                </div>
            </CardHeader>

            <CardContent className="flex-1 p-0">
                <ScrollArea className="h-full">
                    {error && (
                        <div className="p-4 text-sm text-destructive">
                            {error}
                        </div>
                    )}
                    
                    {loading && conversations.length === 0 ? (
                        <div className="p-4 text-center text-muted-foreground">
                            Loading conversations...
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="p-4 text-center text-muted-foreground">
                            <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>No conversations yet</p>
                            <p className="text-xs mt-1">Start chatting to create history</p>
                        </div>
                    ) : (
                        <div className="divide-y">
                            {conversations.map((conv) => (
                                <div
                                    key={conv.id}
                                    onClick={() => onSelectConversation(conv)}
                                    className={`p-3 hover:bg-accent cursor-pointer transition-colors ${
                                        conv.session_id === currentSessionId ? 'bg-accent' : ''
                                    }`}
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <h4 className="font-medium text-sm truncate">
                                                {conv.title}
                                            </h4>
                                            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                                                <Clock className="w-3 h-3" />
                                                <span>{formatDate(conv.updated_at)}</span>
                                                <span>•</span>
                                                <span>{conv.message_count} msgs</span>
                                            </div>
                                        </div>
                                        <div className="flex gap-1">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={(e) => handleExportConversation(conv.id, 'md', e)}
                                                className="h-6 w-6 p-0"
                                                title="Export as Markdown"
                                            >
                                                <Download className="w-3 h-3" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={(e) => handleDeleteConversation(conv.id, e)}
                                                className="h-6 w-6 p-0 text-destructive"
                                                title="Delete conversation"
                                            >
                                                <Trash2 className="w-3 h-3" />
                                            </Button>
                                        </div>
                                    </div>
                                    {conv.namespace !== 'default' && (
                                        <div className="mt-1">
                                            <span className="text-xs bg-secondary px-2 py-0.5 rounded">
                                                {conv.namespace}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
