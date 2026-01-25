import torch
from torch.optim import Adam
from ner.corpus import Corpus
from ner.models import NERModel
from ner.lr_finder import LRFinder
from ner.trainer import Trainer
from pprint import pprint
from tqdm import tqdm
import os
import csv
import argparse
import time
import json

def csv_reader(path):
    with open(path, 'r', encoding='utf-8') as fp:
        reader = csv.reader(fp)
        data = [i for i in reader]
    return data

def csv_writer(path, header, data):
    with open(path, 'w', encoding='utf-8_sig', newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(header)
        writer.writerows(data)

def set_seed(seed=42):
    os.environ['PYHTONHASHSEED'] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True


if __name__ == "__main__":
    config = argparse.ArgumentParser()
    config.add_argument('-full', '--full_data',
                        help="Set this if you want to test on full dataset",
                        default=False, action='store_true')
    config = config.parse_args()
    data_type = 'full' if config.full_data else '2k'
    find_lr = False
    set_seed(42)
    use_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    datasets = ['Apache', 'BGL', 'HDFS', 'HPC', 'Hadoop', 'HealthApp', 'Linux', 'Mac', 'OpenSSH', 'OpenStack',
             'Proxifier', 'Spark', 'Thunderbird', 'Zookeeper']

    # Dictionary to store parsing times for all datasets
    parsing_times = {}

    for dataset in datasets:
        print("\n" + "=" * 50)
        print(f"=== Parsing {dataset} ===")
        print("=" * 50)
        
        training_config = {
            "max_epochs": 50,
            "no_improvement": 10,
            "batch_size": 16,
            "lr": 1e-1,
            "weight_decay": 1e-2
        }
        input_folder = os.path.join(f"{data_type}_annotations", dataset, "Loghub-2.0_bin_random")
        corpus = Corpus(
            input_folder=input_folder,
            min_word_freq=3,
            batch_size=training_config['batch_size'],
            wv_file="model/glove.6B.50d.txt"
        )
        print(f"Train set: {len(corpus.train_dataset)} sentences")
        print(f"Val set: {len(corpus.val_dataset)} sentences")
        print(f"Test set: {len(corpus.test_dataset)} sentences")

        # configurations building block
        base = {
            "word_input_dim": len(corpus.word_field.vocab),
            "char_pad_idx": corpus.char_pad_idx,
            "word_pad_idx": corpus.word_pad_idx,
            "tag_names": corpus.tag_field.vocab.itos,
            "device": use_device
        }
        w2v = {
            "word_emb_pretrained": corpus.word_field.vocab.vectors if corpus.word_vectors else None,
            "word_emb_dim": 50,
            "word_emb_dropout": 0.5,
            "word_emb_froze": True
        }
        cnn = {
            "use_char_emb": True,
            "char_emb_pretrained": None,
            "char_input_dim": len(corpus.char_field.vocab),
            "char_emb_dim": 37,
            "char_emb_dropout": 0.25,
            "char_cnn_filter_num": 4,
            "char_cnn_kernel_size": 3,
            "char_cnn_dropout": 0.25
        }
        lstm = {
            "lstm_hidden_dim": 64,
            "lstm_layers": 2,
            "lstm_dropout": 0.1
        }
        configs = {
            "bilstm+w2v+cnn": {**base, **w2v, **cnn, **lstm},
        }
        if find_lr:
            suggested_lrs = {}
            for model_name in configs:
                model = NERModel(**configs[model_name])
                lr_finder = LRFinder(model, Adam(model.parameters(), lr=1e-4, weight_decay=1e-2), device=use_device)
                lr_finder.range_test(corpus.train_iter, corpus.val_iter, end_lr=1, num_iter=25, step_mode="exp")
                _, suggested_lrs[model_name] = lr_finder.plot(skip_start=10, skip_end=0)
        else:
            suggested_lrs = {model_name: training_config['lr'] for model_name in configs}
        pprint(suggested_lrs)

        for model_name in configs:
            checkpoint_path = f"saved_states_{data_type}/{dataset}/bilstm+w2v+cnn-w50c37f4k3-lstm64L2-lr0.1-epoch100bz16.pt"

            model = NERModel(**configs[model_name])
            trainer = Trainer(
                model=model,
                data=corpus,
                optimizer=Adam(model.parameters(), lr=suggested_lrs[model_name], weight_decay=training_config['weight_decay']),
                device=use_device,
                checkpoint_path=checkpoint_path
            )
            if os.path.exists(checkpoint_path):
                trainer.model.load_state(checkpoint_path)
            else:
                print("No checkpoint found. Use model's last state for inference.")

            infer_config = {
                "infering_data_dir": f"../../../result/result_Drain_{data_type}",
                "output_dir": f"../../../result/result_UniParser_{data_type}",
                "batch_size": 8
            }

            # Check if low-confidence file exists
            low_confidence_file = os.path.join(f"{infer_config['infering_data_dir']}/{dataset}_{data_type}.log_low_confidence.csv")
            
            print(f"\nLooking for low-confidence file: {low_confidence_file}")
            
            if not os.path.exists(low_confidence_file):
                print(f"WARNING: Low-confidence file not found for {dataset}: {low_confidence_file}")
                print(f"Skipping {dataset}. Please run Drain before running UniParser.")
                parsing_times[dataset] = 0
                continue

            # Start inferring... (the actual parsing)
            print(f"Reading low-confidence logs from: {low_confidence_file}")
            infer_data = csv_reader(low_confidence_file)
            
            # Check if file is empty (only header or completely empty)
            if len(infer_data) <= 1:
                print(f"INFO: No low-confidence logs found for {dataset} (file is empty or has only header). Skipping with 0 time recorded.")
                parsing_times[dataset] = 0
                continue

            print(f"Found {len(infer_data) - 1} low-confidence log entries to process")
            
            begin_time = time.time()
            
            header = infer_data[0]
            sentence_idx = header.index("Content")
            infer_data = infer_data[1:]
            predictions = []

            do_batch_infer = True

            if do_batch_infer:
                batchs = [[item[sentence_idx] for item in infer_data[i:i+infer_config['batch_size']]] for i in range(0, len(infer_data), infer_config['batch_size'])]
                for batch in tqdm(batchs, desc=f"BatchSize-{infer_config['batch_size']}, total: {len(infer_data)}"):
                    words, infer_tags = trainer.infer_batch(sentences=batch)
                    merged_words = [[i if j == 'O' else "<*>" for i, j in zip(word, infer_tag)] for word, infer_tag in zip(words, infer_tags)]
                    def merge_list(lst):
                        new_lst = []
                        i = 0
                        while i < len(lst):
                            if lst[i] == '<*>':
                                new_lst.append(lst[i])
                                i += 1
                                while i < len(lst) and lst[i] == '<*>':
                                    i += 1
                            else:
                                new_lst.append(lst[i])
                                i += 1
                        return new_lst
                    predictions.extend([" ".join(merge_list(_merged_words)) for _merged_words in merged_words])
            else:
                for line in tqdm(infer_data):
                    words, infer_tags, unknown_tokens = trainer.infer(sentence=line[sentence_idx])
                    merged_words = [i if j == 'O' else "<*>" for i, j in zip(words, infer_tags)]
                    def merge_list(lst):
                        new_lst = []
                        i = 0
                        while i < len(lst):
                            if lst[i] == '<*>':
                                new_lst.append(lst[i])
                                i += 1
                                while i < len(lst) and lst[i] == '<*>':
                                    i += 1
                            else:
                                new_lst.append(lst[i])
                                i += 1
                        return new_lst
                    predictions.append(" ".join(merge_list(merged_words)))

            template2id = {k: i for i, k in enumerate(list(set(predictions)))}
            new_csv = [[ori_item[sentence_idx], template2id[pred], pred] for ori_item, pred in zip(infer_data, predictions)]
            write_path = os.path.join(f"{infer_config['output_dir']}/{dataset}_{data_type}.log_structured.csv")

            # Create output directory if it doesn't exist
            os.makedirs(infer_config['output_dir'], exist_ok=True)

            csv_writer(write_path, ["Content", "EventId", "EventTemplate"], new_csv)

            with open(f"{infer_config['output_dir']}/{dataset}_{data_type}.log_templates.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['EventId', 'EventTemplate'])
                for key, value in template2id.items():
                    writer.writerow([value, key])
            
            end_time = time.time()
            elapsed_time = end_time - begin_time
            parsing_times[dataset] = elapsed_time
            print(f"UniParser: {dataset} - {elapsed_time:.4f}s")

    # Save all parsing times to JSON file
    json_output_path = f"../../../result/result_UniParser_{data_type}/parsing_times.json"
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
    
    with open(json_output_path, 'w') as json_file:
        json.dump(parsing_times, json_file, indent=2)
    
    print(f"\nParsing times saved to: {json_output_path}")
