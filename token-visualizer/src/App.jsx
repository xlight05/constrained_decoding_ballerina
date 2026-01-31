
import React, { useState } from 'react';
import { Container, Grid, Typography, CircularProgress, Alert, Paper, Box, CssBaseline, ThemeProvider, createTheme, RadioGroup, FormControlLabel, Radio, FormControl, FormLabel } from '@mui/material';
import { useTokenTrace } from './hooks/useTokenTrace';
import TokenStream from './components/TokenStream';
import TokenDetail from './components/TokenDetail';

const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#6366f1', // Indigo 500
      light: '#818cf8',
      dark: '#4f46e5',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f8fafc', // Slate 50
      paper: '#ffffff',
    },
    text: {
      primary: '#0f172a', // Slate 900
      secondary: '#64748b', // Slate 500
    },
    divider: '#e2e8f0', // Slate 200
  },
  typography: {
    fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    h4: {
      fontWeight: 700,
      letterSpacing: '-0.02em',
      color: '#0f172a',
    },
    h6: {
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: '0px 1px 3px rgba(0,0,0,0.05), 0px 5px 15px rgba(0,0,0,0.02)',
        },
        elevation3: {
          boxShadow: '0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px -1px rgba(0, 0, 0, 0.06)',
        }
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
        }
      }
    }
  },
});

const ITERATIONS = [
  { id: 'no-grammar', label: 'No Grammar', file: '/no-grammar.json' },
  { id: 'with-grammar', label: 'With Grammar', file: '/with-grammar.json' },
  { id: 'with-prefill', label: 'With Prefill', file: '/with-prefill.json' },
  { id: 'with-prefill-no-expr', label: 'Without Expression', file: '/with-prefill-no-expr.json' },
];

function App() {
  const [selectedIteration, setSelectedIteration] = useState(ITERATIONS[0].id);
  const [selectedTokenIndex, setSelectedTokenIndex] = useState(null);

  const currentIterationFile = ITERATIONS.find(iter => iter.id === selectedIteration)?.file || ITERATIONS[0].file;
  const { data, loading, error } = useTokenTrace(currentIterationFile);

  const handleSelectToken = (index) => {
    setSelectedTokenIndex(index);
  };

  const handleIterationChange = (event) => {
    setSelectedIteration(event.target.value);
    setSelectedTokenIndex(null); // Reset selected token when changing iterations
  };

  const selectedStep = data && selectedTokenIndex !== null ? data[selectedTokenIndex] : null;

  return (
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Container maxWidth="xl" sx={{ flexGrow: 1, py: 2, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                LLM <Typography component="span" variant="h4" color="primary" sx={{ fontWeight: 700 }}>Token Visualizer</Typography>
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
                Inspect generation steps and token probabilities
              </Typography>
            </Box>

            <Paper elevation={0} sx={{ p: '4px', border: '1px solid', borderColor: 'divider', bgcolor: 'background.paper', borderRadius: 3 }}>
              <RadioGroup
                row
                value={selectedIteration}
                onChange={handleIterationChange}
                sx={{ px: 1 }}
              >
                {ITERATIONS.map((iteration) => (
                  <FormControlLabel
                    key={iteration.id}
                    value={iteration.id}
                    control={<Radio size="small" />}
                    label={<Typography variant="body2" fontWeight={500}>{iteration.label}</Typography>}
                    sx={{ mr: 2, '&:last-child': { mr: 0 } }}
                  />
                ))}
              </RadioGroup>
            </Paper>
          </Box>

          {loading && (
            <Box display="flex" justifyContent="center" my={8}>
              <CircularProgress />
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error.message}
            </Alert>
          )}

          {!loading && !error && data && (
            <Box sx={{ flexGrow: 1, minHeight: 0, display: 'flex', gap: 3, flexDirection: { xs: 'column', md: 'row' } }}>
              {/* Left Panel: Token Stream */}
              <Box sx={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', minHeight: '600px', minWidth: 0 }}>
                <Paper elevation={3} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid', borderColor: 'divider' }}>
                  <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.default', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" sx={{ fontSize: '1rem' }}>Generated Output</Typography>
                    <Typography variant="caption" sx={{ bgcolor: 'primary.main', color: 'white', px: 1, py: 0.5, borderRadius: 1, fontWeight: 600 }}>
                      {data.length} TOKENS
                    </Typography>
                  </Box>
                  <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', bgcolor: 'white' }}>
                    <TokenStream
                      steps={data}
                      onSelectToken={handleSelectToken}
                      selectedIndex={selectedTokenIndex}
                    />
                  </Box>
                </Paper>
              </Box>

              {/* Right Panel: Token Details */}
              <Box sx={{ width: { xs: '100%', md: '380px' }, height: '100%', minHeight: '600px', flexShrink: 0 }}>
                <Paper elevation={3} sx={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column', border: '1px solid', borderColor: 'divider' }}>
                  <TokenDetail step={selectedStep} />
                </Paper>
              </Box>
            </Box>
          )}
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
