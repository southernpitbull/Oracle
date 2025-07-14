# -*- coding: utf-8 -*-
# File: core/last_read_marker.py
# Author: The Oracle Development Team
# Date: 2024-12-19
# Description: Last Read Marker system for tracking conversation reading progress

"""
Last Read Marker System

This module provides functionality to track and manage the last read position
in conversations, allowing users to quickly resume where they left off.
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path

from utils.error_handler import (
    ErrorCategory,
    ErrorSeverity,
    error_handler,
    log_function_call,
    safe_execute
)


class LastReadMarker:
    """
    Manages last read positions for conversations.
    
    Tracks the last message ID and timestamp that the user has read
    in each conversation, providing visual indicators and navigation.
    """
    
    def __init__(self, data_dir: str = "conversations"):
        """
        Initialize the LastReadMarker system.
        
        Args:
            data_dir: Directory to store last read data
        """
        self.data_dir = Path(data_dir)
        self.last_read_file = self.data_dir / "last_read_markers.json"
        self._markers: Dict[str, Dict] = {}
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing markers
        self._load_markers()
    
    @log_function_call
    @error_handler(category=ErrorCategory.FILE_SYSTEM, severity=ErrorSeverity.ERROR)
    def _load_markers(self) -> None:
        """Load last read markers from persistent storage."""
        if self.last_read_file.exists():
            try:
                with open(self.last_read_file, 'r', encoding='utf-8') as f:
                    self._markers = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # If file is corrupted, start fresh
                self._markers = {}
    
    @log_function_call
    @error_handler(category=ErrorCategory.FILE_SYSTEM, severity=ErrorSeverity.ERROR)
    def _save_markers(self) -> None:
        """Save last read markers to persistent storage."""
        try:
            with open(self.last_read_file, 'w', encoding='utf-8') as f:
                json.dump(self._markers, f, indent=2, ensure_ascii=False)
        except IOError as e:
            # Log error but don't crash
            pass
    
    @log_function_call
    def mark_as_read(self, conversation_id: str, message_id: str, 
                    timestamp: Optional[datetime] = None) -> None:
        """
        Mark a message as read in a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            message_id: Unique identifier for the message
            timestamp: When the message was read (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if conversation_id not in self._markers:
            self._markers[conversation_id] = {}
        
        self._markers[conversation_id].update({
            'last_message_id': message_id,
            'last_read_timestamp': timestamp.isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        
        self._save_markers()
    
    @log_function_call
    def get_last_read(self, conversation_id: str) -> Optional[Dict]:
        """
        Get the last read information for a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Dictionary with last read info or None if not found
        """
        return self._markers.get(conversation_id)
    
    @log_function_call
    def get_last_read_message_id(self, conversation_id: str) -> Optional[str]:
        """
        Get the last read message ID for a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Last read message ID or None if not found
        """
        marker = self.get_last_read(conversation_id)
        return marker.get('last_message_id') if marker else None
    
    @log_function_call
    def get_last_read_timestamp(self, conversation_id: str) -> Optional[datetime]:
        """
        Get the last read timestamp for a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Last read timestamp or None if not found
        """
        marker = self.get_last_read(conversation_id)
        if marker and 'last_read_timestamp' in marker:
            try:
                return datetime.fromisoformat(marker['last_read_timestamp'])
            except ValueError:
                return None
        return None
    
    @log_function_call
    def has_unread_messages(self, conversation_id: str, 
                           latest_message_id: str) -> bool:
        """
        Check if a conversation has unread messages.
        
        Args:
            conversation_id: Unique identifier for the conversation
            latest_message_id: ID of the latest message in the conversation
            
        Returns:
            True if there are unread messages, False otherwise
        """
        last_read_id = self.get_last_read_message_id(conversation_id)
        if last_read_id is None:
            return True
        
        # Simple string comparison - assumes message IDs are sortable
        return latest_message_id > last_read_id
    
    @log_function_call
    def get_unread_count(self, conversation_id: str, 
                        all_message_ids: list) -> int:
        """
        Get the count of unread messages in a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            all_message_ids: List of all message IDs in the conversation
            
        Returns:
            Number of unread messages
        """
        last_read_id = self.get_last_read_message_id(conversation_id)
        if last_read_id is None:
            return len(all_message_ids)
        
        # Count messages after the last read message
        unread_count = 0
        for msg_id in all_message_ids:
            if msg_id > last_read_id:
                unread_count += 1
        
        return unread_count
    
    @log_function_call
    def clear_conversation_marker(self, conversation_id: str) -> None:
        """
        Clear the last read marker for a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
        """
        if conversation_id in self._markers:
            del self._markers[conversation_id]
            self._save_markers()
    
    @log_function_call
    def clear_all_markers(self) -> None:
        """Clear all last read markers."""
        self._markers.clear()
        self._save_markers()
    
    @log_function_call
    def get_all_markers(self) -> Dict[str, Dict]:
        """
        Get all last read markers.
        
        Returns:
            Dictionary of all conversation markers
        """
        return self._markers.copy()
    
    @log_function_call
    def get_conversations_with_unread(self, 
                                    conversation_data: Dict[str, Dict]) -> list:
        """
        Get list of conversations with unread messages.
        
        Args:
            conversation_data: Dictionary mapping conversation_id to conversation data
                              Each conversation should have a 'messages' list with 'id' fields
            
        Returns:
            List of conversation IDs that have unread messages
        """
        unread_conversations = []
        
        for conv_id, conv_data in conversation_data.items():
            if 'messages' in conv_data and conv_data['messages']:
                latest_message_id = conv_data['messages'][-1]['id']
                if self.has_unread_messages(conv_id, latest_message_id):
                    unread_conversations.append(conv_id)
        
        return unread_conversations
    
    @log_function_call
    def mark_conversation_as_read(self, conversation_id: str, 
                                conversation_data: Dict) -> None:
        """
        Mark an entire conversation as read.
        
        Args:
            conversation_id: Unique identifier for the conversation
            conversation_data: Conversation data containing messages
        """
        if 'messages' in conversation_data and conversation_data['messages']:
            latest_message = conversation_data['messages'][-1]
            self.mark_as_read(conversation_id, latest_message['id'])
    
    @log_function_call
    def get_marker_summary(self) -> Dict:
        """
        Get a summary of all markers.
        
        Returns:
            Dictionary with marker statistics
        """
        total_conversations = len(self._markers)
        recent_markers = 0
        oldest_marker = None
        newest_marker = None
        
        for marker_data in self._markers.values():
            if 'updated_at' in marker_data:
                try:
                    timestamp = datetime.fromisoformat(marker_data['updated_at'])
                    if (datetime.now() - timestamp).days <= 7:
                        recent_markers += 1
                    
                    if oldest_marker is None or timestamp < oldest_marker:
                        oldest_marker = timestamp
                    if newest_marker is None or timestamp > newest_marker:
                        newest_marker = timestamp
                except ValueError:
                    continue
        
        return {
            'total_conversations': total_conversations,
            'recent_markers': recent_markers,
            'oldest_marker': oldest_marker.isoformat() if oldest_marker else None,
            'newest_marker': newest_marker.isoformat() if newest_marker else None
        } 
