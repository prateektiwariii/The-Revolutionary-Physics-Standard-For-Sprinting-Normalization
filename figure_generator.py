import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D
from math import pi

# --- 1. CONFIGURATION & STYLING ---
plt.style.use('dark_background')
sns.set_context("talk")
CUSTOM_COLORS = ["#00e5ff", "#ff007f", "#9d00ff", "#ff8800", "#adff2f"]

try:
    df = pd.read_csv('Olympics_Data_Normalization.csv')
except FileNotFoundError:
    print("Error: 'Olympics_Data_Normaliziation.csv' not found. Run your C++ code first!")
    exit()

# --- PRE-CALCULATIONS ---
df['Wind_Impact'] = df['Wind'] * 0.05
df['Alt_Impact'] = df['Altitude'] * 0.0001
df['Raw_per_100'] = df['RawTime'] / df['Event'].map({'100m':1, '200m':2, '400m':4})
df['Total_Correction'] = df['Normalized100m'] - df['Raw_per_100']

# --- WIND LEGALITY (ONLY NEW DATA COLUMN) ---
df['WindLegal'] = df['Wind'] <= 2.0

# =========================================================
# FIGURE 1: THE ULTIMATE LEADERBOARD
# =========================================================
plt.figure(figsize=(16, 12))
df_sorted = df.sort_values('Normalized100m')

ax1 = sns.barplot(
    x='Normalized100m',
    y='Name',
    data=df_sorted,
    hue='Name',
    palette='magma',
    legend=False
)

for container in ax1.containers:
    ax1.bar_label(
        container,
        fmt='%.4f s',
        padding=15,
        color='white',
        fontweight='bold',
        fontsize=14
    )

plt.title('Physics-Normalized 100m Equivalent Leaderboard', fontsize=26, fontweight='bold', pad=30)
plt.xlabel('Normalized Time (s)', fontsize=18)
plt.ylabel('Athlete', fontsize=18)
plt.xlim(df['Normalized100m'].min() - 0.2, df['Normalized100m'].max() + 1.2)
plt.grid(axis='x', linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig('01_leaderboard.png')

# =========================================================
# FIGURE 2: THE "BIG THREE" FACTOR BREAKDOWN
# =========================================================
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
sns.histplot(df['Wind'], kde=True, color=CUSTOM_COLORS[0], ax=axes[0]).set_title('Wind Speed (m/s)')
sns.histplot(df['Altitude'], kde=True, color=CUSTOM_COLORS[1], ax=axes[1]).set_title('Altitude (m)')
sns.histplot(df['ReactionTime'], kde=True, color=CUSTOM_COLORS[2], ax=axes[2]).set_title('Reaction Time (s)')
plt.suptitle("Raw Factor Distributions", fontsize=20)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig('02_factors_distribution.png')

# =========================================================
# FIGURE 3: WIND vs. NORMALIZATION (LEGALITY AWARE)
# =========================================================
plt.figure(figsize=(10, 6))
sns.scatterplot(
    x='Wind',
    y='Normalized100m',
    data=df,
    hue='WindLegal',
    style='WindLegal',
    palette={True: '#00ffcc', False: '#ff4444'},
    s=120
)
plt.axvline(2.0, color='red', linestyle='--', alpha=0.7)
plt.title("How Wind Speed Shifts Normalized Times\n(Green = Legal, Red = Illegal)")
plt.savefig('03_wind_impact.png')

# =========================================================
# FIGURE 4: ALTITUDE vs. NORMALIZATION
# =========================================================
plt.figure(figsize=(10, 6))
sns.scatterplot(
    x='Altitude',
    y='Normalized100m',
    size='Wind',
    hue='Event',
    data=df,
    palette='Set2',
    sizes=(50, 400)
)
plt.title("Altitude vs Performance (Bubble Size = Wind)")
plt.savefig('04_altitude_impact.png')

# =========================================================
# FIGURE 5: EVENT EFFICIENCY DECAY
# =========================================================
plt.figure(figsize=(10, 6))
sns.boxplot(
    x='Event',
    y='Normalized100m',
    data=df,
    hue='Event',
    palette='viridis',
    legend=False
)
plt.title("Normalization Consistency Across Events")
plt.savefig('05_event_consistency.png')

# =========================================================
# FIGURE 6: 3D PERFORMANCE LANDSCAPE
# =========================================================
fig6 = plt.figure(figsize=(12, 10))
ax6 = fig6.add_subplot(111, projection='3d')
img6 = ax6.scatter(
    df['Wind'],
    df['Altitude'],
    df['Normalized100m'],
    c=df['Normalized100m'],
    cmap='plasma',
    s=200
)
ax6.set_xlabel('Wind (m/s)')
ax6.set_ylabel('Altitude (m)')
ax6.set_zlabel('Normalized Time (s)')
plt.colorbar(img6, label='Normalized Time', shrink=0.5)
plt.title("3D Condition vs Performance Mapping")
plt.savefig('06_3d_landscape.png')

# =========================================================
# FIGURE 7: CORRELATION HEATMAP
# =========================================================
plt.figure(figsize=(10, 8))
sns.heatmap(df.select_dtypes(include=[np.number]).corr(), annot=True, cmap='RdBu', center=0)
plt.title("Factor Correlation Heatmap")
plt.savefig('07_correlation.png')

# =========================================================
# FIGURE 8: TIME ADJUSTMENT DELTA
# =========================================================
plt.figure(figsize=(12, 8))
df['Delta'] = df['Normalized100m'] - df['Raw_per_100']
df_delta = df.sort_values('Delta')
colors = ['red' if x > 0 else 'green' for x in df_delta['Delta']]
plt.hlines(
    y=df_delta['Name'],
    xmin=0,
    xmax=df_delta['Delta'],
    color=colors,
    alpha=0.8,
    linewidth=5
)
plt.title("Net Correction Applied by Physics Engine (Seconds Added/Removed)")
plt.xlabel("Seconds Shifted")
plt.grid(axis='x', alpha=0.2)
plt.savefig('08_physics_tax.png')

# =========================================================
# FIGURE 9: THE OVERALL PERFORMANCE COMPARISON
# =========================================================
plt.figure(figsize=(12, 6))
sns.pointplot(x='Event', y='Raw_per_100', data=df, color='white', label='Raw (scaled to 100m)')
sns.pointplot(x='Event', y='Normalized100m', data=df, color='cyan', label='Physics Normalized')
plt.title("Raw Velocity vs. Physics-Adjusted Velocity")
plt.ylabel("Time (s)")
plt.legend()
plt.savefig('09_velocity_comparison.png')

# =========================================================
# FIGURE 10: ATHLETE RADAR
# =========================================================
def draw_radar(name, color):
    factors = ['ReactionTime', 'Wind', 'Altitude', 'Normalized100m']
    athlete_data = df[df['Name'] == name].iloc[0]

    stats = [
        1 - (athlete_data['ReactionTime'] / 0.25),
        (athlete_data['Wind'] + 2) / 4,
        athlete_data['Altitude'] / 2500,
        1 - (athlete_data['Normalized100m'] - 9) / 2
    ]

    angles = [n / float(len(factors)) * 2 * pi for n in range(len(factors))]
    stats += stats[:1]
    angles += angles[:1]

    fig10, ax10 = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    plt.xticks(angles[:-1], factors, color='white', size=12)
    ax10.plot(angles, stats, color=color, linewidth=2)
    ax10.fill(angles, stats, color=color, alpha=0.3)
    plt.title(f"Performance Profile: {name}", size=20, color=color, y=1.1)
    plt.savefig(f'10_radar_{name.replace(" ", "_")}.png')
    plt.close()

top_athlete = df.sort_values('Normalized100m').iloc[0]['Name']
draw_radar(top_athlete, '#00ffcc')

# =========================================================
# FIGURE 11: HEXBIN DENSITY
# =========================================================
plt.figure(figsize=(10, 8))
hb = plt.hexbin(
    df['ReactionTime'],
    df['Normalized100m'],
    gridsize=15,
    cmap='magma',
    mincnt=1
)
plt.colorbar(hb, label='Number of Athletes')
plt.xlabel('Reaction Time (s)')
plt.ylabel('Normalized 100m (s)')
plt.title('Performance Density Heatmap (RT vs Physics Output)')
plt.savefig('11_hexbin_density.png')

# =========================================================
# FIGURE 12: PAIRGRID
# =========================================================
g = sns.PairGrid(df[['Normalized100m', 'Wind', 'Altitude', 'ReactionTime']], diag_sharey=False)
g.map_upper(sns.scatterplot, s=80, alpha=0.6, color='#ff007f')
g.map_lower(sns.kdeplot, cmap='magma_r', fill=True)
g.map_diag(sns.histplot, kde=True, color='cyan')
plt.suptitle("Total Dataset Interaction Matrix", y=1.02, fontsize=20)
plt.savefig('12_pair_matrix.png')

# =========================================================
# FIGURE 13: CATEGORICAL SWARM (LEGALITY SPLIT)
# =========================================================
df['Wind_Type'] = pd.cut(
    df['Wind'],
    bins=[-10, -0.1, 0.1, 2.0, 10],
    labels=['Headwind', 'Neutral', 'Legal Tailwind', 'Illegal Tailwind']
)

plt.figure(figsize=(12, 7))
sns.swarmplot(
    x='Wind_Type',
    y='Normalized100m',
    hue='Event',
    data=df,
    size=9,
    palette='cool'
)
plt.title('Normalization Efficiency across Wind Conditions')
plt.grid(axis='y', alpha=0.2)
plt.savefig('13_wind_swarm.png')

print("All figures generated successfully with wind legality respected (nothing else changed).")
