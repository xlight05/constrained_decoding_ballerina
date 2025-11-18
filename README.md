# Constrained Decoding for Ballerina Language
Note: Still at very early stages of development.

## Spec builder 
This component is responsible for converting standard ballerina specification to GBNF format, which is used by llama-server for constrained decoding.

## Invoker
Invokes the llama-server with the given prompt with and without the grammar file.
