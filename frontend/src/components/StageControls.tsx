import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Button,
  Chip,
  Typography,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow,
  CheckCircle,
  Error as ErrorIcon,
  HourglassEmpty,
  Refresh,
  Assessment,
  Description,
} from '@mui/icons-material';
import { api, RunInfo } from '../api/client';
import StageLogsDialog from './StageLogsDialog';

interface StageControlsProps {
  run: RunInfo;
  onUpdate?: () => void;
}

interface StageInfo {
  name: string;
  displayName: string;
  dependencies: string[];
  description: string;
}

const STAGES: StageInfo[] = [
  {
    name: 'qc_raw',
    displayName: 'QC Raw',
    dependencies: [],
    description: 'Run FastQC to assess raw FASTQ file quality (sequencing quality scores, GC content, adapter contamination)'
  },
  {
    name: 'trim',
    displayName: 'Trim Adapters',
    dependencies: ['qc_raw'],
    description: 'Remove adapter sequences and low-quality bases using Trimmomatic'
  },
  {
    name: 'qc_trimmed',
    displayName: 'QC Trimmed',
    dependencies: ['trim'],
    description: 'Run FastQC on trimmed reads to verify quality improvement'
  },
  {
    name: 'star',
    displayName: 'STAR Alignment',
    dependencies: ['trim'],
    description: 'Align reads to reference genome using STAR aligner (generates BAM files and gene counts)'
  },
  {
    name: 'featurecounts',
    displayName: 'Count Features',
    dependencies: ['star'],
    description: 'Quantify gene expression by counting reads mapped to genomic features using featureCounts'
  },
  {
    name: 'deseq2',
    displayName: 'DESeq2 Analysis',
    dependencies: ['featurecounts'],
    description: 'Perform differential expression analysis using DESeq2 (requires metadata.csv with sample conditions)'
  }
];

const StageControls: React.FC<StageControlsProps> = ({ run, onUpdate }) => {
  const [stageStatuses, setStageStatuses] = useState<Record<string, any>>({});
  const [submitting, setSubmitting] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const [logsDialog, setLogsDialog] = useState<{ open: boolean; stage: string; stageName: string }>({
    open: false,
    stage: '',
    stageName: '',
  });
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isLoadingRef = useRef(false);
  const lastUpdateRef = useRef<number>(0);

  // Load stage statuses with debouncing to prevent rapid API calls
  const loadStageStatuses = useCallback(async (force: boolean = false) => {
    // Prevent multiple simultaneous calls and add minimum interval between updates
    const now = Date.now();
    if ((isLoadingRef.current && !force) || (!force && now - lastUpdateRef.current < 2000)) {
      return;
    }
    
    isLoadingRef.current = true;
    lastUpdateRef.current = now;
    
    try {
      const statuses: Record<string, any> = {};
      
      await Promise.all(
        STAGES.map(async (stage) => {
          try {
            const status = await api.getStageStatus(run.run_id, stage.name);
            statuses[stage.name] = status;
          } catch (err) {
            // Stage might not have been submitted yet
            statuses[stage.name] = { state: 'PENDING', job_id: '' };
          }
        })
      );
      
      setStageStatuses(prevStatuses => {
        // Only update if statuses have actually changed to prevent unnecessary re-renders
        const hasChanged = JSON.stringify(prevStatuses) !== JSON.stringify(statuses);
        return hasChanged ? statuses : prevStatuses;
      });
      setError(null);
    } catch (err) {
      console.error('Failed to load stage statuses:', err);
      setError('Failed to load stage statuses');
    } finally {
      isLoadingRef.current = false;
    }
  }, [run.run_id]);

  // Auto-refresh every 15 seconds if any jobs are running (increased from 10s to reduce load)
  useEffect(() => {
    const hasRunningJobs = Object.values(stageStatuses).some(
      status => status?.state === 'RUNNING' || status?.state === 'PENDING'
    );

    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (hasRunningJobs) {
      setPolling(true);
      intervalRef.current = setInterval(() => {
        loadStageStatuses();
      }, 15000); // Increased interval to 15 seconds
    } else {
      setPolling(false);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [stageStatuses, loadStageStatuses]);

  // Initial load
  useEffect(() => {
    loadStageStatuses();
  }, [run.run_id, loadStageStatuses]);

  const submitStage = async (stageName: string, confirmRerun: boolean = false) => {
    setSubmitting(prev => ({ ...prev, [stageName]: true }));
    setError(null);
    
    try {
      // Validate stage before submission (unless confirming rerun)
      if (!confirmRerun) {
        const validation = await api.validateStage(run.run_id, stageName);
        
        // Show warnings if any
        if (validation.warnings && validation.warnings.length > 0) {
          console.warn(`Stage ${stageName} validation warnings:`, validation.warnings);
        }
        
        // Block submission if validation fails
        if (!validation.valid) {
          const errorMessage = validation.errors.join('\n• ');
          setError(`Cannot submit ${stageName}:\n• ${errorMessage}`);
          setSubmitting(prev => ({ ...prev, [stageName]: false }));
          return;
        }
      }
      
      // Submit the stage
      await api.submitStage(run.run_id, stageName, {
        account: run.account || 'default',
        confirm_rerun: confirmRerun
      });
      
      // Keep button disabled and poll for status update to RUNNING
      // This prevents duplicate submissions during the brief window
      // between job submission and status update appearing in squeue
      const checkStatusUpdate = async (attempts: number = 0): Promise<void> => {
        if (attempts >= 10) {
          // After 10 seconds, give up and re-enable button
          setSubmitting(prev => ({ ...prev, [stageName]: false }));
          return;
        }
        
        // Fetch fresh status
        try {
          const status = await api.getStageStatus(run.run_id, stageName);
          
          if (status.status === 'RUNNING' || status.status === 'COMPLETED' || status.status === 'FAILED') {
            // Status updated successfully, refresh all statuses and re-enable
            await loadStageStatuses(true);
            setSubmitting(prev => ({ ...prev, [stageName]: false }));
          } else {
            // Status not updated yet, check again in 1 second
            setTimeout(() => checkStatusUpdate(attempts + 1), 1000);
          }
        } catch (err) {
          // Error fetching status, retry
          setTimeout(() => checkStatusUpdate(attempts + 1), 1000);
        }
      };
      
      checkStatusUpdate();
      
      // Don't call onUpdate() here - it causes parent re-render which may close dialogs
      // The stage status refresh above is sufficient to update the UI
    } catch (err: any) {
      console.error(`Failed to submit stage ${stageName}:`, err);
      
      // Check if this is a rerun confirmation error (409 Conflict)
      if (err.response?.status === 409) {
        const shouldRerun = window.confirm(
          `⚠️ Warning: Stage "${stageName}" was previously completed.\n\n` +
          `Re-running this stage will DELETE all previous results for this stage.\n\n` +
          `Are you sure you want to proceed?`
        );
        
        if (shouldRerun) {
          // User confirmed, retry with confirmation flag
          setSubmitting(prev => ({ ...prev, [stageName]: false }));
          await submitStage(stageName, true);
          return;
        }
      }
      
      setError(`Failed to submit ${stageName}: ${err.response?.data?.detail || err.message}`);
      setSubmitting(prev => ({ ...prev, [stageName]: false }));
    }
  };

  const getStageStatus = (stageName: string): string => {
    const status = stageStatuses[stageName];
    if (!status) return 'PENDING';
    return status.state || 'PENDING';
  };

  const canSubmitStage = (stage: StageInfo): boolean => {
    const currentStatus = getStageStatus(stage.name);
    
    // Can't submit if already completed or running
    if (currentStatus === 'COMPLETED' || currentStatus === 'RUNNING') {
      return false;
    }
    
    // Check if all dependencies are completed
    return stage.dependencies.every(dep => getStageStatus(dep) === 'COMPLETED');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle color="success" />;
      case 'FAILED': case 'CANCELLED': return <ErrorIcon color="error" />;
      case 'RUNNING': return <HourglassEmpty color="primary" />;
      default: return <HourglassEmpty color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'success';
      case 'FAILED': case 'CANCELLED': return 'error';
      case 'RUNNING': return 'primary';
      case 'PENDING': return 'default';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Pipeline Stages</Typography>
        <Tooltip title="Refresh status">
          <IconButton size="small" onClick={() => loadStageStatuses(true)}>
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Pipeline workflow info */}
      <Alert severity="info" sx={{ mb: 2 }}>
        <Typography variant="body2" gutterBottom>
          <strong>Pipeline Workflow:</strong> Stages must be run in order. Upload FASTQ files first, then execute stages sequentially.
        </Typography>
        <Typography variant="body2">
          • Each stage depends on the completion of previous stages<br/>
          • Submit buttons are enabled when dependencies are met<br/>
          • Monitor job status and view logs for each stage
        </Typography>
      </Alert>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          <Box sx={{ whiteSpace: 'pre-line' }}>
            {error}
          </Box>
        </Alert>
      )}

      <List>
        {STAGES.map((stage, index) => {
          const status = getStageStatus(stage.name);
          const canSubmit = canSubmitStage(stage);
          const isSubmitting = submitting[stage.name];
          const stageData = stageStatuses[stage.name];

          return (
            <ListItem
              key={stage.name}
              divider={index < STAGES.length - 1}
              sx={{ 
                flexDirection: 'column',
                alignItems: 'flex-start',
                py: 2
              }}
            >
              <Box display="flex" alignItems="center" width="100%" mb={1}>
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {getStatusIcon(status)}
                </ListItemIcon>
                
                <ListItemText
                  primary={stage.displayName}
                  secondary={stage.description}
                  sx={{ flex: 1 }}
                />
                
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip
                    label={status}
                    color={getStatusColor(status) as any}
                    size="small"
                  />
                  
                  {/* Show QC results available indicator */}
                  {stage.name === 'qc_raw' && status === 'COMPLETED' && (
                    <Chip
                      icon={<Assessment />}
                      label="Results Available"
                      size="small"
                      variant="outlined"
                      color="success"
                    />
                  )}
                  
                  {/* View Logs button for stages with job IDs */}
                  {stageData?.job_id && (
                    <Tooltip title="View job logs">
                      <IconButton
                        size="small"
                        onClick={() => setLogsDialog({ open: true, stage: stage.name, stageName: stage.displayName })}
                      >
                        <Description fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  
                  <Button
                    size="small"
                    variant={canSubmit ? "contained" : "outlined"}
                    disabled={!canSubmit || isSubmitting}
                    onClick={() => submitStage(stage.name)}
                    startIcon={<PlayArrow />}
                  >
                    {isSubmitting ? 'Submitting...' : 'Run'}
                  </Button>
                </Box>
              </Box>

              {/* Show job ID and additional info for active/completed stages */}
              {stageData?.job_id && (
                <Box ml={5} mt={1} width="100%">
                  <Typography variant="caption" color="text.secondary">
                    Job ID: {stageData.job_id}
                  </Typography>
                  
                  {status === 'RUNNING' && (
                    <Box mt={1}>
                      <LinearProgress variant="indeterminate" />
                      <Typography variant="caption" color="text.secondary">
                        Running on cluster...
                      </Typography>
                    </Box>
                  )}
                </Box>
              )}

              {/* Special message for trim stage when QC is complete */}
              {stage.name === 'trim' && getStageStatus('qc_raw') === 'COMPLETED' && status === 'PENDING' && (
                <Box ml={5} mt={1} width="100%">
                  <Alert severity="info" sx={{ fontSize: '0.75rem' }}>
                    <Typography variant="caption">
                      <strong>Tip:</strong> Review QC results below to select the optimal adapter type before trimming.
                    </Typography>
                  </Alert>
                </Box>
              )}

              {/* Show dependencies */}
              {stage.dependencies.length > 0 && (
                <Box ml={5} mt={1}>
                  <Typography variant="caption" color="text.secondary">
                    Requires: {stage.dependencies.map(dep => 
                      STAGES.find(s => s.name === dep)?.displayName || dep
                    ).join(', ')}
                  </Typography>
                </Box>
              )}

              {/* Show current adapter type for trim stage */}
              {stage.name === 'trim' && run.parameters?.adapter_type && (
                <Box ml={5} mt={1}>
                  <Chip
                    label={`Using: ${run.parameters.adapter_type}`}
                    size="small"
                    variant="outlined"
                    color="primary"
                  />
                </Box>
              )}
            </ListItem>
          );
        })}
      </List>

      {polling && (
        <Box mt={2} display="flex" alignItems="center" gap={1}>
          <Typography variant="caption" color="text.secondary">
            Auto-refreshing every 15 seconds...
          </Typography>
          <Box sx={{ width: 12, height: 12 }}>
            <LinearProgress variant="indeterminate" sx={{ height: 2 }} />
          </Box>
        </Box>
      )}

      {/* Logs Dialog */}
      <StageLogsDialog
        open={logsDialog.open}
        onClose={() => setLogsDialog({ open: false, stage: '', stageName: '' })}
        runId={run.run_id}
        stage={logsDialog.stage}
        stageName={logsDialog.stageName}
      />
    </Box>
  );
};

export default StageControls;