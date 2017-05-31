from plotly import tools
import plotly
import plotly.graph_objs as go
from os.path import isfile, join


base_path = "C:\\Users\\pitu\\Desktop\\DATA\\"

def make_pearson_corr_graph(dicts, pdict, dicts_title, set_dir, title, hasDicts = True):
    data_comp = []

    i = 0
    if hasDicts:
        for d in dicts:
            ord_dict = sorted(d.items())
            x_c, y_c = zip(*ord_dict)
            # Create a trace
            trace = go.Scatter(
                x=x_c,
                y=y_c,
                name=dicts_title[i]
            )
            i = i + 1
            data_comp.append(trace)
    else:
        for d in dicts:
            # Create a trace
            trace = go.Scatter(
                x=d[0],
                y=d[1],
                name=dicts_title[i]
            )
            i = i + 1
            data_comp.append(trace)


    """annotations = [(dict(xref='paper', yref='paper', x=0.95, y=0.8,
                            xanchor='right', yanchor='bottom',
                            text='Pearson Correlation =  %.3f' % pearson,
                            font=dict(family='Arial',
                                      size=18,
                                      color='rgb(37,37,37)'),
                            bordercolor= 'rgb(55, 128, 191)',
                            borderwidth=3,
                            borderpad=5,
                            bgcolor='rgba(55, 128, 191, 0.6)',
                            showarrow=False))] 
    fig['layout']['annotations'] = annotations"""

    fig = tools.make_subplots(rows=2, cols=1)
    fig['data'] = data_comp
    fig.data[1].yaxis = 'y1'
    fig.data[1].xaxis = 'x1'

    ord_pdict = sorted(pdict.items())
    x_p, y_p = zip(*ord_pdict)
    traceP = go.Scatter(
        x=x_p,
        y=y_p,
        name= "Pearson Correlation"
    )
    fig.append_trace(traceP, 2, 1)

    fig['layout']['title'] = title

    fig['layout']['xaxis1'].update(
            title='Date',
            ticklen=5,
            zeroline=False,
            gridwidth=2,
        )
    fig['layout']['yaxis1'].update(
            title='Price/Usage',
            ticklen=5,
            gridwidth=2,
        )
    fig['layout']['xaxis2']['title'] = "Prices Graph forward Shift"
    fig['layout']['yaxis2']['title'] = "Coeff. value"
    plotly.offline.plot(fig, filename=str(join(base_path, set_dir)) + "\\" + str(title), auto_open=False)




def get_sorted_values(d):
    ord_dict = sorted(d.items())
    x_c, y_c = zip(*ord_dict)
    return y_c


def make_pearson_histogram(plist, plist5, plist10, plist20, set_dir):
    trace1 = go.Histogram(
        x=plist,
        histnorm='count',
        name='Pearson Value',
        autobinx=False,
        xbins=dict(
            start= -1,
            end=1,
            size=0.1
        ),
        marker=dict(
            color='#33ccff',
        ),
        opacity=0.9
    )

    trace2 = go.Histogram(
        x=plist5,
        histnorm='count',
        name='Pearson Value t = 5',
        autobinx=False,
        xbins=dict(
            start=-1,
            end=1,
            size=0.1
        ),
        marker=dict(
            color='#ff9966',
        ),
        opacity=0.90
    )

    trace3 = go.Histogram(
        x=plist10,
        histnorm='count',
        name='Pearson Value t = 10',
        autobinx=False,
        xbins=dict(
            start=-1,
            end=1,
            size=0.1
        ),
        marker=dict(
            color='0066ff',
        ),
        opacity=0.90
    )

    trace4 = go.Histogram(
        x=plist20,
        histnorm='count',
        name='Pearson Value t = 20',
        autobinx=False,
        xbins=dict(
            start=-1,
            end=1,
            size=0.1
        ),
        marker=dict(
            color='#339933',
        ),
        opacity=0.90
    )

    layout = go.Layout(
        title='Pearson Correlation for set ' + set_dir,
        xaxis=dict(
            title='Value',
            zeroline=True,
            zerolinecolor='#969696',
            zerolinewidth=4,
            linecolor='#636363',
            linewidth=6
        ),
        yaxis=dict(
            title='Count'
        ),
        bargap=0.4,
        bargroupgap=0.1
    )

    annotations = [(dict(xref='paper', yref='paper', x=0.95, y=0.85,
                                xanchor='right', yanchor='bottom',
                                text=('Pearson Correlation Avg =  %.3f' % (sum(plist)/float(len(plist))) ),
                                font=dict(family='Arial',
                                          size=14,
                                          color='rgb(37,37,37)'),
                                bordercolor= 'rgb(55, 128, 191)',
                                borderwidth=2,
                                borderpad=4,
                                bgcolor='rgba(55, 128, 191, 0.6)',
                                showarrow=False)),
                   (dict(xref='paper', yref='paper', x=0.95, y=0.8,
                         xanchor='right', yanchor='bottom',
                         text=('Pearson Correlation[t = 5] Avg =  %.3f' % (sum(plist5)/float(len(plist5))) ),
                         font=dict(family='Arial',
                                   size=14,
                                   color='rgb(37,37,37)'),
                         bordercolor='rgb(55, 128, 191)',
                         borderwidth=2,
                         borderpad=4,
                         bgcolor='rgba(55, 128, 191, 0.6)',
                         showarrow=False)),
                   (dict(xref='paper', yref='paper', x=0.95, y=0.75,
                         xanchor='right', yanchor='bottom',
                         text= ('Pearson Correlation[t = 10] Avg =  %.3f' % (sum(plist10)/float(len(plist10))) ),
                         font=dict(family='Arial',
                                   size=14,
                                   color='rgb(37,37,37)'),
                         bordercolor='rgb(55, 128, 191)',
                         borderwidth=2,
                         borderpad=4,
                         bgcolor='rgba(55, 128, 191, 0.6)',
                         showarrow=False)),
                   (dict(xref='paper', yref='paper', x=0.95, y=0.7,
                         xanchor='right', yanchor='bottom',
                         text=('Pearson Correlation[t = 20] Avg =  %.3f' % (sum(plist20)/float(len(plist20))) ),
                         font=dict(family='Arial',
                                   size=14,
                                   color='rgb(37,37,37)'),
                         bordercolor='rgb(55, 128, 191)',
                         borderwidth=2,
                         borderpad=4,
                         bgcolor='rgba(55, 128, 191, 0.6)',
                         showarrow=False))]

    data = [trace1, trace2, trace3, trace4]
    fig = go.Figure(data=data, layout=layout)
    fig['layout']['annotations'] = annotations
    plotly.offline.plot(fig, filename='Pearson Correlation ' + str(set_dir), auto_open=False)


