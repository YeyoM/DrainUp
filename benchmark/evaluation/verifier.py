import pandas as pd
import hashlib
import sys

def verify_merge(dataset, data_type="2k"):
    """
    Verify the merge logic by checking:
    1. EventId consistency (same template = same EventId)
    2. EventId format (all MD5 hashes)
    3. Low-confidence replacements
    4. Template matching
    """
    print(f"\n{'='*60}")
    print(f"VERIFICATION FOR {dataset}")
    print(f"{'='*60}")
    
    drain_dir = f"../../result/result_Drain_{data_type}"
    uniparser_dir = f"../../result/result_UniParser_{data_type}"
    drainup_dir = f"../../result/result_DrainUP_{data_type}"
    
    base_name = f"{dataset}_{data_type}.log"
    
    # Load files
    print("\n1. Loading files...")
    df_drain = pd.read_csv(f"{drain_dir}/{base_name}_structured.csv")
    df_drainup = pd.read_csv(f"{drainup_dir}/{base_name}_structured.csv")
    df_low_conf = pd.read_csv(f"{drain_dir}/{base_name}_low_confidence_with_eventid.csv")
    df_uniparser = pd.read_csv(f"{uniparser_dir}/{base_name}_structured.csv")
    
    print(f"   Drain rows: {len(df_drain)}")
    print(f"   DrainUP rows: {len(df_drainup)}")
    print(f"   Low-confidence rows: {len(df_low_conf)}")
    print(f"   UniParser rows: {len(df_uniparser)}")
    
    # Check 1: Row counts match
    print("\n2. Checking row counts...")
    if len(df_drain) != len(df_drainup):
        print(f"   ❌ ERROR: Row count mismatch!")
    else:
        print(f"   ✓ Row counts match: {len(df_drain)}")
    
    # Check 2: EventId format (should all be 8-char hex)
    print("\n3. Checking EventId format...")
    invalid_ids = []
    for idx, row in df_drainup.iterrows():
        event_id = str(row['EventId'])
        if len(event_id) != 8 or not all(c in '0123456789abcdef' for c in event_id.lower()):
            invalid_ids.append((idx, event_id))
    
    if invalid_ids:
        print(f"   ❌ Found {len(invalid_ids)} invalid EventIds:")
        for idx, eid in invalid_ids[:5]:
            print(f"      Row {idx}: '{eid}'")
    else:
        print(f"   ✓ All EventIds are valid 8-char MD5 hashes")
    
    # Check 3: EventId consistency (same template should have same EventId)
    print("\n4. Checking EventId consistency...")
    template_to_ids = {}
    for idx, row in df_drainup.iterrows():
        template = row['EventTemplate']
        event_id = row['EventId']
        
        if template not in template_to_ids:
            template_to_ids[template] = set()
        template_to_ids[template].add(event_id)
    
    inconsistent_templates = {t: ids for t, ids in template_to_ids.items() if len(ids) > 1}
    
    if inconsistent_templates:
        print(f"   ❌ Found {len(inconsistent_templates)} templates with multiple EventIds:")
        for template, ids in list(inconsistent_templates.items())[:3]:
            print(f"      Template: {template[:60]}...")
            print(f"      EventIds: {ids}")
    else:
        print(f"   ✓ All templates have consistent EventIds")
    
    # Check 4: Verify EventId is correct MD5 hash of template
    print("\n5. Checking EventId = MD5(template)...")
    mismatched = []
    for idx, row in df_drainup.iterrows():
        template = row['EventTemplate']
        event_id = row['EventId']
        expected_id = hashlib.md5(template.encode('utf-8')).hexdigest()[0:8]
        
        if event_id != expected_id:
            mismatched.append((idx, template[:50], event_id, expected_id))
    
    if mismatched:
        print(f"   ❌ Found {len(mismatched)} EventIds that don't match MD5(template):")
        for idx, template, actual, expected in mismatched[:5]:
            print(f"      Row {idx}: {template}...")
            print(f"         Actual: {actual}, Expected: {expected}")
    else:
        print(f"   ✓ All EventIds match MD5(template)")
    
    # Check 5: Verify low-confidence replacements
    print("\n6. Verifying low-confidence replacements...")
    replaced_count = 0
    not_replaced = []
    
    for idx in range(len(df_low_conf)):
        low_conf_row = df_low_conf.iloc[idx]
        uniparser_row = df_uniparser.iloc[idx]
        
        # Find in DrainUP
        content = low_conf_row['Content']
        matches = df_drainup[df_drainup['Content'] == content]
        
        if len(matches) == 0:
            not_replaced.append(content[:50])
            continue
        
        drainup_row = matches.iloc[0]
        
        # Check if EventTemplate was replaced with UniParser's
        uniparser_template = uniparser_row['EventTemplate']
        drainup_template = drainup_row['EventTemplate']
        
        if drainup_template == uniparser_template:
            replaced_count += 1
        else:
            print(f"   ! Row {idx}: Template mismatch")
            print(f"      UniParser: {uniparser_template}")
            print(f"      DrainUP:   {drainup_template}")
    
    print(f"   Replaced: {replaced_count}/{len(df_low_conf)}")
    if not_replaced:
        print(f"   ❌ Could not find {len(not_replaced)} low-confidence rows in DrainUP")
    
    # Check 6: Compare templates files
    print("\n7. Checking templates files...")
    df_drain_templates = pd.read_csv(f"{drain_dir}/{base_name}_templates.csv")
    df_drainup_templates = pd.read_csv(f"{drainup_dir}/{base_name}_templates.csv")
    
    print(f"   Drain templates: {len(df_drain_templates)}")
    print(f"   DrainUP templates: {len(df_drainup_templates)}")
    
    # Verify template occurrences match actual counts
    print("\n8. Verifying template occurrence counts...")
    actual_counts = df_drainup['EventTemplate'].value_counts().to_dict()
    
    mismatched_counts = []
    for idx, row in df_drainup_templates.iterrows():
        template = row['EventTemplate']
        reported = row['Occurrences']
        actual = actual_counts.get(template, 0)
        
        if reported != actual:
            mismatched_counts.append((template[:50], reported, actual))
    
    if mismatched_counts:
        print(f"   ❌ Found {len(mismatched_counts)} templates with incorrect occurrence counts:")
        for template, reported, actual in mismatched_counts[:5]:
            print(f"      {template}...")
            print(f"         Reported: {reported}, Actual: {actual}")
    else:
        print(f"   ✓ All template occurrence counts are correct")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY:")
    issues = []
    if len(df_drain) != len(df_drainup):
        issues.append("Row count mismatch")
    if invalid_ids:
        issues.append(f"{len(invalid_ids)} invalid EventIds")
    if inconsistent_templates:
        issues.append(f"{len(inconsistent_templates)} inconsistent templates")
    if mismatched:
        issues.append(f"{len(mismatched)} EventId hash mismatches")
    if not_replaced:
        issues.append(f"{len(not_replaced)} missing replacements")
    if mismatched_counts:
        issues.append(f"{len(mismatched_counts)} wrong occurrence counts")
    
    if issues:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✓ All checks passed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    datasets = ["HealthApp", "OpenStack", "Apache", "Zookeeper"]
    
    if len(sys.argv) > 1:
        datasets = [sys.argv[1]]
    
    for dataset in datasets:
        try:
            verify_merge(dataset)
        except Exception as e:
            print(f"\n❌ ERROR processing {dataset}: {e}")
            import traceback
            traceback.print_exc()
