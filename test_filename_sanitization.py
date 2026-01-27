#!/usr/bin/env python3
"""
Unit tests voor Obsidian filename sanitization.

Test dat titels met ongeldige karakters correct worden gesanitizeerd
voor gebruik als Obsidian bestandsnamen.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.obsidian.uri_builder import sanitize_filename


def test_sanitize_filename():
    """Test alle edge cases voor filename sanitization."""

    test_cases = [
        # (input, expected_output, description)

        # Dubbele punt → spatie-dash
        ("AI: De nieuwe revolutie", "AI - De nieuwe revolutie", "Colon replacement"),
        ("Vraag: Is AI veilig?", "Vraag - Is AI veilig", "Colon with question mark"),

        # Slash → dash
        ("GPT-4/Claude vergelijking", "GPT-4-Claude vergelijking", "Forward slash"),
        ("A/B testing voor prompts", "A-B testing voor prompts", "Multiple slashes"),

        # Backslash → dash
        ("Path\\to\\file", "Path-to-file", "Backslash replacement"),

        # Asterisk verwijderen
        ("Breaking news*", "Breaking news", "Trailing asterisk"),
        ("*Important* update", "Important update", "Asterisks around word"),

        # Vraagteken verwijderen
        ("Wat is AI?", "Wat is AI", "Question mark removal"),
        ("Hoe werkt het? En waarom?", "Hoe werkt het En waarom", "Multiple question marks"),

        # Dubbele quotes → enkele quotes
        ('Wat is "prompt engineering"?', "Wat is 'prompt engineering'", "Quote conversion"),
        ('"Revolutionary" AI model', "'Revolutionary' AI model", "Quoted word"),

        # Kleiner/groter dan verwijderen
        ("<html> tags in AI", "html tags in AI", "HTML tags"),
        ("A > B < C", "A B C", "Comparison operators"),  # Multiple spaces collapsed to single

        # Pipe → dash
        ("Option A | Option B", "Option A - Option B", "Pipe separator"),

        # Combinatie van meerdere ongeldige karakters
        ('AI: "De toekomst"? | Ja/Nee', "AI - 'De toekomst' - Ja-Nee", "Multiple invalid chars"),

        # Edge cases
        ("", "", "Empty string"),
        ("   ", "", "Only whitespace"),
        ("---", "", "Only dashes"),
        ("  Leading/trailing  ", "Leading-trailing", "Whitespace cleanup"),
        ("Multiple   spaces", "Multiple spaces", "Multiple spaces collapsed"),
        ("Multiple---dashes", "Multiple-dashes", "Multiple dashes collapsed"),

        # Normaal geldige titels (geen wijzigingen)
        ("Claude Sonnet 4.5 release", "Claude Sonnet 4.5 release", "Normal title"),
        ("AI News Update (2024)", "AI News Update (2024)", "With parentheses"),
        ("GPT-4 vs Claude-3", "GPT-4 vs Claude-3", "With hyphens"),
    ]

    print("=" * 80)
    print("TESTING FILENAME SANITIZATION")
    print("=" * 80)

    passed = 0
    failed = 0

    for input_str, expected, description in test_cases:
        result = sanitize_filename(input_str)

        if result == expected:
            print(f"✓ PASS: {description}")
            print(f"  Input:    '{input_str}'")
            print(f"  Output:   '{result}'")
            passed += 1
        else:
            print(f"✗ FAIL: {description}")
            print(f"  Input:    '{input_str}'")
            print(f"  Expected: '{expected}'")
            print(f"  Got:      '{result}'")
            failed += 1
        print()

    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0


def test_obsidian_invalid_chars():
    r"""
    Verify dat ALLE Obsidian ongeldige karakters worden afgehandeld.

    Obsidian bestandsnamen kunnen NIET bevatten: / \ : * ? " < > |
    """
    print("\n" + "=" * 80)
    print("TESTING ALL OBSIDIAN INVALID CHARACTERS")
    print("=" * 80)

    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']

    all_pass = True
    for char in invalid_chars:
        test_input = f"Test{char}File"
        result = sanitize_filename(test_input)

        # Resultaat mag het karakter NIET bevatten
        if char in result:
            print(f"✗ FAIL: Character '{char}' still present in result: '{result}'")
            all_pass = False
        else:
            print(f"✓ PASS: Character '{char}' correctly removed/replaced")

    print("=" * 80)
    return all_pass


if __name__ == '__main__':
    # Run tests
    test1_pass = test_sanitize_filename()
    test2_pass = test_obsidian_invalid_chars()

    # Exit code
    if test1_pass and test2_pass:
        print("\n✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
