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
def get_data(universe, sector, timeframe, custom_tickers=None, custom_benchmark=None):
    end_date = datetime.now()
    if timeframe == "Weekly":
        start_date = end_date - timedelta(weeks=100)
    else:  # Daily
        start_date = end_date - timedelta(days=500)

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
                   "^TWII", "000300.SS", "^N225", "HYG", "AGG", "EEM", "GDX", "XLE", "XME", "AAXJ","IBB","DBA"]
        sector_names = {
            "^GSPC": "標普500", "^NDX": "納指100", "^RUT": "羅素2000", "^HSI": "恆指",
            "3032.HK": "恒生科技", "^STOXX50E": "歐洲", "^BSESN": "印度", "^KS11": "韓國",
            "^TWII": "台灣", "000300.SS": "滬深300", "^N225": "日本", "HYG": "高收益債券",
            "AGG": "投資級別債券", "EEM": "新興市場", "GDX": "金礦", "XLE": "能源",
            "XME": "礦業", "AAXJ": "亞太日本除外", "IBB": "生物科技","DBA":"農業"
        }
    elif universe == "US":
        benchmark = "^GSPC"
        sectors = list(sector_universes["US"].keys())
        sector_names = {
            "XLK": "科技", "XLY": "非必須消費", "XLV": "健康護理",
            "XLF": "金融", "XLC": "通訊", "XLI": "工業", "XLE": "能源",
            "XLB": "物料", "XLP": "必須消費", "XLU": "公用", "XLRE": "房地產"
        }
    elif universe == "US Sectors":
        if sector:
            benchmark = sector
            sectors = sector_universes["US"][sector]
            sector_names = {s: "" for s in sectors}  # Assign empty strings as names
        else:
            st.error("Please select a US sector.")
            return None, None, None, None
    elif universe == "HK":
        benchmark = "^HSI"
        sectors = list(sector_universes["HK"].keys())
        sector_names = {"^HSNU": "公用", "^HSNF": "金融", "^HSNP": "地產", "^HSNC": "工商"}
    elif universe == "HK Sub-indexes":
        if sector:
            benchmark = sector
            sectors = sector_universes["HK"][sector]
            sector_names = {s: "" for s in sectors}  # Assign empty strings as names
        else:
            st.error("Please select a HK sub-index.")
            return None, None, None, None
    elif universe == "Customised Portfolio":
        if custom_benchmark and custom_tickers:
            benchmark = custom_benchmark
            sectors = [ticker for ticker in custom_tickers if ticker]  # Remove empty strings
            sector_names = {s: "" for s in sectors}  # Assign empty strings as names
        else:
            st.error("Please provide at least one stock ticker and select a benchmark for your custom portfolio.")
            return None, None, None, None

    try:
        tickers_to_download = [benchmark] + sectors
        data = yf.download(tickers_to_download, start=start_date, end=end_date)['Close']
        
        # Check if any tickers are missing from the downloaded data
        missing_tickers = set(tickers_to_download) - set(data.columns)
        if missing_tickers:
            st.warning(f"The following tickers could not be downloaded: {', '.join(missing_tickers)}")
            # Remove missing tickers from sectors
            sectors = [s for s in sectors if s not in missing_tickers]
            sector_names = {s: sector_names[s] for s in sectors if s in sector_names}

        if data.empty:
            st.error(f"No data available for the selected universe and sector.")
            return None, benchmark, sectors, sector_names
        
        # Remove columns with all NaN values
        data = data.dropna(axis=1, how='all')
        
        # Check if benchmark data is available
        if benchmark not in data.columns:
            st.error(f"No data available for the benchmark {benchmark}. Please choose a different benchmark.")
            return None, benchmark, sectors, sector_names
        
        # Remove sectors with no data
        valid_sectors = [s for s in sectors if s in data.columns]
        if len(valid_sectors) == 0:
            st.error("No valid sector data available. Please check your input and try again.")
            return None, benchmark, sectors, sector_names
        
        sectors = valid_sectors
        sector_names = {s: sector_names[s] for s in valid_sectors if s in sector_names}
        
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None, benchmark, sectors, sector_names

    return data, benchmark, sectors, sector_names

def create_rrg_chart(data, benchmark, sectors, sector_names, universe, timeframe):
    if timeframe == "Weekly":
        data_resampled = data.resample('W-FRI').last()
    else:  # Daily
        data_resampled = data

    rrg_data = pd.DataFrame()
    valid_sectors = []
    for sector in sectors:
        if sector in data_resampled.columns and benchmark in data_resampled.columns:
            try:
                rs_ratio, rs_momentum = calculate_rrg_values(data_resampled[sector], data_resampled[benchmark])
                rrg_data[f"{sector}_RS-Ratio"] = rs_ratio
                rrg_data[f"{sector}_RS-Momentum"] = rs_momentum
                valid_sectors.append(sector)
            except Exception as e:
                st.warning(f"Could not calculate RRG values for {sector}: {str(e)}")
        else:
            st.warning(f"Data for {sector} or benchmark {benchmark} is missing. Skipping this sector.")

    if not valid_sectors:
        st.error("No valid data available to create the RRG chart.")
        return None

    # Use only the last 5 data points (current + 4 historical)
    last_n_periods = rrg_data.iloc[-5:]

    # Calculate the min and max values with padding
    padding = 0.05  # 5% padding
    min_x = last_n_periods[[f"{sector}_RS-Ratio" for sector in valid_sectors]].min().min()
    max_x = last_n_periods[[f"{sector}_RS-Ratio" for sector in valid_sectors]].max().max()
    min_y = last_n_periods[[f"{sector}_RS-Momentum" for sector in valid_sectors]].min().min()
    max_y = last_n_periods[[f"{sector}_RS-Momentum" for sector in valid_sectors]].max().max()

    range_x = max_x - min_x
    range_y = max_y - min_y
    min_x = max(min_x - range_x * padding, 90)  # Ensure minimum is not less than 90
    max_x = min(max_x + range_x * padding, 110)  # Ensure maximum is not more than 110
    min_y = max(min_y - range_y * padding, 90)
    max_y = min(max_y + range_y * padding, 110)

    fig = go.Figure()

    quadrant_colors = {"Lagging": "pink", "Weakening": "lightyellow", "Improving": "lightblue", "Leading": "lightgreen"}
    curve_colors = {"Lagging": "red", "Weakening": "orange", "Improving": "darkblue", "Leading": "darkgreen"}

    def get_quadrant(x, y):
        if x < 100 and y < 100: return "Lagging"
        elif x >= 100 and y < 100: return "Weakening"
        elif x < 100 and y >= 100: return "Improving"
        else: return "Leading"

    for sector in valid_sectors:
        x_values = last_n_periods[f"{sector}_RS-Ratio"].dropna()
        y_values = last_n_periods[f"{sector}_RS-Momentum"].dropna()
        if len(x_values) > 0 and len(y_values) > 0:
            current_quadrant = get_quadrant(x_values.iloc[-1], y_values.iloc[-1])
            color = curve_colors[current_quadrant]
            
            # Modify the legend label and chart label based on the universe
            if universe == "US Sectors" or universe == "HK Sub-indexes" or universe == "Customised Portfolio":
                legend_label = sector
                chart_label = sector.replace('.HK', '')  # Remove .HK suffix
            else:
                legend_label = f"{sector} ({sector_names.get(sector, '')})"
                chart_label = f"{sector_names.get(sector, sector)}"
            
            fig.add_trace(go.Scatter(
                x=x_values, y=y_values, mode='lines+markers', name=legend_label,
                line=dict(color=color, width=2), marker=dict(size=6, symbol='circle'),
                legendgroup=sector, showlegend=True
            ))
            
            # Determine if current momentum is higher or lower than previous
            momentum_change = y_values.iloc[-1] - y_values.iloc[-2] if len(y_values) > 1 else 0
            text_position = "top center" if momentum_change >= 0 else "bottom center"
            
            fig.add_trace(go.Scatter(
                x=[x_values.iloc[-1]], y=[y_values.iloc[-1]], mode='markers+text',
                name=f"{sector} (latest)", marker=dict(color=color, size=12, symbol='circle'),
                text=[chart_label], textposition=text_position, legendgroup=sector, showlegend=False,
                textfont=dict(color='black', size=12, family='Arial Black')
            ))

    fig.update_layout(
        title=f"Relative Rotation Graph (RRG) for {universe} ({timeframe})",
        xaxis_title="RS-Ratio",
        yaxis_title="RS-Momentum",
        width=1200,
        height=800,
        xaxis=dict(range=[min_x, max_x], title_font=dict(size=14)),
        yaxis=dict(range=[min_y, max_y], title_font=dict(size=14)),
        plot_bgcolor='white',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02, title=f"Legend<br>Benchmark: {benchmark}"),
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
    label_font = dict(size=32, color='black', family='Arial Black')
    fig.add_annotation(x=min_x, y=min_y, text="落後", showarrow=False, font=label_font, xanchor="left", yanchor="bottom")
    fig.add_annotation(x=max_x, y=min_y, text="轉弱", showarrow=False, font=label_font, xanchor="right", yanchor="bottom")
    fig.add_annotation(x=min_x, y=max_y, text="改善", showarrow=False, font=label_font, xanchor="left", yanchor="top")
    fig.add_annotation(x=max_x, y=max_y, text="領先", showarrow=False, font=label_font, xanchor="right", yanchor="top")

    return fig

# Main Streamlit app
st.title("Relative Rotation Graph (RRG) Chart by JC")

st.sidebar.header("Chart Settings")

# Timeframe selection
timeframe = st.sidebar.selectbox(
    "Select Timeframe",
    options=["Weekly", "Daily"],
    key="timeframe_selector"
)

st.sidebar.header("Universe Selection")

universe_options = ["WORLD", "US", "US Sectors", "HK", "HK Sub-indexes", "Customised Portfolio"]
universe_names = {"WORLD": "World", "US": "US", "US Sectors": "US Sectors", "HK": "Hong Kong", "HK Sub-indexes": "HK Sub-indexes", "Customised Portfolio": "Customised Portfolio"}

selected_universe = st.sidebar.selectbox(
    "Select Universe",
    options=universe_options,
    format_func=lambda x: universe_names[x],
    key="universe_selector"
)

sector = None
custom_tickers = None
custom_benchmark = None

if selected_universe == "WORLD":
    # No additional selection needed for WORLD
    pass
elif selected_universe == "US":
    # No additional selection needed for US main sectors
    pass
elif selected_universe == "US Sectors":
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
    # No additional selection needed for HK main sectors
    pass
elif selected_universe == "HK Sub-indexes":
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
elif selected_universe == "Customised Portfolio":
    st.sidebar.subheader("Customised Portfolio")
    
    # Create 3 columns for input boxes
    col1, col2, col3 = st.sidebar.columns(3)
    
    # Create 15 input boxes for stock tickers
    custom_tickers = []
    for i in range(15):
        if i % 3 == 0:
            ticker = col1.text_input(f"Stock {i+1}", key=f"stock_{i+1}")
        elif i % 3 == 1:
            ticker = col2.text_input(f"Stock {i+1}", key=f"stock_{i+1}")
        else:
            ticker = col3.text_input(f"Stock {i+1}", key=f"stock_{i+1}")
        
        if ticker:
            # Process the ticker input
            if ticker.isalpha():
                # Convert alphabetic input to uppercase
                processed_ticker = ticker.upper()
            elif ticker.isdigit() and len(ticker) == 4:
                # Add .HK to 4-digit numeric input
                processed_ticker = f"{ticker}.HK"
            else:
                # For any other input, just use as is (this includes inputs already in correct format)
                processed_ticker = ticker
            
            custom_tickers.append(processed_ticker)
    
    # Dropdown for benchmark selection
    custom_benchmark = st.sidebar.selectbox(
        "Select Benchmark",
        options=["ACWI", "^GSPC", "^HSI"],
        key="custom_benchmark_selector"
    )

# Main app logic
if selected_universe:
    data, benchmark, sectors, sector_names = get_data(selected_universe, sector, timeframe, custom_tickers, custom_benchmark)
    if data is not None and not data.empty:
        fig = create_rrg_chart(data, benchmark, sectors, sector_names, selected_universe, timeframe)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("Latest Data")
            st.dataframe(data.tail())
        else:
            st.error("Failed to create the RRG chart. Please check your input data and try again.")
    else:
        st.error("No data available for the selected universe and sector. Please try a different selection.")
else:
    st.write("Please select a universe from the sidebar.")

# Add this at the end of your script to help with debugging
if st.checkbox("Show raw data"):
    st.write("Raw data:")
    st.write(data)
    st.write("Sectors:")
    st.write(sectors)
    st.write("Benchmark:")
    st.write(benchmark)

