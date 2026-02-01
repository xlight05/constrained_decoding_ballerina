//TODO: See why OpenAI connector logprobs is not working with llamacpp properly.
//Migrate to OpenAI instead of using http afterwards.

type ChatMessage record {
    string role; // "system" | "user" | "assistant"
    string content;
};

type ChatReq record {
    ChatMessage[] messages;
    decimal? temperature = 0.2;
    string grammar?;

    // other llama.cpp knobs (supported by server):
    int max_tokens = 256;
    decimal top_p?;
    int top_k?;
    decimal logprobs?;
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
