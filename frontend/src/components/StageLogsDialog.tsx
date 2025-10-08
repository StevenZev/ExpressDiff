import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
} from '@mui/material';
import { api, StageLogs } from '../api/client';

interface StageLogsDialogProps {
  open: boolean;
  onClose: () => void;
  runId: string;
  stage: string;
  stageName: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`log-tabpanel-${index}`}
      aria-labelledby={`log-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

export default function StageLogsDialog({
  open,
  onClose,
  runId,
  stage,
  stageName,
}: StageLogsDialogProps) {
  const [logs, setLogs] = useState<StageLogs | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    if (open) {
      loadLogs();
    }
  }, [open, runId, stage]);

  const loadLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getStageLogs(runId, stage);
      setLogs(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        {stageName} Logs
        {logs?.job_id && (
          <Typography variant="caption" display="block" color="text.secondary">
            Job ID: {logs.job_id}
          </Typography>
        )}
      </DialogTitle>
      <DialogContent dividers>
        {loading && (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && logs && (
          <>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label="Standard Output" id="log-tab-0" />
                <Tab label="Standard Error" id="log-tab-1" />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              {logs.stdout ? (
                <Box
                  component="pre"
                  sx={{
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    backgroundColor: 'grey.50',
                    p: 2,
                    borderRadius: 1,
                    overflow: 'auto',
                    maxHeight: '60vh',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {logs.stdout}
                </Box>
              ) : (
                <Alert severity="info">No standard output available.</Alert>
              )}
              {logs.stdout_file && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  File: {logs.stdout_file}
                </Typography>
              )}
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              {logs.stderr && logs.stderr !== "No error log found." ? (
                <Box
                  component="pre"
                  sx={{
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    backgroundColor: 'grey.50',
                    p: 2,
                    borderRadius: 1,
                    overflow: 'auto',
                    maxHeight: '60vh',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {logs.stderr}
                </Box>
              ) : (
                <Alert severity="success">No errors logged.</Alert>
              )}
              {logs.stderr_file && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  File: {logs.stderr_file}
                </Typography>
              )}
            </TabPanel>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={loadLogs} disabled={loading}>
          Refresh
        </Button>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
