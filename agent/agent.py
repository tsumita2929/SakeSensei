import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

try:  # pragma: no cover - exercised in integration tests
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    from bedrock_agentcore.runtime.context import BedrockAgentCoreContext
    from bedrock_agentcore.runtime.models import CUSTOM_HEADER_PREFIX
    from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole
    from bedrock_agentcore.memory.session import MemorySession, MemorySessionManager
except (ModuleNotFoundError, ImportError):  # pragma: no cover - lightweight fallback for unit tests
    class BedrockAgentCoreApp:  # type: ignore[misc]
        def entrypoint(self, func):
            return func

        def run(self, *_args, **_kwargs):
            raise RuntimeError("BedrockAgentCoreApp is unavailable in the test environment")

    class BedrockAgentCoreContext:  # type: ignore[misc]
        @classmethod
        def get_request_headers(cls):
            return {}

    CUSTOM_HEADER_PREFIX = "X-Amzn-Bedrock-AgentCore-Runtime-Custom-"  # type: ignore[assignment]

    @dataclass
    class ConversationalMessage:  # type: ignore[misc]
        text: str
        role: str

    class MessageRole:  # type: ignore[misc]
        USER = "USER"
        ASSISTANT = "ASSISTANT"

    class MemorySession:  # type: ignore[misc]
        def add_turns(self, *args, **kwargs):
            return None

        def get_last_k_turns(self, k: int = 20):
            return []

    class MemorySessionManager:  # type: ignore[misc]
        def __init__(self, *args, **kwargs):
            pass

        def create_memory_session(self, *args, **kwargs):
            return MemorySession()

try:  # pragma: no cover - integration helpers
    from bedrock_agentcore.memory.integrations.strands.config import (
        AgentCoreMemoryConfig,
        RetrievalConfig,
    )
    from bedrock_agentcore.memory.integrations.strands.session_manager import (
        AgentCoreMemorySessionManager,
    )
except (ModuleNotFoundError, ImportError):  # pragma: no cover - fallback for unit tests
    @dataclass
    class AgentCoreMemoryConfig:  # type: ignore[misc]
        memory_id: str
        actor_id: str
        session_id: str
        retrieval_config: Dict[str, Any]

    @dataclass
    class RetrievalConfig:  # type: ignore[misc]
        top_k: int
        relevance_score: float

    class AgentCoreMemorySessionManager:  # type: ignore[misc]
        def __init__(self, *_args, **_kwargs):
            pass
from sake_tools import ALL_TOOLS
from runtime_context import clear_runtime_context, set_runtime_context

# Enable .env usage for local smoke-testing. AgentCore runtime injects env vars.
load_dotenv()

app = BedrockAgentCoreApp()

REGION = os.getenv("AWS_REGION", "us-west-2")
MEMORY_ID = os.getenv("SAKE_AGENT_MEMORY_ID")
DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
DEFAULT_SYSTEM_PROMPT = """# Sake-Sensei (酒先生) システムプロンプト

**あなたは日本酒の専門家「Sake-Sensei（酒先生）」です。ユーザーの好みや要望に基づいて、最適な日本酒を推薦します。**

## 利用可能なツール
- `search_sake`: 名前、地域、種類、味わいで日本酒を検索
- `semantic_search`: 曖昧な表現や自然言語で意味的に類似した日本酒を検索
- `recommend_sake`: ユーザーの好みに基づいて日本酒を推薦
- `pairing_recommendation`: 料理の種類や名前から日本酒とのペアリングを提案
- `get_sake_details`: 特定の日本酒の詳細情報を取得
- `search_user_preferences`: ユーザーの過去の好みや会話履歴をMemoryから検索
- `fetch_sake_price`: Web上から最新の日本酒価格を取得

## 日本酒の専門知識

### 日本酒の種類と特徴
1. **吟醸酒**: 精米歩合60%以下、吟醸造り、固有の香味、色沢が良好
2. **大吟醸酒**: 精米歩合50%以下、吟醸造り、固有の香味、色沢が特に良好
3. **純米酒**: 米・米こうじ使用、香味・色沢が良好
4. **純米吟醸酒**: 精米歩合60%以下、吟醸造り、固有の香味、色沢が良好
5. **純米大吟醸酒**: 精米歩合50%以下、吟醸造り、固有の香味、色沢が特に良好
6. **特別純米酒**: 精米歩合60%以下または特別な製造方法、香味・色沢が特に良好
7. **本醸造酒**: 精米歩合70%以下、香味・色沢が良好
8. **特別本醸造酒**: 精米歩合60%以下または特別な製造方法、香味・色沢が特に良好
9. **にごり酒**: 粗くこして造られた日本酒、ソフトでなめらかな口当たり
10. **スパークリング日本酒**: 発泡性の日本酒、アルコール分が低めの製品もあり
11. **長期熟成酒**: 特徴的な香りとなめらかな口当たり、独自のカテゴリー
12. **生酒**: 通常日本酒は2回加熱殺菌を行うが、生酒は一度も加熱殺菌を行わない。フレッシュな香味が特徴

### 日本酒の飲用温度（表現と温度）
- **雪冷え（ゆきびえ）**: 5℃
- **花冷え（はなびえ）**: 10℃
- **涼冷え（すずびえ）**: 15℃
- **日向燗（ひなたかん）**: 30℃
- **人肌燗（ひとはだかん）**: 35℃
- **ぬる燗**: 40℃
- **上燗（じょうかん）**: 45℃
- **熱燗（あつかん）**: 50℃
- **飛び切り燗（とびきりかん）**: 55℃

**冷酒の適温**: 5℃～10℃
**燗酒の適温**: 35℃～50℃

## 重要な指示

### 1. 推薦依頼への対応
- 必ず最初に`search_user_preferences`ツールを使用してユーザーの過去の好みを確認
- long-term memory（抽出された好み）の情報を活用

### 2. 情報管理
- ユーザーが新しい好みを伝えた場合、その情報は自動的にMemoryに保存される
- 過去の会話履歴と現在の要望を総合的に判断

### 3. 検索戦略
- 曖昧な表現（例: "華やかで女性向け"、"爽やかで夏に飲みたい"）には`semantic_search`を使用
- 具体的な条件がある場合は`search_sake`を使用

### 4. 推薦時の説明
- 味わいの特徴（吟醸香、米の旨味、酸味、甘辛度など）を詳しく説明
- 料理との相性を具体的に提案
- 推奨する飲用温度を温度帯の名称と共に伝える

### 5. ペアリング提案
- `pairing_recommendation`を使用して最適な組み合わせを提案
- なぜその日本酒が料理に合うのか、味の相互作用を説明
- 温度帯による味わいの変化も考慮

### 6. 価格情報
- 必要に応じて`fetch_sake_price`で最新価格を取得
- 予算に応じた複数の選択肢を提示

### 7. 初心者対応
- 専門用語は平易な言葉で説明
- 精米歩合、アルコール度数、日本酒度などの数値の意味を分かりやすく解説

### 8. 対話的アプローチ
- ユーザーが迷っている場合、好みの味わい、飲むシチュエーション、予算などを質問
- 段階的に最適な日本酒に導く

### 9. 情熱的な伝達
- 日本酒の製造方法の違いによる味わいの特徴を熱く語る
- 季節や料理との楽しみ方を提案
- 酒米（米・米麹）とその他の原料による違いを説明

### 10. 総合的なアドバイス
- 保存方法（冷暗所での保管など）
- グラスや酒器による味わいの違い
- 開栓後の楽しみ方

**ユーザーに対して親切で丁寧に対応し、日本酒の奥深い世界を楽しく探求できるよう導いてください。**
"""


CUSTOM_ACTOR_HEADER = f"{CUSTOM_HEADER_PREFIX}Actor-Id"


def _build_memory_config(memory_id: str, actor_id: str, session_id: str) -> AgentCoreMemoryConfig:
    retrieval_config = {
        f"/users/{actor_id}/preferences": RetrievalConfig(top_k=5, relevance_score=0.5),
        f"/users/{actor_id}/facts": RetrievalConfig(top_k=5, relevance_score=0.5),
    }

    return AgentCoreMemoryConfig(
        memory_id=memory_id,
        actor_id=actor_id,
        session_id=session_id,
        retrieval_config=retrieval_config,
    )


def _create_session_manager(memory_id: str, actor_id: str, session_id: str) -> AgentCoreMemorySessionManager:
    memory_config = _build_memory_config(memory_id, actor_id, session_id)
    return AgentCoreMemorySessionManager(memory_config, REGION)


def create_agent(
    session_manager: AgentCoreMemorySessionManager,
    system_prompt: Optional[str] = None,
    model_id: Optional[str] = None,
) -> Agent:
    """Create a configured Strands agent for the Bedrock AgentCore runtime."""

    bedrock_model = BedrockModel(
        model_id=model_id or os.getenv("SAKE_AGENT_MODEL_ID", DEFAULT_MODEL_ID),
        temperature=0.7,
        region_name=REGION,
    )

    return Agent(
        model=bedrock_model,
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        session_manager=session_manager,
    )


def _resolve_actor_id(context: Any, payload: Dict[str, Any]) -> str:
    """Resolve actor_id from runtime headers with payload fallback."""

    header_sources = (
        getattr(context, "request_headers", None),
        getattr(context, "headers", None),  # backwards-compatible fallback
        BedrockAgentCoreContext.get_request_headers(),
    )

    for header_map in header_sources:
        if isinstance(header_map, dict):
            actor_id = header_map.get(CUSTOM_ACTOR_HEADER)
            if actor_id:
                return actor_id

    actor_id = payload.get("actor_id") or payload.get("actorId")
    return actor_id or "default_user"


def _resolve_session_id(context: Any, actor_id: str, payload: Dict[str, Any]) -> str:
    session_id = getattr(context, "session_id", None)
    if not session_id:
        session_id = payload.get("session_id") or payload.get("sessionId")

    return session_id or f"sake_session_{actor_id}"


def _resolve_memory_id(context: Any) -> Optional[str]:
    """Resolve the Memory ID from env or runtime metadata."""

    if MEMORY_ID:
        return MEMORY_ID

    candidates = [
        getattr(context, "memory_id", None),
        getattr(context, "memoryId", None),
    ]

    memory_info = getattr(context, "memory", None)
    if isinstance(memory_info, dict):
        candidates.extend(
            [
                memory_info.get("memoryId"),
                memory_info.get("id"),
            ]
        )

    for candidate in candidates:
        if candidate:
            return candidate

    return None


def get_memory_session(memory_id: str, actor_id: str, session_id: str) -> MemorySession:
    """Instantiate a MemorySession for direct event interactions."""

    if not memory_id:
        raise ValueError("memory_id is required to create a MemorySession")

    manager = MemorySessionManager(memory_id=memory_id, region_name=REGION)
    return manager.create_memory_session(actor_id=actor_id, session_id=session_id)


def save_conversation_to_memory(
    memory_id: str,
    actor_id: str,
    session_id: str,
    user_message: Optional[str],
    assistant_message: Optional[str],
) -> None:
    """Persist a user/assistant exchange, keeping turns isolated per role."""

    session = get_memory_session(memory_id, actor_id, session_id)

    if user_message:
        session.add_turns(
            messages=[ConversationalMessage(text=user_message, role=MessageRole.USER)]
        )

    if assistant_message:
        session.add_turns(
            messages=[ConversationalMessage(text=assistant_message, role=MessageRole.ASSISTANT)]
        )


def load_conversation_history(
    memory_id: str,
    actor_id: str,
    session_id: str,
    *,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """Fetch recent conversation turns as a flattened message list."""

    session = get_memory_session(memory_id, actor_id, session_id)
    turns = session.get_last_k_turns(k=max_results)

    history: List[Dict[str, Any]] = []
    for turn in turns:
        if isinstance(turn, list):
            history.extend(turn)
        elif isinstance(turn, dict):
            history.append(turn)

    return history


def _extract_prompt(payload: Dict[str, Any]) -> Optional[str]:
    prompt = payload.get("prompt") or payload.get("input")
    if isinstance(prompt, str):
        return prompt.strip() or None

    return None


def _format_response(agent_response: Any) -> Dict[str, Any]:
    message_text = ""

    try:
        message = getattr(agent_response, "message", agent_response)
        if isinstance(message, str):
            message_text = message
        elif hasattr(message, "content") and isinstance(message.content, list):
            for block in message.content:
                text = getattr(block, "text", None)
                if text:
                    message_text += text
        else:
            message_text = str(message)
    except Exception as parse_error:  # pragma: no cover - defensive
        message_text = f"応答の解析に失敗しました: {parse_error}"

    response: Dict[str, Any] = {"message": message_text or ""}

    metrics = getattr(agent_response, "metrics", None)
    if metrics:
        response["metrics"] = {
            "usage": getattr(metrics, "accumulated_usage", {}),
            "latency_ms": getattr(metrics, "accumulated_metrics", {}).get("latencyMs"),
        }

    return response


def _content_blocks_to_text(content: list[Dict[str, Any]]) -> str:
    """Concatenate plain-text blocks from structured model content."""

    text_parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        text = block.get("text")
        if isinstance(text, str):
            text_parts.append(text)

    return "".join(text_parts)


def _stringify_unknown(value: Any) -> Any:
    """Best-effort conversion of streaming payloads to JSON-serializable values."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    if isinstance(value, dict):
        return {key: _stringify_unknown(val) for key, val in value.items()}

    if isinstance(value, list):
        return [_stringify_unknown(item) for item in value]

    return str(value)


def _format_stream_event(
    event: Dict[str, Any],
    stream_state: Dict[str, Any],
) -> Dict[str, Any]:
    """Normalize Strands streaming events into consumable JSON payloads."""

    if not isinstance(event, dict):
        return {"type": "event", "payload": _stringify_unknown(event)}

    if "data" in event:
        chunk = event["data"]
        if isinstance(chunk, str):
            stream_state["message"] += chunk
        return {
            "type": "text-delta",
            "delta": _stringify_unknown(chunk),
        }

    current_tool = event.get("current_tool_use")
    if current_tool:
        return {
            "type": "tool",
            "tool": _stringify_unknown(current_tool),
        }

    if "message" in event and isinstance(event["message"], dict):
        message_content = event["message"].get("content", [])
        if isinstance(message_content, list):
            accumulated = _content_blocks_to_text(message_content)
            if accumulated:
                stream_state["message"] = accumulated
        return {
            "type": "message",
            "message": _stringify_unknown(event["message"]),
        }

    if "result" in event:
        formatted = _format_response(event["result"])
        if stream_state.get("message") and not formatted.get("message"):
            formatted["message"] = stream_state["message"]
        formatted["type"] = "final"
        return formatted

    if event.get("complete"):
        payload: Dict[str, Any] = {"type": "complete"}
        if stream_state.get("message"):
            payload["message"] = stream_state["message"]
        return payload

    if event.get("force_stop"):
        reason = event.get("force_stop_reason") or event.get("force_stop")
        return {
            "type": "force_stop",
            "reason": _stringify_unknown(reason),
        }

    if "error" in event:
        return {
            "type": "error",
            **_stringify_unknown(event),
        }

    return {
        "type": "event",
        "payload": _stringify_unknown(event),
    }


def main() -> None:
    """Interactive CLI loop for local smoke testing."""

    memory_id = os.getenv("SAKE_AGENT_MEMORY_ID")
    if not memory_id:
        raise RuntimeError("SAKE_AGENT_MEMORY_ID is required for CLI mode")

    actor_id = os.getenv("SAKE_AGENT_ACTOR_ID", "default_user")
    session_id = os.getenv("SAKE_AGENT_SESSION_ID", f"sake_session_{actor_id}")

    session_manager = _create_session_manager(memory_id, actor_id, session_id)
    memory_session = get_memory_session(memory_id, actor_id, session_id)
    agent_instance = create_agent(session_manager=session_manager)

    set_runtime_context(actor_id=actor_id, session_id=session_id)

    try:
        while True:
            user_input = input("ユーザー > ").strip()
            if not user_input:
                continue

            lowered = user_input.lower()
            if lowered in {"exit", "quit"}:
                print("Sake-Sensei > またお話ししましょう！")
                break

            memory_session.add_turns(
                messages=[ConversationalMessage(user_input, MessageRole.USER)]
            )

            agent_result = agent_instance(user_input)
            formatted = _format_response(agent_result)
            reply = formatted.get("message", "") or "申し訳ありません、応答を生成できませんでした。"

            print(f"Sake-Sensei > {reply}")

            memory_session.add_turns(
                messages=[ConversationalMessage(reply, MessageRole.ASSISTANT)]
            )
    finally:
        clear_runtime_context()


@app.entrypoint
async def invoke(payload: Dict[str, Any], context: Any) -> AsyncIterator[Dict[str, Any]]:
    prompt = _extract_prompt(payload)
    if not prompt:
        yield {"type": "error", "error": "A non-empty 'prompt' field is required."}
        return

    actor_id = _resolve_actor_id(context, payload)
    session_id = _resolve_session_id(context, actor_id, payload)
    memory_id = _resolve_memory_id(context)

    if not memory_id:
        yield {"type": "error", "error": "Memory is not configured for this runtime."}
        return

    session_manager = _create_session_manager(memory_id, actor_id, session_id)
    agent = create_agent(session_manager=session_manager)
    stream_state: Dict[str, Any] = {"message": ""}

    set_runtime_context(actor_id=actor_id, session_id=session_id)

    try:
        async for event in agent.stream_async(prompt):
            yield _format_stream_event(event, stream_state)
    finally:
        clear_runtime_context()


if __name__ == "__main__":  # pragma: no cover - local development entrypoint
    app.run()
