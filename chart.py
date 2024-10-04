# Take the data in the csv file (./data/2019.csv) and plot it on a pie chart

import pandas as pd
import matplotlib.pyplot as plt
import yaml

# Read the data from the csv file
data = pd.read_csv('./data/2019.csv')

# Read the languages.yml file
with open('./charts/languages.yml', 'r') as file:
    languages_data = yaml.safe_load(file)

# Create a dictionary mapping language names to their colors
language_colors = {}
for language, attributes in languages_data.items():
    if 'color' in attributes:
        language_colors[language] = attributes['color']

# Get the language counts
language_counts = data['language'].value_counts()

# Calculate the total count of all languages
total_count = language_counts.sum()

# Group languages with a frequency less than 0.5% into an "Other" category
threshold = 0.005 * total_count
other_count = language_counts[language_counts < threshold].sum()
language_counts = language_counts[language_counts >= threshold]
language_counts['Other'] = other_count

# Get the colors for the languages in the pie chart
colors = [language_colors.get(lang, '#0d1117') for lang in language_counts.index]
colors[language_counts.index.get_loc('Other')] = '#FFFFFF'  # Set color for "Other" to white

# Custom autopct function
def custom_autopct(pct):
    return ('%1.1f%%' % pct) if pct >= 2 else ''

# Create a pie chart using the column language as the labels and report the percentage of each language
fig, ax = plt.subplots()
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

# Set text properties
textprops = {'color': 'white', 'fontweight': 'bold'}

# Create labels with percentage for entries less than 2%
labels = [f'{lang} ({pct:.1f}%)' if pct < 2 else lang for lang, pct in zip(language_counts.index, 100 * language_counts / total_count)]

# Create the pie chart
wedges, texts, autotexts = ax.pie(language_counts, labels=labels, autopct=custom_autopct, colors=colors, textprops=textprops)

# Move the "Other" label up by a few pixels
for text in texts:
    if text.get_text().startswith('Other'):
        text.set_y(text.get_position()[1] + 0.03)  # Adjust the y-position

plt.title(f'Updated data for "Visual Basic" repos \nthat were last updated in 2019 (Total: {total_count})', color='white', fontweight='bold')
plt.savefig('./charts/2019.png', facecolor=fig.get_facecolor())
plt.show()



