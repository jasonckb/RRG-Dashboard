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
            "XLK": ["AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "CSCO", "CRM", "ACN", "ORCL", "IBM", "INTC", "TXN", "NOW", "QCOM", "AMD"],
            "XLY": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "MAR", "F", "GM", "ORLY", "DHI", "CMG"],
            "XLV": ["UNH", "JNJ", "LLY", "PFE", "ABT", "TMO", "MRK", "ABBV", "DHR", "BMY", "AMGN", "CVS", "ISRG", "MDT", "GILD"],
            "XLF": ["BRK.B", "JPM", "BAC", "WFC", "GS", "MS", "SPGI", "BLK", "C", "AXP", "CB", "MMC", "PGR", "PNC", "TFC"],
            "XLC": ["META", "GOOGL", "GOOG", "NFLX", "CMCSA", "DIS", "VZ", "T", "TMUS", "ATVI", "EA", "TTWO", "MTCH", "CHTR", "DISH"],
            "XLI": ["UNP", "HON", "UPS", "BA", "CAT", "GE", "MMM", "RTX", "LMT", "FDX", "DE", "ETN", "EMR", "NSC", "CSX"],
            "XLE": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "KMI", "WMB", "HES", "HAL", "DVN", "BKR"],
            "XLB": ["LIN", "APD", "SHW", "FCX", "ECL", "NEM", "DOW", "DD", "CTVA", "PPG", "NUE", "VMC", "ALB", "FMC", "CE"],
            "XLP": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "EL", "CL", "GIS", "KMB", "SYY", "KHC", "STZ", "HSY"],
            "XLU": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "PCG", "WEC", "ES", "ED", "DTE", "AEE", "ETR"],
            "XLRE": ["PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "SPG", "SBAC", "AVB", "EQR", "DLR", "VTR", "ARE", "CBRE"]
        },
        "HK": {
            "^HSNU": ["0002.HK", "0003.HK", "0006.HK", "0836.HK", "1038.HK"],
            "^HSNF": ["0005.HK", "0011.HK", "0388.HK", "0939.HK", "1299.HK"],
            "^HSNP": ["0001.HK", "0016.HK", "0688.HK", "1109.HK", "1113.HK"],
            "^HSNC": ["0700.HK", "0857.HK", "0883.HK", "0941.HK", "0992.HK"]
        }
    }

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
        if sector:
            sectors = sector_universes["US"][sector]
            sector_names = {s: s for s in sectors}
        else:
            sectors = list(sector_universes["US"].keys())
            sector_names = {
                "XLK": "Technology", "XLY": "Consumer Discretionary", "XLV": "Health Care",
                "XLF": "Financials", "XLC": "Communications", "XLI": "Industrials", "XLE": "Energy",
                "XLB": "Materials", "XLP": "Consumer Staples", "XLU": "Utilities", "XLRE": "Real Estate"
            }
    elif universe == "HK":
        benchmark = "^HSI"
        if sector:
            sectors = sector_universes["HK"][sector]
            sector_names = {s: s for s in sectors}
        else:
            sectors = list(sector_universes["HK"].keys())
            sector_names = {"^HSNU": "Utilities", "^HSNF": "Financials", "^HSNP": "Properties", "^HSNC": "Commerce & Industry"}

    data = yf.download([benchmark] + sectors, start=start_date, end=end_date)['Close']
    return data, benchmark, sectors, sector_names

# ... [rest of the functions remain the same] ...

st.title("Relative Rotation Graph (RRG) Chart")

st.sidebar.header("Universe Selection")
cols = st.sidebar.columns(3)
world = cols[0].checkbox("World", value=True)
us = cols[1].checkbox("US")
hk = cols[2].checkbox("HK")

universe = None
sector = None

if world:
    universe = "WORLD"
    us, hk = False, False
elif us:
    universe = "US"
    world, hk = False, False
    us_sectors = ["XLK", "XLY", "XLV", "XLF", "XLC", "XLI", "XLE", "XLB", "XLP", "XLU", "XLRE"]
    us_sector_names = {
        "XLK": "Technology", "XLY": "Consumer Discretionary", "XLV": "Health Care",
        "XLF": "Financials", "XLC": "Communications", "XLI": "Industrials", "XLE": "Energy",
        "XLB": "Materials", "XLP": "Consumer Staples", "XLU": "Utilities", "XLRE": "Real Estate"
    }
    st.sidebar.subheader("US Sectors")
    us_cols = st.sidebar.columns(3)
    for i, s in enumerate(us_sectors):
        if us_cols[i % 3].checkbox(us_sector_names[s], key=f"us_{s}"):
            sector = s
            for j, other_s in enumerate(us_sectors):
                if other_s != s:
                    st.session_state[f"us_{other_s}"] = False
elif hk:
    universe = "HK"
    world, us = False, False
    hk_sectors = ["^HSNU", "^HSNF", "^HSNP", "^HSNC"]
    hk_sector_names = {"^HSNU": "Utilities", "^HSNF": "Financials", "^HSNP": "Properties", "^HSNC": "Commerce & Industry"}
    st.sidebar.subheader("Hang Seng Sub-indexes")
    hk_cols = st.sidebar.columns(2)
    for i, s in enumerate(hk_sectors):
        if hk_cols[i % 2].checkbox(hk_sector_names[s], key=f"hk_{s}"):
            sector = s
            for j, other_s in enumerate(hk_sectors):
                if other_s != s:
                    st.session_state[f"hk_{other_s}"] = False
else:
    universe = "WORLD"

if universe:
    data, benchmark, sectors, sector_names = get_data(universe, sector)
    fig = create_rrg_chart(data, benchmark, sectors, sector_names, universe)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Latest Data")
    st.dataframe(data.tail())
else:
    st.write("Please select a universe from the sidebar.")







