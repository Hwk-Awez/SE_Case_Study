"""
Binary Search Algorithm Implementation
O(log n) time complexity searching routines.
"""
from typing import List, Any

def binary_search(arr: List[Any], target: Any) -> int:
    """Returns index of target in sorted list `arr`, or -1 if absent."""
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

def binary_search_leftmost(arr: List[Any], target: Any) -> int:
    """Finds the lowest index where target occurs."""
    low, high = 0, len(arr)
    while low < high:
        mid = (low + high) // 2
        if arr[mid] < target:
            low = mid + 1
        else:
            high = mid
    return low if low < len(arr) and arr[low] == target else -1
