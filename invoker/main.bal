import ballerina/http;
import ballerina/io;
import ballerina/lang.regexp;

type ChatMessage record {
    string role;         // "system" | "user" | "assistant"
    string content;
};

type ChatReq record {
    ChatMessage[]        messages;
    decimal?             temperature = 0.2;
    string              grammar?;

    // other llama.cpp knobs (supported by server):
    int                 max_tokens = 256;
    decimal             top_p?;
    int                 top_k?;
    decimal             logprobs?;
};

type Choice record {
    record {
        string role;
        string content;
    } message;
};

type ChatResp record {
    string id?;
    Choice[] choices;
};

string prompt = "Write an app to print from 0 to 10 in ballerina";
// string prompt = "Write an ballerina hello world main";

http:Client cl = check new ("http://localhost:8080/v1", timeout = 120);

# Build a templated grammar that wraps Ballerina code in markdown code blocks.
# Takes the spec.gbnf grammar, renames `root` to `ballerina-program`, 
# and injects it into the template.gbnf wrapper.
#
# + return - The combined GBNF grammar string or an error
function buildTemplatedGrammar() returns string|error {
    // Read the original Ballerina grammar
    string specGrammar = check io:fileReadString("../spec_builder/grammars/spec.gbnf");
    
    // Read the template grammar
    string templateGrammar = check io:fileReadString("template.gbnf");
    
    // Rename 'root ::=' to 'ballerina-program ::=' in the spec grammar
    regexp:RegExp rootPattern = re `root\s*::=`;
    string transformedGrammar = rootPattern.replace(specGrammar, "ballerina-program ::=");
    
    // Replace the placeholder with the transformed grammar
    regexp:RegExp placeholderPattern = re `\{BALLERINA_GRAMMAR\}`;
    string combinedGrammar = placeholderPattern.replace(templateGrammar, transformedGrammar);
    
    return combinedGrammar;
}

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
    check io:fileWriteJson("no-grammar.json", resp.toJson());
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

# Generate a response with the no-while GBNF grammar.
#
# + userPrompt - The user's prompt
# + grammar - The no-while GBNF grammar string
# + return - The generated content or an error
function generateWithNoWhileGrammar(string userPrompt, string grammar) returns string|error {
    ChatReq req = {
        messages: [
            {role: "user", content: userPrompt}
        ],
        grammar: grammar,
        max_tokens: 256,
        temperature: 0.0
        // logprobs: 50,
        // top_k: 100,
        // top_p: 1
    };
    ChatResp resp = check cl->post("/chat/completions", req);
    check io:fileWriteJson("grammar-without-while.json", resp.toJson());
    return resp.choices[0].message.content;
}

# Generate a response with the templated grammar (markdown wrapper).
#
# + userPrompt - The user's prompt
# + grammar - The templated GBNF grammar string
# + return - The generated content or an error
function generateWithTemplatedGrammar(string userPrompt, string grammar) returns string|error {
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

public function main() returns error? {
    // Load grammars
    // string templatedGbnf = check buildTemplatedGrammar();
    // string larkSpec = "%llguidance {}\n" + check io:fileReadString("../lark/spec.lark");
    string rawGbnf = check io:fileReadString("../spec_builder/grammars/spec.gbnf");
    string noExprGbnf = check io:fileReadString("../spec_builder/grammars/spec_no_expr.gbnf");

    // // Generate without grammar
    // string resultNoGrammar = check generateWithoutGrammar(prompt);
    // io:println("=== Result without Grammar ===");
    // io:println(resultNoGrammar);

    // // Generate with raw GBNF grammar without prefill
    // string resultRawGrammar = check generateWithRawGrammar(prompt, rawGbnf, false, "with-grammar.json");
    // io:println("=== Result with Raw Grammar (without prefill) ===");
    // io:println(resultRawGrammar);

    // // Generate with raw GBNF grammar with prefill
    // string resultRawGrammarPrefill = check generateWithRawGrammar(prompt, rawGbnf, true, "with-prefill.json");
    // io:println("=== Result with Raw Grammar (with prefill) ===");
    // io:println(resultRawGrammarPrefill);

    // Generate with no expr GBNF grammar with prefill
    string resultNoExprGrammarPrefill = check generateWithRawGrammar(prompt, noExprGbnf, false, "with-prefill-no-expr.json");
    io:println("=== Result with No Expr Grammar (with prefill) ===");
    io:println(resultNoExprGrammarPrefill);
}



