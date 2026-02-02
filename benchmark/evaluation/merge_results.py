import sys
import os
import shutil
import pandas as pd
from collections import defaultdict, deque, Counter

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

def _safe_read_csv(path, **kwargs):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path, **kwargs)

def merge_results(dataset,
                  input_drain_dir,
                  input_uniparser_dir,
                  output_dir,
                  data_type="2k",
                  make_backups: bool = True):
    """
    Merge Drain + UniParser results for a single dataset.

    Changes:
    - File paths use pattern: {dataset}_{data_type}.log_*.csv
    - For each Drain EventId that UniParser produced templates for (via mapping),
      replace EventTemplate for ALL structured rows with that EventId by the
      most-common UniParser template mapped to that EventId.
    - Recompute template occurrences after replacement.
    """
    print(f"\n--- Merging dataset: {dataset} ---")

    # Input file paths (updated to requested pattern)
    drain_struct_path = os.path.join(input_drain_dir, f"{dataset}_{data_type}.log_structured.csv")
    drain_low_with_eid_path = os.path.join(input_drain_dir, f"{dataset}_{data_type}.log_low_confidence_with_eventid.csv")
    uni_struct_path = os.path.join(input_uniparser_dir, f"{dataset}_{data_type}.log_structured.csv")
    uni_templates_path = os.path.join(input_uniparser_dir, f"{dataset}_{data_type}.log_templates.csv")

    # Output file paths
    out_struct_path = os.path.join(output_dir, f"{dataset}_{data_type}.log_structured.csv")
    out_templates_path = os.path.join(output_dir, f"{dataset}_{data_type}.log_templates.csv")
    mapping_path = os.path.join(output_dir, f"{dataset}_{data_type}.uni_to_drain_mapping.csv")
    backups_dir = os.path.join(output_dir, "backups")

    # Read inputs
    try:
        drain_struct = _safe_read_csv(drain_struct_path, encoding='utf-8-sig', dtype=str)
        drain_low = _safe_read_csv(drain_low_with_eid_path, encoding='utf-8-sig', dtype=str)
        uni_struct = _safe_read_csv(uni_struct_path, encoding='utf-8-sig', dtype=str)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return

    # Backups of UniParser inputs (safe-guard)
    if make_backups:
        os.makedirs(backups_dir, exist_ok=True)
        try:
            shutil.copy2(uni_struct_path, os.path.join(backups_dir, os.path.basename(uni_struct_path)))
            if os.path.exists(uni_templates_path):
                shutil.copy2(uni_templates_path, os.path.join(backups_dir, os.path.basename(uni_templates_path)))
            print(f"[INFO] Backed up UniParser input files to {backups_dir}")
        except Exception as e:
            print(f"[WARN] Could not create backups: {e}")

    # Validate presence of Content column (required)
    if 'Content' not in drain_struct.columns:
        raise KeyError("Drain structured missing required column: 'Content'")
    if 'Content' not in drain_low.columns:
        raise KeyError("Drain low_confidence missing required column: 'Content'")
    if 'Content' not in uni_struct.columns:
        raise KeyError("UniParser structured must have a 'Content' column")

    # Decide matching keys (Level optional)
    possible = []
    if 'Time' in drain_struct.columns and 'Time' in drain_low.columns:
        possible.append('Time')
    if 'Level' in drain_struct.columns and 'Level' in drain_low.columns:
        possible.append('Level')
    # Content is always present
    if 'Time' in possible and 'Level' in possible:
        match_keys = ['Time', 'Level', 'Content']
    elif 'Time' in possible:
        match_keys = ['Time', 'Content']
    elif 'Level' in possible:
        match_keys = ['Level', 'Content']
    else:
        match_keys = ['Content']

    print(f"[INFO] Using match keys: {match_keys}")

    # Normalization helper
    def _norm(x):
        if pd.isna(x):
            return ""
        return str(x).strip()

    # Build candidate_map using chosen match_keys
    candidate_map = defaultdict(deque)
    drain_positions = list(drain_struct.index)
    for pos in drain_positions:
        key = tuple(_norm(drain_struct.at[pos, k]) if k in drain_struct.columns else "" for k in match_keys)
        candidate_map[key].append(pos)

    # Map each drain_low row in order to the next unused drain_struct position
    used_idx = set()
    mappings = []
    for low_idx in range(len(drain_low)):
        low_row = drain_low.iloc[low_idx]
        key = tuple(_norm(low_row[k]) if k in drain_low.columns else "" for k in match_keys)
        mapped_pos = None
        if candidate_map.get(key):
            while candidate_map[key]:
                pos = candidate_map[key].popleft()
                if pos not in used_idx:
                    mapped_pos = pos
                    break
        if mapped_pos is None:
            # Fallback: match by Content only (search next unused)
            content_key = _norm(low_row.get('Content', ""))
            found = False
            for pos in drain_positions:
                if pos in used_idx:
                    continue
                if _norm(drain_struct.at[pos, 'Content']) == content_key:
                    mapped_pos = pos
                    found = True
                    break
            if not found:
                print(f"[WARN] Could not find matching Drain structured row for drain_low row {low_idx} using keys {match_keys}. "
                      "This low-confidence row will be skipped.")
                mappings.append({
                    'low_row_index': low_idx,
                    'mapped_drain_index': None,
                    'drain_eventid': _norm(low_row.get('EventId', "")),
                    'uni_row_index': None,
                    'uni_eventid_original': None,
                    'uni_eventtemplate': None,
                    'drain_LineId': None,
                })
                continue

        used_idx.add(mapped_pos)
        mappings.append({
            'low_row_index': low_idx,
            'mapped_drain_index': mapped_pos,
            'drain_eventid': _norm(low_row.get('EventId', "")),
            'uni_row_index': None,
            'uni_eventid_original': None,
            'uni_eventtemplate': None,
            'drain_LineId': drain_struct.at[mapped_pos, 'LineId'] if 'LineId' in drain_struct.columns else None,
        })

    # Assign UniParser rows (in order) to mappings (in order)
    uni_len = len(uni_struct)
    m_idx = 0
    assigned_mappings = []  # will hold mappings that actually got uni rows assigned
    for uni_idx in range(uni_len):
        # find next mapping with a mapped_drain_index not None
        while m_idx < len(mappings) and mappings[m_idx]['mapped_drain_index'] is None:
            m_idx += 1
        if m_idx >= len(mappings):
            print(f"[WARN] More UniParser rows ({uni_len}) than mappings ({len(mappings)}). Extra UniParser rows will be ignored.")
            break
        mapping = mappings[m_idx]
        mapping['uni_row_index'] = uni_idx
        uni_row = uni_struct.iloc[uni_idx]
        mapping['uni_eventid_original'] = _norm(uni_row.get('EventId', ""))
        mapping['uni_eventtemplate'] = _norm(uni_row.get('EventTemplate', ""))
        assigned_mappings.append(mapping)
        m_idx += 1

    # Build DrainEventId -> Counter(uni_templates) from assigned_mappings
    drainid_to_uni_templates = defaultdict(Counter)
    for mp in assigned_mappings:
        if mp['mapped_drain_index'] is None:
            continue
        did = mp['drain_eventid']
        tmpl = mp['uni_eventtemplate']
        if tmpl:
            drainid_to_uni_templates[did][tmpl] += 1

    # For each drain_eventid that UniParser provided templates for,
    # pick most common uni template and apply it to ALL drain_struct rows with that EventId.
    templates_replaced = 0
    for drain_eid, counter in drainid_to_uni_templates.items():
        if not counter:
            continue
        chosen_template, count = counter.most_common(1)[0]
        # replace all structured rows that have EventId == drain_eid
        mask = drain_struct['EventId'].astype(str) == str(drain_eid)
        affected = mask.sum()
        if affected == 0:
            # If no rows currently have that EventId, still continue (shouldn't happen often)
            print(f"[WARN] No structured rows found with EventId {drain_eid} while trying to apply UniParser template.")
            continue
        # Ensure column exists
        if 'EventTemplate' not in drain_struct.columns:
            drain_struct['EventTemplate'] = ""
        drain_struct.loc[mask, 'EventTemplate'] = chosen_template
        templates_replaced += affected

    print(f"[INFO] Applied UniParser templates to {len(drainid_to_uni_templates)} Drain EventIds, affecting {templates_replaced} structured rows total.")

    # Final sanity & recompute templates
    total_struct_rows = len(drain_struct)
    drain_struct['EventId'] = drain_struct['EventId'].astype(str)
    drain_struct['EventTemplate'] = drain_struct['EventTemplate'].astype(str)

    merged_templates = (
        drain_struct
        .groupby(['EventId', 'EventTemplate'], dropna=False)
        .size()
        .reset_index(name='Occurrences')
        .sort_values(by=['Occurrences'], ascending=False)
    )

    # Write outputs
    os.makedirs(output_dir, exist_ok=True)
    try:
        drain_struct.to_csv(out_struct_path, index=False, encoding='utf-8')
        print(f"[INFO] Wrote merged structured file to: {out_struct_path}")
    except Exception as e:
        print(f"[ERROR] Could not write merged structured file: {e}")

    try:
        merged_templates.to_csv(out_templates_path, index=False, encoding='utf-8')
        print(f"[INFO] Wrote merged templates file to: {out_templates_path}")
    except Exception as e:
        print(f"[ERROR] Could not write merged templates file: {e}")

    # Write mapping for traceability (include assigned_mappings so you see which uni rows were used)
    mapping_df = pd.DataFrame(mappings)
    try:
        mapping_df.to_csv(mapping_path, index=False, encoding='utf-8')
        print(f"[INFO] Wrote mapping file to: {mapping_path}")
    except Exception as e:
        print(f"[WARN] Could not write mapping file: {e}")

    # Final checks
    occurrences_sum = merged_templates['Occurrences'].sum()
    if occurrences_sum != total_struct_rows:
        print(f"[WARN] Sum of template occurrences ({occurrences_sum}) != number of structured rows ({total_struct_rows}). "
              "Double-check merged output.")
    else:
        print(f"[OK] Template occurrences sum matches structured rows ({total_struct_rows}).")

    print(f"[DONE] Dataset {dataset}: structured_rows={total_struct_rows}, templates={len(merged_templates)}\n")


def merge_results_wrapper():
    args = common_args()
    data_type = "full" if args.full_data else "2k"

    input_drain_dir = f"../../result/result_Drain_{data_type}"
    input_uniparser_dir = f"../../result/result_UniParser_{data_type}"
    output_dir = f"../../result/result_DrainUP_{data_type}"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    datasets = datasets_full if args.full_data else datasets_2k

    for dataset in datasets:
        try:
            merge_results(dataset, input_drain_dir, input_uniparser_dir, output_dir, data_type=data_type, make_backups=True)
        except Exception as e:
            print(f"[ERROR] Failed merging dataset {dataset}: {e}")


if __name__ == "__main__":
    merge_results_wrapper()
    print('\n=== All merges complete! ===')

