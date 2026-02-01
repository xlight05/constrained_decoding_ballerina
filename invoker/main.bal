import ballerina/io;

string prompt = "Write an app to print from 0 to 10 in ballerina";

public function main() returns error? {
    string rawGbnf = check io:fileReadString("../spec_builder/grammars/spec.gbnf");
    string noExprGbnf = check io:fileReadString("../spec_builder/grammars/spec_no_expr.gbnf");

    // Generate without grammar
    string resultNoGrammar = check generateWithoutGrammar(prompt);
    io:println("=== Result without Grammar ===");
    io:println(resultNoGrammar);

    // Generate with raw GBNF grammar without prefill
    string resultRawGrammar = check generateWithRawGrammar(prompt, rawGbnf, false, "../token-visualizer/public/with-grammar.json");
    io:println("=== Result with Raw Grammar (without prefill) ===");
    io:println(resultRawGrammar);

    // Generate with raw GBNF grammar with prefill
    string resultRawGrammarPrefill = check generateWithRawGrammar(prompt, rawGbnf, true, "../token-visualizer/public/with-prefill.json");
    io:println("=== Result with Raw Grammar (with prefill) ===");
    io:println(resultRawGrammarPrefill);

    // Generate with no expr GBNF grammar with prefill
    string resultNoExprGrammarPrefill = check generateWithRawGrammar(prompt, noExprGbnf, true, "../token-visualizer/public/with-prefill-no-expr.json");
    io:println("=== Result with No Expr Grammar (with prefill) ===");
    io:println(resultNoExprGrammarPrefill);
}
