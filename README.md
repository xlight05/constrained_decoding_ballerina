# Constrained Decoding for Ballerina Language
Note: Still at very early stages of development. Spec is not complete. Not even close. Just a PoC. 


## Running the project
1. Clone the repository
2. Install llama.cpp and execute the following `llama-server -hf unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q4_K_XL`
3. Navigate to invoker and run `bal run`
4. Navigate to token-visualizer, run `npm install` and then `npm run dev` to visualize the token log probabilities.


## Spec builder 
This component is responsible for converting standard ballerina specification to GBNF format, which is used by llama-server for constrained decoding.

## Invoker
Invokes the llama-server with the given prompt with and without the grammar file and saves the log probabilities for comparison.

## token-visualizer
A simple tool to visualize the token log probabilities from the invoker component.
