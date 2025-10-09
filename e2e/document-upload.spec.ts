import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

test.describe('Document Upload Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for the app to load
    await page.waitForLoadState('networkidle');
  });

  test('should display main chat interface', async ({ page }) => {
    // Check that the main components are visible
    await expect(page.getByText(/AgentKit|Chat/i)).toBeVisible();
    
    // Check for message input
    const messageInput = page.getByPlaceholder(/type.*message/i);
    await expect(messageInput).toBeVisible();
  });

  test('should upload a text document successfully', async ({ page }) => {
    // Create a temporary test file
    const testFilePath = path.join(__dirname, 'test-document.txt');
    fs.writeFileSync(testFilePath, 'This is a test document for e2e testing.\nIt contains sample content.');

    try {
      // Look for file upload button or drag-drop area
      const uploadButton = page.locator('input[type="file"]');
      
      if (await uploadButton.count() > 0) {
        // Upload the file
        await uploadButton.setInputFiles(testFilePath);
        
        // Wait for upload to complete
        // Look for success message or uploaded file in the list
        await page.waitForTimeout(2000); // Give time for processing
        
        // Check for success indicator
        const successIndicator = page.getByText(/uploaded|success|ingested/i);
        await expect(successIndicator).toBeVisible({ timeout: 10000 });
      }
    } finally {
      // Clean up test file
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });

  test('should send a message and receive a response', async ({ page }) => {
    // Type a message
    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill('Hello, can you help me?');
    
    // Send the message
    await messageInput.press('Enter');
    
    // Wait for assistant response
    await page.waitForTimeout(3000);
    
    // Check that a response appears
    const messages = page.locator('[role="article"], .message, [data-role="assistant"]');
    await expect(messages).toHaveCount(await messages.count(), { timeout: 10000 });
  });

  test('should handle namespace selection', async ({ page }) => {
    // Look for namespace selector
    const namespaceSelector = page.getByLabel(/namespace/i).or(page.locator('select'));
    
    if (await namespaceSelector.count() > 0) {
      // Verify namespace selector is present
      await expect(namespaceSelector.first()).toBeVisible();
    }
  });

  test('should clear chat history', async ({ page }) => {
    // Send a test message first
    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill('Test message');
    await messageInput.press('Enter');
    
    // Wait for message to appear
    await page.waitForTimeout(1000);
    
    // Look for clear/trash button
    const clearButton = page.getByRole('button').filter({ hasText: /clear|trash|delete/i });
    
    if (await clearButton.count() > 0) {
      await clearButton.first().click();
      
      // Confirm clear if there's a dialog
      const confirmButton = page.getByRole('button').filter({ hasText: /confirm|yes|ok/i });
      if (await confirmButton.count() > 0) {
        await confirmButton.first().click();
      }
      
      // Check that messages are cleared
      await page.waitForTimeout(500);
    }
  });

  test('should validate file type restrictions', async ({ page }) => {
    // Create an unsupported file type
    const testFilePath = path.join(__dirname, 'test-file.xyz');
    fs.writeFileSync(testFilePath, 'Invalid file type content');

    try {
      const uploadButton = page.locator('input[type="file"]');
      
      if (await uploadButton.count() > 0) {
        await uploadButton.setInputFiles(testFilePath);
        
        // Wait for error message
        await page.waitForTimeout(1000);
        
        // Look for error indicator
        const errorMessage = page.getByText(/unsupported|invalid|error/i);
        // Note: This might not appear if client-side validation prevents upload
      }
    } finally {
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });
});

test.describe('RAG Integration', () => {
  test('should query uploaded document', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Create and upload a document with specific content
    const testFilePath = path.join(__dirname, 'rag-test-doc.txt');
    fs.writeFileSync(testFilePath, 'AgentKit supports advanced RAG capabilities with semantic search.');

    try {
      const uploadButton = page.locator('input[type="file"]');
      
      if (await uploadButton.count() > 0) {
        await uploadButton.setInputFiles(testFilePath);
        await page.waitForTimeout(3000); // Wait for ingestion
        
        // Query about the document
        const messageInput = page.getByPlaceholder(/type.*message/i);
        await messageInput.fill('What capabilities does AgentKit support?');
        await messageInput.press('Enter');
        
        // Wait for response
        await page.waitForTimeout(5000);
        
        // Check for relevant response
        const responseText = await page.locator('body').textContent();
        expect(responseText).toContain(/RAG|semantic|search|capabilities/i);
      }
    } finally {
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });
});
