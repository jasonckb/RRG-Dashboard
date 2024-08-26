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
def get_data(universe, sector=None):
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=100)

    sector_universes = {
        "US": {
            "XLK": ["AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "MU", "CRM", "ASML", "SNPS", "IBM", "INTC", "TXN", "NOW", "QCOM", "AMD", "AMAT", "NOW", "PANW", "CDNS", "TSMC"],
            "XLY": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "MAR", "F", "GM", "ORLY", "DHI", "CMG", "TJX", "YUM", "LEN", "ULTA", "CCL", "EXPE"],
            "XLV": ["UNH", "JNJ", "LLY", "PFE", "ABT", "TMO", "MRK", "ABBV", "DHR", "BMY", "AMGN", "CVS", "ISRG", "MDT", "GILD", "VRTX", "CI", "ZTS", "RGEN", "BSX", "HCA"],
            "XLF": ["BRK.B", "JPM", "BAC", "WFC", "GS", "MS", "SPGI", "BLK", "C", "AXP", "CB", "MMC", "PGR", "PNC", "TFC", "V", "MA", "PYPL", "AON", "CME", "ICE", "COF"],
            "XLC": ["META", "GOOGL", "GOOG", "NFLX", "CMCSA", "DIS", "VZ", "T", "TMUS", "ATVI", "EA", "TTWO", "MTCH", "CHTR", "DISH", "FOXA", "TTWO", "FOX", "NWS", "WBD"],
            "XLI": ["UNP", "HON", "UPS", "BA", "CAT", "GE", "MMM", "RTX", "LMT", "FDX", "DE", "ETN", "EMR", "NSC", "CSX", "ADP", "GD", "NOC", "FDX", "JCI", "CARR", "ITW"],
            "XLE": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "KMI", "WMB", "HES", "HAL", "DVN", "BKR", "CTRA", "EQT", "APA", "MRO", "TRGP", "FANG"],
            "XLB": ["LIN", "APD", "SHW", "FCX", "ECL", "NEM", "DOW", "DD", "CTVA", "PPG", "NUE", "VMC", "ALB", "FMC", "CE", "MLM", "IFF", "STLD", "CF", "FMC"],
            "XLP": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "EL", "CL", "GIS", "KMB", "SYY", "KHC", "STZ", "HSY", "TGT", "ADM", "MNST", "DG", "DLTR", "WBA", "SJM"],
            "XLU": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "PCG", "WEC", "ES", "ED", "DTE", "AEE", "ETR", "CEG", "PCG", "EIX", "FFE", "CMS", "CNP", "PPL"],
            "XLRE": ["PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "SPG", "SBAC", "AVB", "EQR", "DLR", "VTR", "ARE", "CBRE", "WY", "EXR", "MAA", "IRM", "ESS", "HST"]
        },
        "HK": {
            "^HSNU": ["0002.HK", "0003.HK", "0006.HK", "0836.HK", "1038.HK", "2688.HK",],
            "^HSNF": ["0005.HK", "0011.HK", "0388.HK", "0939.HK", "1398.HK", "2318.HK", "2388.HK", "2628.HK","3968.HK","3988.HK","1299.HK"],
            "^HSNP": ["0012.HK", "0016.HK", "0017.HK", "0101.HK", "0823.HK", "0688.HK", "1109.HK", "1997.HK", "1209.HK", "0960.HK","1113.HK"],
            "^HSNC": ["0700.HK", "0857.HK", "0883.HK", "0941.HK", "0001.HK","0175.HK","0241.HK","0267.HK","0285.HK","0027.HK",
                      "0288.HK","0291.HK","0316.HK","0332.HK", "0386.HK", "0669.HK", "0762.HK", "0968.HK", "0981.HK", "0386.HK"]
        }
    }

    if universe == "WORLD":
        benchmark = "ACWI"
        sectors = ["^GSPC", "^NDX", "^RUT", "^HSI", "3032.HK", "^STOXX50E", "^BSESN", "^KS11", 
                   "^TWII", "000300", "^N225", "HYG", "AGG", "EEM", "GDX", "XLE", "XME", "AAXJ","IBB","DBA"]
        sector_names = {
            "^GSPC": "SP500", "^NDX": "Nasdaq 100", "^RUT": "US Small Cap", "^HSI": "Hang Seng",
            "3032.HK": "HS Tech", "^STOXX50E": "Europe", "^BSESN": "India", "^KS11": "Korea",
            "^TWII": "Taiwan", "000300": "China 300", "^N225": "Japan", "HYG": "High Yield Bond",
            "AGG": "IG Corporate Bond", "EEM": "Emerging Mkt Equity", "GDX": "Gold", "XLE": "Energy",
            "XME": "Mining", "AAXJ": "Asia ex Japan", "IBB": "Biotech","DBA":"Agriculture"
        }
    elif universe == "US":
        if sector:
            benchmark = sector
            sectors = sector_universes["US"][sector]
            sector_names = {s: "" for s in sectors}  # Assign empty strings as names
        else:
            benchmark = "^GSPC"
            sectors = list(sector_universes["US"].keys())
            sector_names = {
                "XLK": "Technology", "XLY": "Consumer Discretionary", "XLV": "Health Care",
                "XLF": "Financials", "XLC": "Communications", "XLI": "Industrials", "XLE": "Energy",
                "XLB": "Materials", "XLP": "Consumer Staples", "XLU": "Utilities", "XLRE": "Real Estate"
            }
    elif universe == "HK":
        if sector:
            benchmark = sector
            sectors = sector_universes["HK"][sector]
            sector_names = {s: "" for s in sectors}  # Assign empty strings as names
        else:
            benchmark = "^HSI"
            sectors = list(sector_universes["HK"].keys())
            sector_names = {"^HSNU": "Utilities", "^HSNF": "Financials", "^HSNP": "Properties", "^HSNC": "Commerce & Industry"}

    try:
        data = yf.download([benchmark] + sectors, start=start_date, end=end_date)['Close']
        if data.empty:
            st.error(f"No data available for the selected universe and sector.")
            return None, benchmark, sectors, sector_names
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, benchmark, sectors, sector_names

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

    # Calculate the actual min and max values for both axes
    actual_min_x = last_n_weeks[[f"{sector}_RS-Ratio" for sector in sectors]].min().min()
    actual_max_x = last_n_weeks[[f"{sector}_RS-Ratio" for sector in sectors]].max().max()
    actual_min_y = last_n_weeks[[f"{sector}_RS-Momentum" for sector in sectors]].min().min()
    actual_max_y = last_n_weeks[[f"{sector}_RS-Momentum" for sector in sectors]].max().max()

    # Calculate padding based on data range
    padding_x = (actual_max_x - actual_min_x) * 0.05
    padding_y = (actual_max_y - actual_min_y) * 0.05

    # Set the chart boundaries with adaptive padding
    min_x = max(min(actual_min_x - padding_x, 99), actual_min_x - padding_x)
    max_x = min(max(actual_max_x + padding_x, 101), actual_max_x + padding_x)
    min_y = max(min(actual_min_y - padding_y, 99), actual_min_y - padding_y)
    max_y = min(max(actual_max_y + padding_y, 101), actual_max_y + padding_y)

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
        xaxis_title="RS-Ratio",
        yaxis_title="RS-Momentum",
        width=1200,
        height=800,
        xaxis=dict(range=[min_x, max_x], title_font=dict(size=14)),
        yaxis=dict(range=[min_y, max_y], title_font=dict(size=14)),
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

universe_options = ["WORLD", "US", "HK"]
universe_names = {"WORLD": "World", "US": "US", "HK": "Hong Kong"}

selected_universe = st.sidebar.selectbox(
    "Select Universe",
    options=universe_options,
    format_func=lambda x: universe_names[x],
    key="universe_selector"
)

sector = None

if selected_universe == "WORLD":
    # No additional selection needed for WORLD
    pass
elif selected_universe == "US":
    us_sectors = ["XLK", "XLY", "XLV", "XLF", "XLC", "XLI", "XLE", "XLB", "XLP", "XLU", "XLRE"]
    us_sector_names = {
        "XLK": "Technology", "XLY": "Consumer Discretionary", "XLV": "Health Care",
        "XLF": "Financials", "XLC": "Communications", "XLI": "Industrials", "XLE": "Energy",
        "XLB": "Materials", "XLP": "Consumer Staples", "XLU": "Utilities", "XLRE": "Real Estate"
    }
    st.sidebar.subheader("US Sectors")
    selected_us_sector = st.sidebar.selectbox(
        "Select US Sector",
        options=us_sectors,
        format_func=lambda x: us_sector_names[x],
        key="us_sector_selector"
    )
    if selected_us_sector:
        sector = selected_us_sector
elif selected_universe == "HK":
    hk_sectors = ["^HSNU", "^HSNF", "^HSNP", "^HSNC"]
    hk_sector_names = {"^HSNU": "Utilities", "^HSNF": "Financials", "^HSNP": "Properties", "^HSNC": "Commerce & Industry"}
    st.sidebar.subheader("Hang Seng Sub-indexes")
    selected_hk_sector = st.sidebar.selectbox(
        "Select HK Sub-index",
        options=hk_sectors,
        format_func=lambda x: hk_sector_names[x],
        key="hk_sector_selector"
    )
    if selected_hk_sector:
        sector = selected_hk_sector

if selected_universe:
    data, benchmark, sectors, sector_names = get_data(selected_universe, sector)
    if data is not None and not data.empty:
        fig = create_rrg_chart(data, benchmark, sectors, sector_names, selected_universe)
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Latest Data")
        st.dataframe(data.tail())
    else:
        st.error("No data available for the selected universe and sector. Please try a different selection.")
else:
    st.write("Please select a universe from the sidebar.")