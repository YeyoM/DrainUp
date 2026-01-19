"""
File to only Run a Given Parser on a given Dataset
"""

import os
import time
from multiprocessing import Process
import sys
import argparse
import json

from Drain import LogParser


sys.path.append('../')


TIMEOUT = 3600 * 12  # log template identification timeout (sec)


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


benchmark_settings = {
    'HDFS': {
        'log_file': 'HDFS/HDFS_2k.log',
        'log_format': '<Date> <Time> <Pid> <Level> <Component>: <Content>',
        'regex': [r'blk_-?\d+', r'(\d+\.){3}\d+(:\d+)?'],
        'st': 0.5,
        'depth': 4
        },

    'Hadoop': {
        'log_file': 'Hadoop/Hadoop_2k.log',
        'log_format': '<Date> <Time> <Level> \[<Process>\] <Component>: <Content>',
        'regex': [r'(\d+\.){3}\d+'],
        'st': 0.5,
        'depth': 4        
        },

    'Spark': {
        'log_file': 'Spark/Spark_2k.log',
        'log_format': '<Date> <Time> <Level> <Component>: <Content>', 
        'regex': [r'(\d+\.){3}\d+', r'\b[KGTM]?B\b', r'([\w-]+\.){2,}[\w-]+'],
        'regex': [],
        'st': 0.5,
        'depth': 4
        },

    'Zookeeper': {
        'log_file': 'Zookeeper/Zookeeper_2k.log',
        'log_format': '<Date> <Time> - <Level>  \[<Node>:<Component>@<Id>\] - <Content>',
        'regex': [r'(/|)(\d+\.){3}\d+(:\d+)?'],
        'st': 0.5,
        'depth': 4        
        },

    'BGL': {
        'log_file': 'BGL/BGL_2k.log',
        'log_format': '<Label> <Timestamp> <Date> <Node> <Time> <NodeRepeat> <Type> <Component> <Level> <Content>',
        'regex': [r'core\.\d+'],
        'st': 0.5,
        'depth': 4        
        },

    'HPC': {
        'log_file': 'HPC/HPC_2k.log',
        'log_format': '<LogId> <Node> <Component> <State> <Time> <Flag> <Content>',
        'regex': [r'=\d+'],
        'st': 0.5,
        'depth': 4
        },

    'Thunderbird': {
        'log_file': 'Thunderbird/Thunderbird_2k.log',
        'log_format': '<Label> <Timestamp> <Date> <User> <Month> <Day> <Time> <Location> <Component>(\[<PID>\])?: <Content>',
        'regex': [r'(\d+\.){3}\d+'],
        'st': 0.5,
        'depth': 4        
        },

    'Windows': {
        'log_file': 'Windows/Windows_2k.log',
        'log_format': '<Date> <Time>, <Level>                  <Component>    <Content>',
        'regex': [r'0x.*?\s'],
        'st': 0.7,
        'depth': 5      
        },

    'Linux': {
        'log_file': 'Linux/Linux_2k.log',
        'log_format': '<Month> <Date> <Time> <Level> <Component>(\[<PID>\])?: <Content>',
        'regex': [r'(\d+\.){3}\d+', r'\d{2}:\d{2}:\d{2}'],
        'st': 0.39,
        'depth': 6        
        },

    'Android': {
        'log_file': 'Android/Android_2k.log',
        'log_format': '<Date> <Time>  <Pid>  <Tid> <Level> <Component>: <Content>',
        'regex': [r'(/[\w-]+)+', r'([\w-]+\.){2,}[\w-]+', r'\b(\-?\+?\d+)\b|\b0[Xx][a-fA-F\d]+\b|\b[a-fA-F\d]{4,}\b'],
        'st': 0.2,
        'depth': 6   
        },

    'HealthApp': {
        'log_file': 'HealthApp/HealthApp_2k.log',
        'log_format': '<Time>\|<Component>\|<Pid>\|<Content>',
        'regex': [],
        'st': 0.2,
        'depth': 4
        },

    'Apache': {
        'log_file': 'Apache/Apache_2k.log',
        'log_format': '\[<Time>\] \[<Level>\] <Content>',
        'regex': [r'(\d+\.){3}\d+'],
        'st': 0.5,
        'depth': 4        
        },

    'Proxifier': {
        'log_file': 'Proxifier/Proxifier_2k.log',
        'log_format': '\[<Time>\] <Program> - <Content>',
        'regex': [r'<\d+\ssec', r'([\w-]+\.)+[\w-]+(:\d+)?', r'\d{2}:\d{2}(:\d{2})*', r'[KGTM]B'],
        'st': 0.6,
        'depth': 3
        },

    'OpenSSH': {
        'log_file': 'OpenSSH/OpenSSH_2k.log',
        'log_format': '<Date> <Day> <Time> <Component> sshd\[<Pid>\]: <Content>',
        'regex': [r'(\d+\.){3}\d+', r'([\w-]+\.){2,}[\w-]+'],
        'st': 0.6,
        'depth': 5   
        },

    'OpenStack': {
        'log_file': 'OpenStack/OpenStack_2k.log',
        'log_format': '<Logrecord> <Date> <Time> <Pid> <Level> <Component> \[<ADDR>\] <Content>',
        'regex': [r'((\d+\.){3}\d+,?)+', r'/.+?\s', r'\d+'],
        'st': 0.5,
        'depth': 5
        },

    'Mac': {
        'log_file': 'Mac/Mac_2k.log',
        'log_format': '<Month>  <Date> <Time> <User> <Component>\[<PID>\]( \(<Address>\))?: <Content>',
        'regex': [r'([\w-]+\.){2,}[\w-]+'],
        'st': 0.7,
        'depth': 6   
        },
}


def common_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-otc', '--oracle_template_correction',
                        help="Set this if you want to use corrected oracle templates",
                        default=False, action='store_true')
    parser.add_argument('-full', '--full_data',
                        help="Set this if you want to test on full dataset",
                        default=False, action='store_true')
    parser.add_argument('--complex', type=int,
                        help="Set this if you want to test on complex dataset",
                        default=0)
    parser.add_argument('--frequent', type=int,
                        help="Set this if you want to test on frequent dataset",
                        default=0)
    parser.add_argument('--shot', type=int,
                        help="Set this if you want to test on complex dataset",
                        default=0)
    parser.add_argument('--example_size', type=int,
                        help="Set this if you want to test on frequent dataset",
                        default=0)    
    args = parser.parse_args()
    return args


def is_file_empty(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        return len(content) == 0


def runner(
        dataset,
        output_dir,
        log_file,
        LogParser,
        param_dict,
):
    """
    Unit function to execute the Runner for a specific configuration.
    """

    if LogParser is None:
        print('\nSkipping parsing for %s (Parser = None)' % dataset)
        return 

    log_file_basename = os.path.basename(log_file)

    parsedresult = os.path.join(output_dir, log_file_basename + '_structured.csv')

    # identify templates using the given Parser as argument
    start_time = time.time()
    print("Starting to Parse...")
    parser = LogParser(**param_dict)
    p = Process(target=parser.parse, args=(log_file_basename,))
    p.start()
    p.join(timeout=TIMEOUT)
    if p.is_alive():
        print('*** TIMEOUT for Template Identification')
        p.terminate()
        with open(parsedresult, 'w') as fw:
            pass
        return
    parse_time = time.time() - start_time  
    print("Parsing Finished!")
    print("Parsing Time (s): ", parse_time)

    return parse_time


if __name__ == "__main__":
    args = common_args()
    data_type = "full" if args.full_data else "2k"

    parsing_times = {}

    # Choosing between datasets
    if args.full_data:
        datasets = datasets_full
    else:
        datasets = datasets_2k

    input_dir = f"../../../{data_type}_dataset/"
    output_dir = f"../../../result/result_Drain_{data_type}"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for dataset in datasets:
        print('\n=== Parsing %s ===' % dataset)
        setting = benchmark_settings[dataset]
        log_file = setting['log_file'].replace("_2k", f"_{data_type}")
        indir = os.path.join(input_dir, os.path.dirname(log_file))
        if os.path.exists(os.path.join(output_dir, f"{dataset}_{data_type}.log_structured.csv")):
            parser = None
            print("Parsing Result Exist. Skipping")
            continue
        else:
            parser = LogParser

        # execute runner for the given dataset
        print(setting['log_format'])
        parse_time = runner(
            dataset=dataset,
            output_dir=output_dir,
            log_file=log_file,
            LogParser=parser,
            param_dict={
                'log_format': setting['log_format'], 'indir': indir, 'outdir': output_dir, 'rex': setting['regex'],
                'depth': setting['depth'], 'st': setting['st']
            },
        )  
        parsing_times[dataset] = parse_time

    parsing_times_path = os.path.join(output_dir, "parsing_times.json")
    with open(parsing_times_path, "w") as f:
        json.dump(parsing_times, f, indent=2)
    print(f"\n\nParsing times saved to {parsing_times_path}")
    print("\n")

