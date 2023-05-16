import matplotlib.pyplot as plt
import mplhep as hep
import matplotlib.colors as colors
import numpy as np

# plot histograms
def plot_count_hist(data, title, output_path, single_pixel=False):
    plt.style.use(hep.style.ROOT)
    fig, ax = plt.subplots()
    hep.histplot(data, ax=ax)
    ax.set_title(title)
    ax.set_xlabel('Threshold [a.u.]')
    if single_pixel:
        ax.set_ylabel('Normalised single pixel counts [a.u.]')
    else:
        ax.set_ylabel('Normalised counts [a.u.]')
    ax.set_xlim([1100, 1400])
    ax.set_yscale("log")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close()


def plot_map(data, value, output_path):
    plt.style.use(hep.style.ROOT)
    fig, ax = plt.subplots()
    hep.hist2dplot(data, ax=ax, norm=colors.LogNorm(vmin=0.01, vmax=np.max(data)))
    ax.set_title(value)
    ax.set_xlabel('Columns')
    ax.set_ylabel('Rows')
    fig.savefig(output_path)
    plt.close()


def plot_hotpixel(data, cut_value, output_path):
    plt.style.use(hep.style.ROOT)
    fig, ax = plt.subplots()
    hep.histplot(data, ax=ax)
    ax.axvline(cut_value, color='red')
    ax.set_xlabel('Sum of counts [a.u.]')
    ax.set_ylabel('Number of pixels')
    ax.set_yscale("log")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close()


def plot_tot_hist(data, title, output_path):
    plt.style.use(hep.style.ROOT)
    fig, ax = plt.subplots()
    hep.histplot(data, ax=ax)
    ax.set_title(title)
    ax.set_xlim([1, 14])
    ax.set_ylim([0.1, 1e4])
    ax.set_xlabel('Time over threshold')
    ax.set_ylabel('Entries')
    ax.set_yscale("log")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close()