import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. Load Data
try:
    df = pd.read_csv('Olympics_PAT_V1.2.1(Trial 1).csv')
except FileNotFoundError:
    print("Error: Ensure 'Olympics_PAT_V1.2.1(Trial 1).csv' is in the same directory.")
    exit()

# Set professional style
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'serif'

# 2. Figure 1: The Unified PAT Leaderboard
plt.figure(figsize=(12, 8))
df_sorted = df.sort_values('PAT_V1.2.1', ascending=True)
ax = sns.barplot(data=df_sorted, x='PAT_V1.2.1', y='Name', hue='Event', palette='flare')

plt.title('OmniSprint V1.2.1: Global Normalized Performance Rankings', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Physics Adjusted Time (PAT) in Seconds', fontsize=12)
plt.ylabel('Athlete', fontsize=12)
plt.xlim(df_sorted['PAT_V1.2.1'].min() - 0.5, df_sorted['PAT_V1.2.1'].max() + 0.5)

# Add value labels
for p in ax.patches:
    ax.annotate(f'{p.get_width():.4f}s', 
                (p.get_width() + 0.05, p.get_y() + p.get_height()/2),
                va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('OmniSprint_V121_Leaderboard.png', dpi=300)
print("Saved: OmniSprint_V121_Leaderboard.png")

# 3. Figure 2: Metabolic Efficiency Decay (200m/400m Analysis)
# This highlights why Tebogo's 200m PAT is calculated differently
df_long = df[df['Event'].isin(['200m', '400m'])].copy()
df_long['Adjustment'] = df_long['RawTime'] - df_long['PAT_V1.2.1']

plt.figure(figsize=(10, 6))
sns.scatterplot(data=df_long, x='RawTime', y='PAT_V1.2.1', size='Adjustment', hue='Name', sizes=(100, 400))

plt.title('Ward-Smith Metabolic Fade Analysis (V1.2.1)', fontsize=14, fontweight='bold')
plt.xlabel('Official Raw Clock Time (s)')
plt.ylabel('Normalized PAT (s)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('Metabolic_Decay_Analysis.png', dpi=300)
print("Saved: Metabolic_Decay_Analysis.png")

# 4. Figure 3: Atmospheric Sensitivity (Theoretical Contour)
# Showing how the RK4 engine perceives the Wind/Altitude relationship
wind = np.linspace(-2.0, 2.0, 50)
alt = np.linspace(0, 2500, 50)
W, A = np.meshgrid(wind, alt)
# Physics-informed proxy for PAT shift
Z = (0.05 * W) + (0.00008 * A) 

plt.figure(figsize=(10, 7))
contour = plt.contourf(W, A, Z, levels=20, cmap='RdYlGn')
plt.colorbar(contour, label='Time Advantage/Penalty (Seconds)')
plt.title('OmniSprint V1.2.1 Environmental Sensitivity Map', fontsize=14, fontweight='bold')
plt.xlabel('Wind Velocity (m/s)')
plt.ylabel('Altitude (m)')
plt.tight_layout()
plt.savefig('Environmental_Sensitivity_Map.png', dpi=300)
print("Saved: Environmental_Sensitivity_Map.png")