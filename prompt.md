I have a gbnf spec(spec_builder/grammars/spec.gbnf) for ballerina. For a given prompt
  (write a ballerina app which prints 0 to 10) i wanna see which path in gbnf it took in
  the inference time. I'm running llama-server locally. I have the control over it. \
  \
  \
  my llamacpp clone is at /Users/wso2/llamacpp/llama.cpp. \
  \
  Make sure to pipe the logs to a file, then i need a proper way to visualzie those logs. I
  wanna see the probabability distrubtion for each case, and how spec influenced to go on
  different path based on this log file.

i want you to finish off logging in llama cpp, get the log, verify if it has everything,
  get the actual log by invoking the llama-server with grammar,  then write the func to
  retrive token, write test, then only move to ui stuff.



I want a to make an structured json for given json from the logs. you have to change the (tracer) implementaitno to make this json.

Example structured json:
[
  {
    "step": 1,
    "accepted_token": "The",
    "accepted_probability": 0.42,
    "all_tokens": [
      { "token": "The", "probability": 0.42 },
      { "token": "A", "probability": 0.31 },
      { "token": "An", "probability": 0.15 },
      { "token": "This", "probability": 0.08 },
      { "token": "That", "probability": 0.04 }
    ]
  },
  {
    "step": 2,
    "accepted_token": " quick",
    "accepted_probability": 0.37,
    "all_tokens": [
      { "token": " quick", "probability": 0.37 },
      { "token": " fast", "probability": 0.29 },
      { "token": " small", "probability": 0.18 },
      { "token": " lazy", "probability": 0.11 },
      { "token": " clever", "probability": 0.05 }
    ]
  },
  {
    "step": 3,
    "accepted_token": " brown",
    "accepted_probability": 0.46,
    "all_tokens": [
      { "token": " brown", "probability": 0.46 },
      { "token": " red", "probability": 0.21 },
      { "token": " black", "probability": 0.17 },
      { "token": " white", "probability": 0.09 },
      { "token": " gray", "probability": 0.07 }
    ]
  },
  {
    "step": 4,
    "accepted_token": " fox",
    "accepted_probability": 0.51,
    "all_tokens": [
      { "token": " fox", "probability": 0.51 },
      { "token": " dog", "probability": 0.26 },
      { "token": " cat", "probability": 0.13 },
      { "token": " wolf", "probability": 0.07 },
      { "token": " rabbit", "probability": 0.03 }
    ]
  }
]


This should be created from the tracer, write a test case to verify this funcitonality. 

if you dont have enough details in the log file, first see if its possible with llamacpp. if so you are free to modify llamacpp logs.


I have a gbnf spec(spec_builder/grammars/spec.gbnf) for ballerina. For a given prompt
  (write a ballerina app which prints 0 to 10) i wanna see which path in gbnf it took in
  the inference time. I'm running llama-server locally. I have the control over it. \
  \
  \
  my llamacpp clone is at /Users/wso2/llamacpp/llama.cpp. \
  \
  Make sure to pipe the logs to a file, then i need a proper way to visualzie those logs. I
  wanna see the probabability distrubtion for each case, and how spec influenced to go on
  different path based on this log file.

i want you to finish off logging in llama cpp, get the log, verify if it has everything,
  get the actual log by invoking the llama-server with grammar,  then write the func to
  retrive token, write test, then only move to ui stuff.



