import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Card,
  CardContent,
  Button,
  Stack,
  Tooltip,
} from '@mui/material';
import {
  Download as DownloadIcon,
  TrendingUp as UpIcon,
  TrendingDown as DownIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { api } from '../api/client';

interface DESeq2ResultsProps {
  runId: string;
}

interface DEG {
  Geneid: string;
  baseMean: number;
  log2FoldChange: number;
  lfcSE: number;
  stat: number;
  pvalue: number;
  padj: number;
}

interface DESeq2Data {
  summary: {
    [key: string]: string;
  };
  significant_degs: DEG[];
  num_significant: number;
  available_files: {
    summary?: string;
    significant_degs?: string;
    full_results?: string;
    top_degs?: string;
    counts_matrix?: string;
  };
}

const DESeq2Results: React.FC<DESeq2ResultsProps> = ({ runId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DESeq2Data | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        setError(null);
        const results = await api.getDESeq2Results(runId);
        setData(results);
      } catch (err: any) {
        if (err.response?.status === 404) {
          setError('DESeq2 results not available. Run the DESeq2 Analysis stage first.');
        } else {
          setError(err.message || 'Failed to load DESeq2 results');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [runId]);

  const handleDownload = (fileType: string) => {
    const url = api.downloadDESeq2File(runId, fileType);
    window.open(url, '_blank');
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!data) {
    return null;
  }

  const getRegulationChip = (log2FC: number) => {
    if (log2FC > 0) {
      return (
        <Chip
          icon={<UpIcon />}
          label="Up"
          color="error"
          size="small"
          sx={{ fontWeight: 'bold' }}
        />
      );
    } else {
      return (
        <Chip
          icon={<DownIcon />}
          label="Down"
          color="primary"
          size="small"
          sx={{ fontWeight: 'bold' }}
        />
      );
    }
  };

  const formatPValue = (value: number): string => {
    if (value < 0.0001) {
      return value.toExponential(2);
    }
    return value.toFixed(4);
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" gutterBottom>
            DESeq2 Differential Expression Analysis
          </Typography>
          <Tooltip title="DESeq2 identifies genes with significant expression differences between conditions">
            <InfoIcon color="action" fontSize="small" />
          </Tooltip>
        </Box>

        {/* Summary Statistics */}
        <Box 
          sx={{ 
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' },
            gap: 2,
            mb: 3
          }}
        >
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                Comparison
              </Typography>
              <Typography variant="h6">
                {data.summary['Comparison'] || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                Total Genes
              </Typography>
              <Typography variant="h6">
                {data.summary['Total genes'] || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                Significant DEGs
              </Typography>
              <Typography variant="h6" color="primary">
                {data.num_significant}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                padj &lt; 0.05, |log2FC| &gt; 1
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                Regulation
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Chip
                  icon={<UpIcon />}
                  label={data.summary['Upregulated']?.replace(/\D/g, '') || '0'}
                  color="error"
                  size="small"
                />
                <Chip
                  icon={<DownIcon />}
                  label={data.summary['Downregulated']?.replace(/\D/g, '') || '0'}
                  color="primary"
                  size="small"
                />
              </Stack>
            </CardContent>
          </Card>
        </Box>

        {/* Download Buttons */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Download Results
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {data.available_files.significant_degs && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={() => handleDownload('significant_degs')}
              >
                Significant DEGs
              </Button>
            )}
            {data.available_files.full_results && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={() => handleDownload('full_results')}
              >
                All Results
              </Button>
            )}
            {data.available_files.top_degs && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={() => handleDownload('top_degs')}
              >
                Top 50 DEGs
              </Button>
            )}
            {data.available_files.counts_matrix && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={() => handleDownload('counts_matrix')}
              >
                Counts Matrix
              </Button>
            )}
            {data.available_files.summary && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={() => handleDownload('summary')}
              >
                Summary
              </Button>
            )}
          </Stack>
        </Box>

        {/* Significant DEGs Table */}
        {data.significant_degs && data.significant_degs.length > 0 ? (
          <>
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              Significant Differentially Expressed Genes
            </Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 500 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Gene ID</strong></TableCell>
                    <TableCell align="right"><strong>Base Mean</strong></TableCell>
                    <TableCell align="right">
                      <strong>log₂ Fold Change</strong>
                    </TableCell>
                    <TableCell align="center"><strong>Regulation</strong></TableCell>
                    <TableCell align="right"><strong>P-value</strong></TableCell>
                    <TableCell align="right"><strong>Adj. P-value</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.significant_degs.map((deg, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {deg.Geneid}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{deg.baseMean.toFixed(2)}</TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          fontWeight="bold"
                          color={deg.log2FoldChange > 0 ? 'error.main' : 'primary.main'}
                        >
                          {deg.log2FoldChange > 0 ? '+' : ''}
                          {deg.log2FoldChange.toFixed(3)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        {getRegulationChip(deg.log2FoldChange)}
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontFamily="monospace" fontSize="0.85rem">
                          {formatPValue(deg.pvalue)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontFamily="monospace" fontSize="0.85rem" fontWeight="bold">
                          {formatPValue(deg.padj)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        ) : (
          <Alert severity="info" sx={{ mt: 2 }}>
            No significant differentially expressed genes found with the current thresholds
            (padj &lt; 0.05, |log2FC| &gt; 1). Check the full results file for all genes.
          </Alert>
        )}
      </Paper>
    </Box>
  );
};

export default DESeq2Results;
