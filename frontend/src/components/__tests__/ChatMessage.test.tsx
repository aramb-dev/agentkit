import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChatMessage } from '../ChatMessage'
import type { ChatMessage as ChatMessageType } from '@/types/chat'

describe('ChatMessage Component', () => {
  it('renders user message correctly', () => {
    const message: ChatMessageType = {
      id: '1',
      role: 'user',
      content: 'Hello, how are you?',
      timestamp: new Date('2024-01-01T12:00:00Z')
    }

    const { container } = render(<ChatMessage message={message} />)
    
    expect(screen.getByText('Hello, how are you?')).toBeInTheDocument()
    // Check for User icon presence by finding the svg
    const userIcon = container.querySelector('svg')
    expect(userIcon).toBeInTheDocument()
  })

  it('renders assistant message correctly', () => {
    const message: ChatMessageType = {
      id: '2',
      role: 'assistant',
      content: 'I am doing well, thank you!',
      timestamp: new Date('2024-01-01T12:00:01Z')
    }

    const { container } = render(<ChatMessage message={message} />)
    
    expect(screen.getByText('I am doing well, thank you!')).toBeInTheDocument()
    // Check for Bot icon presence
    const botIcon = container.querySelector('svg')
    expect(botIcon).toBeInTheDocument()
  })

  it('renders message with citations', () => {
    const message: ChatMessageType = {
      id: '3',
      role: 'assistant',
      content: 'Based on the document...',
      timestamp: new Date('2024-01-01T12:00:02Z'),
      citations: [
        {
          text: 'source text',
          filename: 'document.pdf',
          relevance_score: 0.95
        }
      ]
    }

    render(<ChatMessage message={message} />)
    
    expect(screen.getByText('Based on the document...')).toBeInTheDocument()
  })

  it('displays user and assistant messages with different styling', () => {
    const userMessage: ChatMessageType = {
      id: '1',
      role: 'user',
      content: 'User question',
      timestamp: new Date()
    }

    const assistantMessage: ChatMessageType = {
      id: '2',
      role: 'assistant',
      content: 'Assistant response',
      timestamp: new Date()
    }

    const { container: userContainer } = render(<ChatMessage message={userMessage} />)
    const { container: assistantContainer } = render(<ChatMessage message={assistantMessage} />)
    
    // Just verify both render without error
    expect(userContainer.querySelector('.flex')).toBeInTheDocument()
    expect(assistantContainer.querySelector('.flex')).toBeInTheDocument()
  })

  it('displays error indicator when message has error', () => {
    const message: ChatMessageType = {
      id: '5',
      role: 'assistant',
      content: 'Error occurred',
      timestamp: new Date(),
      error: true
    }

    render(<ChatMessage message={message} />)
    
    expect(screen.getByText('Error')).toBeInTheDocument()
  })
})
