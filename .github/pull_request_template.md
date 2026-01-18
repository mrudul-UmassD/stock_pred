## Description
<!-- Provide a clear and concise description of what this PR does -->


## Type of Change
<!-- Check all that apply -->
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement

## Related Issue
<!-- Link to the issue this PR addresses (e.g., Closes #123) -->


## Changes Made
<!-- List the main changes in bullet points -->
-
-
-

## Testing
<!-- Describe the tests you ran and how to reproduce them -->
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All existing tests pass

## Checklist
<!-- All items must be checked before merge -->
- [ ] Code follows project style guidelines (PEP 8 for Python, ESLint for TypeScript)
- [ ] Type hints added for all Python functions
- [ ] Docstrings added for all public functions/classes (Google style)
- [ ] TypeScript types defined (no `any` used)
- [ ] All CodeRabbit comments addressed
- [ ] Linting passes (`black`, `flake8`, `eslint`)
- [ ] Security scan passes (no vulnerabilities introduced)
- [ ] No data leakage in ML code (forward-looking bias prevented)
- [ ] No hardcoded secrets or API keys
- [ ] Input validation added for new API endpoints
- [ ] Error handling implemented with appropriate logging
- [ ] Documentation updated (README, docstrings, comments)
- [ ] Database migrations included (if schema changed)
- [ ] Frontend accessibility checked (if UI changes)

## Data Leakage Prevention
<!-- Required for ML/feature engineering changes -->
- [ ] Features use only historical data (no look-ahead)
- [ ] Walk-forward validation used (no random splits)
- [ ] Macro data forward-filled without future information
- [ ] Labels computed after feature cutoff date
- [ ] N/A - This PR does not involve ML/features

## Screenshots
<!-- If applicable, add screenshots to demonstrate UI changes -->


## Performance Impact
<!-- Describe any performance implications -->
- [ ] No performance impact
- [ ] Performance improvement (describe below)
- [ ] Performance regression (justified below)


## Deployment Notes
<!-- Any special deployment considerations -->
- [ ] No special deployment steps
- [ ] Requires environment variable changes (list below)
- [ ] Requires database migration
- [ ] Requires dependency updates


## Reviewer Notes
<!-- Additional context for reviewers -->


---

**By submitting this PR, I confirm:**
- [ ] I have reviewed my own code
- [ ] I will address all CodeRabbit comments before requesting merge
- [ ] I have tested the changes locally
- [ ] This code is ready for production
