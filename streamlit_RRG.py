import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

@st.cache_data
def ma(data, period):
    return data.rolling(window=period).mean()

@st.cache_data
def calculate_rrg_values(data, benchmark):
    sbr = data / benchmark
    rs1 = ma(sbr, 10)
    rs2 = ma(sbr, 26)
    rs = 100 * ((rs1 - rs2) / rs2 + 1)
    rm1 = ma(rs, 1)
    rm2 = ma(rs, 4)
    rm = 100 * ((rm1 - rm2) / rm2 + 1)
    return rs, rm

@st.cache_data
def get_data(universe):
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=100)

    if universe == "WORLD":
        benchmark = "ACWI"
        sectors = ["^GSPC", "^NDX", "^RUT", "^HSI", "3032.HK", "^STOXX50E", "^BSESN", "^KS11", 
                   "^TWII", "000001.SS", "^N225", "HYG", "LQD", "EEM", "GLD"]
        sector_names = {
            "^GSPC": "SP500", "^NDX": "Nasdaq 100", "^RUT": "US Small Cap", "^HSI": "Hang Seng",
            "3032.HK": "HS Tech", "^STOXX50E": "Europe", "^BSESN": "India", "^KS11": "Korea",
            "^TWII": "Taiwan", "000001.SS": "China A", "^N225": "Japan", "HYG": "High Yield Bond",
            "LQD": "IG Corporate Bond", "EEM": "Emerging Mkt Equity", "GLD": "Gold"
        }
    elif universe == "US":
        benchmark = "^GSPC"
        sectors = ["XLK", "XLY", "XLV", "XLF", "XLC", "XLI", "XLE", "XLB", "XLP", "XLU", "XLRE"]
        sector_names = {
            "XLK": "Technology", "XLY": "Consumer Discretionary", "XLV": "Health Care",
            "XLF": "Financials", "XLC": "Communications", "XLI": "Industrials", "XLE": "Energy",
            "XLB": "Materials", "XLP": "Consumer Staples", "XLU": "Utilities", "XLRE": "Real Estate"
        }
    elif universe == "HK":
        benchmark = "^HSI"
        sectors = ["^HSNU", "^HSNF", "^HSNP", "^HSNC"]
        sector_names = {"^HSNU": "Utilities", "^HSNF": "Financials", "^HSNP": "Properties","^HSNC": "Commerce & Industry"}

    data = yf.download([benchmark] + sectors, start=start_date, end=end_date)['Close']
    return data, benchmark, sectors, sector_names

def create_rrg_chart(data, benchmark, sectors, sector_names, universe):
    data_weekly = data.resample('W-FRI').last()
    rrg_data = pd.DataFrame()
    for sector in sectors:
        rs_ratio, rs_momentum = calculate_rrg_values(data_weekly[sector], data_weekly[benchmark])
        rrg_data[f"{sector}_RS-Ratio"] = rs_ratio
        rrg_data[f"{sector}_RS-Momentum"] = rs_momentum

    weeks_to_plot = 4
    last_n_weeks = rrg_data.iloc[-weeks_to_plot:]

    # Calculate the min and max values for each quadrant
    quadrant_data = {
        'Lagging': {'x': [], 'y': []},
        'Weakening': {'x': [], 'y': []},
        'Improving': {'x': [], 'y': []},
        'Leading': {'x': [], 'y': []}
    }

    for sector in sectors:
        x_values = last_n_weeks[f"{sector}_RS-Ratio"]
        y_values = last_n_weeks[f"{sector}_RS-Momentum"]
        for x, y in zip(x_values, y_values):
            if x < 100 and y < 100:
                quadrant_data['Lagging']['x'].append(x)
                quadrant_data['Lagging']['y'].append(y)
            elif x >= 100 and y < 100:
                quadrant_data['Weakening']['x'].append(x)
                quadrant_data['Weakening']['y'].append(y)
            elif x < 100 and y >= 100:
                quadrant_data['Improving']['x'].append(x)
                quadrant_data['Improving']['y'].append(y)
            else:
                quadrant_data['Leading']['x'].append(x)
                quadrant_data['Leading']['y'].append(y)

    # Calculate the overall min and max with padding
    padding = 1
    min_x = min(min(quadrant_data['Lagging']['x'] + quadrant_data['Improving']['x'], default=100) - padding, 96)
    max_x = max(max(quadrant_data['Weakening']['x'] + quadrant_data['Leading']['x'], default=100) + padding, 104)
    min_y = min(min(quadrant_data['Lagging']['y'] + quadrant_data['Weakening']['y'], default=100) - padding, 96)
    max_y = max(max(quadrant_data['Improving']['y'] + quadrant_data['Leading']['y'], default=100) + padding, 104)

    fig = go.Figure()

    quadrant_colors = {"Lagging": "pink", "Weakening": "lightyellow", "Improving": "lightblue", "Leading": "lightgreen"}
    curve_colors = {"Lagging": "red", "Weakening": "orange", "Improving": "darkblue", "Leading": "darkgreen"}

    def get_quadrant(x, y):
        if x < 100 and y < 100: return "Lagging"
        elif x >= 100 and y < 100: return "Weakening"
        elif x < 100 and y >= 100: return "Improving"
        else: return "Leading"

    for sector in sectors:
        x_values = last_n_weeks[f"{sector}_RS-Ratio"]
        y_values = last_n_weeks[f"{sector}_RS-Momentum"]
        current_quadrant = get_quadrant(x_values.iloc[-1], y_values.iloc[-1])
        color = curve_colors[current_quadrant]
        
        fig.add_trace(go.Scatter(
            x=x_values, y=y_values, mode='lines+markers', name=f"{sector} ({sector_names[sector]})",
            line=dict(color=color, width=2), marker=dict(size=6, symbol='circle'),
            legendgroup=sector, showlegend=True
        ))
        
        fig.add_trace(go.Scatter(
            x=[x_values.iloc[-1]], y=[y_values.iloc[-1]], mode='markers+text',
            name=f"{sector} (latest)", marker=dict(color=color, size=12, symbol='circle'),
            text=[sector], textposition="top center", legendgroup=sector, showlegend=False
        ))

    fig.update_layout(
        title=f"Relative Rotation Graph (RRG) for {'S&P 500' if universe == 'US' else 'Hang Seng' if universe == 'HK' else 'World'} {'Sectors' if universe != 'WORLD' else 'Indices'} (Weekly)",
        xaxis_title="RS-Ratio", yaxis_title="RS-Momentum",
        width=1200, height=800,
        xaxis=dict(range=[min_x, max_x], title_font=dict(size=14), dtick=1),
        yaxis=dict(range=[min_y, max_y], title_font=dict(size=14), scaleanchor="x", scaleratio=1, dtick=1),
        plot_bgcolor='white',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02, title=f"Legend<br>Benchmark: {'ACWI (MSCI World)' if universe == 'WORLD' else benchmark}"),
        shapes=[
            dict(type="rect", xref="x", yref="y", x0=min_x, y0=100, x1=100, y1=max_y, fillcolor="lightblue", opacity=0.5, line_width=0),
            dict(type="rect", xref="x", yref="y", x0=100, y0=100, x1=max_x, y1=max_y, fillcolor="lightgreen", opacity=0.5, line_width=0),
            dict(type="rect", xref="x", yref="y", x0=min_x, y0=min_y, x1=100, y1=100, fillcolor="pink", opacity=0.5, line_width=0),
            dict(type="rect", xref="x", yref="y", x0=100, y0=min_y, x1=max_x, y1=100, fillcolor="lightyellow", opacity=0.5, line_width=0),
            dict(type="line", xref="x", yref="y", x0=100, y0=min_y, x1=100, y1=max_y, line=dict(color="black", width=1)),
            dict(type="line", xref="x", yref="y", x0=min_x, y0=100, x1=max_x, y1=100, line=dict(color="black", width=1)),
        ]
    )

    # Adjust quadrant label positions to corners
    fig.add_annotation(x=min_x, y=min_y, text="Lagging", showarrow=False, font=dict(size=16), xanchor="left", yanchor="bottom")
    fig.add_annotation(x=max_x, y=min_y, text="Weakening", showarrow=False, font=dict(size=16), xanchor="right", yanchor="bottom")
    fig.add_annotation(x=min_x, y=max_y, text="Improving", showarrow=False, font=dict(size=16), xanchor="left", yanchor="top")
    fig.add_annotation(x=max_x, y=max_y, text="Leading", showarrow=False, font=dict(size=16), xanchor="right", yanchor="top")

    return fig

st.title("Relative Rotation Graph (RRG) Chart")

st.sidebar.header("Universe Selection")
world = st.sidebar.checkbox("World", value=True)
us = st.sidebar.checkbox("US")
hk = st.sidebar.checkbox("HK")

if world:
    universe = "WORLD"
elif us:
    universe = "US"
elif hk:
    universe = "HK"
else:
    universe = "WORLD"

data, benchmark, sectors, sector_names = get_data(universe)
fig = create_rrg_chart(data, benchmark, sectors, sector_names, universe)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Latest Data")
st.dataframe(data.tail())






