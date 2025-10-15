# Design Workplan - Senior Review Issues

## Verification Summary

I've analyzed the four flagged issues from the senior reviewers and can confirm each one:

### 1. ✅ **Flatter Repository Layout** - CONFIRMED
- **Issue**: The `design.md` (lines 916-1005) proposed a nested structure with `src/minutia/steps/`, `src/minutia/clients/`, `src/minutia/pipeline/`
- **Current Reality**: All modules are directly under `src/minutia/` (verified via `ls src/minutia/`)
- **Impact**: Minor deviation that reduces the modularity envisioned in the original plan

### 2. ✅ **Improper Exception Chaining** - CONFIRMED
- **Issue**: Multiple locations in `src/minutia/cli.py` catch exceptions and re-raise as `click.ClickException(str(e))` without chaining
- **Locations Found**: 
  - `cli.py:74` - extract_audio command
  - `cli.py:91` - transcribe command  
  - `cli.py:106` - merge_transcripts command
  - `cli.py:156` - summarize command
- **Impact**: High priority - obscures original stack traces, making debugging much harder

### 3. ✅ **Linting Errors** - CONFIRMED
- **UP007**: 1 error in `src/minutia/logging.py:20` using `Union[str, Path]` instead of `str | Path`
- **Whitespace Issues**: 11 errors in `tests/conftest.py` (W291, W293) - trailing whitespace and blank lines with whitespace
- **Impact**: Code quality degradation, inconsistent formatting

### 4. ✅ **Cleanup Policy Not Wired** - CONFIRMED
- **Issue**: `MinutiaConfig.cleanup_policy` is parsed (`src/minutia/config.py:114-190`) but never used in execution
- **Evidence**: No references to `cleanup_policy` in orchestrator, pipeline, or baseline modules
- **Impact**: Configuration option exists but has no effect on artifact management

---

## Proposed Workplan

### Phase 1: Critical Fixes (Immediate) - 1-2 hours
**Priority: High - Affects debugging and code quality**

#### 1.1 Fix Exception Chaining (30 minutes)
- **Target**: `src/minutia/cli.py` lines 74, 91, 106, 156
- **Change**: Replace `raise click.ClickException(str(e))` with `raise click.ClickException(str(e)) from e`
- **Verification**: Run `uv run ruff check src/minutia/cli.py --select=B904` - should show 0 errors

#### 1.2 Fix Type Hint Issues (15 minutes)  
- **Target**: `src/minutia/logging.py:20`
- **Change**: Replace `Union[str, Path]` with `str | Path`
- **Verification**: Run `uv run ruff check . --select=UP007` - should show 0 errors

#### 1.3 Fix Whitespace Issues (15 minutes)
- **Target**: `tests/conftest.py` 
- **Change**: Remove trailing whitespace and whitespace-only blank lines
- **Verification**: Run `uv run ruff check . --select=W291,W293,W292` - should show 0 errors

### Phase 2: Architecture Alignment (Medium-term) - 4-6 hours
**Priority: Medium - Improves maintainability and follows design intent**

#### 2.1 Implement Cleanup Policy Wiring (2-3 hours)
- **Research**: Review design.md sections 107-210 for artifact management goals
- **Implementation**:
  - Add cleanup logic to `PipelineOrchestrator.execute()` method
  - Add cleanup method to `RunPaths` class 
  - Wire `MinutiaConfig.cleanup_policy` through `PipelineConfig`
  - Add cleanup execution at appropriate pipeline stages
- **Testing**: Add unit tests for cleanup behavior with each policy type
- **Verification**: Create test scenarios demonstrating each cleanup policy works as intended

#### 2.2 Restructure Repository Layout (2-3 hours)
- **Planning**: Decide whether to follow design.md structure or update design.md to match current structure
- **Recommendation**: Update design.md to match current flatter structure (lower risk)
- **Alternative**: Implement nested structure if team prefers original design
- **Actions**:
  - If keeping flat: Update design.md lines 916-1005 to reflect actual structure
  - If going nested: Create subdirectories and move modules, update all imports
- **Verification**: Ensure all imports work and tests pass after restructuring

### Phase 3: Quality Improvements (Optional) - 2-3 hours
**Priority: Low - Nice to have improvements**

#### 3.1 Comprehensive Linting Fix
- **Target**: Run full ruff check and fix remaining issues
- **Actions**: `uv run ruff check --fix .` and address any remaining issues
- **Verification**: Clean `uv run ruff check .` output

#### 3.2 Documentation Updates
- **Target**: Update CLAUDE.md and design.md to reflect current reality
- **Actions**: Align documentation with actual implementation choices
- **Verification**: Documentation accurately describes current codebase

---

## Implementation Strategy

### Immediate Actions (Today)
1. **Start with Phase 1** - These are quick wins that improve code quality immediately
2. **Fix exception chaining first** - Critical for debugging capabilities
3. **Run tests after each fix** - Ensure no regression

### Near-term Planning (This Week)
1. **Decide on repository structure** - Flat vs nested, update documentation accordingly  
2. **Implement cleanup policy** - This was explicitly called out in design goals
3. **Create integration tests** - Verify cleanup policies work end-to-end

### Quality Gates
- All ruff linting errors resolved
- Exception chaining preserves stack traces  
- Cleanup policies demonstrably affect artifact management
- Documentation matches implementation reality
- All existing tests continue to pass

---

## Risk Assessment

### Low Risk Changes
- Exception chaining fixes (straightforward, well-understood pattern)
- Type hint modernization (automated fix available)
- Whitespace cleanup (cosmetic, no functional impact)

### Medium Risk Changes  
- Cleanup policy implementation (requires careful integration testing)
- Repository restructuring (affects import paths, requires thorough testing)

### Recommended Approach
1. **Start with low-risk fixes** - Build confidence and improve baseline quality
2. **Tackle cleanup policy next** - Highest business value of remaining items
3. **Defer repository restructuring** - Unless team strongly prefers nested structure

This workplan addresses all four senior review issues while prioritizing based on impact and implementation complexity.