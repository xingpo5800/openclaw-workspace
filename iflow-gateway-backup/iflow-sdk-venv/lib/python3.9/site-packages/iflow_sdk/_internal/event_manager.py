"""Event management with weak references for memory safety."""

import logging
import weakref
from typing import Any, Callable, Dict, Set

logger = logging.getLogger(__name__)


class EventManager:
    """Event manager using weak references to prevent memory leaks.
    
    This manager stores event listeners as weak references, allowing
    them to be garbage collected when no longer used elsewhere.
    """
    
    def __init__(self):
        """Initialize the event manager."""
        self._listeners: Dict[str, weakref.WeakSet] = {}
    
    def add_listener(self, event_type: str, callback: Callable) -> None:
        """Add an event listener using weak reference.
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function to invoke
            
        Note:
            The callback is stored as a weak reference. If the callback
            is garbage collected, it will be automatically removed.
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = weakref.WeakSet()
        
        try:
            self._listeners[event_type].add(callback)
            logger.debug(f"Added listener for event '{event_type}'")
        except TypeError:
            # Callback cannot be weakly referenced (e.g., lambda, bound method)
            logger.warning(
                f"Cannot add weak reference for {callback}. "
                "Consider using a regular function or class method."
            )
    
    def remove_listener(self, event_type: str, callback: Callable) -> None:
        """Remove an event listener.
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].discard(callback)
                logger.debug(f"Removed listener for event '{event_type}'")
            except Exception as e:
                logger.error(f"Failed to remove listener: {e}")
    
    def emit(self, event_type: str, *args, **kwargs) -> int:
        """Emit an event to all listeners.
        
        Args:
            event_type: Type of event to emit
            *args: Positional arguments for callbacks
            **kwargs: Keyword arguments for callbacks
            
        Returns:
            Number of listeners that were notified
        """
        if event_type not in self._listeners:
            return 0
        
        # Get current listeners (creates a copy to avoid modification during iteration)
        listeners = list(self._listeners[event_type])
        
        notified_count = 0
        for callback in listeners:
            try:
                callback(*args, **kwargs)
                notified_count += 1
            except Exception as e:
                logger.error(f"Event listener error for '{event_type}': {e}")
        
        return notified_count
    
    def get_listener_count(self, event_type: str) -> int:
        """Get number of listeners for an event type.
        
        Args:
            event_type: Type of event
            
        Returns:
            Number of active listeners
        """
        if event_type not in self._listeners:
            return 0
        return len(self._listeners[event_type])
    
    def clear_event(self, event_type: str) -> None:
        """Clear all listeners for an event type.
        
        Args:
            event_type: Type of event to clear
        """
        if event_type in self._listeners:
            self._listeners[event_type].clear()
            logger.debug(f"Cleared all listeners for event '{event_type}'")
    
    def clear_all(self) -> None:
        """Clear all listeners for all events."""
        self._listeners.clear()
        logger.debug("Cleared all event listeners")
    
    def cleanup_dead_references(self) -> int:
        """Clean up dead weak references.
        
        Returns:
            Number of dead references cleaned up
        """
        cleaned = 0
        for event_type in list(self._listeners.keys()):
            # WeakSet automatically removes dead references,
            # but we can check if the set is empty and remove it
            if len(self._listeners[event_type]) == 0:
                del self._listeners[event_type]
                cleaned += 1
        
        if cleaned > 0:
            logger.debug(f"Cleaned up {cleaned} empty event types")
        
        return cleaned
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event manager statistics.
        
        Returns:
            Dictionary with event statistics
        """
        return {
            "event_types": len(self._listeners),
            "total_listeners": sum(len(listeners) for listeners in self._listeners.values()),
            "events": {
                event_type: len(listeners)
                for event_type, listeners in self._listeners.items()
            }
        }
