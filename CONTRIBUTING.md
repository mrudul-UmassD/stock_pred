# Contributing to stock-predict-live

Thank you for contributing to this project! We value high-quality, maintainable code that is production-ready.

## Code Review Process

All pull requests undergo automated review via **CodeRabbit**. CodeRabbit analyzes your code for:
- Code quality and style
- Security vulnerabilities
- Performance issues
- Best practices
- Documentation completeness
- Test coverage

### **IMPORTANT: All PRs must address CodeRabbit comments before merge.**

## Pull Request Guidelines

1. **Create a descriptive PR title**
   - Use conventional commits format: `feat:`, `fix:`, `docs:`, `refactor:`, etc.
   - Example: `feat: add RSI indicator to feature engineering`

2. **Fill out the PR template completely**
   - Describe what changed and why
   - Reference any related issues
   - Complete all checklist items

3. **Address all CodeRabbit feedback**
   - Review each comment carefully
   - Make requested changes or provide justification
   - Mark conversations as resolved when addressed

4. **Ensure all checks pass**
   - Tests must pass
   - Linting must pass
   - No security vulnerabilities
   - Documentation updated

## Code Standards

### Python (Backend & Notebooks)
- **Type hints**: Use typing for all function signatures
- **Docstrings**: Google-style docstrings for all public functions/classes
- **Formatting**: Follow PEP 8 (black formatter recommended)
- **Error handling**: Proper try/except with logging
- **No hardcoded values**: Use config files or environment variables

Example:
```python
from typing import List, Optional
import pandas as pd

def fetch_ohlcv(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data for a given ticker.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL')
        start: Start date in 'YYYY-MM-DD' format
        end: End date in 'YYYY-MM-DD' format
        
    Returns:
        DataFrame with OHLCV columns or None if fetch fails
        
    Raises:
        ValueError: If date format is invalid
    """
    # Implementation
```

### TypeScript (Frontend)
- **Type safety**: Use TypeScript strictly, avoid `any`
- **Component structure**: Functional components with hooks
- **Props interfaces**: Define explicit interfaces for all props
- **Error boundaries**: Handle errors gracefully in UI

Example:
```typescript
interface PredictionRowProps {
  ticker: string;
  direction: 'up' | 'down' | 'flat';
  probability: number;
  horizon: number;
}

export function PredictionRow({ ticker, direction, probability, horizon }: PredictionRowProps) {
  // Implementation
}
```

## Data Leakage Prevention

**Critical**: Any feature engineering or modeling code must prevent data leakage.

✅ **Good practices:**
- Use walk-forward validation (expanding window)
- Forward-fill only with past data
- Compute indicators using rolling windows
- Separate train/validation by time

❌ **Avoid:**
- Random train/test splits on time-series
- Using future information in features
- Look-ahead bias in indicators
- Fitting scalers on entire dataset

## Testing Requirements

### Backend Tests
- Unit tests for all service functions
- Integration tests for API endpoints
- Test both success and error cases
- Mock external API calls (yfinance, FRED)

### Frontend Tests
- Component unit tests
- Integration tests for key user flows
- Test SSE connection handling
- Test error states

## Security Checklist

- [ ] No API keys or secrets in code
- [ ] Input validation on all API endpoints
- [ ] SQL injection prevention (use parameterized queries)
- [ ] CORS properly configured
- [ ] Rate limiting on public endpoints
- [ ] Error messages don't leak sensitive info

## Documentation Requirements

- [ ] Update README.md if adding new features
- [ ] Add docstrings to all new functions
- [ ] Update API documentation for endpoint changes
- [ ] Add inline comments for complex logic
- [ ] Update troubleshooting section for new issues

## Commit Message Format

Use conventional commits:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(backend): add Stooq fallback data source

Implement CSV downloader from Stooq as fallback when yfinance
fails or returns incomplete data. Includes retry logic and error
handling.

Closes #42
```

## Branch Naming

- Feature: `feat/short-description`
- Bug fix: `fix/short-description`
- Documentation: `docs/short-description`
- Refactor: `refactor/short-description`

## Questions?

Open an issue for:
- Feature proposals
- Bug reports
- Architecture discussions
- Documentation improvements

Thank you for helping make this project better!
