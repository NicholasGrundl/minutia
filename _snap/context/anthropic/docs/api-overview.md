# API Overview
The Claude API is a RESTful API at `https://api.anthropic.com` that provides programmatic access to Claude models. The primary API is the Messages API (`POST /v1/messages`) for conversational interactions.

To use the Claude API, you'll need an Anthropic Console account and an API key.

### Available APIs
*   **Messages API**: Send messages to Claude for conversational interactions (`POST /v1/messages`).
*   **Message Batches API**: Process large volumes of Messages requests asynchronously with a 50% cost reduction (`POST /v1/messages/batches`).
*   **Token Counting API**: Count tokens in a message before sending to manage costs and rate limits (`POST /v1/messages/count_tokens`).
*   **Models API**: List available Claude models and their details (`GET /v1/models`).

### Beta APIs
*   **Files API**: Upload and manage files for use across multiple API calls (`POST /v1/files`, `GET /v1/files`).
*   **Skills API**: Create and manage custom agent skills (`POST /v1/skills`, `GET /v1/skills`).

### Headers
All requests to the Claude API must include the following headers:
*   `x-api-key`: Your API key from Console (Required).
*   `anthropic-version`: API version (e.g., `2023-06-01`) (Required).
*   `content-type`: `application/json` (Required).

Anthropic provides official SDKs that simplify API integration by handling authentication, request formatting, error handling, and more.

Claude is available through Anthropic's direct API and through partner platforms like Amazon Bedrock, Google Cloud's Vertex AI, and Microsoft Azure.

### Limits
The API has different maximum request sizes depending on the endpoint:
*   Standard endpoints (Messages, Token Counting): 32 MB
*   Batch API: 256 MB
*   Files API: 500 MB

The Claude API includes `request-id` and `anthropic-organization-id` headers in every response.

The API enforces rate limits and spend limits to prevent misuse and manage capacity, organized into usage tiers that increase automatically.

### Basic Example (curl)
```bash
curl https://api.anthropic.com/v1/messages 
  --header "x-api-key: $ANTHROPIC_API_KEY" 
  --header "anthropic-version: 2023-06-01" 
  --header "content-type: application/json" 
  --data '{
    "model": "claude-opus-4-6",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Hello, Claude"}
    ]
  }'
```

### Response Example
```json
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I assist you today?"
    }
  ],
  "model": "claude-opus-4-6",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 12,
    "output_tokens": 8
  }
}
```
