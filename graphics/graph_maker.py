import datetime
from os.path import join

import plotly
import plotly.graph_objs as go
from plotly import tools
from data_parsing.tournament_reader import get_data_location

base_path = get_data_location() + "DATA\\"

""" list of dates of Set Releases in milliseconds """
releases = [(1485730800000, "AER release"), (1476050400000, "KLD release"), (1470002400000, "EMN release"), (1460930400000, "SOI release"), (1454281200000, "OGW release"),  (1444600800000, "BFZ release")]


def make_pearson_corr_graph(lists, pdict, adict, dicts_title, set_dir, title):

    data_comp = []
    annotations = []
    dates = [x[0] for x in lists[0]]

    for release in releases:
        y_val = 0
        release_date = datetime.datetime.fromtimestamp(release[0] / 1000.0)
        inside = False
        for date in dates:
            if date.day == release_date.day and date.month == release_date.month and date.year == release_date.year:
                index = dates.index(date)
                y_val = lists[0][index][1]
                inside = True
                x_val = date
                break
        if inside:
            annotations.append(
                dict(
                    x=x_val,
                    y=y_val,
                    xref='x',
                    yref='y',
                    text=release[1],
                    showarrow=True,
                    arrowhead=7,
                    ax=0,
                    ay=-20
                ))
    i = 0
    for lis in lists:
        # Create a trace
        trace = go.Scatter(
            x=[x[0] for x in lis],
            y=[y[1] for y in lis],
            name=dicts_title[i]
        )
        i = i + 1
        data_comp.append(trace)
    draw_graph(data_comp, annotations, pdict, adict, set_dir, title)



def draw_graph(data_comp, annotations, pdict, adict, set_dir, title):

    fig = tools.make_subplots(rows=2, cols=1)
    fig['layout']['annotations'] = annotations
    fig['data'] = data_comp
    fig.data[1].yaxis = 'y1'
    fig.data[1].xaxis = 'x1'

    ord_pdict = sorted(pdict.items())
    x_p, y_p = zip(*ord_pdict)
    traceP = go.Scatter(
        x=x_p,
        y=y_p,
        name="Pearson Correlation"
    )
    fig.append_trace(traceP, 2, 1)

    ord_adict = sorted(adict.items())
    x_a, y_a = zip(*ord_adict)
    traceA = go.Scatter(
        x=x_a,
        y=y_a,
        name="Pearson AutoCorrelation"
    )
    fig.append_trace(traceA, 2, 1)

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



def make_pearson_histogram(plist, plist2, plist5, plist10, set_dir):
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
        x=plist2,
        histnorm='count',
        name='Pearson Value t = 2',
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
            color='0066ff',
        ),
        opacity=0.90
    )

    trace4 = go.Histogram(
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
                         text=('Pearson Correlation[t = 2] Avg =  %.3f' % (sum(plist2) / float(len(plist2)))),
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
                         text=('Pearson Correlation[t = 5] Avg =  %.3f' % (sum(plist5)/float(len(plist5))) ),
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
                         text= ('Pearson Correlation[t = 10] Avg =  %.3f' % (sum(plist10)/float(len(plist10))) ),
                         font=dict(family='Arial',
                                   size=14,
                                   color='rgb(37,37,37)'),
                         bordercolor='rgb(55, 128, 191)',
                         borderwidth=2,
                         borderpad=4,
                         bgcolor='rgba(55, 128, 191, 0.6)',
                         showarrow=False))
                   ]
    data = [trace1, trace2, trace3, trace4]
    fig = go.Figure(data=data, layout=layout)
    fig['layout']['annotations'] = annotations
    plotly.offline.plot(fig, filename='Pearson Correlation ' + str(set_dir), auto_open=False)


def make_prediction_graph(dates, prices, predicted_prices, title, set_dir, MSE):
    base_path = get_data_location() + "PREDICTIONS\\"
    data_comp = []
    annotations = [(dict(xref='paper', yref='paper', x=0.95, y=0.85,
                         xanchor='right', yanchor='bottom',
                         text=('MSE =  %.3f' % MSE),
                         font=dict(family='Arial',
                                   size=14,
                                   color='rgb(37,37,37)'),
                         bordercolor='rgb(55, 128, 191)',
                         borderwidth=2,
                         borderpad=4,
                         bgcolor='rgba(55, 128, 191, 0.6)',
                         showarrow=False))]
    for release in releases:
        y_val = 0
        release_date = datetime.datetime.fromtimestamp(release[0] / 1000.0)
        inside = False
        for date in dates:
            if date.day == release_date.day and date.month == release_date.month and date.year == release_date.year:
                index = dates.index(date)
                y_val = prices[index]
                inside = True
                x_val = date
                break
        if inside:
            annotations.append(
                dict(
                    x=x_val,
                    y=y_val,
                    xref='x',
                    yref='y',
                    text=release[1],
                    showarrow=True,
                    arrowhead=7,
                    ax=0,
                    ay=-20
                ))
    trace = go.Scatter(
        x=dates,
        y=prices,
        name="Real Price"
    )
    data_comp.append(trace)
    trace2 = go.Scatter(
        x=dates,
        y=predicted_prices,
        name="Predicted Price"
    )
    data_comp.append(trace2)

    layout = go.Layout(
        title='Prediction ' + str(title)
    )
    title = title + "_Prediction"
    fig = go.Figure(data=data_comp, layout=layout)
    fig['layout']['annotations'] = annotations
    fig['data'] = data_comp
    plotly.offline.plot(fig, filename=str(join(base_path, set_dir)) + "\\" + str(title), auto_open=False)


def make_Q_validation_graph(validation_lists, title_list, title):
    base_path = get_data_location() + "Q_validation_graph\\"
    data_comp = []
    i = 0
    for lis in validation_lists:
        # Create a trace
        trace = go.Scatter(
            x=[x[0] for x in lis],
            y=[y[1] for y in lis],
            name= title_list[i]
        )
        i = i + 1
        data_comp.append(trace)
    layout = go.Layout(
        title=title
    )
    fig = go.Figure(data=data_comp, layout=layout)
    fig['data'] = data_comp
    plotly.offline.plot(fig, filename=str(base_path) + "\\" + str(title), auto_open=False)


def make_Q_validation_intervals_graph(x_axis, triplets, title_list, title):
    base_path = get_data_location() + "Q_validation_graph\\"
    data = []
    i = 0
    for triplet in triplets:
        upper_bound = go.Scatter(
            name='Lower Bound',
            x=x_axis,
            y=triplet[0],
            mode='lines',
            marker=dict(color="444"),
            line=dict(width=0),
            fillcolor='rgba(68, 68, 68, 0.3)',
            fill='tonexty')

        trace = go.Scatter(
            name=title_list[i],
            x=x_axis,
            y=triplet[1],
            mode='lines',
            line=dict(color='rgb(31, 119, 180)'),
            fillcolor='rgba(68, 68, 68, 0.3)',
            fill='tonexty')

        lower_bound = go.Scatter(
            name='Upper Bound',
            x=x_axis,
            y=triplet[2],
            marker=dict(color="444"),
            line=dict(width=0),
            mode='lines')

        # Trace order can be important
        # with continuous error bars
        data.append(lower_bound)
        data.append(trace)
        data.append(upper_bound)
        i = i + 1

    layout = go.Layout(
        title=title,
        showlegend = False)

    fig = go.Figure(data=data, layout=layout)
    plotly.offline.plot(fig, filename=str(base_path) + "\\" + str(title), auto_open=False)

def make_intervals_comparison_graph(x_axis, names, triplets, title, budget):
    base_path = get_data_location() + "Intervals\\"
    colors = ['rgba(214,39,40,0.3)', 'rgba(86, 72, 146, 0.3)', 'rgba(148,103,189, 0.3)', 'rgba(31,119,180, 0.3)', 'rgba(255,127,14, 0.3)', 'rgba(44,160,44, 0.3)']
    # 31 blue 0.0, 44 green 0.4, 214 red 0.6, 255 orange 0.2, 148 purple 0.8   rgba(112, 73, 147, 0.3)
    data = []
    i = 0
    for triplet in triplets:
        upper_bound = go.Scatter(
            x=x_axis,
            y=triplet[0],
            mode='lines',
            line=dict(width=0),
            fillcolor=colors[i],
            fill='tonexty',
            showlegend=False)

        trace = go.Scatter(
            name=names[i],
            x=x_axis,
            y=triplet[1],
            mode='lines',
            line=dict(color=colors[i].replace("0.3", "1"), width=5),
            fillcolor=colors[i],
            fill='tonexty')

        lower_bound = go.Scatter(
            x=x_axis,
            y=triplet[2],
            line=dict(width=0),
            mode='lines',
            showlegend=False)

        # Trace order can be important
        # with continuous error bars
        data.append(lower_bound)
        data.append(trace)
        data.append(upper_bound)
        i = i + 1

    layout = go.Layout(
        legend=dict(orientation="h",
                    x=0, y=1.05,
                    font=dict(
                        family='Raleway',
                        size=40,
                        color='#000000'
                    ),
                    ),
        yaxis=dict(
            title='Profit Rate',
            gridwidth=5,
            showline=True,
            linewidth=5,
            zeroline=True,
            zerolinewidth=5
        ),
        xaxis=dict(
            title='Experiment Start',
            gridwidth = 5
        ),
        margin=go.Margin(
            l=140,
            r=120,
            b=140,
            t=50,
            pad=0
        ),
        shapes=[{
            'type': 'line',
            'xref': 'x',
            'yref': 'y',
            'x0': 0,
            'y0': budget,
            'x1': 5,
            'y1': budget,
            'line': {
                'color': '#444444',
                'width': 5,
            },
        }],
        font=dict(family='Raleway', size=40, color='#000000')
    )

    fig = go.Figure(data=data, layout=layout)
    plotly.offline.plot(fig, filename=str(base_path) + "\\" + str(title), auto_open=False)


def draw_box_graph(names, xes, lists, title, grouped = True, budget = 100):
    base_path = get_data_location() + "box_plots"
    data_comp = []
    i = 0
    for lis in lists:
        trace = go.Box(
            y=lis,
            x = xes[i],
            name=names[i],
            boxmean=True,
            boxpoints=False,
            line=dict(width=5),
        )
        data_comp.append(trace)
        i += 1
    layout = go.Layout(
        legend=dict(orientation="h",
                    x = 0, y = 1.05,
                    font=dict(
                        family='Raleway',
                        size=40,
                        color='#000000'
                    ),
                    ),
        yaxis = dict(
            title='Profit Rate',
            gridwidth=5,
            showline=True,
            linewidth=5,
            zeroline =True,
            zerolinewidth=5
        ),
        xaxis = dict(
            title='Experiment Start',
        ),
        margin=go.Margin(
            l=140,
            r=20,
            b=140,
            t=100,
            pad=0
        ),
        font=dict(family='Raleway', size=40, color='#000000')
    )
    if grouped:
        layout['boxmode'] = "group"
    fig = go.Figure(data=data_comp, layout=layout)
    fig['data'] = data_comp
    plotly.offline.plot(fig, filename=str(base_path) + "\\" + str(title), auto_open=False)





def draw_running_profit_graph(x_axis, names, profits, title, budget):
    base_path = get_data_location() + "Running_Profit\\"
    colors = ['rgba(214,39,40,0.3)', 'rgba(86, 72, 146, 0.3)', 'rgba(148,103,189, 0.3)', 'rgba(31,119,180, 0.3)', 'rgba(255,127,14, 0.3)', 'rgba(44,160,44, 0.3)']
    # 31 blue 0.0, 44 green 0.4, 214 red 0.6, 255 orange 0.2, 148 purple 0.8   rgba(112, 73, 147, 0.3)
    data = []
    i = 0
    for profit in profits:
        trace = go.Scatter(
            name=names[i],
            x=x_axis,
            y=profits[i],
            mode='lines',
            line=dict(color=colors[i].replace("0.3", "1"), width=5),
        )
        data.append(trace)
        i = i + 1

    layout = go.Layout(
        legend=dict(orientation="h",
                    x=0, y=1.05,
                    font=dict(
                        family='Raleway',
                        size=40,
                        color='#000000'
                    ),
                    ),
        yaxis=dict(
            title='Profit Rate',
            gridwidth=5,
            showline=True,
            linewidth=5,
            zeroline=True,
            zerolinewidth=5
        ),
        xaxis=dict(
            title='Date',
            gridwidth = 5
        ),
        margin=go.Margin(
            l=140,
            r=120,
            b=140,
            t=50,
            pad=0
        ),
        font=dict(family='Raleway', size=40, color='#000000')
    )

    fig = go.Figure(data=data, layout=layout)
    plotly.offline.plot(fig, filename=str(base_path) + "\\" + str(title), auto_open=False)