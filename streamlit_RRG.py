import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from investpy import get_index_historical_data

def ma(data, period):
    return data.rolling(window=period).mean()

def calculate_rrg_values(data, benchmark):
    sbr = data / benchmark
    
    rs1 = ma(sbr, 10)
    rs2 = ma(sbr, 26)
    rs = 100 * ((rs1 - rs2) / rs2 + 1)
    
    rm1 = ma(rs, 1)
    rm2 = ma(rs, 4)
    rm = 100 * ((rm1 - rm2) / rm2 + 1)
    
    return rs, rm

# User input for stock universe
universe = input("Enter stock universe (WORLD, US or HK): ").upper()

# Parameters
weeks_to_plot = 4  # Show 4 weeks of data

end_date = datetime.now()
start_date = end_date - timedelta(weeks=100)  # 100 weeks of data

if universe == "WORLD":
    benchmark = "ACWI"
    sectors = ["^GSPC", "^NDX", "^RUT", "^HSI", "^HSTECH", "^STOXX50E", "^BSESN", "^KS11", 
               "^TWII", "000001.SS", "^N225", "HYG", "LQD", "EEM", "GLD"]
    sector_names = {
        "^GSPC": "SP500",
        "^NDX": "Nasdaq 100",
        "^RUT": "US Small Cap",
        "^HSI": "Hang Seng",
        "^HSTECH": "HS Tech",
        "^STOXX50E": "Europe",
        "^BSESN": "India",
        "^KS11": "Korea",
        "^TWII": "Taiwan",
        "000001.SS": "China A",
        "^N225": "Japan",
        "HYG": "High Yield Bond",
        "LQD": "IG Corporate Bond",
        "EEM": "Emerging Mkt Equity",
        "GLD": "Gold"
    }
    data = yf.download([benchmark] + sectors, start=start_date, end=end_date)['Close']

elif universe == "US":
    benchmark = "^GSPC"
    sectors = ["XLK", "XLY", "XLV", "XLF", "XLC", "XLI", "XLE", "XLB", "XLP", "XLU", "XLRE"]
    sector_names = {
        "XLK": "Technology",
        "XLY": "Consumer Discretionary",
        "XLV": "Health Care",
        "XLF": "Financials",
        "XLC": "Communications",
        "XLI": "Industrials",
        "XLE": "Energy",
        "XLB": "Materials",
        "XLP": "Consumer Staples",
        "XLU": "Utilities",
        "XLRE": "Real Estate"
    }
    data = yf.download([benchmark] + sectors, start=start_date, end=end_date)['Close']

elif universe == "HK":
    benchmark = "HSCI"
    sectors = ["HSCICD", "HSCICS", "HSCIH", "HSCIC", "HSCIIT", "HSCIPC", "HSCIF", "HSCIU", "HSCIT", "HSCIIG", "HSCIM"]
    sector_names = {sector: sector for sector in sectors}  # Using ticker as name for HK
    data = pd.DataFrame()
    for index in [benchmark] + sectors:
        try:
            index_data = get_index_historical_data(index=index, country="hong kong", 
                                                   from_date=start_date.strftime('%d/%m/%Y'), 
                                                   to_date=end_date.strftime('%d/%m/%Y'))
            data[index] = index_data['Close']
        except Exception as e:
            print(f"Error fetching data for {index}: {e}")
else:
    raise ValueError("Invalid universe selection. Please choose 'WORLD', 'US', or 'HK'.")

data_weekly = data.resample('W-FRI').last()

rrg_data = pd.DataFrame()
for sector in sectors:
    rs_ratio, rs_momentum = calculate_rrg_values(data_weekly[sector], data_weekly[benchmark])
    rrg_data[f"{sector}_RS-Ratio"] = rs_ratio
    rrg_data[f"{sector}_RS-Momentum"] = rs_momentum

last_n_weeks = rrg_data.iloc[-weeks_to_plot:]

# Calculate the actual min and max values for both axes
actual_min_x = last_n_weeks[[f"{sector}_RS-Ratio" for sector in sectors]].min().min()
actual_max_x = last_n_weeks[[f"{sector}_RS-Ratio" for sector in sectors]].max().max()
actual_min_y = last_n_weeks[[f"{sector}_RS-Momentum" for sector in sectors]].min().min()
actual_max_y = last_n_weeks[[f"{sector}_RS-Momentum" for sector in sectors]].max().max()

# Set the chart boundaries to include all data points
padding = 0.5
min_x = min(actual_min_x - padding, 97)
max_x = max(actual_max_x + padding, 103)
min_y = min(actual_min_y - padding, 97)
max_y = max(actual_max_y + padding, 103)

fig = go.Figure()

quadrant_colors = {
    "Lagging": "pink",
    "Weakening": "lightyellow",
    "Improving": "lightblue",
    "Leading": "lightgreen"
}

curve_colors = {
    "Lagging": "red",
    "Weakening": "orange",
    "Improving": "darkblue",
    "Leading": "darkgreen"
}

def get_quadrant(x, y):
    if x < 100 and y < 100:
        return "Lagging"
    elif x >= 100 and y < 100:
        return "Weakening"
    elif x < 100 and y >= 100:
        return "Improving"
    else:
        return "Leading"

for sector in sectors:
    x_values = last_n_weeks[f"{sector}_RS-Ratio"]
    y_values = last_n_weeks[f"{sector}_RS-Momentum"]
    
    current_quadrant = get_quadrant(x_values.iloc[-1], y_values.iloc[-1])
    color = curve_colors[current_quadrant]
    
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        name=f"{sector} ({sector_names[sector]})",
        line=dict(color=color, width=2),
        marker=dict(size=6, symbol='circle'),
        legendgroup=sector,
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[x_values.iloc[-1]],
        y=[y_values.iloc[-1]],
        mode='markers+text',
        name=f"{sector} (latest)",
        marker=dict(color=color, size=12, symbol='circle'),
        text=[sector],
        textposition="top center",
        legendgroup=sector,
        showlegend=False
    ))

fig.update_layout(
    title=f"Relative Rotation Graph (RRG) for {'S&P 500' if universe == 'US' else 'Hang Seng Composite' if universe == 'HK' else 'World'} {'Sectors' if universe != 'WORLD' else 'Indices'} (Weekly)",
    xaxis_title="JdK RS-Ratio",
    yaxis_title="JdK RS-Momentum",
    width=1200,  # Increased width to accommodate legend
    height=800,
    xaxis=dict(range=[min_x, max_x], title_font=dict(size=14), dtick=1),
    yaxis=dict(range=[min_y, max_y], title_font=dict(size=14), scaleanchor="x", scaleratio=1, dtick=1),
    plot_bgcolor='white',
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.02,
        title=f"Legend<br>Benchmark: {'ACWI (MSCI World)' if universe == 'WORLD' else benchmark}"
    ),
    shapes=[
        dict(type="rect", xref="x", yref="y", x0=min_x, y0=100, x1=100, y1=max_y, fillcolor="lightblue", opacity=0.5, line_width=0),
        dict(type="rect", xref="x", yref="y", x0=100, y0=100, x1=max_x, y1=max_y, fillcolor="lightgreen", opacity=0.5, line_width=0),
        dict(type="rect", xref="x", yref="y", x0=min_x, y0=min_y, x1=100, y1=100, fillcolor="pink", opacity=0.5, line_width=0),
        dict(type="rect", xref="x", yref="y", x0=100, y0=min_y, x1=max_x, y1=100, fillcolor="lightyellow", opacity=0.5, line_width=0),
        dict(type="line", xref="x", yref="y", x0=100, y0=min_y, x1=100, y1=max_y, line=dict(color="black", width=1)),
        dict(type="line", xref="x", yref="y", x0=min_x, y0=100, x1=max_x, y1=100, line=dict(color="black", width=1)),
    ]
)

# Adjust quadrant label positions to be inside the colored areas
label_offset = 1
fig.add_annotation(x=min_x + label_offset, y=min_y + label_offset, text="Lagging", showarrow=False, font=dict(size=16))
fig.add_annotation(x=max_x - label_offset, y=min_y + label_offset, text="Weakening", showarrow=False, font=dict(size=16))
fig.add_annotation(x=min_x + label_offset, y=max_y - label_offset, text="Improving", showarrow=False, font=dict(size=16))
fig.add_annotation(x=max_x - label_offset, y=max_y - label_offset, text="Leading", showarrow=False, font=dict(size=16))

fig.show()

print(last_n_weeks)