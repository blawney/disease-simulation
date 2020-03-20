import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import io
import re

plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['font.family'] = 'Raleway'
plt.rcParams['font.size'] = 16
colors = ['#2A8B12', '#ECA117']
sns.set_palette(sns.color_palette(colors))

def extract_svg_text(s):
    '''
    Extracts the text content of the SVG and sets the viewbox so it shows up
    well on front end.  Returns a proper svg object as text.
    '''
    # strip off the namespacing stuff-- only want the svg element itself
    m=re.search('<svg.*<\/svg>', s, flags=re.DOTALL)
    svg_text = m.group(0)

    # look in the opening SVG tag for the SVG viewbox that matplotlib created
    # We remove the width/height, as that ends up causing problems when
    # rendering in the browser
    prefix = re.findall('<svg.*?>', svg_text, flags=re.DOTALL)[0]
    viewbox_match = re.search('viewBox=".*?"', prefix, flags = re.DOTALL)
    viewbox = viewbox_match.group(0)
    new_prefix = '<svg %s>' % viewbox
    svg_text = svg_text[len(prefix):]
    svg_text = new_prefix + svg_text
    return svg_text

def history_plot(t1, mc1, t2, mc2):

    # convert from hours to days:
    t1 = t1/24
    t2 = t2/24

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.fill_between(t1, mc1, alpha=0.5, label='Modified')
    ax.fill_between(t2, mc2, alpha=0.5, label='Original')
    ax.set_xlabel('Time (Days)', fontsize=20)
    ax.set_ylabel('Mean Symptomatic Cases', fontsize=20)
    ax.legend()

    fh = io.BytesIO()
    fig.savefig(fh, format='svg', bbox_inches='tight')
    s=fh.getvalue().decode()
    svg_text = extract_svg_text(s)
    plt.close()
    return svg_text

def violin_plot(c1, c2):
    '''
    c1 and c2 are arrays of integers representing the number of total infections
    for each simulation.  c1 corresponds to the altered network, c2 to the original
    '''
    df1 = pd.DataFrame({'counts': c1, 'status': 'altered'})
    df2 = pd.DataFrame({'counts': c2, 'status': 'original'})
    df = pd.concat([df1,df2])
    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    sns.violinplot(y='counts', x='status', data=df, order=('altered', 'original'), 
                ax=ax)
    ax.set_xlabel('Configuration', fontsize=20)
    ax.set_xticklabels(['Altered', 'Original'])
    ax.set_ylabel('Total Infected', fontsize=20)
    ax.set_ylim((0,1.3*df['counts'].max()))
    plt.setp(ax.collections, alpha=0.5)
    fh = io.BytesIO()
    fig.savefig(fh, format='svg', bbox_inches='tight')
    s=fh.getvalue().decode()
    svg_text = extract_svg_text(s)
    plt.close()
    return svg_text