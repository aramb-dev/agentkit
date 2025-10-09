import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MessageInput } from '../MessageInput'

describe('MessageInput Component', () => {
  const defaultProps = {
    onSendMessage: vi.fn(),
    isLoading: false,
    selectedModel: 'gemini-1.5-flash'
  }

  it('renders textarea and send button', () => {
    render(<MessageInput {...defaultProps} />)
    
    expect(screen.getByPlaceholderText(/Type your message/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '' })).toBeInTheDocument()
  })

  it('displays selected model', () => {
    render(<MessageInput {...defaultProps} />)
    
    expect(screen.getByText(/Model:/i)).toBeInTheDocument()
    expect(screen.getByText(/gemini-1.5-flash/i)).toBeInTheDocument()
  })

  it('calls onSendMessage when send button is clicked', async () => {
    const mockOnSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<MessageInput {...defaultProps} onSendMessage={mockOnSendMessage} />)
    
    const textarea = screen.getByPlaceholderText(/Type your message/i)
    await user.type(textarea, 'Hello world')
    
    const sendButtons = screen.getAllByRole('button')
    const sendButton = sendButtons.find(btn => !btn.querySelector('svg[class*="paperclip"]'))
    await user.click(sendButton!)
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Hello world', [])
  })

  it('clears textarea after sending message', async () => {
    const user = userEvent.setup()
    
    render(<MessageInput {...defaultProps} />)
    
    const textarea = screen.getByPlaceholderText(/Type your message/i) as HTMLTextAreaElement
    await user.type(textarea, 'Test message')
    
    const sendButtons = screen.getAllByRole('button')
    const sendButton = sendButtons.find(btn => !btn.querySelector('svg[class*="paperclip"]'))
    await user.click(sendButton!)
    
    expect(textarea.value).toBe('')
  })

  it('does not send empty messages', async () => {
    const mockOnSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<MessageInput {...defaultProps} onSendMessage={mockOnSendMessage} />)
    
    const sendButtons = screen.getAllByRole('button')
    const sendButton = sendButtons.find(btn => !btn.querySelector('svg[class*="paperclip"]'))
    await user.click(sendButton!)
    
    expect(mockOnSendMessage).not.toHaveBeenCalled()
  })

  it('disables input when isLoading is true', () => {
    render(<MessageInput {...defaultProps} isLoading={true} />)
    
    const textarea = screen.getByPlaceholderText(/Type your message/i)
    expect(textarea).toBeDisabled()
  })

  it('shows loading spinner when sending', () => {
    render(<MessageInput {...defaultProps} isLoading={true} />)
    
    const buttons = screen.getAllByRole('button')
    const hasSpinner = buttons.some(btn => btn.querySelector('svg[class*="animate-spin"]'))
    expect(hasSpinner).toBe(true)
  })
})
