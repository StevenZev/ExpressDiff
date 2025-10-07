# Metadata Builder Feature - Implementation Plan

## Overview

**Feature Goal**: Allow users to interactively group their uploaded FASTQ files and automatically generate the required `metadata.csv` for DESeq2 analysis.

## Current Workflow (Manual)

1. User uploads FASTQ files
2. User must manually create `metadata.csv`:
   ```csv
   sample_name,condition
   control_1,control
   control_2,control
   treatment_1,treatment
   ```
3. User uploads metadata.csv
4. User runs DESeq2

## Proposed Workflow (Interactive)

1. User uploads FASTQ files
2. **NEW**: UI shows "Metadata Builder" tab/section
3. **NEW**: System displays all detected samples in a table
4. **NEW**: User assigns conditions via dropdowns/text inputs
5. **NEW**: Optional: AI suggests conditions based on naming patterns
6. **NEW**: UI validates (minimum 2 conditions, ≥2 replicates recommended)
7. **NEW**: Click "Generate Metadata" → creates and uploads metadata.csv automatically
8. User runs DESeq2

## Feature Design

### UI Components

#### 1. Sample Grouping Table
```
┌───────────────────────────────────────────────────────────┐
│ Metadata Builder                              [Auto-Detect]│
├──────────────────┬─────────────────┬─────────────────────┤
│ Sample Name      │ Condition       │ Additional Factors   │
├──────────────────┼─────────────────┼─────────────────────┤
│ control_1        │ [control    ▼]  │ [Add Factor+]       │
│ control_2        │ [control    ▼]  │                     │
│ control_3        │ [control    ▼]  │                     │
│ treatment_1      │ [treatment  ▼]  │                     │
│ treatment_2      │ [treatment  ▼]  │                     │
│ treatment_3      │ [treatment  ▼]  │                     │
└──────────────────┴─────────────────┴─────────────────────┘
           [Download CSV] [Save & Upload Metadata]
```

#### 2. Auto-Detection Panel
- Scan sample names for patterns:
  - `control_*`, `ctrl_*`, `wt_*` → suggest "control"
  - `treatment_*`, `trt_*`, `exp_*` → suggest "treatment"
  - `mutant_*`, `ko_*`, `mut_*` → suggest "mutant"
- Show suggestions: "Apply 'control' to 3 samples" [Apply]

#### 3. Validation Feedback
- ✅ **Valid**: All samples have conditions, ≥2 conditions exist
- ⚠️ **Warnings**:
  - "Condition 'control' has only 1 sample (recommend ≥2)"
  - "Consider adding batch/timepoint factors for complex designs"
- ❌ **Errors**:
  - "3 samples missing condition assignment"
  - "Only 1 condition defined (need ≥2 for differential expression)"

#### 4. Condition Summary
```
Conditions: [control (n=3)] [treatment (n=3)]
Ready for DESeq2 ✓
```

### Backend Support

#### API Endpoint: `POST /runs/{run_id}/metadata/generate`
```python
@app.post("/runs/{run_id}/metadata/generate")
async def generate_metadata(run_id: str, metadata: List[SampleMetadata]):
    """
    Generate and save metadata.csv from user-provided sample assignments.
    
    Args:
        metadata: List of {sample_name, condition, ...} dicts
    
    Returns:
        Success response with file path
    """
    # Validate metadata
    # Convert to CSV
    # Save to {run_dir}/metadata/metadata.csv
    # Return success
```

#### Data Model
```python
class SampleMetadata(BaseModel):
    sample_name: str
    condition: str
    batch: Optional[str] = None
    timepoint: Optional[str] = None
    # Allow arbitrary additional factors
    extra_factors: Optional[Dict[str, str]] = {}
```

## Implementation Phases

### Phase 1: Basic Functionality (MVP)
**Effort**: 2-3 hours
- [x] Create React component with sample table
- [ ] Add condition input fields (text or dropdown)
- [ ] Client-side validation
- [ ] Generate CSV and upload via existing upload endpoint
- [ ] Integrate into FileUpload tab

### Phase 2: Auto-Detection
**Effort**: 1-2 hours
- [ ] Pattern matching for common naming conventions
- [ ] Suggestion UI
- [ ] "Apply suggestion" and "Apply all" buttons

### Phase 3: Advanced Features
**Effort**: 2-3 hours  
- [ ] Support additional factors (batch, timepoint, etc.)
- [ ] Dynamic column addition
- [ ] Condition color coding
- [ ] Replicate grouping visualization
- [ ] Download CSV before uploading

### Phase 4: Polish
**Effort**: 1-2 hours
- [ ] Comprehensive validation messages
- [ ] Tooltips and help text
- [ ] Integration with pipeline status
- [ ] "Metadata complete" indicator in run card

## Benefits

### For Users
1. **Faster**: No manual CSV creation
2. **Error-proof**: Validation prevents common mistakes
3. **User-friendly**: Visual interface vs text file editing
4. **Guided**: Suggestions help new users

### For Pipeline
1. **Better data quality**: Validated metadata
2. **Fewer errors**: Catch issues before DESeq2 runs
3. **Flexibility**: Easy to add factors for complex designs
4. **Traceable**: Metadata generation is logged

## Technical Considerations

### Challenges
1. **State management**: Syncing sample list with metadata assignments
2. **Validation logic**: Client-side + server-side consistency
3. **File upload**: Metadata should upload automatically, not manual
4. **Sample name parsing**: Extracting base name from FASTQ filenames

### Solutions
1. Use React hooks (useState, useEffect) for state
2. Share validation schema between frontend (TypeScript) and backend (Pydantic)
3. Direct API call to save generated metadata
4. Leverage existing sample validation logic

## Testing Plan

1. **Unit Tests**:
   - Pattern detection accuracy
   - Validation rules
   - CSV generation format

2. **Integration Tests**:
   - Upload files → generate metadata → run DESeq2
   - Edge cases: 1 sample, 10+ conditions, special characters

3. **User Testing**:
   - Test with real user workflows
   - Collect feedback on UI/UX

## Future Enhancements

1. **Metadata Templates**: Save/load common experimental designs
2. **Batch Import**: Upload existing metadata CSV and edit
3. **Visualization**: Preview PCA, sample clustering before analysis
4. **Multi-run**: Copy metadata structure to new runs
5. **Export**: Download filled template for external use

## Example User Flow

```
1. User uploads 12 FASTQ files (6 samples, paired-end)
   ↓
2. FileUpload shows "✓ 6 samples detected" 
   ↓
3. "Metadata Builder" section appears below
   ↓
4. Table shows 6 samples, empty condition fields
   ↓
5. Click "Auto-Detect" → suggests:
   - control_1, control_2, control_3 → "control"
   - treatment_1, treatment_2, treatment_3 → "treatment"
   ↓
6. User clicks "Apply All"
   ↓
7. Validation shows: ✓ Ready (2 conditions, 3 replicates each)
   ↓
8. Click "Save & Upload Metadata"
   ↓
9. metadata.csv created and uploaded to run directory
   ↓
10. DESeq2 stage now enabled (dependency satisfied)
```

## Recommendation

**Start with Phase 1 (MVP)**: Basic table with manual condition assignment and generation. This provides immediate value with relatively low effort (~2-3 hours). Can iterate with auto-detection and advanced features based on user feedback.

**Priority**: Medium-High
- Not critical for basic pipeline function
- Significantly improves user experience
- Reduces support burden (fewer metadata format errors)
- Makes pipeline more accessible to non-computational users

