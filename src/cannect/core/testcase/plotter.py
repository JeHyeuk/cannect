from cannect.config import env
from cannect.core.mdf import MdfReader
from pandas import DataFrame, Series
from plotly.graph_objs import Figure, Layout, Scatter
import os


class Plot(Figure):

    def __init__(
        self,
        data:DataFrame,
        separate:bool=False,
        linewidth:int=2,
        legendfontsize:int=14,
    ):
        super().__init__(
            layout=Layout(
                plot_bgcolor="white",   # [str] colors
                hovermode="x unified",  # [str] one of ( "x" | "y" | "closest" | False | "x unified" | "y unified" )
                dragmode="zoom",        # [str] one of ( "zoom" | "pan" | "select" | "lasso" |
                                        #                "drawclosedpath" | "drawopenpath" | "drawline" |
                                        #                "drawrect" | "drawcircle" | "orbit" | "turntable" | False )
                margin={
                    "b": 40,            # [int] bottom margin
                    "l": 40,            # [int] left margin
                    "r": 40,            # [int] right margin
                    "t": 40             # [int] top margin
                },
                legend={
                    "font": {
                        "size": legendfontsize,
                    },
                    "bgcolor": "white",                 # [str]
                    "bordercolor": "#444",              # [str]
                    "borderwidth": 0,                   # [float]
                    "groupclick": "togglegroup",        # [str] one of ( "toggleitem" | "togglegroup" )
                    "itemclick": "toggle",              # [str] one of ( "toggle" | "toggleothers" | False )
                    "itemdoubleclick": "toggleothers",  # [str | bool] one of ( "toggle" | "toggleothers" | False )
                    "itemsizing": "trace",              # [str] one of ( "trace" | "constant" )
                    "itemwidth": 30,                    # [int] greater than or equal to 30
                    "orientation": "h",                 # [str] one of ( "v" | "h" )
                    "tracegroupgap": 10,                # [int] greater than or equal to 0
                    "traceorder": "normal",             # [str] combination of "normal", "reversed", "grouped" joined with "+"
                    "valign": "middle",                 # [str] one of ( "top" | "middle" | "bottom" )
                    "xanchor": "right",                 # [str] one of ( "auto" | "left" | "center" | "right" )
                    "x": 1.0,                           # [float] 1.02 for "v", 0.96 for "h"
                    "yanchor": "top",                   # [str] one of ( "auto" | "top" | "middle" | "bottom" )
                    "y": 1.04,                           # [float] 1.0 for both "v" and "h",

                },
                xaxis={
                    "autorange": True,              # [str | bool] one of ( True | False | "reversed" | "min reversed" |
                                                    #                       "max reversed" | "min" | "max" )
                    "color": "#444",                # [str]
                    "showgrid": True,               # [bool]
                    "gridcolor": "lightgrey",       # [str]
                    "griddash": "solid",            # [str] one of ( "solid" | "dot" | "dash" | "longdash" | "dashdot" )
                    "gridwidth": 0.5,               # [float]
                    "showline": True,               # [bool]
                    "linecolor": "grey",            # [str]
                    "linewidth": 1,                 # [float]
                    "mirror": False,                # [str | bool] one of ( True | "ticks" | False | "all" | "allticks" )
                    "rangeslider": {
                        "visible": False            # [bool]
                    },
                    "rangeselector": {
                        "visible": False,            # [bool]
                    },
                    "showticklabels": True,         # [bool]
                    "tickformat": "%Y/%m/%d",       # [str]
                    "zeroline": True,               # [bool]
                    "zerolinecolor": "lightgrey",   # [str]
                    "zerolinewidth": 1,             # [float]
                    "hoverformat": ".3f"
                },
                yaxis={
                    "autorange": True,              # [str | bool] one of ( True | False | "reversed" | "min reversed" |
                                                    #                       "max reversed" | "min" | "max" )
                    "color": "#444",                # [str]
                    "showgrid": True,               # [bool]
                    "gridcolor": "lightgrey",       # [str]
                    "griddash": "solid",            # [str] one of ( "solid" | "dot" | "dash" | "longdash" | "dashdot" )
                    "gridwidth": 0.5,               # [float]
                    "showline": True,               # [bool]
                    "linecolor": "grey",            # [str]
                    "linewidth": 1,                 # [float]
                    "mirror": False,                # [str | bool] one of ( True | "ticks" | False | "all" | "allticks" )
                    "showticklabels": True,         # [bool]
                    "zeroline": True,               # [bool]
                    "zerolinecolor": "lightgrey",   # [str]
                    "zerolinewidth": 1              # [float]
                }
            )
        )

        if separate:
            self.set_subplots(
                rows=max(len(data.columns), 1),
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.01
            )

        for n, col in enumerate(data, start=1):
            series = data[col]
            if separate:
                self.add_trace(self.trace(series, linewidth), row=n, col=1)
            else:
                self.add_trace(self.trace(series, linewidth))

            if separate:
                for axis in self['layout']:
                    if axis.startswith('xaxis') or axis.startswith('yaxis'):
                        self['layout'][axis].update({
                            "showgrid": True,  # [bool]
                            "gridcolor": "lightgrey",  # [str]
                            "griddash": "solid",  # [str] one of ( "solid" | "dot" | "dash" | "longdash" | "dashdot" )
                            "gridwidth": 0.5,  # [float]
                            "linecolor": "grey",  # [str]
                            "linewidth": 1,  # [float]
                            "mirror": False,
                            "zeroline": True,  # [bool]
                            "zerolinecolor": "lightgrey",  # [str]
                            "zerolinewidth": 1,  # [float]
                        })

        # self.layout.legend.font.size = legendfontsize
        # figure = Figure(layout=self.layout)
        # if separate:
        #     self.subplot['rows'] = len(data.columns)
        #     figure.set_subplots(**self.subplot)
        # else:
        #     self.layout.xaxis.title = "Time[s]"
        #
        # for n, col in enumerate(data, start=1):
        #     series = data[col]
        #     if separate:
        #         figure.add_trace(self.trace(series, linewidth), row=n, col=1)
        #     else:
        #         figure.add_trace(self.trace(series, linewidth))
        #
        #     if separate:
        #         for axis in figure['layout']:
        #             if axis.startswith('xaxis') or axis.startswith('yaxis'):
        #                 figure['layout'][axis].update(**self.multiaxis)
        #
        #
        # self.figure = figure
        return

    @classmethod
    def trace(cls, series:Series, linewidth:int) -> Scatter:
        return Scatter(
            name=series.name,
            x=series.index,
            y=series,
            mode='lines',
            line={
                'width':linewidth
            },
            showlegend=True,
            hovertemplate=f'{series.name}: %{{y}}<extra></extra>'
        )

    def save(self, filename:str='') -> str:
        if not filename:
            filename = self.filename
        file = str(env.DOWNLOADS / f"{filename}")
        self.write_image(
            file=file,
            width=1920,
            height=1080
        )
        return file

if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)


