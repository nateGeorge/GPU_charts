import os
from glob import glob

import pandas as pd
import numpy as np
import requests as req
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup as bs
import matplotlib
matplotlib.rcParams.update({'font.size': 30})

def convert_process(x):
    """
    Converts process column in wikipedia transistor count table to numeric.
    """
    # NANs are floats
    if isinstance(x, float):
        return x
    else:
        return x.replace('nm', '').replace(',', '').strip()


def convert_area(x):
    """
    Converts area column in wikipedia transistor count table to numeric.
    """
    # NANs are floats
    if isinstance(x, float):
        return x
    else:
        return x.replace('mm²', '').replace(',', '').strip()


def update_transistor_data():
    """
    Retrieves GPU transistor count table from wikipedia and writes to disk
    as a csv.
    """
    res = req.get('https://en.wikipedia.org/wiki/Transistor_count')
    soup = bs(res.content, 'lxml')
    tables = soup.find_all('table', {'class': 'wikitable'})
    # find the table with GPU data
    for t in tables:
        if 'ARTC HD63484' in t.text:
            break

    # bs4 object has to be converted to a string
    # read_html returns a list for some reason
    df = pd.read_html(str(t))[0]
    # some data cleaning/type conversions
    df['Date of introduction'] = pd.to_datetime(df['Date of introduction'])

    df['Process'] = df['Process'].apply(convert_process).astype('float')
    df['Area'] = df['Area'].apply(convert_area).astype('float')
    df.rename({'Process': 'Process (nm)', 'Area': 'Area (mm²)'}, inplace=True)

    todays_date = str(pd.Timestamp('now').date())
    # clear old files
    for f in glob('data/gpu_transistor_count*'):
        os.remove(f)

    df.to_csv('data/gpu_transistor_count_' + todays_date + '.csv', index=False)


def plot_gpu_transistor_count(show=True, fit=True):
    """
    Creates plot of GPU transistor count with optional exponential fit to data.

    params:
    show: if True, shows plot
    fit: if True, fits and plots exponential fit.
    """
    # Should only be one file
    filename = glob('data/gpu_transistor_count*')[0]
    filedate = filename.split('.')[0].split('_')[-1]
    df = pd.read_csv(filename, parse_dates=['Date of introduction'], infer_datetime_format=True)
    # Need to convert date to a number for plotting.  Only a few with months so we'll ignore those
    df['Date of introduction'] = df['Date of introduction'].dt.year.astype('int')

    f = plt.figure(figsize=(12, 12))
    plt.scatter(x=df['Date of introduction'], y=df['Transistor count'], alpha=0.75, s=100)
    if fit:
        fit_params = np.polyfit(df['Date of introduction'].values, np.log(df['Transistor count'].values), 1)
        x = np.linspace(df['Date of introduction'].min(), df['Date of introduction'].max(), 10)
        log_y = fit_params[1] + fit_params[0] * x
        y = np.exp(log_y)
        # Showing the legend is too messy but left the label in there anyway
        label = 'Transistors = {} * e^({} * Year)'.format(round(fit_params[1], 3),
                                                        round(fit_params[0], 3))
        plt.plot(x, y, label=label, lw=4)

    ax = plt.gca()
    ax.set_yscale('log')
    plt.xlabel('Year')
    plt.ylabel('GPU transistor count')
    plt.title('GPU computational power over time')
    plt.tight_layout()
    for f in glob('images/gpu_moores_law_*'):
        os.remove(f)
    plt.savefig('images/gpu_moores_law_{}.png'.format(filedate))
    if show:
        plt.show()
