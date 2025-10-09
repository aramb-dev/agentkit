# Testing Guide for AgentKit

This document provides comprehensive information about the testing infrastructure, conventions, and best practices for AgentKit.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Running Tests](#running-tests)
- [Coverage Reports](#coverage-reports)
- [CI/CD Integration](#cicd-integration)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)

## Overview

AgentKit uses a comprehensive testing strategy that includes:

- **Unit Tests**: Testing individual components and functions in isolation
- **Integration Tests**: Testing interactions between components and APIs
- **End-to-End Tests**: Testing complete user workflows from UI to backend

### Testing Stack

**Backend:**
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage reporting
- `httpx` - HTTP client for API testing

**Frontend:**
- `vitest` - Fast unit test runner
- `@testing-library/react` - React component testing utilities
- `@testing-library/user-event` - User interaction simulation
- `jsdom` - DOM environment for tests

**End-to-End:**
- `@playwright/test` - Browser automation and E2E testing

## Test Structure

```
agentkit/
├── test_*.py              # Backend unit and integration tests
├── e2e/                   # End-to-end tests
│   └── *.spec.ts         # Playwright test specs
├── frontend/
│   └── src/
│       ├── test/         # Test setup and utilities
│       │   └── setup.ts  # Global test configuration
│       └── components/
│           └── __tests__/ # Component tests
└── .github/
    └── workflows/
        └── test.yml      # CI test automation
```

## Backend Testing

### Running Backend Tests

```bash
# Run all backend tests
python -m pytest test_*.py -v

# Run with coverage
python -m pytest test_*.py --cov=agent --cov=app --cov=rag --cov-report=html

# Run specific test file
python -m pytest test_main.py -v

# Run specific test function
python -m pytest test_main.py::TestAPI::test_models_endpoint -v
```

### Backend Test Categories

1. **API Tests** (`test_main.py`)
   - Endpoint functionality
   - Request/response validation
   - Error handling

2. **Agent Tests** (`test_agent.py`)
   - Tool routing and selection
   - LLM client integration
   - Tool execution

3. **RAG Tests** (`test_rag_*.py`)
   - Document ingestion
   - Vector storage and retrieval
   - Query optimization
   - Namespace isolation

4. **Error Handling Tests** (`test_error_handling.py`)
   - File validation
   - Error response formats
   - Path traversal protection

### Writing Backend Tests

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestMyFeature:
    """Test suite for my feature."""
    
    def test_basic_functionality(self):
        """Test basic feature behavior."""
        response = client.get("/my-endpoint")
        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async feature behavior."""
        result = await some_async_function()
        assert result is not None
```

### Test Conventions

- Use descriptive test names that explain what is being tested
- Group related tests in classes
- Use fixtures for common setup/teardown
- Mock external dependencies (API calls, file I/O)
- Test both success and failure cases

## Frontend Testing

### Running Frontend Tests

```bash
cd frontend

# Run tests once
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm run test:coverage

# Run tests with UI
npm run test:ui
```

### Frontend Test Structure

Tests are located alongside components in `__tests__` directories:

```
components/
├── ChatMessage.tsx
├── MessageInput.tsx
└── __tests__/
    ├── ChatMessage.test.tsx
    └── MessageInput.test.tsx
```

### Writing Frontend Tests

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MyComponent } from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    const mockCallback = vi.fn()
    
    render(<MyComponent onClick={mockCallback} />)
    
    const button = screen.getByRole('button')
    await user.click(button)
    
    expect(mockCallback).toHaveBeenCalled()
  })
})
```

### Frontend Testing Best Practices

1. **Query Priority**: Use queries in this order:
   - `getByRole` (best for accessibility)
   - `getByLabelText`
   - `getByPlaceholderText`
   - `getByText`
   - `getByTestId` (last resort)

2. **User Interactions**: Use `@testing-library/user-event` instead of `fireEvent`

3. **Async Operations**: Use `waitFor` or `findBy*` queries for async updates

4. **Mocking**: Mock API calls and external dependencies

## End-to-End Testing

### Running E2E Tests

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run all E2E tests
npx playwright test

# Run tests in UI mode
npx playwright test --ui

# Run specific test file
npx playwright test e2e/document-upload.spec.ts

# Run with specific browser
npx playwright test --project=chromium
```

### E2E Test Structure

E2E tests simulate complete user workflows:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Document Upload Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should upload and query document', async ({ page }) => {
    // Upload file
    await page.setInputFiles('input[type="file"]', 'path/to/file.txt');
    
    // Wait for processing
    await expect(page.getByText(/uploaded/i)).toBeVisible();
    
    // Query the document
    await page.fill('input[placeholder*="message"]', 'What is in the document?');
    await page.press('input[placeholder*="message"]', 'Enter');
    
    // Verify response
    await expect(page.getByText(/response/i)).toBeVisible({ timeout: 10000 });
  });
});
```

### E2E Test Conventions

- Tests should be independent and not rely on each other
- Clean up test data after tests (files, database entries)
- Use appropriate timeouts for async operations
- Test critical user paths and workflows

## Running Tests

### Quick Test Run

```bash
# Run all tests using the test script
./run_tests.sh
```

This script runs:
1. Backend tests with coverage
2. Frontend tests with coverage
3. Generates coverage reports

### Individual Test Suites

```bash
# Backend only
python -m pytest test_*.py -v --cov

# Frontend only
cd frontend && npm test -- --run

# E2E only
npx playwright test
```

## Coverage Reports

### Viewing Coverage Reports

After running tests with coverage, reports are generated in:

- **Backend**: `htmlcov/index.html`
- **Frontend**: `frontend/coverage/index.html`

Open these files in a browser to view detailed coverage information.

### Coverage Targets

We aim for:
- **Overall**: 80%+ coverage
- **Critical paths**: 90%+ coverage (authentication, data processing, RAG pipeline)
- **Utility functions**: 70%+ coverage

### Coverage Configuration

**Backend** (`.coveragerc`):
```ini
[run]
source = agent,app,rag
omit = */test_*.py

[report]
exclude_lines =
    pragma: no cover
    if __name__ == .__main__.:
```

**Frontend** (`vitest.config.ts`):
```typescript
coverage: {
  provider: 'v8',
  reporter: ['text', 'json', 'html'],
  exclude: ['node_modules/', 'src/test/', '**/*.d.ts']
}
```

## CI/CD Integration

### GitHub Actions Workflow

The test suite runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

### CI Test Jobs

1. **backend-tests**: Runs Python tests with coverage
2. **frontend-tests**: Runs React component tests
3. **e2e-tests**: Runs Playwright browser tests
4. **test-summary**: Aggregates results from all test jobs

### Viewing CI Results

- Go to the "Actions" tab in GitHub
- Select the workflow run
- View individual job logs and artifacts
- Download coverage reports from artifacts

## Writing Tests

### Test Naming Conventions

```python
# Backend
def test_<feature>_<scenario>():
    """Test that <feature> <expected behavior> when <scenario>."""

# Frontend
it('should <expected behavior> when <scenario>', () => {})
```

### Test Organization

- Group related tests in classes or describe blocks
- Use `beforeEach`/`afterEach` for setup/teardown
- Keep tests focused on a single behavior
- Use descriptive assertions

### Mocking Guidelines

```python
# Backend
from unittest.mock import patch, MagicMock

@patch('agent.llm_client.generate_response')
async def test_with_mock(mock_generate):
    mock_generate.return_value = "Mocked response"
    result = await some_function()
    assert result == "Expected result"
```

```typescript
// Frontend
import { vi } from 'vitest'

const mockFunction = vi.fn()
mockFunction.mockReturnValue('mocked value')
```

### Test Data

- Use fixtures for reusable test data
- Create minimal test data (only what's needed)
- Clean up test data after tests
- Use unique identifiers to avoid conflicts

## Troubleshooting

### Common Issues

**Backend Tests Fail:**
```bash
# Install missing dependencies
pip install -r requirements.txt

# Clear pytest cache
rm -rf .pytest_cache

# Run with verbose output
python -m pytest -vv --tb=long
```

**Frontend Tests Fail:**
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install

# Clear test cache
npx vitest --clearCache
```

**E2E Tests Fail:**
```bash
# Reinstall Playwright browsers
npx playwright install --with-deps

# Run with headed mode to see browser
npx playwright test --headed

# Enable debug mode
PWDEBUG=1 npx playwright test
```

### Test Debugging

**Backend:**
- Use `pytest -v` for verbose output
- Add `import pdb; pdb.set_trace()` for breakpoints
- Use `pytest -s` to see print statements

**Frontend:**
- Use `screen.debug()` to see rendered output
- Add `console.log` statements
- Use `test.only()` to run single test

**E2E:**
- Use `--headed` to see browser
- Use `page.pause()` for breakpoints
- Enable trace: `--trace on`

## Best Practices

1. **Test Pyramid**: More unit tests, fewer integration tests, minimal E2E tests
2. **Fast Tests**: Keep tests fast to encourage frequent running
3. **Reliable Tests**: Avoid flaky tests with proper waits and assertions
4. **Maintainable**: Write clear, well-documented tests
5. **Isolated**: Tests should not depend on each other
6. **Comprehensive**: Cover happy paths, edge cases, and error conditions

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Vitest documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright documentation](https://playwright.dev/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## Contributing Tests

When contributing code:
1. Write tests for new features
2. Update tests for modified features
3. Ensure all tests pass before submitting PR
4. Maintain or improve code coverage
5. Follow existing test patterns and conventions
