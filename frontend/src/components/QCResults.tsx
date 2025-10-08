import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Assessment,
  OpenInNew,
  Settings,
  CheckCircle,
  Warning,
  ExpandMore,
} from '@mui/icons-material';
import { api, QCResults as QCResultsType, RunInfo } from '../api/client';

interface QCResultsProps {
  run: RunInfo;
  onUpdate?: () => void;
}

const QCResults: React.FC<QCResultsProps> = ({ run, onUpdate }) => {
  const [qcResults, setQCResults] = useState<QCResultsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adapterDialogOpen, setAdapterDialogOpen] = useState(false);
  const [selectedAdapter, setSelectedAdapter] = useState<string>('');
  const [updatingAdapter, setUpdatingAdapter] = useState(false);
  const [rawQCExpanded, setRawQCExpanded] = useState(true);
  const [trimmedQCExpanded, setTrimmedQCExpanded] = useState(true);

  const adapterTypes = [
    'NexteraPE-PE',
    'TruSeq2-PE',
    'TruSeq2-SE',
    'TruSeq3-PE',
    'TruSeq3-PE-2',
    'TruSeq3-SE',
  ];

  const loadQCResults = async () => {
    try {
      setLoading(true);
      const results = await api.getQCResults(run.run_id);
      setQCResults(results);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load QC results:', err);
      setError('Failed to load QC results');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQCResults();
    // Set initial adapter type from run parameters
    setSelectedAdapter(run.parameters?.adapter_type || 'NexteraPE-PE');
  }, [run.run_id, run.parameters]);

  const handleOpenAdapterDialog = () => {
    setSelectedAdapter(run.parameters?.adapter_type || 'NexteraPE-PE');
    setAdapterDialogOpen(true);
  };

  const handleUpdateAdapter = async () => {
    try {
      setUpdatingAdapter(true);
      await api.updateAdapterType(run.run_id, selectedAdapter);
      setAdapterDialogOpen(false);
      if (onUpdate) {
        onUpdate();
      }
    } catch (err: any) {
      console.error('Failed to update adapter type:', err);
      setError(`Failed to update adapter type: ${err.response?.data?.detail || err.message}`);
    } finally {
      setUpdatingAdapter(false);
    }
  };

  const openQCFile = (stage: string, filePath: string) => {
    const url = api.getQCFileUrl(run.run_id, stage, filePath);
    const newWindow = window.open(url, '_blank', 'noopener,noreferrer');
    
    // Check if popup was blocked
    if (!newWindow || newWindow.closed || typeof newWindow.closed === 'undefined') {
      // Fallback: try to navigate in same window
      setError('Popup blocked. Opening in same window...');
      setTimeout(() => {
        window.location.href = url;
      }, 1000);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" py={4}>
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Loading QC results...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  const hasRawQC = qcResults?.qc_raw?.completed;
  const hasTrimmedQC = qcResults?.qc_trimmed?.completed;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Quality Control Results</Typography>
        
        {hasRawQC && (
          <Button
            size="small"
            variant="outlined"
            startIcon={<Settings />}
            onClick={handleOpenAdapterDialog}
          >
            Select Adapter
          </Button>
        )}
      </Box>

      {/* Current adapter type display */}
      {run.parameters?.adapter_type && (
        <Box mb={2}>
          <Chip
            label={`Adapter: ${run.parameters.adapter_type}`}
            color="primary"
            variant="outlined"
            size="small"
          />
        </Box>
      )}

      {/* Raw QC Results */}
      <Accordion 
        expanded={rawQCExpanded} 
        onChange={(e, isExpanded) => setRawQCExpanded(isExpanded)}
      >
        <AccordionSummary
          expandIcon={<ExpandMore />}
          sx={{
            backgroundColor: hasRawQC ? 'success.light' : 'grey.100',
            '&:hover': { backgroundColor: hasRawQC ? 'success.main' : 'grey.200' }
          }}
        >
          <Box display="flex" alignItems="center" width="100%">
            {hasRawQC ? (
              <CheckCircle color="success" sx={{ mr: 1 }} />
            ) : (
              <Warning color="warning" sx={{ mr: 1 }} />
            )}
            <Typography variant="subtitle1">
              Raw FASTQ Quality Control
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            {hasRawQC && (
              <Chip
                label="Completed"
                color="success"
                size="small"
                sx={{ mr: 1 }}
              />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {hasRawQC ? (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Quality control analysis completed. Review the reports below to assess read quality and select appropriate adapter sequences for trimming.
              </Typography>
              
              <List>
                {qcResults?.qc_raw?.files?.map((file, index) => (
                  <ListItem
                    key={index}
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1,
                      '&:hover': { backgroundColor: 'action.hover' }
                    }}
                  >
                    <ListItemIcon>
                      <Assessment color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={file.name}
                      secondary={file.description}
                    />
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<OpenInNew />}
                      onClick={() => openQCFile('qc_raw', file.path)}
                    >
                      View Report
                    </Button>
                  </ListItem>
                ))}
              </List>

              {qcResults?.qc_raw?.multiqc_available && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    <strong>Next Step:</strong> Review the MultiQC report to assess read quality and adapter contamination. 
                    Use the "Select Adapter" button above to choose the appropriate adapter type for trimming based on your analysis.
                    <br />
                    <strong>Tip:</strong> Look for the "Adapter Content" section in the MultiQC report to identify adapter sequences.
                  </Typography>
                </Alert>
              )}
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Raw QC analysis has not been completed yet. Submit the "QC Raw" stage to generate quality control reports.
            </Typography>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Trimmed QC Results */}
      <Accordion 
        expanded={trimmedQCExpanded} 
        onChange={(e, isExpanded) => setTrimmedQCExpanded(isExpanded)}
        sx={{ mt: 1 }}
      >
        <AccordionSummary
          expandIcon={<ExpandMore />}
          sx={{
            backgroundColor: hasTrimmedQC ? 'success.light' : 'grey.100',
            '&:hover': { backgroundColor: hasTrimmedQC ? 'success.main' : 'grey.200' }
          }}
        >
          <Box display="flex" alignItems="center" width="100%">
            {hasTrimmedQC ? (
              <CheckCircle color="success" sx={{ mr: 1 }} />
            ) : (
              <Warning color="warning" sx={{ mr: 1 }} />
            )}
            <Typography variant="subtitle1">
              Trimmed FASTQ Quality Control
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            {hasTrimmedQC && (
              <Chip
                label="Completed"
                color="success"
                size="small"
                sx={{ mr: 1 }}
              />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {hasTrimmedQC ? (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Quality control analysis of trimmed reads completed. Compare these results with the raw QC to assess trimming effectiveness.
              </Typography>
              
              <List>
                {qcResults?.qc_trimmed?.files?.map((file, index) => (
                  <ListItem
                    key={index}
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1,
                      '&:hover': { backgroundColor: 'action.hover' }
                    }}
                  >
                    <ListItemIcon>
                      <Assessment color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={file.name}
                      secondary={file.description}
                    />
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<OpenInNew />}
                      onClick={() => openQCFile('qc_trimmed', file.path)}
                    >
                      View Report
                    </Button>
                  </ListItem>
                ))}
              </List>
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Trimmed QC analysis has not been completed yet. Complete the trimming stage first, then submit "QC Trimmed".
            </Typography>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Adapter Selection Dialog */}
      <Dialog open={adapterDialogOpen} onClose={() => setAdapterDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Select Adapter Type</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Based on your QC results, select the appropriate adapter type for trimming. 
            Review the adapter contamination section in the MultiQC report to help make this decision.
          </Typography>

          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Adapter Type</InputLabel>
            <Select
              value={selectedAdapter}
              label="Adapter Type"
              onChange={(e) => setSelectedAdapter(e.target.value)}
            >
              {adapterTypes.map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            Common adapter types:
            <br />• NexteraPE-PE: Nexus/Nextera paired-end
            <br />• TruSeq3-PE: Illumina TruSeq3 paired-end
            <br />• TruSeq2-PE: Illumina TruSeq2 paired-end
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdapterDialogOpen(false)} disabled={updatingAdapter}>
            Cancel
          </Button>
          <Button
            onClick={handleUpdateAdapter}
            variant="contained"
            disabled={updatingAdapter || !selectedAdapter}
          >
            {updatingAdapter ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Updating...
              </>
            ) : (
              'Update Adapter'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default QCResults;