import pytest
from control_agent.evals.evaluators.tool_sequence import check_list_item_sequence


class TestCheckListItemSequence:
    """Tests for check_list_item_sequence function"""
    
    def test_correct_order_returns_true(self):
        """Test that correct sequence returns True"""
        result = check_list_item_sequence(
            ['tool_a', 'tool_b', 'tool_c'],
            ['tool_a', 'tool_b', 'tool_c']
        )
        assert result is True
    
    def test_wrong_order_returns_false(self):
        """Test that wrong order returns False"""
        result = check_list_item_sequence(
            ['tool_b', 'tool_a', 'tool_c'],
            ['tool_a', 'tool_b', 'tool_c']
        )
        assert result is False
    
    def test_missing_item_returns_false(self):
        """Test that missing item returns False"""
        result = check_list_item_sequence(
            ['tool_a', 'tool_b'],
            ['tool_a', 'tool_b', 'tool_c']
        )
        assert result is False
    
    def test_extra_items_still_passes(self):
        """Test that extra items don't fail if sequence is correct"""
        result = check_list_item_sequence(
            ['tool_a', 'tool_b', 'tool_c', 'tool_d'],
            ['tool_a', 'tool_b']
        )
        assert result is True
    
    def test_empty_expected_sequence_returns_true(self):
        """Test that empty expected sequence returns True"""
        result = check_list_item_sequence(
            ['tool_a', 'tool_b'],
            []
        )
        assert result is True
    
    def test_empty_list_to_check_with_expected_returns_false(self):
        """Test that empty list with expected items returns False"""
        result = check_list_item_sequence(
            [],
            ['tool_a', 'tool_b']
        )
        assert result is False
    
    def test_both_empty_returns_true(self):
        """Test that both empty lists returns True"""
        result = check_list_item_sequence([], [])
        assert result is True
    
    def test_duplicate_items_in_sequence(self):
        """Test that duplicate items in sequence are handled correctly"""
        # Correct order with duplicate
        result = check_list_item_sequence(
            ['tool_a', 'tool_b', 'tool_a'],
            ['tool_a', 'tool_b', 'tool_a']
        )
        assert result is True
        
        # Wrong order with duplicate
        result = check_list_item_sequence(
            ['tool_b', 'tool_a', 'tool_a'],
            ['tool_a', 'tool_b', 'tool_a']
        )
        assert result is False
    
    def test_single_item_sequence(self):
        """Test that single item sequence works"""
        result = check_list_item_sequence(
            ['tool_a'],
            ['tool_a']
        )
        assert result is True
        
        result = check_list_item_sequence(
            ['tool_b'],
            ['tool_a']
        )
        assert result is False
    
    def test_partial_match_fails(self):
        """Test that partial match (missing later items) fails"""
        result = check_list_item_sequence(
            ['tool_a', 'tool_b'],
            ['tool_a', 'tool_b', 'tool_c']
        )
        assert result is False
    
    def test_items_before_expected_sequence(self):
        """Test that items before expected sequence are ignored correctly"""
        result = check_list_item_sequence(
            ['tool_x', 'tool_a', 'tool_b'],
            ['tool_a', 'tool_b']
        )
        assert result is True
    
    def test_items_after_expected_sequence(self):
        """Test that items after expected sequence are ignored correctly"""
        result = check_list_item_sequence(
            ['tool_a', 'tool_b', 'tool_x'],
            ['tool_a', 'tool_b']
        )
        assert result is True
