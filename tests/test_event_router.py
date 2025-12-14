"""
Tests for Event-Action Router

Tests the simple table-based event routing system.
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from report_analyst_jobs.event_router import (
    EventActionRule,
    EventContext,
    EventRouter,
    IGNORE_ACTION,
)


@pytest.fixture
def mock_nats():
    """Mock NATS connection"""
    mock_nc = AsyncMock()
    mock_js = AsyncMock()
    mock_nc.jetstream.return_value = mock_js
    return mock_nc, mock_js


@pytest.fixture
def router():
    """Create event router"""
    return EventRouter(nats_url="nats://localhost:4222")


@pytest.mark.asyncio
async def test_add_rule(router):
    """Test adding rules"""

    async def handler(ctx: EventContext):
        pass

    router.add_rule("document.ready", handler, description="Handle document ready")
    router.add_rule("document.*", IGNORE_ACTION, description="Ignore other docs")

    rules = router.get_rules()
    assert len(rules) == 2
    assert rules[0].event_pattern == "document.ready"
    assert rules[1].event_pattern == "document.*"
    assert rules[1].action == IGNORE_ACTION


@pytest.mark.asyncio
async def test_match_subject(router):
    """Test subject matching"""
    # Exact match
    assert router._match_subject("document.ready", "document.ready") is True
    assert router._match_subject("document.ready", "document.upload") is False

    # Single wildcard
    assert router._match_subject("document.*", "document.ready") is True
    assert router._match_subject("document.*", "document.ready.status") is False

    # Multi-wildcard
    assert router._match_subject("document.>", "document.ready") is True
    assert router._match_subject("document.>", "document.ready.status") is True
    assert router._match_subject("document.>", "analysis.ready") is False


@pytest.mark.asyncio
async def test_find_rule(router):
    """Test finding matching rule"""

    async def handler(ctx: EventContext):
        pass

    router.add_rule("document.*", IGNORE_ACTION, priority=1)
    router.add_rule("document.ready", handler, priority=10)  # Higher priority

    # Should find specific rule first (higher priority)
    rule = router._find_rule("document.ready")
    assert rule is not None
    assert rule.event_pattern == "document.ready"
    assert rule.action != IGNORE_ACTION

    # Should find wildcard rule
    rule = router._find_rule("document.upload")
    assert rule is not None
    assert rule.event_pattern == "document.*"
    assert rule.action == IGNORE_ACTION


@pytest.mark.asyncio
async def test_handle_message_ignore(router, mock_nats):
    """Test handling message with ignore action"""
    mock_nc, mock_js = mock_nats
    router.nc = mock_nc
    router.js = mock_js

    router.add_rule("document.ready", IGNORE_ACTION)

    mock_msg = AsyncMock()
    mock_msg.subject = "document.ready"
    mock_msg.data = json.dumps({"resource_id": "123"}).encode()
    mock_msg.ack = AsyncMock()

    await router._handle_message(mock_msg)

    # Should ack but not process
    mock_msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_handler(router, mock_nats):
    """Test handling message with handler"""
    mock_nc, mock_js = mock_nats
    router.nc = mock_nc
    router.js = mock_js

    handler_called = []

    async def handler(ctx: EventContext):
        handler_called.append(ctx.data)
        await ctx.message.ack()

    router.add_rule("document.ready", handler)

    mock_msg = AsyncMock()
    mock_msg.subject = "document.ready"
    mock_msg.data = json.dumps({"resource_id": "123"}).encode()
    mock_msg.ack = AsyncMock()

    await router._handle_message(mock_msg)

    # Handler should be called
    assert len(handler_called) == 1
    assert handler_called[0]["resource_id"] == "123"


@pytest.mark.asyncio
async def test_handle_message_no_rule(router, mock_nats):
    """Test handling message with no matching rule"""
    mock_nc, mock_js = mock_nats
    router.nc = mock_nc
    router.js = mock_js

    mock_msg = AsyncMock()
    mock_msg.subject = "unknown.event"
    mock_msg.data = json.dumps({}).encode()
    mock_msg.ack = AsyncMock()

    await router._handle_message(mock_msg)

    # Should ack to avoid redelivery
    mock_msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_priority_ordering(router):
    """Test that rules are checked in priority order"""

    async def handler1(ctx: EventContext):
        pass

    async def handler2(ctx: EventContext):
        pass

    router.add_rule("document.*", handler1, priority=1)
    router.add_rule("document.ready", handler2, priority=10)

    # document.ready should match the higher priority specific rule
    rule = router._find_rule("document.ready")
    assert rule.event_pattern == "document.ready"
    assert rule.action == handler2


@pytest.mark.asyncio
async def test_disabled_rule(router):
    """Test that disabled rules are skipped"""
    router.add_rule("document.ready", IGNORE_ACTION, enabled=False)

    rule = router._find_rule("document.ready")
    assert rule is None


@pytest.mark.asyncio
async def test_routing_table(router):
    """Test getting routing table"""

    async def handler(ctx: EventContext):
        pass

    router.add_rule("document.ready", handler, description="Handle docs")
    router.add_rule("analysis.*", IGNORE_ACTION, description="Ignore analysis")

    table = router.get_routing_table()
    assert len(table) == 2
    assert table[0]["pattern"] == "document.ready"
    assert table[0]["action"] == "handler"
    assert table[1]["pattern"] == "analysis.*"
    assert table[1]["action"] == IGNORE_ACTION


@pytest.mark.asyncio
async def test_set_rules(router):
    """Test setting all rules at once"""

    async def handler(ctx: EventContext):
        pass

    rules = [
        EventActionRule("document.ready", handler, priority=10),
        EventActionRule("document.*", IGNORE_ACTION, priority=1),
    ]

    router.set_rules(rules)

    assert len(router.get_rules()) == 2
    # Should be sorted by priority
    assert router.get_rules()[0].priority == 10
