#!/bin/bash
# Sake Sensei - Clear All AgentCore Memory Data
# This script deletes all short-term (events) and long-term (records) memory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ -z "$AWS_REGION" ]; then
    AWS_REGION="us-west-2"
fi

MEMORY_ID=sake_sensei_agent_mem-jaGX86ECBZ
REGION=$AWS_REGION

echo -e "${YELLOW}┌──────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│   Sake Sensei Memory Cleanup Script     │${NC}"
echo -e "${YELLOW}└──────────────────────────────────────────┘${NC}"
echo ""
echo -e "Memory ID: ${GREEN}$MEMORY_ID${NC}"
echo -e "Region:    ${GREEN}$REGION${NC}"
echo ""

echo ""
echo -e "${GREEN}Starting memory cleanup...${NC}"
echo ""

# Function to delete events for a session with pagination
delete_session_events() {
    local actor_id=$1
    local session_id=$2

    echo -e "  ${YELLOW}→${NC} Deleting events for session: $session_id (actor: $actor_id)"

    local next_token=""
    local total_events=0

    while true; do
        # Build command with optional next-token
        local list_cmd="aws bedrock-agentcore list-events \
            --memory-id \"$MEMORY_ID\" \
            --actor-id \"$actor_id\" \
            --session-id \"$session_id\" \
            --region \"$REGION\" \
            --max-items 100 \
            --output json"

        if [ -n "$next_token" ]; then
            list_cmd="$list_cmd --starting-token \"$next_token\""
        fi

        # Get events
        local response=$(eval "$list_cmd" 2>/dev/null || echo '{"events":[]}')

        local events=$(echo "$response" | jq -r '.events // []')
        local batch_count=$(echo "$events" | jq -r 'length')

        if [ "$batch_count" -gt 0 ]; then
            echo "$events" | jq -r '.[] | .eventId' | while read -r event_id; do
                if [ -n "$event_id" ]; then
                    aws bedrock-agentcore delete-event \
                        --memory-id "$MEMORY_ID" \
                        --actor-id "$actor_id" \
                        --session-id "$session_id" \
                        --event-id "$event_id" \
                        --region "$REGION" \
                        --output json >/dev/null 2>&1 || true
                fi
            done

            total_events=$((total_events + batch_count))
        fi

        # Check for next page
        next_token=$(echo "$response" | jq -r '.NextToken // empty')
        if [ -z "$next_token" ]; then
            break
        fi
    done

    if [ "$total_events" -gt 0 ]; then
        echo -e "    ${GREEN}✓${NC} Deleted $total_events events"
    else
        echo -e "    ${YELLOW}○${NC} No events found"
    fi
}

# Step 1: Delete all short-term memory (events)
echo -e "${GREEN}[1/2] Deleting short-term memory (conversation events)...${NC}"
echo ""

# Function to get all actors with pagination
get_all_actors() {
    local next_token=""
    local all_actors=()

    while true; do
        local list_cmd="aws bedrock-agentcore list-actors \
            --memory-id \"$MEMORY_ID\" \
            --region \"$REGION\" \
            --max-items 100 \
            --output json"

        if [ -n "$next_token" ]; then
            list_cmd="$list_cmd --starting-token \"$next_token\""
        fi

        local response=$(eval "$list_cmd" 2>/dev/null || echo '{"actorSummaries":[]}')
        local actors=$(echo "$response" | jq -r '.actorSummaries // [] | .[] | .actorId')

        for actor in $actors; do
            all_actors+=("$actor")
        done

        next_token=$(echo "$response" | jq -r '.NextToken // empty')
        if [ -z "$next_token" ]; then
            break
        fi
    done

    printf '%s\n' "${all_actors[@]}"
}

# Function to process all sessions for an actor
process_actor_sessions() {
    local actor_id=$1
    local next_token=""
    local actor_session_count=0

    echo -e "${YELLOW}Processing actor:${NC} $actor_id"

    while true; do
        local list_cmd="aws bedrock-agentcore list-sessions \
            --memory-id \"$MEMORY_ID\" \
            --actor-id \"$actor_id\" \
            --region \"$REGION\" \
            --max-items 100 \
            --output json"

        if [ -n "$next_token" ]; then
            list_cmd="$list_cmd --starting-token \"$next_token\""
        fi

        local response=$(eval "$list_cmd" 2>/dev/null || echo '{"sessionSummaries":[]}')
        local sessions=$(echo "$response" | jq -r '.sessionSummaries // []')
        local batch_count=$(echo "$sessions" | jq -r 'length')

        if [ "$batch_count" -gt 0 ]; then
            echo "$sessions" | jq -r '.[] | .sessionId' | while read -r session_id; do
                if [ -n "$session_id" ]; then
                    delete_session_events "$actor_id" "$session_id"
                fi
            done

            actor_session_count=$((actor_session_count + batch_count))
        fi

        next_token=$(echo "$response" | jq -r '.NextToken // empty')
        if [ -z "$next_token" ]; then
            break
        fi
    done

    echo "$actor_session_count"
}

# Get all actors
echo "Finding all actors..."
actors=($(get_all_actors))
actor_count=${#actors[@]}

if [ "$actor_count" -gt 0 ]; then
    echo "Found $actor_count actor(s)"
    echo ""

    total_sessions=0
    for actor_id in "${actors[@]}"; do
        sessions=$(process_actor_sessions "$actor_id")
        total_sessions=$((total_sessions + sessions))
    done

    echo ""
    echo -e "${GREEN}✓ All short-term memory deleted (sessions: $total_sessions)${NC}"
else
    echo -e "${YELLOW}No actors found${NC}"
fi

session_count=$total_sessions

echo ""

# Step 2: Delete all long-term memory (records)
echo -e "${GREEN}[2/2] Deleting long-term memory (semantic records)...${NC}"
echo ""

# Function to delete records with pagination
delete_all_records() {
    local next_token=""
    local total_deleted=0

    while true; do
        # Build command with optional next-token
        local list_cmd="aws bedrock-agentcore list-memory-records \
            --memory-id \"$MEMORY_ID\" \
            --region \"$REGION\" \
            --namespace \"/\" \
            --max-items 100 \
            --output json"

        if [ -n "$next_token" ]; then
            list_cmd="$list_cmd --starting-token \"$next_token\""
        fi

        # Get records
        local response=$(eval "$list_cmd" 2>/dev/null || echo '{"memoryRecordSummaries":[]}')

        local records=$(echo "$response" | jq -r '.memoryRecordSummaries // []')
        local record_count=$(echo "$records" | jq -r 'length')

        if [ "$record_count" -gt 0 ]; then
            # Delete each memory record in this batch
            echo "$records" | jq -r '.[] | .memoryRecordId' | while read -r record_id; do
                if [ -n "$record_id" ]; then
                    echo -e "  ${YELLOW}→${NC} Deleting record: $record_id"
                    aws bedrock-agentcore delete-memory-record \
                        --memory-id "$MEMORY_ID" \
                        --memory-record-id "$record_id" \
                        --region "$REGION" \
                        --output json >/dev/null 2>&1 || true
                    echo -e "    ${GREEN}✓${NC} Deleted"
                fi
            done

            total_deleted=$((total_deleted + record_count))
        fi

        # Check for next page
        next_token=$(echo "$response" | jq -r '.NextToken // empty')
        if [ -z "$next_token" ]; then
            break
        fi
    done

    echo "$total_deleted"
}

total_records=$(delete_all_records)

if [ "$total_records" -gt 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All long-term memory deleted (total: $total_records)${NC}"
else
    echo -e "${YELLOW}No memory records found${NC}"
fi

echo ""
echo -e "${GREEN}┌──────────────────────────────────────────┐${NC}"
echo -e "${GREEN}│      Memory cleanup completed! ✓        │${NC}"
echo -e "${GREEN}└──────────────────────────────────────────┘${NC}"
echo ""
echo -e "Summary:"
echo -e "  - Sessions processed: ${GREEN}$session_count${NC}"
echo -e "  - Memory records deleted: ${GREEN}$total_records${NC}"
echo ""
