from genealogy.core.date_normalizer import DateNormalizer
import re
from genealogy.core.patterns import DEATH_PATTERNS, AGE_PATTERNS

def test_date_extraction():
    # Simulate meta description and main obituary text
    meta_desc = "Reunited with her husband Terrence and daughter Patricia on May 24, 2018 at the age of 87 years."
    main_text = meta_desc + " Some extra text that might be in the full obituary, with more details and possibly more noise."
    
    def debug_patterns(label, text):
        norm_text = ' '.join(text.split())
        print(f"\nPattern debug for {label} (normalized): {norm_text}")
        print("Death patterns:")
        for pat in DEATH_PATTERNS:
            m = re.search(pat, norm_text, re.IGNORECASE)
            print(f"Pattern: {pat} => Match: {m.group(1) if m else None}")
        print("Age patterns:")
        for pat in AGE_PATTERNS:
            m = re.search(pat, norm_text, re.IGNORECASE)
            print(f"Pattern: {pat} => Match: {m.group(1) if m else None}")

    print("Testing date extraction with meta description:")
    print(f"Meta description: {meta_desc}\n")
    debug_patterns("meta_desc", meta_desc)
    death_date = DateNormalizer.find_death_date(meta_desc)
    age = DateNormalizer.find_age(meta_desc)
    print(f"Death date (meta): {death_date}")
    print(f"Age (meta): {age}")
    if death_date and age:
        birth_date = DateNormalizer.calculate_birth_date(death_date, age)
        print(f"Calculated birth date (meta): {birth_date}")
    print("\n---\n")
    print("Testing date extraction with main text:")
    print(f"Main text: {main_text}\n")
    debug_patterns("main_text", main_text)
    death_date_main = DateNormalizer.find_death_date(main_text)
    age_main = DateNormalizer.find_age(main_text)
    print(f"Death date (main): {death_date_main}")
    print(f"Age (main): {age_main}")
    if death_date_main and age_main:
        birth_date_main = DateNormalizer.calculate_birth_date(death_date_main, age_main)
        print(f"Calculated birth date (main): {birth_date_main}")

if __name__ == "__main__":
    test_date_extraction() 