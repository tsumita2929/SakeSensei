# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sake-Sensei (酒先生) is an AI agent that recommends Japanese sake based on user preferences and queries. It combines AWS Bedrock Knowledge Base for sake data retrieval, AgentCore Memory for long-term user preference storage, and AgentCore Browser for real-time price scraping.

## Most Important

Always activate the managed virtual environment first: `source .venv/bin/activate`.
When updating Strands or AgentCore integrations, always route requests through the MCP server to pull the latest information and verify specifications.
Test Code should be store in test/

## Development Commands

### Setup

```bash
# Install dependencies
pip install -e .
playwright install chromium

# Check environment variables
cat .env
```

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_agent_memory_turn.py

# Run with unittest
python -m unittest tests.test_agent_memory_turn
```

### Running the Agent

```bash
python agent.py
```

### Data Management

```bash
# Upload sake data to S3
aws s3 cp data/sake_data.json s3://sake-sensei-kb-data-<your-aws-account-id>-us-west-2/

# Sync Knowledge Base (replace <DATA_SOURCE_ID>)
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id YEYBYYQ5GL \
  --data-source-id <DATA_SOURCE_ID>
```

## Architecture

### Core Components

**agent.py** - Main agent loop

- Initializes Bedrock Sonnet 4.5 model
- Manages AgentCore Memory session (actor_id: "default_user", session_id: "sake_recommendation_session")
- Orchestrates conversation flow with automatic memory persistence
- User and assistant messages are saved to Memory separately (one add_turns call per message)

**sake_tools.py** - Tool implementations (7 tools)

1. `search_sake` - Attribute-based search using Bedrock Knowledge Base metadata filters
2. `semantic_search` - Natural language vector search
3. `recommend_sake` - Combines Memory search with Knowledge Base retrieval for personalized recommendations
4. `pairing_recommendation` - Food pairing suggestions
5. `get_sake_details` - Detailed information for specific sake
6. `search_user_preferences` - Searches both long-term and short-term memories using flexible API introspection
7. `fetch_sake_price` - Web scraping via AgentCore Browser (Amazon.co.jp)

### Memory Architecture

Memory is persisted through `MemorySessionManager`:

- User messages saved immediately after input
- Assistant responses saved after agent execution
- Messages are saved individually (not batched)
- Fallback mechanism attempts to save both messages if error occurs during conversation turn

### Data Storage

- **Sake data**: Individual JSON files in `data/` directory (sake_00001.json, sake_00002.json, etc.)
- **Knowledge Base**: AWS Bedrock KB (ID: YEYBYYQ5GL) with S3 bucket for source data
- **Memory**: AgentCore Memory (ID: SakeSenseiMemory-Zo07hdGKva)

### Environment Variables

Required variables (see `.env.example`):

- `AWS_REGION` - AWS region (us-west-2)
- `SAKE_AGENT_KB_ID` - Bedrock Knowledge Base ID
- `SAKE_AGENT_MEMORY_ID` - AgentCore Memory ID
- `SAKE_KB_BUCKET` - S3 bucket for Knowledge Base data
- `SAKE_VECTOR_BUCKET` - S3 bucket for vectors
- `SAKE_VECTOR_INDEX` - Vector index name

## Key Implementation Details

### Tool Parameter Inspection

`search_user_preferences` uses Python's `inspect` module to dynamically check API signatures before calling Memory search methods. This handles different Memory SDK versions gracefully.

### Browser Session Management

`fetch_sake_price` manages browser contexts carefully:

- Reuses existing context if available
- Sets Japanese locale and timezone
- Configures cookies for Amazon.co.jp language preferences
- Closes page but not context to avoid breaking other operations

### Response Parsing

Agent responses are parsed with multiple fallback strategies:

- First checks for `.content` attribute with list of text blocks
- Falls back to string representation if needed
- Handles both structured Message objects and plain strings

### Test Infrastructure

Tests use extensive mocking to avoid external dependencies:

- Mock Strands Agent framework
- Mock Bedrock Memory SDK
- Mock dotenv loading
- Verify memory persistence behavior
