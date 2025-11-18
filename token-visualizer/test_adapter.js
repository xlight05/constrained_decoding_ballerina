
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { processTokenData } from './src/utils/dataAdapter.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to combined.json
const combinedPath = path.join(__dirname, 'public', 'combined.json');
const debugPath = path.join(__dirname, 'debug_response.json'); // We will copy this later or read from absolute path

// Validating combined.json
console.log(`Reading combined.json from ${combinedPath}`);
try {
    const rawData = fs.readFileSync(combinedPath, 'utf-8');
    const json = JSON.parse(rawData);
    const result = processTokenData(json);
    console.log("Processed " + result.length + " steps from combined.json.");
    if (result.length > 0 && result[0].token.text) {
        console.log("PASS: combined.json structure looks correct.");
    } else {
        console.error("FAIL: combined.json processing failed");
    }
} catch (e) {
    console.error("Error reading/processing combined.json:", e);
}

// Validating debug_response.json
const debugFullPath = path.join(__dirname, 'public', 'debug_response.json');
console.log(`Reading debug_response.json from ${debugFullPath}`);

try {
    const rawData = fs.readFileSync(debugFullPath, 'utf-8');
    const json = JSON.parse(rawData);
    const result = processTokenData(json);

    console.log("Processed " + result.length + " steps from debug_response.json.");
    if (result.length > 0) {
        console.log("First step sample:", JSON.stringify(result[0], null, 2));

        // Validation
        const first = result[0];
        // Note: debug_response tokens might not have ids or might be different
        if (typeof first.step !== 'number' || !first.token.text || typeof first.token.logprob !== 'number') {
            console.error("FAIL: debug_response.json structure mismatch");
            process.exit(1);
        }
        console.log("PASS: debug_response.json structure looks correct.");
    } else {
        console.error("FAIL: No steps found in debug_response.json");
        process.exit(1);
    }

} catch (e) {
    console.error("Error:", e);
    process.exit(1);
}
