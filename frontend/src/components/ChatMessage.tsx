import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { ChatMessage as ChatMessageType } from "@/types/chat";
import { Bot, User, Clock, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface ChatMessageProps {
    message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
    const isUser = message.role === 'user';
    const formattedTime = message.timestamp.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });

    return (
        <div className={cn(
            "flex gap-3 mb-4",
            isUser ? "flex-row-reverse" : "flex-row"
        )}>
            <Avatar className="w-8 h-8 mt-1">
                <AvatarFallback className={cn(
                    "text-white",
                    isUser ? "bg-blue-500" : "bg-emerald-500"
                )}>
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </AvatarFallback>
            </Avatar>

            <div className={cn(
                "max-w-[80%] space-y-2",
                isUser ? "items-end" : "items-start"
            )}>
                <Card className={cn(
                    "border-0 shadow-sm",
                    isUser
                        ? "bg-blue-500 text-white"
                        : "bg-muted"
                )}>
                    <CardContent className="p-3">
                        <div className="prose prose-sm max-w-none text-sm dark:prose-invert">
                            {isUser ? (
                                <div className="whitespace-pre-wrap text-white">
                                    {message.content}
                                </div>
                            ) : (
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm, remarkMath]}
                                    rehypePlugins={[rehypeKatex]}
                                    components={{
                                        code({ className, children, ...props }) {
                                            return (
                                                <code
                                                    className={cn(
                                                        "bg-slate-100 text-slate-800 px-1 py-0.5 rounded text-xs",
                                                        className
                                                    )}
                                                    {...props}
                                                >
                                                    {children}
                                                </code>
                                            );
                                        },
                                        pre({ children, ...props }) {
                                            return (
                                                <pre
                                                    className="bg-slate-100 text-slate-800 p-3 rounded-md overflow-x-auto text-xs"
                                                    {...props}
                                                >
                                                    {children}
                                                </pre>
                                            );
                                        }
                                    }}
                                >
                                    {message.content}
                                </ReactMarkdown>
                            )}
                        </div>

                        {/* Show attachments if any */}
                        {message.attachments && message.attachments.length > 0 && (
                            <div className="mt-2 space-y-1">
                                {message.attachments.map((attachment) => (
                                    <Badge
                                        key={attachment.id}
                                        variant="secondary"
                                        className="text-xs"
                                    >
                                        📄 {attachment.name}
                                    </Badge>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Message metadata */}
                <div className={cn(
                    "flex items-center gap-2 text-xs text-muted-foreground",
                    isUser ? "flex-row-reverse" : "flex-row"
                )}>
                    <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formattedTime}
                    </div>

                    {message.model && !isUser && (
                        <Badge variant="outline" className="text-xs">
                            {message.model}
                        </Badge>
                    )}

                    {message.toolUsed && !isUser && (
                        <div className="flex items-center gap-1">
                            <Wrench className="w-3 h-3" />
                            <span className="text-xs">{message.toolUsed}</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}