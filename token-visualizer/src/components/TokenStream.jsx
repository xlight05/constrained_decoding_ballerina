
import React from 'react';
import { Box, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';

// Removed StreamContainer to simplify DOM and use clean Box


const TokenSpan = styled('span')(({ theme, selected, isSpecial }) => ({
    cursor: 'pointer',
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    fontSize: '14px',
    lineHeight: '24px', // Explicit line-height for alignment
    backgroundColor: selected
        ? theme.palette.primary.main
        : 'transparent',
    color: selected
        ? theme.palette.primary.contrastText
        : (isSpecial ? theme.palette.text.secondary : theme.palette.text.primary),
    borderRadius: '2px', // Tighter radius
    display: 'inline', // Reverting to inline to fix formatting flow
    padding: '0', // "without padding" as requested
    margin: '0', // Removing all margins to prevent artificial gaps
    whiteSpace: 'pre',

    // Border: dotted as requested
    border: selected
        ? `1px solid ${theme.palette.primary.main}`
        : '1px dotted rgba(0, 0, 0, 0.3)',


    '&:hover': {
        backgroundColor: selected ? theme.palette.primary.main : theme.palette.action.hover,
        textDecoration: 'none',
    },

    // Special styling for non-text tokens
    ...(isSpecial && {
        fontStyle: 'italic',
        fontSize: '0.85em',
        opacity: 0.7,
        userSelect: 'none', // Prevent selecting the placeholder text
    })
}));

const TokenStream = ({ steps, onSelectToken, selectedIndex }) => {
    return (
        <Box sx={{
            flexGrow: 1,
            overflowY: 'auto',
            height: '100%',
            backgroundColor: 'transparent', // Let parent control bg
        }}>
            <Box sx={{
                p: 3,
                fontFamily: "'JetBrains Mono', monospace",
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
                minHeight: '100%',
                bgcolor: 'background.paper',
            }}>
                {steps.map((step, index) => {
                    const rawText = step.token?.text;
                    const isNewline = rawText === '\n';
                    const isMissingText = !rawText && rawText !== '';

                    let content = rawText;
                    let isSpecial = false;

                    if (isMissingText) {
                        content = `‹ID:${step.token?.id}›`;
                        isSpecial = true;
                    } else if (rawText === '') {
                        content = '‹EPS›';
                        isSpecial = true;
                    }

                    // To make newline clickable:
                    const displayContent = isNewline ? (
                        <React.Fragment>
                            <span style={{ userSelect: 'none', opacity: 0.3, fontSize: '0.8em', marginRight: '2px' }}>↵</span>
                            {'\n'}
                        </React.Fragment>
                    ) : content;

                    return (
                        <Tooltip
                            key={index}
                            title={
                                <Box sx={{ p: 0.5 }}>
                                    <div style={{ fontWeight: 600, borderBottom: '1px solid rgba(255,255,255,0.2)', marginBottom: '4px', paddingBottom: '2px' }}>Step {step.step}</div>
                                    <div style={{ fontFamily: 'monospace' }}>ID: {step.token?.id}</div>
                                    <div style={{ fontFamily: 'monospace' }}>Logprob: {step.token?.logprob?.toFixed(4)}</div>
                                </Box>
                            }
                            arrow
                            placement="top"
                            disableInteractive // Better for rapid scanning
                        >
                            <TokenSpan
                                selected={index === selectedIndex}
                                isSpecial={isSpecial}
                                onClick={() => onSelectToken(index)}
                            >
                                {displayContent}
                            </TokenSpan>
                        </Tooltip>
                    );
                })}
            </Box>
        </Box>
    );
};

export default TokenStream;
