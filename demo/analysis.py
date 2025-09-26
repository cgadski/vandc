import vandc
import seaborn as sns
import matplotlib.pyplot as plt

runs = vandc.fetch_all(this_commit=True, command_glob="demo/example.py %")
df = vandc.collate_runs(runs)
df.to_csv("demo/results.csv")
sns.lineplot(data=df, x="step", y="value", hue="beta")
plt.show()
