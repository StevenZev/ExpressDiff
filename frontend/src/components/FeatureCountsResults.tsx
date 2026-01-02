import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material';
import {
  CheckCircle,
} from '@mui/icons-material';
import { api, RunInfo } from '../api/client';

interface FeatureCountsResultsProps {
  run: RunInfo;
}

interface FeatureCountsStat {
  category: string;
  samples: Record<string, number>;
}

interface FeatureCountsSummary {
  summary: FeatureCountsStat[];
  sample_names: string[];
  file_path: string;
}

const FeatureCountsResults: React.FC<FeatureCountsResultsProps> = ({ run }) => {
  const [summary, setSummary] = useState<FeatureCountsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getFeatureCountsSummary(run.run_id);
      setSummary(data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load featureCounts summary:', err);
      if (err.response?.status === 404) {
        setError('featureCounts has not been run yet');
      } else {
        setError(`Failed to load summary: ${err.response?.data?.detail || err.message}`);
      }
    } finally {
      setLoading(false);
    }
  }, [run.run_id]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" py={4}>
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Loading featureCounts results...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!summary) {
    return null;
  }

  // Calculate totals and assignment rate
  const assignedRow = summary.summary.find(s => s.category === 'Assigned');
  const totalAssigned = assignedRow ? Object.values(assignedRow.samples).reduce((a, b) => a + b, 0) : 0;
  
  // Calculate total reads (sum of all categories for first sample)
  const firstSampleName = summary.sample_names[0];
  const totalReads = summary.summary.reduce((sum, stat) => {
    return sum + (stat.samples[firstSampleName] || 0);
  }, 0);

  const assignmentRate = totalReads > 0 ? (totalAssigned / totalReads * 100).toFixed(2) : '0.00';

  // Format large numbers with commas
  const formatNumber = (num: number) => num.toLocaleString();

  // Get color for assignment rate
  const getAssignmentColor = (rate: number) => {
    if (rate >= 60) return 'success';
    if (rate >= 40) return 'warning';
    return 'error';
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center">
            <CheckCircle color="success" sx={{ mr: 1 }} />
            <Typography variant="h6">
              featureCounts Summary
            </Typography>
          </Box>
          <Chip
            label={`${assignmentRate}% Assigned`}
            color={getAssignmentColor(parseFloat(assignmentRate))}
            size="small"
          />
        </Box>

        <Typography variant="body2" color="text.secondary" gutterBottom>
          Read assignment statistics from featureCounts analysis. 
          Higher assignment rates indicate better alignment quality and appropriate reference annotations.
        </Typography>

        <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                <TableCell><strong>Category</strong></TableCell>
                {summary.sample_names.map((sample) => (
                  <TableCell key={sample} align="right">
                    <strong>{sample}</strong>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {summary.summary.map((stat) => {
                const isAssigned = stat.category === 'Assigned';
                const isUnassigned = stat.category.startsWith('Unassigned_');
                
                return (
                  <TableRow 
                    key={stat.category}
                    sx={{
                      backgroundColor: isAssigned ? 'success.light' : 
                                     isUnassigned ? 'grey.50' : 'inherit',
                      '&:hover': { backgroundColor: 'action.hover' }
                    }}
                  >
                    <TableCell>
                      <Typography
                        variant="body2"
                        fontWeight={isAssigned ? 'bold' : 'normal'}
                        sx={{ 
                          color: isAssigned ? 'success.dark' : 'text.primary',
                          pl: isUnassigned ? 2 : 0
                        }}
                      >
                        {stat.category.replace('Unassigned_', '')}
                      </Typography>
                    </TableCell>
                    {summary.sample_names.map((sample) => (
                      <TableCell key={sample} align="right">
                        <Typography
                          variant="body2"
                          fontWeight={isAssigned ? 'bold' : 'normal'}
                        >
                          {formatNumber(stat.samples[sample])}
                        </Typography>
                      </TableCell>
                    ))}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>

        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="caption">
            <strong>Understanding the results:</strong>
            <br />• <strong>Assigned:</strong> Reads successfully assigned to genes
            <br />• <strong>Unassigned categories:</strong> Reasons why reads could not be assigned
            <br />• Higher "Assigned" counts indicate better data quality
            <br />• Common unassigned reasons: NoFeatures (intergenic), Ambiguity (multiple genes)
          </Typography>
        </Alert>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          File: {summary.file_path}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default FeatureCountsResults;
