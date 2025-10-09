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

    render(<ChatMessage message={message} />)
    
    expect(screen.getByText('Hello, how are you?')).toBeInTheDocument()
    expect(screen.getByText('You')).toBeInTheDocument()
  })

  it('renders assistant message correctly', () => {
    const message: ChatMessageType = {
      id: '2',
      role: 'assistant',
      content: 'I am doing well, thank you!',
      timestamp: new Date('2024-01-01T12:00:01Z')
    }

    render(<ChatMessage message={message} />)
    
    expect(screen.getByText('I am doing well, thank you!')).toBeInTheDocument()
    expect(screen.getByText('Assistant')).toBeInTheDocument()
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

  it('displays timestamp in correct format', () => {
    const message: ChatMessageType = {
      id: '4',
      role: 'user',
      content: 'Test message',
      timestamp: new Date('2024-01-01T12:00:00Z')
    }

    render(<ChatMessage message={message} />)
    
    // Check that some timestamp text is present
    const timestampElement = screen.getByText(/\d{1,2}:\d{2}/)
    expect(timestampElement).toBeInTheDocument()
  })
})
