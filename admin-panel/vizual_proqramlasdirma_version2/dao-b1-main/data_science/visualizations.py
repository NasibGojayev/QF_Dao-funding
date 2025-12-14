"""
Visualization Module for DAO Data Science
==========================================
Dashboard visualizations, model metrics, and KPI charts.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


# =============================================================================
# KPI DASHBOARD VISUALIZATIONS
# =============================================================================

def plot_kpi_dashboard(kpi_data: Dict, save_path: str = None) -> plt.Figure:
    """
    Create a KPI dashboard with current values and trends.
    
    Args:
        kpi_data: Dictionary with 'current', 'previous', 'deltas' keys
        save_path: Optional path to save the figure
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('DAO Platform KPI Dashboard', fontsize=16, fontweight='bold')
    
    kpis = list(kpi_data.get('current', {}).items())
    
    colors = {
        'positive': '#2ecc71',
        'negative': '#e74c3c',
        'neutral': '#3498db'
    }
    
    for idx, (ax, (kpi_name, value)) in enumerate(zip(axes.flatten(), kpis)):
        delta = kpi_data.get('deltas', {}).get(kpi_name, 0)
        
        # Determine color based on delta
        if delta > 0:
            color = colors['positive']
            arrow = '↑'
        elif delta < 0:
            color = colors['negative']
            arrow = '↓'
        else:
            color = colors['neutral']
            arrow = '→'
        
        # Display value
        ax.text(0.5, 0.6, f'{value:.2f}', ha='center', va='center',
                fontsize=36, fontweight='bold', transform=ax.transAxes)
        
        # Display delta
        ax.text(0.5, 0.25, f'{arrow} {abs(delta):.1f}%', ha='center', va='center',
                fontsize=16, color=color, transform=ax.transAxes)
        
        # Title
        ax.set_title(kpi_name.replace('_', ' ').title(), fontsize=12, fontweight='bold')
        ax.axis('off')
    
    # Hide unused axes
    for ax in axes.flatten()[len(kpis):]:
        ax.axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_kpi_trends(trends_data: Dict[str, pd.DataFrame], save_path: str = None) -> plt.Figure:
    """Plot KPI trends over time."""
    n_kpis = len(trends_data)
    fig, axes = plt.subplots(n_kpis, 1, figsize=(12, 4 * n_kpis))
    
    if n_kpis == 1:
        axes = [axes]
    
    for ax, (kpi_name, df) in zip(axes, trends_data.items()):
        ax.plot(df['date'], df['value'], 'b-', linewidth=2, label=kpi_name)
        ax.fill_between(df['date'], df['value'], alpha=0.3)
        
        # Add trend line
        z = np.polyfit(range(len(df)), df['value'], 1)
        p = np.poly1d(z)
        ax.plot(df['date'], p(range(len(df))), 'r--', alpha=0.8, label='Trend')
        
        ax.set_title(f'{kpi_name.replace("_", " ").title()} - 30 Day Trend', fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


# =============================================================================
# MODEL EVALUATION VISUALIZATIONS
# =============================================================================

def plot_confusion_matrix(
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    labels: List[str] = None,
    save_path: str = None
) -> plt.Figure:
    """Plot confusion matrix heatmap."""
    from sklearn.metrics import confusion_matrix
    
    cm = confusion_matrix(y_true, y_pred)
    labels = labels or ['Negative', 'Positive']
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
    ax.figure.colorbar(im, ax=ax)
    
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=labels,
           yticklabels=labels,
           title='Confusion Matrix',
           ylabel='True Label',
           xlabel='Predicted Label')
    
    # Add text annotations
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                   ha="center", va="center",
                   color="white" if cm[i, j] > thresh else "black",
                   fontsize=14)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_roc_curve(
    y_true: np.ndarray, 
    y_proba: np.ndarray,
    model_name: str = "Model",
    save_path: str = None
) -> plt.Figure:
    """Plot ROC curve with AUC."""
    from sklearn.metrics import roc_curve, auc
    
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    roc_auc = auc(fpr, tpr)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.plot(fpr, tpr, color='#3498db', lw=2, 
            label=f'{model_name} (AUC = {roc_auc:.3f})')
    ax.plot([0, 1], [0, 1], color='gray', lw=1, linestyle='--', label='Random')
    
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('Receiver Operating Characteristic (ROC) Curve', fontsize=14, fontweight='bold')
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_model_comparison(
    results: Dict[str, Dict], 
    metrics: List[str] = None,
    save_path: str = None
) -> plt.Figure:
    """Compare multiple models across metrics."""
    metrics = metrics or ['accuracy', 'precision', 'recall', 'f1', 'auc_roc']
    
    models = list(results.keys())
    x = np.arange(len(metrics))
    width = 0.8 / len(models)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = plt.cm.Set2(np.linspace(0, 1, len(models)))
    
    for i, (model, result) in enumerate(results.items()):
        model_metrics = result.get('metrics', result)
        values = [model_metrics.get(m, 0) for m in metrics]
        bars = ax.bar(x + i * width, values, width, label=model, color=colors[i])
        
        # Add value labels
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                   f'{val:.2f}', ha='center', va='bottom', fontsize=8)
    
    ax.set_ylabel('Score')
    ax.set_title('Model Comparison - Performance Metrics', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * (len(models) - 1) / 2)
    ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics])
    ax.legend()
    ax.set_ylim(0, 1.15)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_feature_importance(
    importance: Dict[str, float], 
    top_n: int = 15,
    save_path: str = None
) -> plt.Figure:
    """Plot feature importance bar chart."""
    # Sort by importance
    sorted_features = sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)[:top_n]
    features, importances = zip(*sorted_features)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = ['#2ecc71' if x >= 0 else '#e74c3c' for x in importances]
    y_pos = np.arange(len(features))
    
    ax.barh(y_pos, importances, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f'Feature {f}' if isinstance(f, int) else f for f in features])
    ax.invert_yaxis()
    ax.set_xlabel('Importance Score')
    ax.set_title('Feature Importance (Top 15)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


# =============================================================================
# CLUSTERING VISUALIZATIONS
# =============================================================================

def plot_elbow_curve(elbow_data: List[Tuple[int, float]], save_path: str = None) -> plt.Figure:
    """Plot K-Means elbow curve."""
    k_values, inertias = zip(*elbow_data)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(k_values, inertias, 'bo-', linewidth=2, markersize=8)
    ax.set_xlabel('Number of Clusters (k)', fontsize=12)
    ax.set_ylabel('Inertia', fontsize=12)
    ax.set_title('K-Means Elbow Curve', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_clusters_2d(
    X: np.ndarray, 
    labels: np.ndarray, 
    centers: np.ndarray = None,
    save_path: str = None
) -> plt.Figure:
    """Plot 2D cluster visualization."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    unique_labels = np.unique(labels)
    colors = plt.cm.Set2(np.linspace(0, 1, len(unique_labels)))
    
    for label, color in zip(unique_labels, colors):
        mask = labels == label
        label_name = 'Noise' if label == -1 else f'Cluster {label}'
        ax.scatter(X[mask, 0], X[mask, 1], c=[color], label=label_name, alpha=0.7, s=50)
    
    if centers is not None:
        ax.scatter(centers[:, 0], centers[:, 1], c='red', marker='X', s=200, 
                  edgecolors='black', linewidths=2, label='Centroids')
    
    ax.set_xlabel('Component 1', fontsize=12)
    ax.set_ylabel('Component 2', fontsize=12)
    ax.set_title('Cluster Visualization (2D PCA)', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


# =============================================================================
# EXPERIMENT VISUALIZATIONS
# =============================================================================

def plot_ab_test_results(ab_results: Dict, save_path: str = None) -> plt.Figure:
    """Plot A/B test results with confidence intervals."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Conversion rates comparison
    ax1 = axes[0]
    variants = ['Control', 'Treatment']
    rates = [
        ab_results['control']['conversions'] / ab_results['control']['impressions'] * 100,
        ab_results['treatment']['conversions'] / ab_results['treatment']['impressions'] * 100,
    ]
    colors = ['#3498db', '#2ecc71']
    
    bars = ax1.bar(variants, rates, color=colors, edgecolor='black')
    ax1.set_ylabel('Conversion Rate (%)')
    ax1.set_title('Conversion Rate by Variant', fontsize=12, fontweight='bold')
    
    for bar, rate in zip(bars, rates):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
                f'{rate:.2f}%', ha='center', va='bottom', fontsize=12)
    
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Statistical summary
    ax2 = axes[1]
    ax2.axis('off')
    
    summary_text = f"""
    A/B Test Results Summary
    ========================
    
    Control:
      Impressions: {ab_results['control']['impressions']:,}
      Conversions: {ab_results['control']['conversions']:,}
      Rate: {ab_results['control']['rate']}
    
    Treatment:
      Impressions: {ab_results['treatment']['impressions']:,}
      Conversions: {ab_results['treatment']['conversions']:,}
      Rate: {ab_results['treatment']['rate']}
    
    Lift: {ab_results['lift']}
    P-Value: {ab_results['p_value']}
    Significant: {'✓ Yes' if ab_results['is_significant'] else '✗ No'}
    
    Recommendation: {ab_results['recommendation']}
    """
    
    ax2.text(0.1, 0.9, summary_text, transform=ax2.transAxes, fontsize=11,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_bandit_performance(bandit_stats: Dict, save_path: str = None) -> plt.Figure:
    """Plot Multi-Armed Bandit performance."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    arms = list(bandit_stats.keys())
    avg_rewards = [bandit_stats[arm]['average_reward'] for arm in arms]
    pull_ratios = [bandit_stats[arm]['pull_ratio'] for arm in arms]
    
    # Average rewards
    ax1 = axes[0]
    colors = plt.cm.Set2(np.linspace(0, 1, len(arms)))
    bars = ax1.bar(arms, avg_rewards, color=colors, edgecolor='black')
    ax1.set_ylabel('Average Reward')
    ax1.set_title('Average Reward by Arm', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    for bar, val in zip(bars, avg_rewards):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                f'{val:.3f}', ha='center', va='bottom')
    
    # Pull distribution
    ax2 = axes[1]
    ax2.pie(pull_ratios, labels=arms, autopct='%1.1f%%', colors=colors,
           explode=[0.05] * len(arms), shadow=True)
    ax2.set_title('Pull Distribution', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


# =============================================================================
# ANOMALY DETECTION VISUALIZATIONS
# =============================================================================

def plot_anomaly_scores(
    scores: np.ndarray, 
    labels: np.ndarray = None,
    threshold: float = None,
    save_path: str = None
) -> plt.Figure:
    """Plot anomaly detection scores distribution."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Histogram
    ax1 = axes[0]
    ax1.hist(scores, bins=50, color='#3498db', alpha=0.7, edgecolor='black')
    if threshold:
        ax1.axvline(x=threshold, color='r', linestyle='--', linewidth=2, label=f'Threshold: {threshold:.2f}')
    ax1.set_xlabel('Anomaly Score')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Anomaly Score Distribution', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Scatter plot
    ax2 = axes[1]
    if labels is not None:
        colors = ['#2ecc71' if l == 1 else '#e74c3c' for l in labels]
    else:
        colors = '#3498db'
    
    ax2.scatter(range(len(scores)), scores, c=colors, alpha=0.6, s=20)
    if threshold:
        ax2.axhline(y=threshold, color='r', linestyle='--', linewidth=2)
    ax2.set_xlabel('Sample Index')
    ax2.set_ylabel('Anomaly Score')
    ax2.set_title('Anomaly Scores by Sample', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Legend
    if labels is not None:
        normal_patch = mpatches.Patch(color='#2ecc71', label='Normal')
        anomaly_patch = mpatches.Patch(color='#e74c3c', label='Anomaly')
        ax2.legend(handles=[normal_patch, anomaly_patch])
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


# =============================================================================
# GENERATE ALL VISUALIZATIONS
# =============================================================================

def generate_all_visualizations(output_dir: str = "visualizations") -> List[str]:
    """Generate all sample visualizations and save to directory."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    np.random.seed(42)
    
    # 1. KPI Dashboard
    kpi_data = {
        'current': {
            'active_user_rate': 45.3,
            'avg_tx_per_user': 5.5,
            'avg_donation_amount': 0.85,
            'return_rate': 35.2,
            'anomaly_ratio': 3.2
        },
        'deltas': {
            'active_user_rate': 7.8,
            'avg_tx_per_user': 5.8,
            'avg_donation_amount': 13.3,
            'return_rate': 10.0,
            'anomaly_ratio': -8.6
        }
    }
    path = f"{output_dir}/kpi_dashboard.png"
    plot_kpi_dashboard(kpi_data, save_path=path)
    saved_files.append(path)
    plt.close()
    
    # 2. Confusion Matrix
    y_true = np.random.randint(0, 2, 100)
    y_pred = y_true.copy()
    flip_mask = np.random.random(100) < 0.1
    y_pred[flip_mask] = 1 - y_pred[flip_mask]
    path = f"{output_dir}/confusion_matrix.png"
    plot_confusion_matrix(y_true, y_pred, save_path=path)
    saved_files.append(path)
    plt.close()
    
    # 3. ROC Curve
    y_proba = np.random.beta(2, 5, 100)
    y_proba[y_true == 1] = np.random.beta(5, 2, y_true.sum())
    path = f"{output_dir}/roc_curve.png"
    plot_roc_curve(y_true, y_proba, model_name="XGBoost", save_path=path)
    saved_files.append(path)
    plt.close()
    
    # 4. Model Comparison
    results = {
        'Logistic Regression': {'metrics': {'accuracy': 0.82, 'precision': 0.78, 'recall': 0.85, 'f1': 0.81, 'auc_roc': 0.88}},
        'Random Forest': {'metrics': {'accuracy': 0.87, 'precision': 0.84, 'recall': 0.89, 'f1': 0.86, 'auc_roc': 0.92}},
        'XGBoost': {'metrics': {'accuracy': 0.89, 'precision': 0.86, 'recall': 0.91, 'f1': 0.88, 'auc_roc': 0.94}},
    }
    path = f"{output_dir}/model_comparison.png"
    plot_model_comparison(results, save_path=path)
    saved_files.append(path)
    plt.close()
    
    # 5. Feature Importance
    importance = {f'feature_{i}': np.random.uniform(-0.5, 1) for i in range(15)}
    path = f"{output_dir}/feature_importance.png"
    plot_feature_importance(importance, save_path=path)
    saved_files.append(path)
    plt.close()
    
    # 6. Cluster Visualization
    X = np.vstack([
        np.random.randn(50, 2) + [0, 0],
        np.random.randn(50, 2) + [3, 3],
        np.random.randn(50, 2) + [0, 3],
    ])
    labels = np.array([0]*50 + [1]*50 + [2]*50)
    centers = np.array([[0, 0], [3, 3], [0, 3]])
    path = f"{output_dir}/clusters.png"
    plot_clusters_2d(X, labels, centers, save_path=path)
    saved_files.append(path)
    plt.close()
    
    # 7. A/B Test Results
    ab_results = {
        'control': {'impressions': 10000, 'conversions': 1000, 'rate': '10.00%'},
        'treatment': {'impressions': 10000, 'conversions': 1200, 'rate': '12.00%'},
        'lift': '20.00%',
        'p_value': '0.0012',
        'is_significant': True,
        'recommendation': 'Deploy Treatment'
    }
    path = f"{output_dir}/ab_test_results.png"
    plot_ab_test_results(ab_results, save_path=path)
    saved_files.append(path)
    plt.close()
    
    # 8. Bandit Performance
    bandit_stats = {
        'model_a': {'average_reward': 0.10, 'pull_ratio': 0.20},
        'model_b': {'average_reward': 0.15, 'pull_ratio': 0.55},
        'model_c': {'average_reward': 0.12, 'pull_ratio': 0.25},
    }
    path = f"{output_dir}/bandit_performance.png"
    plot_bandit_performance(bandit_stats, save_path=path)
    saved_files.append(path)
    plt.close()
    
    # 9. Anomaly Detection
    scores = np.random.randn(200)
    scores[180:] = np.random.randn(20) * 3 + 3  # Anomalies
    labels = np.array([1]*180 + [-1]*20)
    path = f"{output_dir}/anomaly_scores.png"
    plot_anomaly_scores(scores, labels, threshold=2.0, save_path=path)
    saved_files.append(path)
    plt.close()
    
    print(f"\nGenerated {len(saved_files)} visualizations in {output_dir}/")
    return saved_files


if __name__ == "__main__":
    files = generate_all_visualizations("visualizations")
    for f in files:
        print(f"  [OK] {f}")
