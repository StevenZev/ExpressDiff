import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Button,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Refresh,
} from '@mui/icons-material';
import { api } from '../api/client';

interface SampleValidationProps {
  runId: string;
}

interface SamplePair {
  sample_name: string;
  forward_file: string;
  reverse_file: string;
  valid: boolean;
  issues?: string[];
}

interface ValidationResult {
  total_files: number;
  valid_pairs: SamplePair[];
  unpaired_files: string[];
  issues: string[];
}

const SampleValidation: React.FC<SampleValidationProps> = ({ runId }) => {
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadValidation = async () => {
    try {
      setLoading(true);
      const result = await api.validateSamples(runId);
      // Transform the API response to match our interface
      setValidation(result as any);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to validate samples');
      console.error('Sample validation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadValidation();
  }, [runId]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" my={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button size="small" onClick={loadValidation}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  if (!validation) {
    return (
      <Alert severity="info">
        No files uploaded yet. Upload FASTQ files to see sample pairing validation.
      </Alert>
    );
  }

  const hasValidPairs = validation.valid_pairs.some(pair => pair.valid);
  const hasIssues = validation.issues.length > 0 || validation.unpaired_files.length > 0;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Sample Validation</Typography>
        <Button size="small" startIcon={<Refresh />} onClick={loadValidation}>
          Refresh
        </Button>
      </Box>

      {/* Summary */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" gap={2} mb={2}>
            <Chip
              icon={<CheckCircle />}
              label={`${validation.total_files} files`}
              color={validation.total_files > 0 ? 'primary' : 'default'}
              variant="outlined"
            />
            <Chip
              icon={<CheckCircle />}
              label={`${validation.valid_pairs.filter(p => p.valid).length} valid pairs`}
              color={hasValidPairs ? 'success' : 'default'}
              variant="outlined"
            />
            {hasIssues && (
              <Chip
                icon={<Warning />}
                label={`${validation.issues.length + validation.unpaired_files.length} issues`}
                color="warning"
                variant="outlined"
              />
            )}
          </Box>

          {validation.total_files === 0 && (
            <Alert severity="info">
              Upload FASTQ files (paired-end naming: *_1.fq.gz, *_2.fq.gz) to begin validation.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Issues */}
      {hasIssues && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Issues Found:
          </Typography>
          <List dense>
            {validation.issues.map((issue, index) => (
              <ListItem key={index} sx={{ py: 0 }}>
                <ListItemText primary={issue} />
              </ListItem>
            ))}
            {validation.unpaired_files.map((file, index) => (
              <ListItem key={`unpaired-${index}`} sx={{ py: 0 }}>
                <ListItemText primary={`Unpaired file: ${file}`} />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* Sample Pairs */}
      {validation.valid_pairs.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              Sample Pairs
            </Typography>
            <List dense>
              {validation.valid_pairs.map((pair, index) => (
                <ListItem key={index} divider={index < validation.valid_pairs.length - 1}>
                  <ListItemIcon>
                    {pair.valid ? (
                      <CheckCircle color="success" />
                    ) : (
                      <ErrorIcon color="error" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={pair.sample_name}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          Forward: {pair.forward_file}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Reverse: {pair.reverse_file}
                        </Typography>
                        {pair.issues && pair.issues.length > 0 && (
                          <Typography variant="caption" color="error" display="block">
                            Issues: {pair.issues.join(', ')}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default SampleValidation;