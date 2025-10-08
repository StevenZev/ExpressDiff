import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Box,
  IconButton,
  Tooltip,
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { api, RunCreate } from '../api/client';

interface CreateRunDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const CreateRunDialog: React.FC<CreateRunDialogProps> = ({ open, onClose, onSuccess }) => {
  const [formData, setFormData] = useState<RunCreate>({
    name: '',
    description: '',
    account: '',
    adapter_type: 'NexteraPE-PE',
  });
  const [accounts, setAccounts] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingAccounts, setLoadingAccounts] = useState(false);

  useEffect(() => {
    if (open) {
      loadAccounts();
      // Reset form
      setFormData({
        name: '',
        description: '',
        account: '',
        adapter_type: 'NexteraPE-PE',
      });
      setError(null);
    }
  }, [open]);

  const loadAccounts = async () => {
    try {
      setLoadingAccounts(true);
      setError(null);
      const accountsData = await api.getAccounts();
      setAccounts(accountsData);
      
      // If no accounts returned, show a helpful message
      if (accountsData.length === 0) {
        setError('No allocations found. Make sure you have access to HPC allocations.');
      }
    } catch (err: any) {
      console.error('Failed to load accounts:', err);
      let errorMessage = 'Failed to load allocations';
      
      if (err.code === 'ECONNREFUSED' || err.message?.includes('Network Error')) {
        errorMessage = 'Cannot connect to backend. Make sure the server is running on port 8000.';
      } else if (err.response?.status === 500) {
        errorMessage = 'Backend error loading allocations. The allocations command can take up to 60 seconds.';
      } else if (err.response?.data?.detail) {
        errorMessage = `Backend error: ${err.response.data.detail}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoadingAccounts(false);
    }
  };

  const retryLoadAccounts = async () => {
    try {
      setLoadingAccounts(true);
      setError(null);
      const accountsData = await api.refreshAccounts();
      setAccounts(accountsData);
      
      // If no accounts returned, show a helpful message
      if (accountsData.length === 0) {
        setError('No allocations found. Make sure you have access to HPC allocations.');
      }
    } catch (err: any) {
      console.error('Failed to retry load accounts:', err);
      let errorMessage = 'Failed to load allocations';
      
      if (err.code === 'ECONNREFUSED' || err.message?.includes('Network Error')) {
        errorMessage = 'Cannot connect to backend. Make sure the server is running on port 8000.';
      } else if (err.response?.status === 500) {
        errorMessage = 'Backend error loading allocations. The allocations command can take up to 60 seconds.';
      } else if (err.response?.data?.detail) {
        errorMessage = `Backend error: ${err.response.data.detail}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoadingAccounts(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.account) {
      setError('Name and allocation are required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await api.createRun(formData);
      onSuccess();
    } catch (err) {
      setError('Failed to create run');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof RunCreate) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | any
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value,
    }));
  };

  const adapterTypes = [
    'NexteraPE-PE',
    'TruSeq2-PE',
    'TruSeq2-SE',
    'TruSeq3-PE',
    'TruSeq3-PE-2',
    'TruSeq3-SE',
  ];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>Create New Pipeline Run</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {/* Informational header */}
            <Alert severity="info" sx={{ mb: 2 }}>
              Set up a new RNA-seq analysis pipeline. You'll be able to upload FASTQ files and configure stages after creation.
            </Alert>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <TextField
              autoFocus
              margin="dense"
              label="Run Name"
              type="text"
              fullWidth
              variant="outlined"
              value={formData.name}
              onChange={handleInputChange('name')}
              required
              placeholder="e.g., mouse_liver_rnaseq"
              helperText="A unique identifier for this pipeline run"
              sx={{ mb: 2 }}
            />

            <TextField
              margin="dense"
              label="Description (Optional)"
              type="text"
              fullWidth
              variant="outlined"
              multiline
              rows={3}
              value={formData.description}
              onChange={handleInputChange('description')}
              placeholder="e.g., Differential expression analysis of wild-type vs knockout mice"
              helperText="Describe the experiment or analysis purpose"
              sx={{ mb: 2 }}
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                <InputLabel>Allocation *</InputLabel>
                <Tooltip title="Refresh allocations list">
                  <IconButton
                    size="small"
                    onClick={retryLoadAccounts}
                    disabled={loadingAccounts}
                    sx={{ mr: 1 }}
                  >
                    <Refresh fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              <Select
                value={formData.account}
                label="Allocation *"
                onChange={handleInputChange('account')}
                required
                disabled={loadingAccounts || accounts.length === 0}
              >
                {loadingAccounts ? (
                  <MenuItem disabled>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Querying HPC system... (may take up to 60 seconds)
                  </MenuItem>
                ) : accounts.length === 0 ? (
                  <MenuItem disabled>
                    No allocations available
                  </MenuItem>
                ) : (
                  accounts.map((account) => (
                    <MenuItem key={account} value={account}>
                      {account}
                    </MenuItem>
                  ))
                )}
              </Select>
              {!loadingAccounts && accounts.length > 0 && (
                <Box component="span" sx={{ mt: 0.5, fontSize: '0.75rem', color: 'text.secondary', display: 'block' }}>
                  Select the HPC allocation to charge compute resources to
                </Box>
              )}
              {loadingAccounts && (
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
                  <CircularProgress size={16} />
                  <span style={{ fontSize: '0.875rem' }}>
                    Querying HPC system for available allocations... This may take up to 60 seconds, please be patient.
                  </span>
                </Box>
              )}
              {accounts.length === 0 && !loadingAccounts && (
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Button
                    size="small"
                    onClick={retryLoadAccounts}
                    variant="outlined"
                  >
                    Retry Loading Allocations
                  </Button>
                </Box>
              )}
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Adapter Type</InputLabel>
              <Select
                value={formData.adapter_type}
                label="Adapter Type"
                onChange={handleInputChange('adapter_type')}
              >
                {adapterTypes.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </Select>
              <Box component="span" sx={{ mt: 0.5, fontSize: '0.75rem', color: 'text.secondary', display: 'block' }}>
                Sequencing adapter type for Trimmomatic (Nextera or TruSeq)
              </Box>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !formData.name.trim() || !formData.account}
          >
            {loading ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Creating...
              </>
            ) : (
              'Create Run'
            )}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default CreateRunDialog;