#!/usr/bin/env python3
"""
Integration test voor filename sanitization met Obsidian URI builder.

Test dat de sanitize functie correct werkt binnen de volledige URI building flow.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.obsidian.uri_builder import build_uri_from_dict


def main():
    """Test URI building met edge case titels."""

    print("=" * 80)
    print("TESTING URI BUILDING WITH SANITIZED FILENAMES")
    print("=" * 80)

    # Test cases met problematische titels
    test_summaries = [
        {
            'title': 'AI: De nieuwe revolutie',
            'why_matters': 'Breakthrough in AI safety',
            'big_picture': 'Major development in the field',
            'key_details': 'Detail 1\nDetail 2',
            'next_step': 'Available next month',
            'source_name': 'TechCrunch',
            'source_url': 'https://techcrunch.com/article'
        },
        {
            'title': 'GPT-4/Claude vergelijking',
            'why_matters': 'Head-to-head comparison',
            'big_picture': 'Two frontier models compared',
            'key_details': 'Performance metrics\nCost analysis',
            'next_step': 'Choose the right model',
            'source_name': 'AI News',
            'source_url': 'https://example.com'
        },
        {
            'title': 'Wat is "prompt engineering"?',
            'why_matters': 'Essential AI skill',
            'big_picture': 'How to get better results from LLMs',
            'key_details': 'Techniques and best practices',
            'next_step': 'Try it yourself',
            'source_name': 'Prompt Guide',
            'source_url': 'https://example.com/prompts'
        },
        {
            'title': 'AI Models: GPT-4 vs Claude-3 | Full Analysis',
            'why_matters': 'Comprehensive comparison',
            'big_picture': 'Which model to use when',
            'key_details': 'Speed\nQuality\nCost',
            'next_step': 'Make informed decision',
            'source_name': 'AI Review',
            'source_url': 'https://example.com/review'
        }
    ]

    all_pass = True

    for i, summary in enumerate(test_summaries, 1):
        print(f"\nTest {i}: {summary['title']}")
        print("-" * 80)

        uri = build_uri_from_dict(summary)

        if not uri:
            print(f"✗ FAIL: No URI generated")
            all_pass = False
            continue

        # Check dat URI begint met obsidian://
        if not uri.startswith('obsidian://new'):
            print(f"✗ FAIL: Invalid URI format")
            print(f"  URI: {uri[:100]}...")
            all_pass = False
            continue

        # Check dat alle ongeldige karakters NIET in de file parameter zitten
        # Extract file parameter
        import urllib.parse
        parsed = urllib.parse.urlparse(uri)
        params = urllib.parse.parse_qs(parsed.query)

        if 'file' not in params:
            print(f"✗ FAIL: No file parameter in URI")
            all_pass = False
            continue

        file_path = params['file'][0]

        # Check voor ongeldige karakters in bestandsnaam
        invalid_chars = [':', '/', '\\', '*', '?', '"', '<', '>', '|']
        # Extract alleen de bestandsnaam (na laatste /)
        filename = file_path.split('/')[-1]

        found_invalid = []
        for char in invalid_chars:
            if char in filename:
                found_invalid.append(char)

        if found_invalid:
            print(f"✗ FAIL: Found invalid characters in filename: {found_invalid}")
            print(f"  Filename: {filename}")
            all_pass = False
        else:
            print(f"✓ PASS: Filename is valid")
            print(f"  Original: {summary['title']}")
            print(f"  Sanitized filename: {filename}")
            print(f"  Full file path: {file_path}")

    print("\n" + "=" * 80)
    if all_pass:
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("=" * 80)
        print("\nObsidian URIs worden correct gebouwd met gesanitizeerde bestandsnamen.")
        print("Edge case titels met ongeldige karakters worden veilig verwerkt.")
        return 0
    else:
        print("✗ SOME INTEGRATION TESTS FAILED")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    sys.exit(main())
