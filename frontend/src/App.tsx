import { useState } from 'react'
import { ChatContainer } from './components/ChatContainer'
import { FileManager } from './components/FileManager'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ToastProvider } from './components/ui/toast'
import { Button } from './components/ui/button'
import { MessageSquare, FolderOpen } from 'lucide-react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'files'>('chat')

  return (
    <ToastProvider>
      <ErrorBoundary>
        <div className="min-h-screen bg-background">
          {/* Tab Navigation */}
          <div className="border-b">
            <div className="flex items-center justify-center gap-2 p-4">
              <Button
                variant={activeTab === 'chat' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('chat')}
                className="flex items-center gap-2"
              >
                <MessageSquare className="w-4 h-4" />
                Chat
              </Button>
              <Button
                variant={activeTab === 'files' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('files')}
                className="flex items-center gap-2"
              >
                <FolderOpen className="w-4 h-4" />
                Files
              </Button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="container mx-auto px-4 py-4">
            <ErrorBoundary>
              {activeTab === 'chat' && <ChatContainer />}
            </ErrorBoundary>
            <ErrorBoundary>
              {activeTab === 'files' && <FileManager />}
            </ErrorBoundary>
          </div>
        </div>
      </ErrorBoundary>
    </ToastProvider>
  )
}

export default App
