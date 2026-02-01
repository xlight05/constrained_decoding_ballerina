import ballerina/io;
import ballerina/http;

http:Client cl = check new ("http://localhost:8080/v1", timeout = 120);

# Generate a response without any grammar constraints.
#
# + userPrompt - The user's prompt
# + return - The generated content or an error
function generateWithoutGrammar(string userPrompt) returns string|error {
    ChatReq req = {
        messages: [
            {role: "user", content: userPrompt}
        ],
        max_tokens: 256,
        temperature: 0.0,
        logprobs: 5
    };
    ChatResp resp = check cl->post("/chat/completions", req);
    check io:fileWriteJson("../token-visualizer/public/no-grammar.json", resp.toJson());
    return resp.choices[0].message.content;
}

# Generate a response with the raw GBNF grammar (with while loops).
#
# + userPrompt - The user's prompt
# + grammar - The raw GBNF grammar string
# + return - The generated content or an error
function generateWithRawGrammar(string userPrompt, string grammar, boolean prefill, string outFile) returns string|error {
    ChatReq req = {
        messages: [
            {role: "user", content: userPrompt}
        ],
        grammar: grammar,
        max_tokens: 256,
        temperature: 0.0,
        logprobs: 10
    };
    if prefill {
        req.messages.push({role: "assistant", content: "<think>\nWe are going to write a Ballerina program that prints numbers from 0 to 10.\n We can use a for loop to iterate from 0 to 10 and print each number.\n In Ballerina, the range is inclusive of the start and exclusive of the end if we use the `to` keyword.\n So, we can do: for i in 0..10\n</think>Here's a Ballerina program that prints numbers from 0 to 10:\n```ballerina\n"});
    }
    ChatResp resp = check cl->post("/chat/completions", req);
    check io:fileWriteJson(outFile, resp.toJson());
    return resp.choices[0].message.content;
}

# Generate a response with the Lark grammar.
#
# + userPrompt - The user's prompt
# + grammar - The Lark grammar string
# + return - The generated content or an error
function generateWithLarkGrammar(string userPrompt, string grammar) returns string|error {
    ChatReq req = {
        messages: [
            {role: "user", content: userPrompt}
        ],
        grammar: grammar,
        max_tokens: 512,
        temperature: 0.0
    };
    ChatResp resp = check cl->post("/chat/completions", req);
    return resp.choices[0].message.content;
}
