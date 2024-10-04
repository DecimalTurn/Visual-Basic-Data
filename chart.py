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

# Get the colors for the languages in the pie chart
colors = [language_colors.get(lang, '#000000') for lang in language_counts.index]

# Create a pie chart using the column language as the labels and report the percentage of each language
plt.pie(language_counts, labels=language_counts.index, autopct='%1.1f%%', colors=colors)
plt.title('Languages Used in 2019')
plt.show()

# Save the pie chart as a png file
plt.savefig('./charts/2019.png')



