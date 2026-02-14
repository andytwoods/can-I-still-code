# ruff: noqa: E501
"""
Seed challenges for the study.

Generates ~50 Python challenges across tiers 1-5, inspired by Exercism
and classic coding interview problems. Each challenge includes a description,
skeleton code, and test cases for client-side Pyodide execution.

Idempotent: skips challenges whose external_id already exists.
"""

from django.core.management.base import BaseCommand

from agenticbrainrot.challenges.models import Challenge

# Test case format: list of dicts with "input", "expected", "description".
# The client-side runner calls the function with input args and compares
# the return value to expected.

CHALLENGES = [
    # =========================================================================
    # TIER 1 — Beginner (15 challenges)
    # =========================================================================
    {
        "external_id": "hello-world-v1",
        "title": "Hello World",
        "description": "Write a function `hello()` that returns the string `'Hello, World!'`.",
        "skeleton_code": "def hello():\n    pass\n",
        "test_cases": [
            {"input": [], "expected": "Hello, World!", "description": "Returns greeting"},
        ],
        "difficulty": 1,
        "tags": ["strings", "basics"],
    },
    {
        "external_id": "two-fer-v1",
        "title": "Two Fer",
        "description": (
            "Write a function `two_fer(name='you')` that returns "
            "`'One for <name>, one for me.'`."
        ),
        "skeleton_code": "def two_fer(name='you'):\n    pass\n",
        "test_cases": [
            {"input": [], "expected": "One for you, one for me.", "description": "No name given"},
            {"input": ["Alice"], "expected": "One for Alice, one for me.", "description": "A name given"},
            {"input": ["Bob"], "expected": "One for Bob, one for me.", "description": "Another name"},
        ],
        "difficulty": 1,
        "tags": ["strings", "basics"],
    },
    {
        "external_id": "reverse-string-v1",
        "title": "Reverse String",
        "description": "Write a function `reverse(text)` that returns the reversed string.",
        "skeleton_code": "def reverse(text):\n    pass\n",
        "test_cases": [
            {"input": [""], "expected": "", "description": "Empty string"},
            {"input": ["robot"], "expected": "tobor", "description": "A word"},
            {"input": ["racecar"], "expected": "racecar", "description": "A palindrome"},
            {"input": ["drawer"], "expected": "reward", "description": "Another word"},
        ],
        "difficulty": 1,
        "tags": ["strings"],
    },
    {
        "external_id": "is-even-v1",
        "title": "Is Even",
        "description": "Write a function `is_even(n)` that returns `True` if `n` is even, `False` otherwise.",
        "skeleton_code": "def is_even(n):\n    pass\n",
        "test_cases": [
            {"input": [2], "expected": True, "description": "2 is even"},
            {"input": [3], "expected": False, "description": "3 is odd"},
            {"input": [0], "expected": True, "description": "0 is even"},
            {"input": [-4], "expected": True, "description": "Negative even"},
        ],
        "difficulty": 1,
        "tags": ["numbers", "basics"],
    },
    {
        "external_id": "max-of-three-v1",
        "title": "Max of Three",
        "description": "Write a function `max_of_three(a, b, c)` that returns the largest of three numbers without using the built-in `max()`.",
        "skeleton_code": "def max_of_three(a, b, c):\n    pass\n",
        "test_cases": [
            {"input": [1, 2, 3], "expected": 3, "description": "Last is largest"},
            {"input": [3, 2, 1], "expected": 3, "description": "First is largest"},
            {"input": [1, 3, 2], "expected": 3, "description": "Middle is largest"},
            {"input": [-1, -2, -3], "expected": -1, "description": "All negative"},
            {"input": [5, 5, 5], "expected": 5, "description": "All equal"},
        ],
        "difficulty": 1,
        "tags": ["numbers", "basics"],
    },
    {
        "external_id": "count-vowels-v1",
        "title": "Count Vowels",
        "description": "Write a function `count_vowels(text)` that returns the number of vowels (a, e, i, o, u) in the string. Case-insensitive.",
        "skeleton_code": "def count_vowels(text):\n    pass\n",
        "test_cases": [
            {"input": ["hello"], "expected": 2, "description": "Two vowels"},
            {"input": ["AEIOU"], "expected": 5, "description": "All uppercase vowels"},
            {"input": ["xyz"], "expected": 0, "description": "No vowels"},
            {"input": [""], "expected": 0, "description": "Empty string"},
        ],
        "difficulty": 1,
        "tags": ["strings"],
    },
    {
        "external_id": "sum-list-v1",
        "title": "Sum a List",
        "description": "Write a function `sum_list(numbers)` that returns the sum of all numbers in the list without using the built-in `sum()`.",
        "skeleton_code": "def sum_list(numbers):\n    pass\n",
        "test_cases": [
            {"input": [[1, 2, 3]], "expected": 6, "description": "Simple sum"},
            {"input": [[]], "expected": 0, "description": "Empty list"},
            {"input": [[-1, 1]], "expected": 0, "description": "Cancelling values"},
            {"input": [[100]], "expected": 100, "description": "Single element"},
        ],
        "difficulty": 1,
        "tags": ["lists", "basics"],
    },
    {
        "external_id": "factorial-v1",
        "title": "Factorial",
        "description": "Write a function `factorial(n)` that returns the factorial of a non-negative integer `n`. `factorial(0)` should return `1`.",
        "skeleton_code": "def factorial(n):\n    pass\n",
        "test_cases": [
            {"input": [0], "expected": 1, "description": "Zero"},
            {"input": [1], "expected": 1, "description": "One"},
            {"input": [5], "expected": 120, "description": "Five"},
            {"input": [10], "expected": 3628800, "description": "Ten"},
        ],
        "difficulty": 1,
        "tags": ["numbers", "recursion"],
    },
    {
        "external_id": "fizzbuzz-v1",
        "title": "FizzBuzz",
        "description": (
            "Write a function `fizzbuzz(n)` that returns a list of strings from 1 to n. "
            "For multiples of 3, use 'Fizz'. For multiples of 5, use 'Buzz'. "
            "For multiples of both, use 'FizzBuzz'. Otherwise, use the number as a string."
        ),
        "skeleton_code": "def fizzbuzz(n):\n    pass\n",
        "test_cases": [
            {"input": [1], "expected": ["1"], "description": "Just 1"},
            {
                "input": [15],
                "expected": [
                    "1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz",
                    "11", "Fizz", "13", "14", "FizzBuzz",
                ],
                "description": "First 15",
            },
        ],
        "difficulty": 1,
        "tags": ["loops", "conditionals"],
    },
    {
        "external_id": "celsius-to-fahrenheit-v1",
        "title": "Celsius to Fahrenheit",
        "description": "Write a function `to_fahrenheit(celsius)` that converts Celsius to Fahrenheit. Formula: F = C * 9/5 + 32.",
        "skeleton_code": "def to_fahrenheit(celsius):\n    pass\n",
        "test_cases": [
            {"input": [0], "expected": 32.0, "description": "Freezing point"},
            {"input": [100], "expected": 212.0, "description": "Boiling point"},
            {"input": [-40], "expected": -40.0, "description": "Same in both scales"},
        ],
        "difficulty": 1,
        "tags": ["numbers", "basics"],
    },
    {
        "external_id": "is-palindrome-v1",
        "title": "Is Palindrome",
        "description": "Write a function `is_palindrome(text)` that returns `True` if the text is a palindrome (case-insensitive, ignoring spaces).",
        "skeleton_code": "def is_palindrome(text):\n    pass\n",
        "test_cases": [
            {"input": ["racecar"], "expected": True, "description": "Simple palindrome"},
            {"input": ["hello"], "expected": False, "description": "Not a palindrome"},
            {"input": ["A man a plan a canal Panama"], "expected": True, "description": "Phrase palindrome"},
            {"input": [""], "expected": True, "description": "Empty string"},
        ],
        "difficulty": 1,
        "tags": ["strings"],
    },
    {
        "external_id": "find-min-v1",
        "title": "Find Minimum",
        "description": "Write a function `find_min(numbers)` that returns the smallest number in a list without using the built-in `min()`. Assume the list is non-empty.",
        "skeleton_code": "def find_min(numbers):\n    pass\n",
        "test_cases": [
            {"input": [[3, 1, 2]], "expected": 1, "description": "Middle element"},
            {"input": [[1]], "expected": 1, "description": "Single element"},
            {"input": [[-5, -3, -1]], "expected": -5, "description": "All negative"},
        ],
        "difficulty": 1,
        "tags": ["lists"],
    },
    {
        "external_id": "remove-duplicates-v1",
        "title": "Remove Duplicates",
        "description": "Write a function `remove_duplicates(items)` that returns a list with duplicates removed, preserving order.",
        "skeleton_code": "def remove_duplicates(items):\n    pass\n",
        "test_cases": [
            {"input": [[1, 2, 2, 3, 3, 3]], "expected": [1, 2, 3], "description": "Numbers"},
            {"input": [["a", "b", "a"]], "expected": ["a", "b"], "description": "Strings"},
            {"input": [[]], "expected": [], "description": "Empty list"},
        ],
        "difficulty": 1,
        "tags": ["lists"],
    },
    {
        "external_id": "title-case-v1",
        "title": "Title Case",
        "description": "Write a function `title_case(text)` that converts a string to title case (first letter of each word capitalised).",
        "skeleton_code": "def title_case(text):\n    pass\n",
        "test_cases": [
            {"input": ["hello world"], "expected": "Hello World", "description": "Two words"},
            {"input": ["HELLO"], "expected": "Hello", "description": "All caps"},
            {"input": [""], "expected": "", "description": "Empty string"},
        ],
        "difficulty": 1,
        "tags": ["strings"],
    },
    {
        "external_id": "absolute-value-v1",
        "title": "Absolute Value",
        "description": "Write a function `absolute(n)` that returns the absolute value of `n` without using the built-in `abs()`.",
        "skeleton_code": "def absolute(n):\n    pass\n",
        "test_cases": [
            {"input": [5], "expected": 5, "description": "Positive"},
            {"input": [-5], "expected": 5, "description": "Negative"},
            {"input": [0], "expected": 0, "description": "Zero"},
        ],
        "difficulty": 1,
        "tags": ["numbers", "basics"],
    },
    # =========================================================================
    # TIER 2 — Easy (15 challenges)
    # =========================================================================
    {
        "external_id": "pangram-v1",
        "title": "Pangram",
        "description": "Write a function `is_pangram(sentence)` that returns `True` if the sentence contains every letter of the alphabet at least once.",
        "skeleton_code": "def is_pangram(sentence):\n    pass\n",
        "test_cases": [
            {"input": ["The quick brown fox jumps over the lazy dog"], "expected": True, "description": "Classic pangram"},
            {"input": ["The quick brown fox"], "expected": False, "description": "Not a pangram"},
            {"input": [""], "expected": False, "description": "Empty string"},
        ],
        "difficulty": 2,
        "tags": ["strings"],
    },
    {
        "external_id": "isogram-v1",
        "title": "Isogram",
        "description": "Write a function `is_isogram(word)` that returns `True` if the word has no repeating letters (case-insensitive). Spaces and hyphens don't count.",
        "skeleton_code": "def is_isogram(word):\n    pass\n",
        "test_cases": [
            {"input": ["isogram"], "expected": True, "description": "An isogram"},
            {"input": ["eleven"], "expected": False, "description": "Not an isogram"},
            {"input": [""], "expected": True, "description": "Empty string"},
            {"input": ["subdermatoglyphic"], "expected": True, "description": "Long isogram"},
        ],
        "difficulty": 2,
        "tags": ["strings"],
    },
    {
        "external_id": "hamming-v1",
        "title": "Hamming Distance",
        "description": "Write a function `hamming_distance(strand1, strand2)` that returns the number of positions where the characters differ. Strands must be equal length (raise `ValueError` if not).",
        "skeleton_code": "def hamming_distance(strand1, strand2):\n    pass\n",
        "test_cases": [
            {"input": ["GAGCCTACTAACGGGAT", "CATCGTAATGACGGCCT"], "expected": 7, "description": "Long strands"},
            {"input": ["A", "A"], "expected": 0, "description": "Identical single char"},
            {"input": ["GGACG", "GGTCG"], "expected": 1, "description": "One difference"},
        ],
        "difficulty": 2,
        "tags": ["strings", "algorithms"],
    },
    {
        "external_id": "flatten-list-v1",
        "title": "Flatten a List",
        "description": "Write a function `flatten(lst)` that takes a nested list and returns a flat list of all values. For example, `flatten([1, [2, [3]], 4])` returns `[1, 2, 3, 4]`.",
        "skeleton_code": "def flatten(lst):\n    pass\n",
        "test_cases": [
            {"input": [[1, [2, [3]], 4]], "expected": [1, 2, 3, 4], "description": "Nested"},
            {"input": [[]], "expected": [], "description": "Empty"},
            {"input": [[1, 2, 3]], "expected": [1, 2, 3], "description": "Already flat"},
            {"input": [[[[[1]]]]], "expected": [1], "description": "Deeply nested"},
        ],
        "difficulty": 2,
        "tags": ["lists", "recursion"],
    },
    {
        "external_id": "word-count-v1",
        "title": "Word Count",
        "description": "Write a function `word_count(text)` that returns a dictionary mapping each word (lowercased) to its count.",
        "skeleton_code": "def word_count(text):\n    pass\n",
        "test_cases": [
            {"input": ["one fish two fish red fish blue fish"], "expected": {"one": 1, "fish": 4, "two": 1, "red": 1, "blue": 1}, "description": "Multiple words"},
            {"input": [""], "expected": {}, "description": "Empty string"},
            {"input": ["Hello hello HELLO"], "expected": {"hello": 3}, "description": "Case insensitive"},
        ],
        "difficulty": 2,
        "tags": ["strings", "dictionaries"],
    },
    {
        "external_id": "fibonacci-v1",
        "title": "Fibonacci",
        "description": "Write a function `fibonacci(n)` that returns the nth Fibonacci number (0-indexed). `fibonacci(0)` = 0, `fibonacci(1)` = 1.",
        "skeleton_code": "def fibonacci(n):\n    pass\n",
        "test_cases": [
            {"input": [0], "expected": 0, "description": "Zero"},
            {"input": [1], "expected": 1, "description": "One"},
            {"input": [6], "expected": 8, "description": "Six"},
            {"input": [10], "expected": 55, "description": "Ten"},
        ],
        "difficulty": 2,
        "tags": ["numbers", "recursion"],
    },
    {
        "external_id": "roman-numerals-v1",
        "title": "Roman Numerals",
        "description": "Write a function `to_roman(number)` that converts an integer (1-3999) to its Roman numeral representation.",
        "skeleton_code": "def to_roman(number):\n    pass\n",
        "test_cases": [
            {"input": [1], "expected": "I", "description": "One"},
            {"input": [4], "expected": "IV", "description": "Four"},
            {"input": [9], "expected": "IX", "description": "Nine"},
            {"input": [27], "expected": "XXVII", "description": "Twenty-seven"},
            {"input": [1994], "expected": "MCMXCIV", "description": "1994"},
        ],
        "difficulty": 2,
        "tags": ["numbers", "algorithms"],
    },
    {
        "external_id": "matrix-transpose-v1",
        "title": "Matrix Transpose",
        "description": "Write a function `transpose(matrix)` that returns the transpose of a 2D list (list of lists).",
        "skeleton_code": "def transpose(matrix):\n    pass\n",
        "test_cases": [
            {"input": [[[1, 2], [3, 4]]], "expected": [[1, 3], [2, 4]], "description": "2x2"},
            {"input": [[[1, 2, 3]]], "expected": [[1], [2], [3]], "description": "1x3 to 3x1"},
            {"input": [[[1], [2], [3]]], "expected": [[1, 2, 3]], "description": "3x1 to 1x3"},
        ],
        "difficulty": 2,
        "tags": ["lists", "algorithms"],
    },
    {
        "external_id": "binary-search-v1",
        "title": "Binary Search",
        "description": "Write a function `binary_search(lst, target)` that returns the index of `target` in a sorted list, or -1 if not found.",
        "skeleton_code": "def binary_search(lst, target):\n    pass\n",
        "test_cases": [
            {"input": [[1, 3, 5, 7, 9], 5], "expected": 2, "description": "Middle element"},
            {"input": [[1, 3, 5, 7, 9], 1], "expected": 0, "description": "First element"},
            {"input": [[1, 3, 5, 7, 9], 9], "expected": 4, "description": "Last element"},
            {"input": [[1, 3, 5, 7, 9], 4], "expected": -1, "description": "Not found"},
            {"input": [[], 1], "expected": -1, "description": "Empty list"},
        ],
        "difficulty": 2,
        "tags": ["algorithms", "searching"],
    },
    {
        "external_id": "rotate-list-v1",
        "title": "Rotate List",
        "description": "Write a function `rotate(lst, k)` that rotates a list `k` positions to the right. `rotate([1,2,3,4,5], 2)` returns `[4,5,1,2,3]`.",
        "skeleton_code": "def rotate(lst, k):\n    pass\n",
        "test_cases": [
            {"input": [[1, 2, 3, 4, 5], 2], "expected": [4, 5, 1, 2, 3], "description": "Rotate by 2"},
            {"input": [[1, 2, 3], 0], "expected": [1, 2, 3], "description": "Rotate by 0"},
            {"input": [[1, 2, 3], 3], "expected": [1, 2, 3], "description": "Rotate by length"},
            {"input": [[], 5], "expected": [], "description": "Empty list"},
        ],
        "difficulty": 2,
        "tags": ["lists"],
    },
    {
        "external_id": "caesar-cipher-v1",
        "title": "Caesar Cipher",
        "description": "Write a function `caesar_encrypt(text, shift)` that shifts each letter in the text by `shift` positions (wrapping around). Non-letter characters are unchanged.",
        "skeleton_code": "def caesar_encrypt(text, shift):\n    pass\n",
        "test_cases": [
            {"input": ["abc", 3], "expected": "def", "description": "Simple shift"},
            {"input": ["xyz", 3], "expected": "abc", "description": "Wrap around"},
            {"input": ["Hello, World!", 13], "expected": "Uryyb, Jbeyq!", "description": "ROT13"},
            {"input": ["abc", 0], "expected": "abc", "description": "No shift"},
        ],
        "difficulty": 2,
        "tags": ["strings", "algorithms"],
    },
    {
        "external_id": "prime-check-v1",
        "title": "Is Prime",
        "description": "Write a function `is_prime(n)` that returns `True` if `n` is a prime number, `False` otherwise.",
        "skeleton_code": "def is_prime(n):\n    pass\n",
        "test_cases": [
            {"input": [2], "expected": True, "description": "Two is prime"},
            {"input": [1], "expected": False, "description": "One is not prime"},
            {"input": [17], "expected": True, "description": "17 is prime"},
            {"input": [15], "expected": False, "description": "15 is not prime"},
            {"input": [0], "expected": False, "description": "Zero is not prime"},
        ],
        "difficulty": 2,
        "tags": ["numbers", "algorithms"],
    },
    {
        "external_id": "valid-parentheses-v1",
        "title": "Valid Parentheses",
        "description": "Write a function `is_valid(s)` that returns `True` if the string contains only valid matched parentheses `()`, brackets `[]`, and braces `{}`.",
        "skeleton_code": "def is_valid(s):\n    pass\n",
        "test_cases": [
            {"input": ["()"], "expected": True, "description": "Simple pair"},
            {"input": ["()[]{}"], "expected": True, "description": "Multiple types"},
            {"input": ["(]"], "expected": False, "description": "Mismatched"},
            {"input": ["([)]"], "expected": False, "description": "Interleaved"},
            {"input": ["{[]}"], "expected": True, "description": "Nested"},
            {"input": [""], "expected": True, "description": "Empty string"},
        ],
        "difficulty": 2,
        "tags": ["strings", "stacks"],
    },
    {
        "external_id": "run-length-encoding-v1",
        "title": "Run-Length Encoding",
        "description": "Write a function `rle_encode(text)` that performs run-length encoding. Consecutive identical characters are replaced with the character followed by the count (omit count of 1). E.g. 'AABCCCDEEEE' becomes 'A2BC3DE4'.",
        "skeleton_code": "def rle_encode(text):\n    pass\n",
        "test_cases": [
            {"input": ["AABCCCDEEEE"], "expected": "A2BC3DE4", "description": "Mixed runs"},
            {"input": ["ABC"], "expected": "ABC", "description": "No runs"},
            {"input": [""], "expected": "", "description": "Empty string"},
            {"input": ["AAAA"], "expected": "A4", "description": "Single run"},
        ],
        "difficulty": 2,
        "tags": ["strings", "algorithms"],
    },
    {
        "external_id": "collatz-conjecture-v1",
        "title": "Collatz Conjecture",
        "description": "Write a function `collatz_steps(n)` that returns the number of steps to reach 1 using the Collatz sequence. If n is even, divide by 2. If n is odd, multiply by 3 and add 1. Raise `ValueError` if n <= 0.",
        "skeleton_code": "def collatz_steps(n):\n    pass\n",
        "test_cases": [
            {"input": [1], "expected": 0, "description": "Already 1"},
            {"input": [16], "expected": 4, "description": "Power of 2"},
            {"input": [12], "expected": 9, "description": "Twelve"},
            {"input": [1000000], "expected": 152, "description": "Large number"},
        ],
        "difficulty": 2,
        "tags": ["numbers", "algorithms"],
    },
    # =========================================================================
    # TIER 3 — Intermediate (10 challenges)
    # =========================================================================
    {
        "external_id": "spiral-matrix-v1",
        "title": "Spiral Matrix",
        "description": "Write a function `spiral_order(matrix)` that returns all elements of a 2D matrix in spiral order (clockwise from top-left).",
        "skeleton_code": "def spiral_order(matrix):\n    pass\n",
        "test_cases": [
            {"input": [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "expected": [1, 2, 3, 6, 9, 8, 7, 4, 5], "description": "3x3 matrix"},
            {"input": [[[1, 2], [3, 4]]], "expected": [1, 2, 4, 3], "description": "2x2 matrix"},
            {"input": [[[1]]], "expected": [1], "description": "1x1 matrix"},
        ],
        "difficulty": 3,
        "tags": ["lists", "algorithms"],
    },
    {
        "external_id": "anagram-groups-v1",
        "title": "Anagram Groups",
        "description": "Write a function `group_anagrams(words)` that groups a list of words into lists of anagrams. Return a list of lists (order doesn't matter within or between groups).",
        "skeleton_code": "def group_anagrams(words):\n    pass\n",
        "test_cases": [
            {
                "input": [["eat", "tea", "tan", "ate", "nat", "bat"]],
                "expected_sorted": [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]],
                "description": "Standard groups",
            },
            {"input": [[]], "expected": [], "description": "Empty list"},
        ],
        "difficulty": 3,
        "tags": ["strings", "dictionaries", "sorting"],
    },
    {
        "external_id": "merge-intervals-v1",
        "title": "Merge Intervals",
        "description": "Write a function `merge_intervals(intervals)` that merges all overlapping intervals. Input: list of [start, end] pairs. Return merged intervals sorted by start.",
        "skeleton_code": "def merge_intervals(intervals):\n    pass\n",
        "test_cases": [
            {"input": [[[1, 3], [2, 6], [8, 10], [15, 18]]], "expected": [[1, 6], [8, 10], [15, 18]], "description": "Some overlap"},
            {"input": [[[1, 4], [4, 5]]], "expected": [[1, 5]], "description": "Adjacent"},
            {"input": [[[1, 4], [0, 4]]], "expected": [[0, 4]], "description": "Contained"},
        ],
        "difficulty": 3,
        "tags": ["lists", "sorting", "algorithms"],
    },
    {
        "external_id": "longest-common-prefix-v1",
        "title": "Longest Common Prefix",
        "description": "Write a function `longest_prefix(strings)` that returns the longest common prefix among a list of strings. Return '' if there is no common prefix.",
        "skeleton_code": "def longest_prefix(strings):\n    pass\n",
        "test_cases": [
            {"input": [["flower", "flow", "flight"]], "expected": "fl", "description": "Common prefix"},
            {"input": [["dog", "racecar", "car"]], "expected": "", "description": "No common prefix"},
            {"input": [["abc"]], "expected": "abc", "description": "Single string"},
            {"input": [[]], "expected": "", "description": "Empty list"},
        ],
        "difficulty": 3,
        "tags": ["strings"],
    },
    {
        "external_id": "two-sum-v1",
        "title": "Two Sum",
        "description": "Write a function `two_sum(nums, target)` that returns the indices of two numbers that add up to `target`. Assume exactly one solution exists. Return the indices as a sorted list.",
        "skeleton_code": "def two_sum(nums, target):\n    pass\n",
        "test_cases": [
            {"input": [[2, 7, 11, 15], 9], "expected": [0, 1], "description": "First two"},
            {"input": [[3, 2, 4], 6], "expected": [1, 2], "description": "Not first pair"},
            {"input": [[3, 3], 6], "expected": [0, 1], "description": "Same values"},
        ],
        "difficulty": 3,
        "tags": ["lists", "dictionaries", "algorithms"],
    },
    {
        "external_id": "pascal-triangle-v1",
        "title": "Pascal's Triangle",
        "description": "Write a function `pascal(n)` that returns the first `n` rows of Pascal's triangle as a list of lists.",
        "skeleton_code": "def pascal(n):\n    pass\n",
        "test_cases": [
            {"input": [1], "expected": [[1]], "description": "One row"},
            {"input": [4], "expected": [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1]], "description": "Four rows"},
            {"input": [0], "expected": [], "description": "Zero rows"},
        ],
        "difficulty": 3,
        "tags": ["lists", "algorithms"],
    },
    {
        "external_id": "matrix-multiply-v1",
        "title": "Matrix Multiplication",
        "description": "Write a function `matrix_multiply(a, b)` that returns the product of two 2D matrices. Raise `ValueError` if dimensions are incompatible.",
        "skeleton_code": "def matrix_multiply(a, b):\n    pass\n",
        "test_cases": [
            {"input": [[[1, 2], [3, 4]], [[5, 6], [7, 8]]], "expected": [[19, 22], [43, 50]], "description": "2x2 * 2x2"},
            {"input": [[[1, 2, 3]], [[4], [5], [6]]], "expected": [[32]], "description": "1x3 * 3x1"},
        ],
        "difficulty": 3,
        "tags": ["lists", "math", "algorithms"],
    },
    {
        "external_id": "balanced-binary-tree-v1",
        "title": "Balanced Brackets with Depth",
        "description": "Write a function `max_depth(s)` that returns the maximum nesting depth of parentheses in the string. Only consider `()`. Return 0 for an empty string. Raise `ValueError` for unbalanced parentheses.",
        "skeleton_code": "def max_depth(s):\n    pass\n",
        "test_cases": [
            {"input": ["(1+(2*3)+((8)/4))+1"], "expected": 3, "description": "Nested parens"},
            {"input": ["(1)+(2)"], "expected": 1, "description": "Flat parens"},
            {"input": [""], "expected": 0, "description": "Empty string"},
            {"input": ["1+2"], "expected": 0, "description": "No parens"},
        ],
        "difficulty": 3,
        "tags": ["strings", "stacks"],
    },
    {
        "external_id": "permutations-v1",
        "title": "Permutations",
        "description": "Write a function `permutations(lst)` that returns all permutations of a list. Return a list of lists, sorted.",
        "skeleton_code": "def permutations(lst):\n    pass\n",
        "test_cases": [
            {"input": [[1, 2, 3]], "expected": [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]], "description": "Three elements"},
            {"input": [[1]], "expected": [[1]], "description": "Single element"},
            {"input": [[]], "expected": [[]], "description": "Empty list"},
        ],
        "difficulty": 3,
        "tags": ["lists", "recursion", "algorithms"],
    },
    {
        "external_id": "phone-letter-combinations-v1",
        "title": "Phone Letter Combinations",
        "description": "Write a function `letter_combinations(digits)` that returns all possible letter combinations for a phone number digit string (2-9). Use standard phone mapping (2=abc, 3=def, etc). Return [] for empty input.",
        "skeleton_code": "def letter_combinations(digits):\n    pass\n",
        "test_cases": [
            {"input": ["23"], "expected": ["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"], "description": "Two digits"},
            {"input": [""], "expected": [], "description": "Empty input"},
            {"input": ["2"], "expected": ["a", "b", "c"], "description": "Single digit"},
        ],
        "difficulty": 3,
        "tags": ["strings", "recursion", "algorithms"],
    },
    # =========================================================================
    # TIER 4 — Advanced (5 challenges)
    # =========================================================================
    {
        "external_id": "lru-cache-v1",
        "title": "LRU Cache",
        "description": (
            "Implement a class `LRUCache` with `__init__(self, capacity)`, "
            "`get(self, key)` (returns value or -1), and `put(self, key, value)`. "
            "When capacity is exceeded, evict the least recently used item."
        ),
        "skeleton_code": "class LRUCache:\n    def __init__(self, capacity):\n        pass\n\n    def get(self, key):\n        pass\n\n    def put(self, key, value):\n        pass\n",
        "test_cases": [
            {
                "input": "operations",
                "ops": [
                    ["init", 2],
                    ["put", 1, 1],
                    ["put", 2, 2],
                    ["get", 1],
                    ["put", 3, 3],
                    ["get", 2],
                    ["put", 4, 4],
                    ["get", 1],
                    ["get", 3],
                    ["get", 4],
                ],
                "expected": [None, None, None, 1, None, -1, None, -1, 3, 4],
                "description": "Standard LRU operations",
            },
        ],
        "difficulty": 4,
        "tags": ["data-structures", "design"],
    },
    {
        "external_id": "word-break-v1",
        "title": "Word Break",
        "description": "Write a function `word_break(s, word_dict)` that returns `True` if the string `s` can be segmented into space-separated words found in the dictionary.",
        "skeleton_code": "def word_break(s, word_dict):\n    pass\n",
        "test_cases": [
            {"input": ["leetcode", ["leet", "code"]], "expected": True, "description": "Can be segmented"},
            {"input": ["applepenapple", ["apple", "pen"]], "expected": True, "description": "Repeated words"},
            {"input": ["catsandog", ["cats", "dog", "sand", "and", "cat"]], "expected": False, "description": "Cannot be segmented"},
        ],
        "difficulty": 4,
        "tags": ["dynamic-programming", "strings"],
    },
    {
        "external_id": "min-path-sum-v1",
        "title": "Minimum Path Sum",
        "description": "Write a function `min_path_sum(grid)` that finds the path from top-left to bottom-right of a grid (2D list of non-negative integers) with the minimum sum. You can only move right or down.",
        "skeleton_code": "def min_path_sum(grid):\n    pass\n",
        "test_cases": [
            {"input": [[[1, 3, 1], [1, 5, 1], [4, 2, 1]]], "expected": 7, "description": "3x3 grid"},
            {"input": [[[1, 2, 3], [4, 5, 6]]], "expected": 12, "description": "2x3 grid"},
        ],
        "difficulty": 4,
        "tags": ["dynamic-programming", "lists"],
    },
    {
        "external_id": "longest-palindromic-substr-v1",
        "title": "Longest Palindromic Substring",
        "description": "Write a function `longest_palindrome(s)` that returns the longest palindromic substring in `s`.",
        "skeleton_code": "def longest_palindrome(s):\n    pass\n",
        "test_cases": [
            {"input": ["babad"], "expected_in": ["bab", "aba"], "description": "Two valid answers"},
            {"input": ["cbbd"], "expected": "bb", "description": "Even length"},
            {"input": ["a"], "expected": "a", "description": "Single character"},
            {"input": [""], "expected": "", "description": "Empty string"},
        ],
        "difficulty": 4,
        "tags": ["strings", "dynamic-programming"],
    },
    {
        "external_id": "trie-implement-v1",
        "title": "Implement Trie",
        "description": (
            "Implement a class `Trie` with `insert(word)`, `search(word)` "
            "(returns True if word is in trie), and `starts_with(prefix)` "
            "(returns True if any word starts with prefix)."
        ),
        "skeleton_code": "class Trie:\n    def __init__(self):\n        pass\n\n    def insert(self, word):\n        pass\n\n    def search(self, word):\n        pass\n\n    def starts_with(self, prefix):\n        pass\n",
        "test_cases": [
            {
                "input": "operations",
                "ops": [
                    ["init"],
                    ["insert", "apple"],
                    ["search", "apple"],
                    ["search", "app"],
                    ["starts_with", "app"],
                    ["insert", "app"],
                    ["search", "app"],
                ],
                "expected": [None, None, True, False, True, None, True],
                "description": "Standard trie operations",
            },
        ],
        "difficulty": 4,
        "tags": ["data-structures", "design"],
    },
    # =========================================================================
    # TIER 5 — Expert (5 challenges)
    # =========================================================================
    {
        "external_id": "median-two-sorted-v1",
        "title": "Median of Two Sorted Arrays",
        "description": "Write a function `find_median(nums1, nums2)` that returns the median of two sorted arrays. The overall run time complexity should be O(log(m+n)).",
        "skeleton_code": "def find_median(nums1, nums2):\n    pass\n",
        "test_cases": [
            {"input": [[1, 3], [2]], "expected": 2.0, "description": "Odd total"},
            {"input": [[1, 2], [3, 4]], "expected": 2.5, "description": "Even total"},
            {"input": [[], [1]], "expected": 1.0, "description": "One empty"},
        ],
        "difficulty": 5,
        "tags": ["algorithms", "binary-search"],
    },
    {
        "external_id": "regex-matching-v1",
        "title": "Regular Expression Matching",
        "description": "Write a function `is_match(s, p)` that implements regular expression matching with `.` (matches any single char) and `*` (matches zero or more of the preceding element). The matching should cover the entire input string.",
        "skeleton_code": "def is_match(s, p):\n    pass\n",
        "test_cases": [
            {"input": ["aa", "a"], "expected": False, "description": "No match"},
            {"input": ["aa", "a*"], "expected": True, "description": "Star matches two"},
            {"input": ["ab", ".*"], "expected": True, "description": "Dot star matches all"},
            {"input": ["aab", "c*a*b"], "expected": True, "description": "Complex pattern"},
            {"input": ["mississippi", "mis*is*p*."], "expected": False, "description": "No full match"},
        ],
        "difficulty": 5,
        "tags": ["dynamic-programming", "strings"],
    },
    {
        "external_id": "serialize-binary-tree-v1",
        "title": "Serialize and Deserialize Binary Tree",
        "description": (
            "Write two functions: `serialize(root)` converts a binary tree to a string, "
            "and `deserialize(data)` converts the string back. "
            "Use a simple node class: `class TreeNode: def __init__(self, val=0, left=None, right=None)`. "
            "The serialised format is up to you, as long as deserialize(serialize(tree)) recreates the original tree."
        ),
        "skeleton_code": (
            "class TreeNode:\n    def __init__(self, val=0, left=None, right=None):\n"
            "        self.val = val\n        self.left = left\n        self.right = right\n\n"
            "def serialize(root):\n    pass\n\n"
            "def deserialize(data):\n    pass\n"
        ),
        "test_cases": [
            {
                "input": "tree_ops",
                "tree": [1, 2, 3, None, None, 4, 5],
                "description": "Roundtrip serialization",
            },
        ],
        "difficulty": 5,
        "tags": ["trees", "design"],
    },
    {
        "external_id": "knapsack-01-v1",
        "title": "0/1 Knapsack",
        "description": "Write a function `knapsack(capacity, weights, values)` that returns the maximum value achievable by selecting items (each item can be used at most once) without exceeding the weight capacity.",
        "skeleton_code": "def knapsack(capacity, weights, values):\n    pass\n",
        "test_cases": [
            {"input": [50, [10, 20, 30], [60, 100, 120]], "expected": 220, "description": "Classic example"},
            {"input": [0, [10, 20], [100, 200]], "expected": 0, "description": "Zero capacity"},
            {"input": [10, [5, 4, 6, 3], [10, 40, 30, 50]], "expected": 90, "description": "Optimal selection"},
        ],
        "difficulty": 5,
        "tags": ["dynamic-programming", "algorithms"],
    },
    {
        "external_id": "edit-distance-v1",
        "title": "Edit Distance",
        "description": "Write a function `edit_distance(word1, word2)` that returns the minimum number of operations (insert, delete, replace) required to convert `word1` to `word2`.",
        "skeleton_code": "def edit_distance(word1, word2):\n    pass\n",
        "test_cases": [
            {"input": ["horse", "ros"], "expected": 3, "description": "Horse to ros"},
            {"input": ["intention", "execution"], "expected": 5, "description": "Longer words"},
            {"input": ["", "abc"], "expected": 3, "description": "Empty to word"},
            {"input": ["abc", "abc"], "expected": 0, "description": "Identical"},
        ],
        "difficulty": 5,
        "tags": ["dynamic-programming", "strings"],
    },
]


class Command(BaseCommand):
    help = "Seed coding challenges (idempotent by external_id)."

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for c_data in CHALLENGES:
            _, created = Challenge.objects.get_or_create(
                external_id=c_data["external_id"],
                defaults={
                    "title": c_data["title"],
                    "description": c_data["description"],
                    "skeleton_code": c_data["skeleton_code"],
                    "test_cases": c_data["test_cases"],
                    "difficulty": c_data["difficulty"],
                    "tags": c_data.get("tags", []),
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created_count}, "
                f"Skipped (already exist): {skipped_count}",
            ),
        )
