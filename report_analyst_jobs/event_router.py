"""
Event-Action Router

Simple table-based event routing system that maps NATS events to actions.
Actions can be callable handlers or "ignore" to skip processing.

This is not BPM - it's a simple event-to-action mapping table.

Configuration is loaded from YAML file (event_routing.yaml) by default.
"""

import asyncio
import importlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import nats
import yaml
from nats.js import JetStreamContext

logger = logging.getLogger(__name__)

# Special action value to ignore events
IGNORE_ACTION = "ignore"


@dataclass
class EventActionRule:
    """A single event-to-action mapping rule"""

    event_pattern: str
    """NATS subject pattern (supports wildcards like 'document.*' or 'analysis.job.>')"""

    action: Union[str, Callable]
    """Action to take: callable handler function, or 'ignore' to skip"""

    description: Optional[str] = None
    """Optional description of what this rule does"""

    enabled: bool = True
    """Whether this rule is enabled"""

    priority: int = 0
    """Priority for matching (higher = checked first)"""


@dataclass
class EventContext:
    """Context passed to action handlers"""

    subject: str
    """NATS subject/channel the event came from"""

    data: Dict[str, Any]
    """Parsed event data"""

    raw_data: bytes
    """Raw message data"""

    message: Any
    """Original NATS message object"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata"""


class EventRouter:
    """
    Simple event-action router for NATS events.

    Maps event patterns to actions using a table-based configuration.
    Actions can be handler functions or "ignore" to skip processing.

    Example:
        router = EventRouter(nats_url="nats://localhost:4222")

        # Define actions
        async def handle_document_ready(ctx: EventContext):
            print(f"Document ready: {ctx.data}")
            await ctx.message.ack()

        # Configure routing table
        router.add_rule("document.ready", handle_document_ready)
        router.add_rule("document.*", "ignore")  # Ignore other document events
        router.add_rule("analysis.job.submit", handle_analysis_job)

        # Start processing
        await router.connect()
        await router.start()
    """

    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc = None
        self.js = None
        self.rules: List[EventActionRule] = []
        self._subscribed_subjects: set = set()

    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(self.nats_url)
            self.js = self.nc.jetstream()
            logger.info(f"Connected to NATS at {self.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def disconnect(self):
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.close()
            logger.info("Disconnected from NATS")

    def add_rule(
        self,
        event_pattern: str,
        action: Union[str, Callable],
        description: Optional[str] = None,
        enabled: bool = True,
        priority: int = 0,
    ):
        """
        Add an event-action rule to the routing table.

        Args:
            event_pattern: NATS subject pattern (supports wildcards)
            action: Handler function or "ignore"
            description: Optional description
            enabled: Whether rule is enabled
            priority: Matching priority (higher = checked first)
        """
        rule = EventActionRule(
            event_pattern=event_pattern,
            action=action,
            description=description,
            enabled=enabled,
            priority=priority,
        )
        self.rules.append(rule)
        # Sort by priority (higher first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"Added rule: {event_pattern} -> {action if action == IGNORE_ACTION else 'handler'}")

    def remove_rule(self, event_pattern: str):
        """Remove a rule by pattern"""
        self.rules = [r for r in self.rules if r.event_pattern != event_pattern]
        logger.info(f"Removed rule: {event_pattern}")

    def set_rules(self, rules: List[EventActionRule]):
        """Set all rules at once (replaces existing)"""
        self.rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        logger.info(f"Set {len(self.rules)} rules")

    def get_rules(self) -> List[EventActionRule]:
        """Get all configured rules"""
        return self.rules.copy()

    def _match_subject(self, pattern: str, subject: str) -> bool:
        """
        Match NATS subject against pattern.
        Supports:
        - Exact match: "document.ready"
        - Single wildcard: "document.*" matches "document.ready" but not "document.ready.status"
        - Multi-wildcard: "document.>" matches "document.ready" and "document.ready.status"
        """
        if pattern == subject:
            return True

        # Handle wildcards
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return subject.startswith(prefix + ".") and "." not in subject[len(prefix) + 1 :]

        if pattern.endswith(".>"):
            prefix = pattern[:-2]
            return subject.startswith(prefix + ".")

        return False

    def _find_rule(self, subject: str) -> Optional[EventActionRule]:
        """Find matching rule for a subject (checks in priority order)"""
        for rule in self.rules:
            if not rule.enabled:
                continue
            if self._match_subject(rule.event_pattern, subject):
                return rule
        return None

    async def _handle_message(self, msg):
        """Handle incoming NATS message"""
        try:
            subject = msg.subject
            logger.debug(f"Received event on subject: {subject}")

            # Find matching rule
            rule = self._find_rule(subject)
            if not rule:
                logger.warning(f"No rule found for subject: {subject}, ignoring")
                await msg.ack()  # Ack to avoid redelivery
                return

            # Check if action is "ignore"
            if rule.action == IGNORE_ACTION:
                logger.debug(f"Ignoring event on subject: {subject} (rule: {rule.event_pattern})")
                await msg.ack()
                return

            # Parse event data
            try:
                data = json.loads(msg.data.decode())
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from subject: {subject}")
                await msg.ack()
                return

            # Create context
            context = EventContext(
                subject=subject,
                data=data,
                raw_data=msg.data,
                message=msg,
            )

            # Execute action handler
            if callable(rule.action):
                logger.info(f"Executing handler for subject: {subject}")
                try:
                    if asyncio.iscoroutinefunction(rule.action):
                        await rule.action(context)
                    else:
                        rule.action(context)
                except Exception as e:
                    logger.error(f"Error executing handler for {subject}: {e}", exc_info=True)
                    # Handler should ack/nak, but if it doesn't, we ack to avoid redelivery loops
                    try:
                        await msg.ack()
                    except:
                        pass
            else:
                logger.warning(f"Invalid action for rule {rule.event_pattern}: {rule.action}")
                await msg.ack()

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            try:
                await msg.ack()  # Ack on error to avoid redelivery loops
            except:
                pass

    async def start(self, subjects: Optional[List[str]] = None):
        """
        Start processing events.

        Args:
            subjects: Optional list of subjects to subscribe to.
                     If None, automatically subscribes to all subjects mentioned in rules.
        """
        if not self.js:
            await self.connect()

        # Determine which subjects to subscribe to
        if subjects is None:
            # Extract unique subjects from rules
            subjects = set()
            for rule in self.rules:
                if not rule.enabled or rule.action == IGNORE_ACTION:
                    continue
                # Convert pattern to subscription pattern
                if rule.event_pattern.endswith(".>"):
                    # Multi-wildcard: subscribe to prefix
                    subjects.add(rule.event_pattern[:-2] + ".>")
                elif rule.event_pattern.endswith(".*"):
                    # Single wildcard: subscribe to prefix
                    subjects.add(rule.event_pattern[:-2] + ".>")
                else:
                    # Exact match
                    subjects.add(rule.event_pattern)
            subjects = list(subjects)

        if not subjects:
            logger.warning("No subjects to subscribe to")
            return

        # Subscribe to each subject
        for subject in subjects:
            if subject in self._subscribed_subjects:
                continue

            try:
                await self.js.subscribe(subject, cb=self._handle_message)
                self._subscribed_subjects.add(subject)
                logger.info(f"Subscribed to: {subject}")
            except Exception as e:
                logger.error(f"Failed to subscribe to {subject}: {e}")

        logger.info(f"Event router started, listening to {len(self._subscribed_subjects)} subjects")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping event router")

    def get_routing_table(self) -> List[Dict[str, Any]]:
        """Get routing table as list of dictionaries for inspection"""
        return [
            {
                "pattern": rule.event_pattern,
                "action": IGNORE_ACTION if rule.action == IGNORE_ACTION else "handler",
                "description": rule.description,
                "enabled": rule.enabled,
                "priority": rule.priority,
            }
            for rule in self.rules
        ]

    @classmethod
    def from_yaml(
        cls,
        yaml_path: Optional[Union[str, Path]] = None,
        handler_registry: Optional[Dict[str, Callable]] = None,
    ) -> "EventRouter":
        """
        Create EventRouter from YAML configuration file.

        Args:
            yaml_path: Path to YAML config file. If None, looks for event_routing.yaml
                      in the same directory as this module.
            handler_registry: Optional dict mapping handler names to callable functions.
                            If None, tries to import handlers from paths specified in YAML.

        Returns:
            Configured EventRouter instance
        """
        router = cls()

        # Default YAML path
        if yaml_path is None:
            yaml_path = Path(__file__).parent / "event_routing.yaml"
        else:
            yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            logger.warning(f"YAML config file not found: {yaml_path}")
            return router

        # Load YAML
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load YAML config: {e}")
            return router

        # Load handler registry
        if handler_registry is None:
            handler_registry = {}
            # Try to load handlers from YAML config
            handler_paths = config.get("handlers", {})
            for handler_name, handler_path in handler_paths.items():
                try:
                    handler = cls._load_handler(handler_path)
                    handler_registry[handler_name] = handler
                except Exception as e:
                    logger.warning(f"Failed to load handler {handler_name} from {handler_path}: {e}")

        # Load routing rules
        routing_rules = config.get("routing", [])
        for rule_config in routing_rules:
            pattern = rule_config.get("pattern")
            action_name = rule_config.get("action")
            description = rule_config.get("description")
            enabled = rule_config.get("enabled", True)
            priority = rule_config.get("priority", 0)

            if not pattern or not action_name:
                logger.warning(f"Invalid rule config: {rule_config}")
                continue

            # Resolve action
            if action_name == IGNORE_ACTION:
                action = IGNORE_ACTION
            elif action_name in handler_registry:
                action = handler_registry[action_name]
            else:
                logger.warning(f"Handler not found for action: {action_name}, ignoring rule")
                continue

            router.add_rule(
                event_pattern=pattern,
                action=action,
                description=description,
                enabled=enabled,
                priority=priority,
            )

        logger.info(f"Loaded {len(router.rules)} routing rules from {yaml_path}")
        return router

    @staticmethod
    def _load_handler(handler_path: str) -> Callable:
        """
        Load handler function from module path string.

        Args:
            handler_path: String like "module.path.to.function"

        Returns:
            Callable handler function
        """
        parts = handler_path.split(".")
        module_path = ".".join(parts[:-1])
        function_name = parts[-1]

        module = importlib.import_module(module_path)
        handler = getattr(module, function_name)

        if not callable(handler):
            raise ValueError(f"{handler_path} is not callable")

        return handler
