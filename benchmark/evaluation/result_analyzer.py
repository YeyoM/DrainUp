#!/usr/bin/env python3
"""
Log Parser Performance Analyzer
Compares Drain, UniParser, and DrainUP across multiple datasets and metrics
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class ParserAnalyzer:
    """Analyze and compare log parser performance"""
    
    def __init__(self):
        self.parsers = ['Drain', 'UniParser', 'DrainUP']
        self.data = {}
        self.parsing_times = {}
        self.datasets = []
        
    def load_csv_data(self, csv_files):
        """Load CSV files for each parser"""
        for parser, filepath in csv_files.items():
            df = pd.read_csv(filepath, index_col=0)
            self.data[parser] = df
            if not self.datasets:
                # Get dataset names (exclude 'Average' column)
                self.datasets = [col for col in df.columns if col != 'Average']
        print(f"✓ Loaded CSV data for {len(self.data)} parsers")
        print(f"✓ Found {len(self.datasets)} datasets: {', '.join(self.datasets)}")
        
    def load_parsing_times(self, time_files):
        """Load parsing time data from different formats"""
        for parser, filepath in time_files.items():
            filepath = Path(filepath)
            
            if filepath.suffix == '.json':
                with open(filepath, 'r') as f:
                    self.parsing_times[parser] = json.load(f)
            elif filepath.suffix == '.txt':
                times = {}
                with open(filepath, 'r') as f:
                    for line in f:
                        # Parse format: "UniParser: Dataset Time"
                        parts = line.strip().split()
                        if len(parts) == 3:
                            dataset = parts[1]
                            time = float(parts[2])
                            times[dataset] = time
                self.parsing_times[parser] = times
        
        print(f"✓ Loaded parsing times for {len(self.parsing_times)} parsers")
        
    def create_combined_dataframe(self):
        """Combine all data into a single DataFrame for easy analysis"""
        all_data = []
        
        for parser in self.parsers:
            if parser not in self.data:
                continue
                
            df = self.data[parser]
            
            for dataset in self.datasets:
                row = {
                    'Parser': parser,
                    'Dataset': dataset,
                }
                
                # Add all metrics
                for metric in df.index:
                    if metric != 'parse_time':
                        row[metric] = df.loc[metric, dataset]
                
                # Add parsing time
                if parser in self.parsing_times and dataset in self.parsing_times[parser]:
                    row['parse_time'] = self.parsing_times[parser][dataset]
                else:
                    row['parse_time'] = np.nan
                
                all_data.append(row)
        
        self.combined_df = pd.DataFrame(all_data)
        print(f"✓ Created combined dataframe with {len(self.combined_df)} rows")
        return self.combined_df
    
    def generate_summary_statistics(self):
        """Generate summary statistics across all parsers"""
        print("\n" + "="*80)
        print("OVERALL PERFORMANCE SUMMARY")
        print("="*80)
        
        metrics = ['GA', 'PA', 'FGA', 'PTA', 'RTA', 'FTA', 'parse_time']
        
        for metric in metrics:
            print(f"\n{metric} (Higher is better for accuracy, Lower is better for time):")
            print("-" * 60)
            
            for parser in self.parsers:
                parser_data = self.combined_df[self.combined_df['Parser'] == parser]
                mean_val = parser_data[metric].mean()
                std_val = parser_data[metric].std()
                print(f"  {parser:12s}: Mean = {mean_val:8.4f}, Std = {std_val:8.4f}")
        
        # Find winners for each metric
        print("\n" + "="*80)
        print("METRIC WINNERS (Best Average Performance)")
        print("="*80)
        
        accuracy_metrics = ['GA', 'PA', 'FGA', 'PTA', 'RTA', 'FTA']
        for metric in accuracy_metrics:
            means = self.combined_df.groupby('Parser')[metric].mean()
            winner = means.idxmax()
            print(f"  {metric:12s}: {winner} ({means[winner]:.4f})")
        
        # Speed winner
        time_means = self.combined_df.groupby('Parser')['parse_time'].mean()
        speed_winner = time_means.idxmin()
        print(f"  {'Speed':12s}: {speed_winner} ({time_means[speed_winner]:.4f}s)")
    
    def plot_metric_comparison(self, output_dir='plots'):
        """Create comparison plots for all metrics"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        metrics = ['GA', 'PA', 'FGA', 'PTA', 'RTA', 'FTA']
        
        # 1. Overall metric comparison (bar plot)
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Average Performance Across All Datasets', fontsize=16, fontweight='bold')
        
        for idx, metric in enumerate(metrics):
            ax = axes[idx // 3, idx % 3]
            
            means = self.combined_df.groupby('Parser')[metric].mean()
            stds = self.combined_df.groupby('Parser')[metric].std()
            
            bars = ax.bar(means.index, means.values, yerr=stds.values, 
                         capsize=5, alpha=0.7, edgecolor='black')
            
            # Color the best performer
            best_idx = means.values.argmax()
            bars[best_idx].set_color('gold')
            bars[best_idx].set_edgecolor('darkgoldenrod')
            bars[best_idx].set_linewidth(2)
            
            ax.set_ylabel(metric, fontweight='bold')
            ax.set_ylim(0, 1.1)
            ax.grid(axis='y', alpha=0.3)
            ax.set_axisbelow(True)
            
        plt.tight_layout()
        plt.savefig(output_dir / 'overall_metrics_comparison.png', dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_dir / 'overall_metrics_comparison.png'}")
        plt.close()
        
    def plot_per_dataset_performance(self, output_dir='plots'):
        """Create heatmap showing performance per dataset"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        metrics = ['GA', 'PA', 'FGA', 'parse_time']
        
        for metric in metrics:
            pivot = self.combined_df.pivot(index='Dataset', columns='Parser', values=metric)
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # For parse_time, lower is better, so invert colormap
            if metric == 'parse_time':
                sns.heatmap(pivot, annot=True, fmt='.3f', cmap='RdYlGn_r', 
                           cbar_kws={'label': 'Time (seconds)'}, ax=ax)
                title = f'{metric} per Dataset (Lower is Better)'
            else:
                sns.heatmap(pivot, annot=True, fmt='.3f', cmap='RdYlGn', 
                           cbar_kws={'label': 'Score'}, ax=ax, vmin=0, vmax=1)
                title = f'{metric} per Dataset (Higher is Better)'
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Parser', fontweight='bold')
            ax.set_ylabel('Dataset', fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(output_dir / f'heatmap_{metric}.png', dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_dir / f'heatmap_{metric}.png'}")
            plt.close()
    
    def plot_speed_vs_accuracy(self, output_dir='plots'):
        """Create speed vs accuracy trade-off plots"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        accuracy_metrics = ['GA', 'PA', 'FGA']
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle('Speed vs Accuracy Trade-off', fontsize=16, fontweight='bold')
        
        colors = {'Drain': 'blue', 'UniParser': 'red', 'DrainUP': 'green'}
        
        for idx, metric in enumerate(accuracy_metrics):
            ax = axes[idx]
            
            for parser in self.parsers:
                parser_data = self.combined_df[self.combined_df['Parser'] == parser]
                
                ax.scatter(parser_data['parse_time'], parser_data[metric], 
                          label=parser, alpha=0.6, s=100, color=colors.get(parser, 'gray'))
                
                # Add dataset labels
                for _, row in parser_data.iterrows():
                    ax.annotate(row['Dataset'], 
                               (row['parse_time'], row[metric]),
                               fontsize=7, alpha=0.5, 
                               xytext=(3, 3), textcoords='offset points')
            
            ax.set_xlabel('Parse Time (seconds)', fontweight='bold')
            ax.set_ylabel(metric, fontweight='bold')
            ax.set_title(f'{metric} vs Speed', fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_axisbelow(True)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'speed_vs_accuracy.png', dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_dir / 'speed_vs_accuracy.png'}")
        plt.close()
    
    def plot_radar_chart(self, output_dir='plots'):
        """Create radar chart comparing parsers across metrics"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        metrics = ['GA', 'PA', 'FGA', 'PTA', 'RTA', 'FTA']
        
        # Calculate average scores
        avg_scores = {}
        for parser in self.parsers:
            parser_data = self.combined_df[self.combined_df['Parser'] == parser]
            avg_scores[parser] = [parser_data[m].mean() for m in metrics]
        
        # Number of variables
        num_vars = len(metrics)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        colors = {'Drain': 'blue', 'UniParser': 'red', 'DrainUP': 'green'}
        
        for parser, scores in avg_scores.items():
            scores += scores[:1]  # Complete the circle
            ax.plot(angles, scores, 'o-', linewidth=2, label=parser, 
                   color=colors.get(parser, 'gray'))
            ax.fill(angles, scores, alpha=0.15, color=colors.get(parser, 'gray'))
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontweight='bold')
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.grid(True)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax.set_title('Parser Performance Radar Chart', 
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'radar_chart.png', dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_dir / 'radar_chart.png'}")
        plt.close()
    
    def plot_winners_per_dataset(self, output_dir='plots'):
        """Show which parser wins for each dataset across different metrics"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        metrics = ['GA', 'PA', 'FGA']
        
        fig, axes = plt.subplots(len(metrics), 1, figsize=(14, 12))
        fig.suptitle('Best Parser per Dataset for Each Metric', 
                    fontsize=16, fontweight='bold')
        
        for idx, metric in enumerate(metrics):
            ax = axes[idx]
            
            # Find winner for each dataset
            winners = []
            scores = []
            
            for dataset in self.datasets:
                dataset_data = self.combined_df[self.combined_df['Dataset'] == dataset]
                best_parser = dataset_data.loc[dataset_data[metric].idxmax(), 'Parser']
                best_score = dataset_data[metric].max()
                winners.append(best_parser)
                scores.append(best_score)
            
            # Create color map
            color_map = {'Drain': 'blue', 'UniParser': 'red', 'DrainUP': 'green'}
            colors = [color_map.get(w, 'gray') for w in winners]
            
            bars = ax.barh(self.datasets, scores, color=colors, alpha=0.7, edgecolor='black')
            
            # Add parser labels on bars
            for i, (bar, winner) in enumerate(zip(bars, winners)):
                width = bar.get_width()
                ax.text(width - 0.05, bar.get_y() + bar.get_height()/2, 
                       winner, ha='right', va='center', fontweight='bold', 
                       color='white', fontsize=9)
            
            ax.set_xlabel('Score', fontweight='bold')
            ax.set_ylabel('Dataset', fontweight='bold')
            ax.set_title(f'{metric} - Best Parser per Dataset', fontweight='bold')
            ax.set_xlim(0, 1.1)
            ax.grid(axis='x', alpha=0.3)
            ax.set_axisbelow(True)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'winners_per_dataset.png', dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_dir / 'winners_per_dataset.png'}")
        plt.close()
    
    def generate_ranking_table(self):
        """Generate ranking table for parsers"""
        print("\n" + "="*80)
        print("PARSER RANKINGS")
        print("="*80)
        
        metrics = ['GA', 'PA', 'FGA', 'PTA', 'RTA', 'FTA', 'parse_time']
        rankings = {parser: [] for parser in self.parsers}
        
        for metric in metrics:
            means = self.combined_df.groupby('Parser')[metric].mean()
            
            # For parse_time, lower is better
            if metric == 'parse_time':
                sorted_parsers = means.sort_values().index.tolist()
            else:
                sorted_parsers = means.sort_values(ascending=False).index.tolist()
            
            for rank, parser in enumerate(sorted_parsers, 1):
                rankings[parser].append(rank)
        
        # Calculate average rank
        for parser in self.parsers:
            avg_rank = np.mean(rankings[parser])
            print(f"\n{parser}:")
            print(f"  Individual ranks: {rankings[parser]}")
            print(f"  Average rank: {avg_rank:.2f}")
    
    def export_results(self, output_file='analysis_results.csv'):
        """Export combined results to CSV"""
        self.combined_df.to_csv(output_file, index=False)
        print(f"\n✓ Exported results to: {output_file}")
    
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE PARSER ANALYSIS")
        print("="*80 + "\n")
        
        self.create_combined_dataframe()
        self.generate_summary_statistics()
        self.generate_ranking_table()
        
        print("\n" + "="*80)
        print("GENERATING PLOTS")
        print("="*80 + "\n")
        
        self.plot_metric_comparison()
        self.plot_per_dataset_performance()
        self.plot_speed_vs_accuracy()
        self.plot_radar_chart()
        self.plot_winners_per_dataset()
        
        self.export_results()
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE!")
        print("="*80)
        print("\nCheck the 'plots/' directory for visualizations")
        print("Check 'analysis_results.csv' for raw data")


def main():
    """Main execution function"""
    
    # Initialize analyzer
    analyzer = ParserAnalyzer()
    
    # Define file paths (UPDATE THESE TO MATCH YOUR FILE LOCATIONS)
    csv_files = {
        'Drain': 'Drain_2k_complex=0_frequent=0.csv',
        'UniParser': 'UniParser_2k_complex=0_frequent=0.csv',
        'DrainUP': 'DrainUP_2k_complex=0_frequent=0.csv',
    }
    
    time_files = {
        'Drain': 'result_Drain_2k/parsing_times.json',
        'UniParser': 'result_UniParser_2k/infer_time_2k.txt',
        'DrainUP': 'result_DrainUp_2k/parsing_times.json',
    }
    
    # Load data
    analyzer.load_csv_data(csv_files)
    analyzer.load_parsing_times(time_files)
    
    # Run full analysis
    analyzer.run_full_analysis()


if __name__ == '__main__':
    main()
