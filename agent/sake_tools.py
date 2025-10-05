"""
Sake Recommendation Tools

7つの日本酒推薦ツール:
1. search_sake: 属性ベースの検索
2. semantic_search: 自然言語によるセマンティック検索
3. recommend_sake: ユーザーの好みに基づく推薦
4. pairing_recommendation: 料理とのペアリング提案
5. get_sake_details: 特定の日本酒の詳細情報取得
6. search_user_preferences: ユーザーの過去の好みを検索
7. fetch_sake_price: Web上の最新価格を取得
"""

import os
import re
from urllib.parse import quote_plus

import boto3
from bedrock_agentcore.memory.session import MemorySessionManager
from bedrock_agentcore.tools.browser_client import browser_session
from playwright.sync_api import sync_playwright
from runtime_context import get_runtime_context
from strands import tool

# AWS Clients
bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime", region_name=os.getenv("AWS_REGION", "us-west-2")
)


def _resolve_identity(
    actor_id: str | None,
    session_id: str | None,
) -> tuple[str, str]:
    """Resolve actor/session identifiers from the invocation context."""

    runtime_context = get_runtime_context()
    resolved_actor = actor_id or os.getenv("SAKE_AGENT_ACTOR_ID") or runtime_context.actor_id
    resolved_session = (
        session_id or os.getenv("SAKE_AGENT_SESSION_ID") or runtime_context.session_id
    )
    return resolved_actor, resolved_session


@tool
def search_sake(
    name: str | None = None,
    region: str | None = None,
    sake_type: str | None = None,
    price_range: str | None = None,
) -> str:
    """名前、地域、種類、価格帯で日本酒を検索します。

    Args:
        name: 日本酒の名前（部分一致）
        region: 産地（例: 山口県、福井県、新潟県）
        sake_type: 種類（例: 純米大吟醸、純米吟醸、特別純米酒）
        price_range: 価格帯（低価格帯、中価格帯、高価格帯）
    """
    try:
        kb_id = os.getenv("SAKE_AGENT_KB_ID")
        if not kb_id:
            return "エラー: SAKE_AGENT_KB_IDが設定されていません"

        # クエリテキストの構築
        query_parts = []
        if name:
            query_parts.append(f"名前: {name}")
        if region:
            query_parts.append(f"地域: {region}")
        if sake_type:
            query_parts.append(f"種類: {sake_type}")
        if price_range:
            query_parts.append(f"価格帯: {price_range}")

        query_text = " ".join(query_parts) if query_parts else "日本酒"

        # メタデータフィルターの構築
        filters = []
        if region:
            filters.append({"equals": {"key": "region", "value": region}})
        if sake_type:
            filters.append({"equals": {"key": "type", "value": sake_type}})
        if price_range:
            filters.append({"equals": {"key": "price_range", "value": price_range}})

        # Bedrock Knowledge Base Retrieve API呼び出し
        retrieve_params = {
            "knowledgeBaseId": kb_id,
            "retrievalQuery": {"text": query_text},
            "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": 5}},
        }

        if filters:
            retrieve_params["retrievalConfiguration"]["vectorSearchConfiguration"]["filter"] = {
                "andAll": filters
            }

        response = bedrock_agent_runtime.retrieve(**retrieve_params)

        # 結果の整形
        results = []
        for item in response.get("retrievalResults", []):
            content = item.get("content", {}).get("text", "")
            score = item.get("score", 0)
            results.append(f"[関連度: {score:.2f}]\n{content}\n")

        if not results:
            return "検索条件に一致する日本酒が見つかりませんでした。"

        return "\n---\n".join(results)

    except Exception as e:
        return f"検索エラー: {str(e)}"


@tool
def semantic_search(query: str) -> str:
    """曖昧な表現や自然言語で日本酒を検索します。

    Args:
        query: 自然言語の検索クエリ（例: "華やかで女性向けの日本酒", "爽やかで夏に飲みたい"）
    """
    try:
        kb_id = os.getenv("SAKE_AGENT_KB_ID")
        if not kb_id:
            return "エラー: SAKE_AGENT_KB_IDが設定されていません"

        # Bedrock Knowledge Base Retrieve API呼び出し
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}},
        )

        # 結果の整形
        results = []
        for item in response.get("retrievalResults", []):
            content = item.get("content", {}).get("text", "")
            score = item.get("score", 0)
            results.append(f"[関連度: {score:.2f}]\n{content}\n")

        if not results:
            return "お探しの条件に合う日本酒が見つかりませんでした。"

        return "\n---\n".join(results)

    except Exception as e:
        return f"検索エラー: {str(e)}"


@tool
def recommend_sake(preferences: str | None = None) -> str:
    """ユーザーの好みに基づいて日本酒を推薦します。

    Args:
        preferences: ユーザーの好みの説明（任意）
    """
    try:
        # まず、Memoryからユーザーの過去の好みを検索
        memory_results = search_user_preferences("日本酒の好み 推薦")
        memory_error = memory_results.startswith("エラー:") or memory_results.startswith(
            "Memory検索エラー"
        )

        # 好みの情報を統合
        query_text = ""
        if not memory_error and "過去の好み情報は見つかりませんでした" not in memory_results:
            query_text += f"過去の好み: {memory_results}\n"

        if preferences:
            query_text += f"現在の好み: {preferences}"

        if not query_text:
            query_text = "おすすめの日本酒"

        # Knowledge Baseから推薦
        kb_id = os.getenv("SAKE_AGENT_KB_ID")
        if not kb_id:
            return "エラー: SAKE_AGENT_KB_IDが設定されていません"

        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query_text},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}},
        )

        # 結果の整形
        results = []
        for idx, item in enumerate(response.get("retrievalResults", []), 1):
            content = item.get("content", {}).get("text", "")
            score = item.get("score", 0)
            results.append(f"【推薦 {idx}】[関連度: {score:.2f}]\n{content}\n")

        if not results:
            return "おすすめの日本酒が見つかりませんでした。"

        recommendation = "\n---\n".join(results)

        # 過去の好み情報も含める（エラーメッセージや空の結果は除外）
        if (
            not memory_error
            and "過去の好み情報は見つかりませんでした" not in memory_results
            and memory_results.strip()
        ):
            recommendation = (
                f"【過去の好み情報】\n{memory_results}\n\n【推薦結果】\n{recommendation}"
            )

        return recommendation

    except Exception as e:
        return f"推薦エラー: {str(e)}"


@tool
def pairing_recommendation(dish: str) -> str:
    """料理の種類や名前から日本酒とのペアリングを提案します。

    Args:
        dish: 料理の種類や名前（例: "刺身", "すき焼き", "フレンチ"）
    """
    try:
        kb_id = os.getenv("SAKE_AGENT_KB_ID")
        if not kb_id:
            return "エラー: SAKE_AGENT_KB_IDが設定されていません"

        # 料理に関するクエリ
        query_text = f"{dish}に合う日本酒 ペアリング"

        # Bedrock Knowledge Base Retrieve API呼び出し
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query_text},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}},
        )

        # 結果の整形
        results = []
        for item in response.get("retrievalResults", []):
            content = item.get("content", {}).get("text", "")
            score = item.get("score", 0)

            # ペアリング情報を強調
            results.append(f"[適合度: {score:.2f}]\n{content}\n")

        if not results:
            return f"{dish}に合う日本酒が見つかりませんでした。"

        pairing_info = "\n---\n".join(results)
        return f"【{dish}とのペアリング提案】\n\n{pairing_info}"

    except Exception as e:
        return f"ペアリング検索エラー: {str(e)}"


@tool
def get_sake_details(sake_name: str) -> str:
    """特定の日本酒の詳細情報を取得します。

    Args:
        sake_name: 日本酒の名前
    """
    try:
        kb_id = os.getenv("SAKE_AGENT_KB_ID")
        if not kb_id:
            return "エラー: SAKE_AGENT_KB_IDが設定されていません"

        # Bedrock Knowledge Base Retrieve API呼び出し
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": sake_name},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 1}},
        )

        # 結果の取得
        results = response.get("retrievalResults", [])
        if not results:
            return f"{sake_name}の情報が見つかりませんでした。"

        content = results[0].get("content", {}).get("text", "")
        score = results[0].get("score", 0)

        return f"【{sake_name}の詳細情報】[関連度: {score:.2f}]\n\n{content}"

    except Exception as e:
        return f"詳細情報取得エラー: {str(e)}"


@tool
def search_user_preferences(
    query: str = "日本酒の好み",
    top_k: int = 5,
    actor_id: str | None = None,
    session_id: str | None = None,
    include_short_term: bool = True,
    include_semantic: bool = True,
) -> str:
    """ユーザーの過去の好みや重要な事実をAgentCore Memoryから検索します。

    Args:
        query: 検索クエリ
        top_k: 各カテゴリで取得する件数
        actor_id: 明示的にActor IDを指定したい場合
        session_id: 明示的にSession IDを指定したい場合
        include_short_term: 直近の短期記憶も補足として載せるか
        include_semantic: セマンティック抽出された事実を含めるか
    """
    try:
        memory_id = os.getenv("SAKE_AGENT_MEMORY_ID")
        if not memory_id:
            return "エラー: SAKE_AGENT_MEMORY_IDが設定されていません"

        resolved_actor_id, resolved_session_id = _resolve_identity(actor_id, session_id)

        session_manager = MemorySessionManager(
            memory_id=memory_id, region_name=os.getenv("AWS_REGION", "us-west-2")
        )

        session = session_manager.create_memory_session(
            actor_id=resolved_actor_id, session_id=resolved_session_id
        )

        def _extract_text(record) -> str | None:
            content = None
            if hasattr(record, "content"):
                content = record.content
            elif isinstance(record, dict):
                content = record.get("content", record)
            if isinstance(content, dict):
                return content.get("text") or str(content)
            if content is not None:
                return str(content)
            if hasattr(record, "text"):
                return str(record.text)
            return str(record) if record else None

        sections: list[str] = []

        def _collect_from_namespace(namespace: str, label: str) -> None:
            try:
                records = session.search_long_term_memories(
                    query=query, namespace_prefix=namespace, top_k=top_k
                )
            except Exception as search_error:
                print(f"⚠️  Long-term memory検索エラー ({namespace}): {search_error}")
                try:
                    records = session.list_long_term_memory_records(
                        namespace_prefix=namespace, max_results=top_k
                    )
                except Exception as list_error:
                    print(f"⚠️  List memory recordsエラー ({namespace}): {list_error}")
                    return

            extracted = []
            for record in records:
                text = _extract_text(record)
                if text:
                    extracted.append(text.strip())

            if extracted:
                sections.append(label)
                sections.extend(extracted[:top_k])

        _collect_from_namespace(
            namespace=f"/users/{resolved_actor_id}/preferences", label="【ユーザー嗜好】"
        )

        if include_semantic:
            _collect_from_namespace(
                namespace=f"/users/{resolved_actor_id}/facts", label="【セマンティック事実】"
            )

        if include_short_term:
            try:
                recent_turns = session.get_last_k_turns(k=top_k)
                extracted_turns = []
                for turn in recent_turns:
                    if hasattr(turn, "messages"):
                        texts = [
                            getattr(msg, "content", None)
                            for msg in turn.messages
                            if hasattr(msg, "content")
                        ]
                        merged = " ".join(str(text) for text in texts if text)
                        if merged:
                            extracted_turns.append(merged.strip())

                if extracted_turns:
                    sections.append("【最近の会話】")
                    sections.extend(extracted_turns[:top_k])

            except Exception as turns_error:
                print(f"⚠️  最近の会話取得エラー: {turns_error}")

        if not sections:
            return "過去の好み情報は見つかりませんでした。"

        return "\n".join(sections)

    except Exception as e:
        return f"Memory検索エラー: {str(e)}"


@tool
def fetch_sake_price(sake_name: str, screenshot_path: str | None = None) -> str:
    """Web検索を使って日本酒の最新価格情報を取得します。

    Args:
        sake_name: 日本酒の名前
        screenshot_path: スクリーンショットを保存するパス（オプション）
    """
    try:
        region = os.getenv("AWS_REGION", "us-west-2")

        # BedrockAgentCore Browserセッションを使用
        with browser_session(region) as client:
            ws_url, headers = client.generate_ws_headers()

            # Playwrightでブラウザ制御
            with sync_playwright() as playwright:
                chromium = playwright.chromium
                browser = chromium.connect_over_cdp(ws_url, headers=headers)

                page = None

                try:
                    # 新しいコンテキストを作成する場合のみ設定を適用
                    if not browser.contexts:
                        context = browser.new_context(
                            locale="ja-JP",
                            timezone_id="Asia/Tokyo",
                            geolocation={"latitude": 35.6762, "longitude": 139.6503},
                            permissions=["geolocation"],
                            extra_http_headers={"Accept-Language": "ja-JP,ja;q=0.9"},
                        )
                    else:
                        context = browser.contexts[0]

                    page = context.pages[0] if context.pages else context.new_page()

                    # Cookieを設定して言語を日本語に固定
                    page.context.add_cookies(
                        [
                            {
                                "name": "lc-acbjp",
                                "value": "ja_JP",
                                "domain": ".amazon.co.jp",
                                "path": "/",
                            },
                            {
                                "name": "i18n-prefs",
                                "value": "JPY",
                                "domain": ".amazon.co.jp",
                                "path": "/",
                            },
                        ]
                    )

                    # Amazon.co.jpで検索（言語パラメータを明示）
                    search_query = f"{sake_name} 日本酒"
                    encoded_query = quote_plus(search_query)
                    amazon_url = f"https://www.amazon.co.jp/s?k={encoded_query}&language=ja_JP"

                    page.goto(amazon_url, wait_until="load", timeout=30000)
                    page.wait_for_timeout(3000)

                    # スクリーンショットを取得（オプション）
                    if screenshot_path:
                        page.screenshot(path=screenshot_path, full_page=True)

                    # 検索結果から価格情報を抽出
                    price_results = []

                    # 商品アイテムを取得（最大5件）
                    items = page.query_selector_all('[data-component-type="s-search-result"]')[:5]

                    for idx, item in enumerate(items):
                        try:
                            # 商品名を取得（複数のセレクターを試す）
                            title = None
                            title_elem = item.query_selector("h2 span")
                            if not title_elem:
                                title_elem = item.query_selector("h2")
                            if title_elem:
                                title = title_elem.inner_text().strip()

                            if not title:
                                title = "不明"

                            # 価格を取得（複数の方法を試す）
                            price = None

                            # 方法1: 価格専用のセレクターで取得
                            price_whole = item.query_selector(".a-price-whole")
                            price_fraction = item.query_selector(".a-price-fraction")
                            if price_whole:
                                price_text = price_whole.inner_text().strip()
                                if price_fraction:
                                    price_text += price_fraction.inner_text().strip()
                                price = f"¥{price_text}"

                            # 方法2: テキストから正規表現で抽出
                            if not price:
                                item_text = item.inner_text()
                                # ¥（半角）または￥（全角）で始まる価格パターンを検索
                                price_match = re.search(r"[¥￥]\s*[\d,]+", item_text)
                                if price_match:
                                    price = price_match.group().replace(" ", "")

                            if not price:
                                price = "価格情報なし"

                            # URLを取得
                            url = ""
                            # まずh2内のaタグを試す
                            link_elem = item.query_selector("h2 a")
                            if not link_elem:
                                # 代替セレクター
                                link_elem = item.query_selector("a.a-link-normal")

                            if link_elem:
                                href = link_elem.get_attribute("href")
                                if href:
                                    if href.startswith("http"):
                                        url = href
                                    elif href.startswith("/"):
                                        url = f"https://www.amazon.co.jp{href}"
                                    else:
                                        url = f"https://www.amazon.co.jp/{href}"

                            if title != "不明":
                                price_results.append({"title": title, "price": price, "url": url})
                        except Exception:
                            continue

                    # 結果の整形
                    if not price_results:
                        return f"{sake_name}の価格情報が見つかりませんでした。"

                    formatted_results = [f"【{sake_name}の価格情報】\n"]
                    for idx, result in enumerate(price_results, 1):
                        formatted_results.append(
                            f"\n{idx}. {result['title']}\n"
                            f"   価格: {result['price']}\n"
                            f"   URL: {result['url']}"
                        )

                    return "\n".join(formatted_results)

                finally:
                    if page and not page.is_closed():
                        page.close()
                    browser.close()

    except Exception as e:
        return f"価格情報取得エラー: {str(e)}"


# すべてのツールをリストでエクスポート
ALL_TOOLS = [
    search_sake,
    semantic_search,
    recommend_sake,
    pairing_recommendation,
    get_sake_details,
    search_user_preferences,
    fetch_sake_price,
]
