import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Box,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Add, Refresh } from '@mui/icons-material';
import { api, RunInfo } from '../api/client';
import CreateRunDialog from './CreateRunDialog';
import RunCard from './RunCard';

const Dashboard: React.FC = () => {
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [healthStatus, setHealthStatus] = useState<string>('unknown');
  const [userInfo, setUserInfo] = useState<{ computing_id: string } | null>(null);
  const [storageInfo, setStorageInfo] = useState<{ data_directory: string } | null>(null);

  const loadRuns = async () => {
    try {
      setLoading(true);
      const runsData = await api.getRuns();
      setRuns(runsData);
      setError(null);
    } catch (err) {
      setError('Failed to load runs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadUserInfo = async () => {
    try {
      const info = await api.getUserInfo();
      setUserInfo(info);
    } catch (err) {
      console.error('Failed to load user info:', err);
    }
  };

  const loadStorageInfo = async () => {
    try {
      const info = await api.getStorageInfo();
      setStorageInfo(info);
    } catch (err) {
      console.error('Failed to load storage info:', err);
    }
  };

  const checkHealth = async () => {
    try {
      const health = await api.health();
      setHealthStatus(health.status);
    } catch (err) {
      setHealthStatus('unhealthy');
    }
  };

  useEffect(() => {
    loadRuns();
    checkHealth();
    loadUserInfo();
    loadStorageInfo();
  }, []);

  const handleCreateRun = () => {
    setCreateDialogOpen(true);
  };

  const handleRunCreated = () => {
    setCreateDialogOpen(false);
    loadRuns();
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

  return (
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1">
            ExpressDiff Pipeline Dashboard
          </Typography>
          {userInfo && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Computing ID: <strong>{userInfo.computing_id}</strong>
            </Typography>
          )}
          {storageInfo && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Working Directory: <strong>{storageInfo.data_directory}</strong>
            </Typography>
          )}
        </Box>
        </Box>
        <Box display="flex" alignItems="center" gap={2}>
          <Chip
            label={`Backend: ${healthStatus}`}
            color={healthStatus === 'healthy' ? 'success' : 'error'}
            size="small"
          />
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadRuns}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleCreateRun}
          >
            New Run
          </Button>
        </Box>
      </Box>

      {/* Welcome Section */}
      <Card sx={{ mb: 3, bgcolor: 'primary.50' }}>
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom color="primary.main">
            Welcome to ExpressDiff
          </Typography>
          <Typography variant="body1" paragraph>
            ExpressDiff is an automated RNA-seq differential expression analysis pipeline that runs on HPC infrastructure. 
            The pipeline performs quality control, read trimming, genome alignment, feature quantification, and differential expression analysis.
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            <strong>Quick Start:</strong> Click "New Run" to create a pipeline run. Select your allocation, upload FASTQ files, 
            configure pipeline stages, and submit jobs to SLURM. Monitor progress in the Pipeline tab and view results in the Results tab.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
            <strong>Support:</strong> For questions, issues, or assistance, contact{' '}
            <a href="mailto:vth3bk@virginia.edu" style={{ color: 'inherit', textDecoration: 'underline' }}>
              vth3bk@virginia.edu
            </a>
          </Typography>
        </Box>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Runs Grid */}
      {!loading && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: 3 }}>
          {runs.length === 0 ? (
            <Box sx={{ gridColumn: '1 / -1' }}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 6 }}>
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No pipeline runs found
                  </Typography>
                  <Typography variant="body2" color="text.secondary" mb={3}>
                    Create your first pipeline run to get started
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={handleCreateRun}
                  >
                    Create First Run
                  </Button>
                </CardContent>
              </Card>
            </Box>
          ) : (
            runs.map((run) => (
              <RunCard key={run.run_id} run={run} onUpdate={loadRuns} />
            ))
          )}
        </Box>
      )}

      {/* Create Run Dialog */}
      <CreateRunDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={handleRunCreated}
      />
    </Container>
  );
};

export default Dashboard;