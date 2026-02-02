import sys
import os
import pandas as pd
import hashlib
sys.path.append('../')
from utils.common import common_args

datasets_2k = [
    "Proxifier",
    "Linux",
    "Apache",
    "Zookeeper",
    "Hadoop",
    "HealthApp",
    "OpenStack",
    "HPC",
    "Mac",
    "OpenSSH",
    "Spark",
    "Thunderbird",
    "BGL",
    "HDFS",
]

datasets_full = [
    "Proxifier",
    "Linux",
    "Apache",
    "Zookeeper",
    "Hadoop",
    "HealthApp",
    "OpenStack",
    "HPC",
    "Mac",
    "OpenSSH",
    "Spark",
    "Thunderbird",
    "BGL",
    "HDFS",
]

def merge_results(dataset, data_type, input_drain_dir, input_uniparser_dir, output_dir):
    """
    Merge Drain and UniParser results:
    - Keep high-confidence Drain results
    - Replace low-confidence results with UniParser results
    - Recalculate template occurrences
    """
    print(f'\n=== Merging results for {dataset} ===')
    
    # File paths
    base_name = f"{dataset}_{data_type}.log"
    drain_structured = os.path.join(input_drain_dir, f"{base_name}_structured.csv")
    drain_low_conf_with_id = os.path.join(input_drain_dir, f"{base_name}_low_confidence_with_eventid.csv")
    
    # UniParser outputs using the base log name (strips _low_confidence)
    uniparser_structured = os.path.join(input_uniparser_dir, f"{base_name}_structured.csv")
    
    output_structured = os.path.join(output_dir, f"{base_name}_structured.csv")
    output_templates = os.path.join(output_dir, f"{base_name}_templates.csv")
    
    # Check if files exist
    if not os.path.exists(drain_structured):
        print(f"ERROR: Drain structured file not found: {drain_structured}")
        return
    
    if not os.path.exists(drain_low_conf_with_id):
        print(f"WARNING: No low-confidence file found. Copying Drain results as-is.")
        # Just copy Drain results
        df_drain = pd.read_csv(drain_structured)
        df_drain.to_csv(output_structured, index=False)
        # Copy templates too
        drain_templates = os.path.join(input_drain_dir, f"{base_name}_templates.csv")
        if os.path.exists(drain_templates):
            df_templates = pd.read_csv(drain_templates)
            df_templates.to_csv(output_templates, index=False)
        return
    
    if not os.path.exists(uniparser_structured):
        print(f"ERROR: UniParser structured file not found: {uniparser_structured}")
        return
    
    # Load data
    print("Loading Drain structured file...")
    df_drain = pd.read_csv(drain_structured)
    
    print("Loading low-confidence mapping file...")
    df_low_conf = pd.read_csv(drain_low_conf_with_id)
    
    print("Loading UniParser results...")
    df_uniparser = pd.read_csv(uniparser_structured)
    
    # Verify row counts match
    if len(df_low_conf) != len(df_uniparser):
        print(f"ERROR: Row count mismatch!")
        print(f"  Low-confidence file: {len(df_low_conf)} rows")
        print(f"  UniParser file: {len(df_uniparser)} rows")
        return
    
    print(f"Processing {len(df_low_conf)} low-confidence logs...")
    
    # Create a merged dataframe starting with Drain results
    df_merged = df_drain.copy()
    
    # For each low-confidence log, find it in the merged dataframe and update it
    replaced_count = 0
    for idx in range(len(df_low_conf)):
        low_conf_row = df_low_conf.iloc[idx]
        uniparser_row = df_uniparser.iloc[idx]
        
        # Find matching row in merged dataframe by Content
        # We use Content as the primary key since it's unique enough
        content = low_conf_row['Content']
        
        # Find all rows with matching content
        matches = df_merged[df_merged['Content'] == content]
        
        if len(matches) == 0:
            print(f"WARNING: Could not find match for: {content[:50]}...")
            continue
        
        # If multiple matches, use additional fields to narrow down
        if len(matches) > 1:
            # Try to match using Time and Level if available
            if 'Time' in low_conf_row and 'Level' in low_conf_row:
                matches = matches[
                    (matches['Time'] == low_conf_row['Time']) & 
                    (matches['Level'] == low_conf_row['Level'])
                ]
        
        # Get the first match (should be unique now)
        if len(matches) > 0:
            match_idx = matches.index[0]
            
            # Get UniParser's EventTemplate
            uniparser_template = uniparser_row['EventTemplate']
            
            # Generate MD5 hash for EventId (to match Drain's format)
            event_id = hashlib.md5(uniparser_template.encode('utf-8')).hexdigest()[0:8]
            
            # Replace EventId and EventTemplate with UniParser's values
            df_merged.at[match_idx, 'EventId'] = event_id
            df_merged.at[match_idx, 'EventTemplate'] = uniparser_template
            replaced_count += 1
    
    print(f"Replaced {replaced_count} low-confidence results with UniParser results")
    
    # Remove the Confidence column before saving (not needed in final output)
    if 'Confidence' in df_merged.columns:
        df_merged = df_merged.drop(columns=['Confidence'])
    
    # Save merged structured file
    print(f"Saving merged structured file to {output_structured}")
    df_merged.to_csv(output_structured, index=False)
    
    # Recalculate templates from merged structured file
    print("Recalculating template occurrences...")
    template_counts = df_merged['EventTemplate'].value_counts().to_dict()
    
    # Create templates dataframe
    unique_templates = df_merged['EventTemplate'].unique()
    df_templates = pd.DataFrame({
        'EventTemplate': unique_templates,
        'EventId': [hashlib.md5(t.encode('utf-8')).hexdigest()[0:8] for t in unique_templates],
        'Occurrences': [template_counts[t] for t in unique_templates]
    })
    
    # Sort by occurrences (descending)
    df_templates = df_templates.sort_values('Occurrences', ascending=False)
    
    # Save templates file
    print(f"Saving merged templates file to {output_templates}")
    df_templates.to_csv(output_templates, index=False, columns=['EventId', 'EventTemplate', 'Occurrences'])
    
    print(f"Merge complete!")
    print(f"  Total logs: {len(df_merged)}")
    print(f"  Unique templates: {len(df_templates)}")
    print(f"  Low-confidence replaced: {replaced_count}")


if __name__ == "__main__":
    args = common_args()
    data_type = "full" if args.full_data else "2k"
    
    input_drain_dir = f"../../result/result_Drain_{data_type}"
    input_uniparser_dir = f"../../result/result_UniParser_{data_type}"
    output_dir = f"../../result/result_DrainUP_{data_type}"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if args.full_data:
        datasets = datasets_full
    else:
        datasets = datasets_2k
    
    for dataset in datasets:
        merge_results(
            dataset=dataset,
            data_type=data_type,
            input_drain_dir=input_drain_dir,
            input_uniparser_dir=input_uniparser_dir,
            output_dir=output_dir
        )
    
    print('\n=== All merges complete! ===')
