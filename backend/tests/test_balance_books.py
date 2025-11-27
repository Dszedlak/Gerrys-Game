"""
Test suite for balance_books function to verify wealth redistribution logic.
"""
from datetime import datetime, timedelta


def test_balance_books_logic():
    """Test the balance books algorithm matches the expected behavior."""
    
    def calculate_balance(player_hours_list):
        """
        Simulates the balance_books logic.
        
        Args:
            player_hours_list: List of hours (floats) each player has
            
        Returns:
            List of final hours after redistribution
        """
        TWELVE_HOURS = 12
        
        # Step 1: Calculate shareable pool and excess
        total_shareable = 0
        player_data = []
        
        for hours in player_hours_list:
            shareable = min(hours, TWELVE_HOURS)
            excess = max(0, hours - TWELVE_HOURS)
            total_shareable += shareable
            player_data.append({
                'shareable': shareable,
                'excess': excess
            })
        
        # Step 2: Calculate equal share
        equal_share = total_shareable / len(player_hours_list)
        
        # Step 3: Redistribute (base share + personal excess)
        final_hours = []
        for data in player_data:
            final = equal_share + data['excess']
            final_hours.append(final)
        
        return final_hours
    
    # Test Case 1: Your example (16 and 4)
    print("Test Case 1: Players with 16 and 4 hours")
    result = calculate_balance([16, 4])
    expected = [12, 8]
    print(f"  Input: [16, 4]")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    assert result == expected, f"Failed! Expected {expected}, got {result}"
    print("  ✅ PASSED\n")
    
    # Test Case 2: Your example (5, 10, 14)
    print("Test Case 2: Players with 5, 10, and 14 hours")
    result = calculate_balance([5, 10, 14])
    expected = [9, 9, 11]
    print(f"  Input: [5, 10, 14]")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    assert result == expected, f"Failed! Expected {expected}, got {result}"
    print("  ✅ PASSED\n")
    
    # Test Case 3: All players under 12 hours
    print("Test Case 3: All players under 12 hours")
    result = calculate_balance([6, 8, 10])
    expected = [8, 8, 8]
    print(f"  Input: [6, 8, 10]")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    assert result == expected, f"Failed! Expected {expected}, got {result}"
    print("  ✅ PASSED\n")
    
    # Test Case 4: All players at exactly 12 hours
    print("Test Case 4: All players at exactly 12 hours")
    result = calculate_balance([12, 12, 12])
    expected = [12, 12, 12]
    print(f"  Input: [12, 12, 12]")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    assert result == expected, f"Failed! Expected {expected}, got {result}"
    print("  ✅ PASSED\n")
    
    # Test Case 5: One player with massive excess
    print("Test Case 5: One player with 24 hours, one with 0")
    result = calculate_balance([24, 0])
    expected = [18, 6]  # Pool: 12+0=12, share: 6 each, player1: 6+12=18
    print(f"  Input: [24, 0]")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    assert result == expected, f"Failed! Expected {expected}, got {result}"
    print("  ✅ PASSED\n")
    
    # Test Case 6: Multiple players with excess
    print("Test Case 6: Multiple players above 12 hours")
    result = calculate_balance([15, 18, 3])
    expected = [15, 18, 3]  # Pool: 12+12+3=27, share: 9 each
                             # P1: 9+3=12, P2: 9+6=15, P3: 9+0=9
    # Wait, let me recalculate:
    # Player 1: 15 hours → shareable: 12, excess: 3
    # Player 2: 18 hours → shareable: 12, excess: 6
    # Player 3: 3 hours → shareable: 3, excess: 0
    # Pool: 12 + 12 + 3 = 27
    # Share: 27 / 3 = 9
    # P1: 9 + 3 = 12
    # P2: 9 + 6 = 15
    # P3: 9 + 0 = 9
    expected = [12, 15, 9]
    print(f"  Input: [15, 18, 3]")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    assert result == expected, f"Failed! Expected {expected}, got {result}"
    print("  ✅ PASSED\n")
    
    print("=" * 50)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 50)


if __name__ == "__main__":
    test_balance_books_logic()
