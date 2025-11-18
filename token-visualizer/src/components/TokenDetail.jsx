
import React from 'react';
import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip } from '@mui/material';

const TokenDetail = ({ step }) => {
    if (!step) {
        return (
            <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                <Typography variant="body1">Select a token to view details</Typography>
            </Box>
        );
    }

    const { token, api_top_logprobs } = step;

    return (
        <Paper elevation={0} sx={{ p: 0, height: '100%', overflowY: 'auto', bgcolor: 'transparent' }}>
            <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.paper' }}>
                <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.05em' }} display="block" gutterBottom>
                    Selected Token
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 1 }}>
                    <Chip
                        label={token?.text === '\n' ? '↵' : (token?.text || 'ID:' + token?.id)}
                        color="primary"
                        sx={{
                            borderRadius: '8px',
                            fontSize: '1.1rem',
                            height: 'auto',
                            py: 1,
                            px: 1,
                            fontFamily: "'JetBrains Mono', monospace",
                            boxShadow: '0px 2px 4px rgba(99, 102, 241, 0.2)'
                        }}
                    />
                    <Box>
                        <Typography variant="h5" sx={{ fontWeight: 700, lineHeight: 1.2 }}>Step {step.step}</Typography>
                        <Typography variant="body2" color="text.secondary" fontFamily="monospace">ID: {token?.id}</Typography>
                    </Box>
                </Box>
                <Box sx={{ mt: 2, display: 'flex', gap: 3 }}>
                    <Box>
                        <Typography variant="caption" color="text.secondary" display="block">Logprob</Typography>
                        <Typography variant="body1" fontWeight={600}>{token?.logprob?.toFixed(4)}</Typography>
                    </Box>
                    <Box>
                        <Typography variant="caption" color="text.secondary" display="block">Probability</Typography>
                        <Typography variant="body1" fontWeight={600} color="success.main">
                            {Math.exp(token?.logprob > -0.000001 ? 0 : token?.logprob).toFixed(2)}%
                        </Typography>
                    </Box>
                </Box>
            </Box>

            <Box sx={{ p: 0 }}>
                <Box sx={{ px: 3, py: 2, bgcolor: 'background.default', borderBottom: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                        Top Candidates
                    </Typography>
                </Box>

                <TableContainer elevation={0} sx={{ bgcolor: 'transparent' }}>
                    <Table size="small" sx={{ '& .MuiTableCell-root': { borderBottom: '1px solid', borderColor: 'divider' } }}>
                        <TableHead>
                            <TableRow sx={{ '& th': { fontWeight: 600, color: 'text.secondary', bgcolor: 'background.paper' } }}>
                                <TableCell>Token</TableCell>
                                <TableCell>ID</TableCell>
                                <TableCell align="right">Logprob</TableCell>
                                <TableCell align="right">Prob (%)</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {api_top_logprobs?.map((cand, idx) => {
                                const isSelected = cand.id === token?.id;
                                const prob = Math.exp(cand.logprob) * 100;
                                return (
                                    <TableRow
                                        key={idx}
                                        sx={{
                                            bgcolor: isSelected ? 'primary.50' : 'inherit',
                                            '&:hover': { bgcolor: isSelected ? 'primary.100' : 'action.hover' },
                                            transition: 'background-color 0.1s'
                                        }}
                                    >
                                        <TableCell component="th" scope="row" sx={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 500 }}>
                                            {cand.token === '\n' ? '↵' : (cand.token?.replace(/\n/g, '\\n') || '<empty>')}
                                        </TableCell>
                                        <TableCell sx={{ color: 'text.secondary', fontSize: '0.85rem' }}>{cand.id}</TableCell>
                                        <TableCell align="right" sx={{ fontFamily: 'monospace' }}>{cand.logprob?.toFixed(4)}</TableCell>
                                        <TableCell align="right" sx={{ fontWeight: 500 }}>{prob.toFixed(2)}%</TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </TableContainer>

                {!api_top_logprobs?.find(c => c.id === token?.id) && (
                    <Box sx={{ m: 3, p: 2, bgcolor: 'warning.50', color: 'warning.dark', borderRadius: 2, border: '1px solid', borderColor: 'warning.200' }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            Selected token was not in top {api_top_logprobs?.length || 0} candidates.
                        </Typography>
                    </Box>
                )}
            </Box>
        </Paper>
    );
};

export default TokenDetail;
