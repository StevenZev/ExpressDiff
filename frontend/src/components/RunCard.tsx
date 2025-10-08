import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  LinearProgress,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  PlayArrow,
  Delete,
  MoreVert,
  Assessment,
  Settings,
  CloudUpload,
} from '@mui/icons-material';
import { api, RunInfo } from '../api/client';
import FileUpload from './FileUpload';
import StageControls from './StageControls';
import QCResults from './QCResults';
import FeatureCountsResults from './FeatureCountsResults';
import DESeq2Results from './DESeq2Results';

interface RunCardProps {
  run: RunInfo;
  onUpdate: () => void;
}

const RunCard: React.FC<RunCardProps> = ({ run, onUpdate }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [deleting, setDeleting] = useState(false);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleOpenDetails = () => {
    setDetailsOpen(true);
    handleMenuClose();
  };

  const handleOpenResults = () => {
    setSelectedTab(2); // Select Results tab
    setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const handleDeleteRun = async () => {
    if (!window.confirm(`Are you sure you want to delete "${run.name}"? This will permanently remove all files and cannot be undone.`)) {
      return;
    }

    setDeleting(true);
    handleMenuClose();

    try {
      await api.deleteRun(run.run_id);
      onUpdate(); // Refresh the runs list
    } catch (error: any) {
      alert(`Failed to delete run: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDeleting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'created': return 'default';
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getProgress = () => {
    if (!run.stages) return 0;
    const stages = Object.values(run.stages);
    const completed = stages.filter(stage => stage.status === 'completed').length;
    return (completed / stages.length) * 100;
  };

  const hasQCResults = () => {
    // Check if qc_raw stage is completed
    return run.stages && 
           run.stages['qc_raw'] && 
           (run.stages['qc_raw'].status === 'completed' || run.stages['qc_raw'].status === 'COMPLETED');
  };

  const getStagesSummary = () => {
    if (!run.stages) return 'No stages';
    const stages = Object.values(run.stages);
    const running = stages.filter(stage => stage.status === 'running').length;
    const completed = stages.filter(stage => stage.status === 'completed').length;
    const failed = stages.filter(stage => stage.status === 'failed').length;
    
    return `${completed} completed, ${running} running, ${failed} failed`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Typography variant="h6" component="h2" noWrap>
            {run.name}
          </Typography>
          <IconButton size="small" onClick={handleMenuOpen}>
            <MoreVert />
          </IconButton>
        </Box>

        <Typography variant="body2" color="text.secondary" gutterBottom>
          {run.description || 'No description'}
        </Typography>

        <Box mb={2}>
          <Chip
            label={run.status}
            color={getStatusColor(run.status) as any}
            size="small"
            sx={{ mr: 1 }}
          />
          {run.account && (
            <Chip
              label={`Allocation: ${run.account}`}
              variant="outlined"
              size="small"
              sx={{ mr: 1 }}
            />
          )}
          {hasQCResults() && (
            <Chip
              label="QC Available"
              color="success"
              size="small"
              variant="outlined"
            />
          )}
        </Box>

        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
          Created: {formatDate(run.created_at)}
        </Typography>

        {run.updated_at && (
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            Updated: {formatDate(run.updated_at)}
          </Typography>
        )}

        {run.stages && (
          <Box mt={2}>
            <Typography variant="body2" gutterBottom>
              Pipeline Progress
            </Typography>
            <LinearProgress
              variant="determinate"
              value={getProgress()}
              sx={{ mb: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              {getStagesSummary()}
            </Typography>
          </Box>
        )}
      </CardContent>

      <CardActions>
        <Button size="small" startIcon={<Settings />} onClick={handleOpenDetails}>
          Manage
        </Button>
        <Tooltip title={hasQCResults() ? "QC results available" : "Results will be available after pipeline stages complete"}>
          <Button 
            size="small" 
            startIcon={<Assessment />} 
            onClick={handleOpenResults}
            variant={hasQCResults() ? "outlined" : "text"}
            color={hasQCResults() ? "primary" : "inherit"}
          >
            Results {hasQCResults() && "●"}
          </Button>
        </Tooltip>
      </CardActions>

      {/* Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleOpenDetails}>
          <Settings sx={{ mr: 1 }} />
          Manage Run
        </MenuItem>
        <MenuItem 
          onClick={handleDeleteRun}
          disabled={deleting}
          sx={{ color: 'error.main' }}
        >
          <Delete sx={{ mr: 1 }} />
          {deleting ? 'Deleting...' : 'Delete Run'}
        </MenuItem>
      </Menu>

      {/* Run Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={handleCloseDetails}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { height: '80vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Typography variant="h6">
              Manage Run: {run.name}
            </Typography>
            <Chip
              label={run.status}
              color={getStatusColor(run.status) as any}
              size="small"
            />
          </Box>
        </DialogTitle>

        <DialogContent sx={{ p: 0 }}>
          <Tabs
            value={selectedTab}
            onChange={handleTabChange}
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab icon={<CloudUpload />} label="Files" />
            <Tab icon={<PlayArrow />} label="Pipeline" />
            <Tab icon={<Assessment />} label="Results" />
          </Tabs>

          <Box sx={{ p: 3 }}>
            {selectedTab === 0 && (
              <Box>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Upload your paired-end FASTQ files (ending with _1.fq.gz and _2.fq.gz). Files will be stored in the run directory.
                </Alert>
                <FileUpload
                  runId={run.run_id}
                  onUploadComplete={onUpdate}
                />
              </Box>
            )}

            {selectedTab === 1 && (
              <Box>
                <StageControls
                  run={run}
                  onUpdate={onUpdate}
                />
              </Box>
            )}

            {selectedTab === 2 && (
              <Box>
                <Alert severity="info" sx={{ mb: 2 }}>
                  View quality control reports, read counts, and differential expression analysis results. Download data files as needed.
                </Alert>
                <QCResults run={run} onUpdate={onUpdate} />
                <Box sx={{ mt: 3 }}>
                  <FeatureCountsResults run={run} />
                </Box>
                <Box sx={{ mt: 3 }}>
                  <DESeq2Results runId={run.run_id} />
                </Box>
              </Box>
            )}
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleCloseDetails}>Close</Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default RunCard;