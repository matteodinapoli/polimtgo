from plotly import tools
import plotly
import plotly.graph_objs as go


def make_pearson_corr_graph(dicts, pdict, dicts_title, set_dir, title):
    data_comp = []
    i = 0
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
    plotly.offline.plot(fig, filename=str(set_dir) + "\\" + str(title))




def get_sorted_values(d):
    ord_dict = sorted(d.items())
    x_c, y_c = zip(*ord_dict)
    return y_c

