import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def parse_benchmark_data(filepath="result.txt"):
    
    with open(filepath, 'r') as f:
        content = f.read()

    all_records = []
    current_system = None
    current_install_method = None

    title_regex = re.compile(r"^(AION|IRIS) \((EESSI|EASYBUILD|SOURCE)\)")
    scenario_regex = re.compile(r"(?:EESSIOsu|EasyBuildOsu|Osu)?(DifferentNodes|DifferentSockets|SameSocketDifferentNuma|SameNumaNode)")

    lines = content.splitlines()
    table_header = ['name_full', 'sysenv', 'job_nodelist', 'pvar', 'punit', 'pval', 'result']

    for line in lines:
        line = line.strip()
        if not line:
            continue

        title_match = title_regex.match(line)
        if title_match:
            current_system = title_match.group(1)
            current_install_method = title_match.group(2)
            continue

        if line.startswith('│') and 'name' not in line and '━━━━━━━━' not in line and '────────' not in line:
            if not current_system or not current_install_method:
                continue

            parts = [p.strip() for p in line.split('│')[1:-1]]
            if len(parts) == len(table_header):
                record = dict(zip(table_header, parts))
                record['system'] = current_system
                record['install_method'] = current_install_method

                scenario_match = scenario_regex.search(record['name_full'])
                if scenario_match:
                    record['scenario'] = scenario_match.group(1)
                else:
                    record['scenario'] = "Unknown"

                try:
                    record['pval'] = float(record['pval'])
                except ValueError:
                    record['pval'] = None

                all_records.append(record)

    df = pd.DataFrame(all_records)
    df.dropna(subset=['pval'], inplace=True)
    return df

def plot_metrics(df):
    """
    Generates and saves plots for latency and bandwidth with values on bars.
    """
    if df.empty:
        print("DataFrame is empty. No data to plot.")
        return

    sns.set_theme(style="whitegrid")

    scenario_order = [
        "DifferentNodes",
        "DifferentSockets",
        "SameSocketDifferentNuma",
        "SameNumaNode"
    ]
    df['scenario'] = pd.Categorical(df['scenario'], categories=scenario_order, ordered=True)

    # --- Latency Plot ---
    latency_df = df[df['pvar'] == 'latency'].copy()
    if not latency_df.empty:
        g_latency = sns.catplot(
            data=latency_df,
            x='scenario',
            y='pval',
            hue='install_method',
            col='system',
            kind='bar',
            palette='viridis',
            sharey=False,
            order=scenario_order,
            height=5,
            aspect=1.25,
            legend_out=True,
            margin_titles=True
        )
        g_latency.set_titles(template="{col_name}", y=1.03)
        g_latency.set_axis_labels("Test Scenario", "Latency (µs)")
        g_latency.set_xticklabels(rotation=30, ha='right') # Keep rotation

        for ax in g_latency.axes.flat:
            for p in ax.patches:
                height = p.get_height()
                if pd.isna(height) or height == 0:
                    continue
                ax.annotate(f'{height:.2f}',
                            xy=(p.get_x() + p.get_width() / 2., height),
                            xytext=(0, 5),
                            textcoords='offset points',
                            ha='center', va='bottom',
                            fontsize=7, color='dimgray')

        g_latency.fig.suptitle("MPI Latency Comparison (Lower is Better)", fontsize=16)

        if hasattr(g_latency, 'legend') and g_latency.legend is not None:
            legend_title = g_latency.legend.get_title()
            if legend_title is not None:
                legend_title.set_fontsize(10)

        try:
            # rect = [left, bottom, right, top]
            # Increased bottom margin from 0.05 to 0.12
            g_latency.fig.tight_layout(rect=[0.02, 0.12, 0.88, 0.92])
        except Exception as e:
            print(f"Warning: tight_layout encountered an issue for latency plot: {e}")
            g_latency.fig.subplots_adjust(left=0.05, bottom=0.15, right=0.85, top=0.9) # Fallback with more bottom

        plt.savefig("latency_comparison.png", dpi=150)
        plt.show()
        print("Latency plot saved as latency_comparison.png")
    else:
        print("No latency data found to plot.")

    # --- Bandwidth Plot ---
    bandwidth_df = df[df['pvar'] == 'bandwidth'].copy()
    if not bandwidth_df.empty:
        g_bandwidth = sns.catplot(
            data=bandwidth_df,
            x='scenario',
            y='pval',
            hue='install_method',
            col='system',
            kind='bar',
            palette='mako',
            sharey=False,
            order=scenario_order,
            height=5,
            aspect=1.25,
            legend_out=True,
            margin_titles=True
        )
        g_bandwidth.set_titles(template="{col_name}", y=1.03)
        g_bandwidth.set_axis_labels("Test Scenario", "Bandwidth (MB/s)")
        g_bandwidth.set_xticklabels(rotation=30, ha='right') # Keep rotation

        for ax in g_bandwidth.axes.flat:
            for p in ax.patches:
                height = p.get_height()
                if pd.isna(height) or height == 0:
                    continue
                ax.annotate(f'{height:.1f}',
                            xy=(p.get_x() + p.get_width() / 2., height),
                            xytext=(0, 5),
                            textcoords='offset points',
                            ha='center', va='bottom',
                            fontsize=6, color='dimgray')

        g_bandwidth.fig.suptitle("MPI Bandwidth Comparison (Higher is Better)", fontsize=16)

        if hasattr(g_bandwidth, 'legend') and g_bandwidth.legend is not None:
            legend_title = g_bandwidth.legend.get_title()
            if legend_title is not None:
                legend_title.set_fontsize(10)
        try:
            # rect = [left, bottom, right, top]
            # Increased bottom margin from 0.05 to 0.12
            g_bandwidth.fig.tight_layout(rect=[0.02, 0.12, 0.88, 0.92])
        except Exception as e:
            print(f"Warning: tight_layout encountered an issue for bandwidth plot: {e}")
            g_bandwidth.fig.subplots_adjust(left=0.05, bottom=0.15, right=0.85, top=0.9) # Fallback with more bottom

        plt.savefig("bandwidth_comparison.png", dpi=150)
        plt.show()
        print("Bandwidth plot saved as bandwidth_comparison.png")
    else:
        print("No bandwidth data found to plot.")


if __name__ == "__main__":
    data_df = parse_benchmark_data()
    if not data_df.empty:
        plot_metrics(data_df)
    else:
        print("No data parsed. Check 'benchmark_data.txt' and parsing logic.")