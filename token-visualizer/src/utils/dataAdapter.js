
/**
 * Adapts the raw JSON data into a normalized format for the UI.
 * 
 * Target Output Format (Array of objects):
 * {
 *   step: number,
 *   token: {
 *     text: string,
 *     id: number,
 *     logprob: number
 *   },
 *   api_top_logprobs: Array<{
 *     token: string,
 *     id: number,
 *     logprob: number
 *   }>
 * }
 */
export const processTokenData = (data) => {
    // Check if it's the old combined.json format
    if (data.steps && Array.isArray(data.steps)) {
        return data.steps.map(stepItem => ({
            step: stepItem.step,
            token: {
                text: stepItem.token.text,
                id: stepItem.token.id,
                logprob: stepItem.token.logprob
            },
            api_top_logprobs: stepItem.api_top_logprobs.map(cand => ({
                token: cand.token,
                id: cand.id,
                logprob: cand.logprob
            }))
        }));
    }

    // Check if it's the debug_response.json format (OpenAI-like logprobs)
    if (data.choices && data.choices[0] && data.choices[0].logprobs && data.choices[0].logprobs.content) {
        return data.choices[0].logprobs.content.map((item, index) => ({
            step: index,
            token: {
                text: item.token,
                id: item.id || -1, // debug_response.json content items have 'id' ? Let's check. Yes they do.
                logprob: item.logprob
            },
            api_top_logprobs: (item.top_logprobs || []).map(cand => ({
                token: cand.token,
                id: cand.id || -1,
                logprob: cand.logprob
            }))
        }));
    }

    // Default fallback or error
    console.warn("Unknown data format");
    return [];
};
