import os
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import time

# Set page configuration
st.set_page_config(
    page_title="Stock Performance Comparison",
    page_icon="📈",
    layout="wide",  # This makes the view wider
    initial_sidebar_state="expanded"
)

# Constants for colors
STOCK1_COLOR = "blue"
STOCK2_COLOR = "#ffae21"
DEFAULT_INVESTMENT = 100


def handle_exceptions(func):
    """Surface errors in the UI instead of silently swallowing them."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.warning(f"{func.__name__} failed: {type(e).__name__}: {e}")
            return None

    return wrapper

def retry_request(func):
    """Decorator to retry a function call with exponential backoff."""
    def wrapper(*args, **kwargs):
        max_retries = 3
        for i in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i == max_retries - 1:
                    raise e
                time.sleep(2 ** i)
    return wrapper

_HERE = os.path.dirname(os.path.abspath(__file__))


@st.cache_data
def load_ticker_universe():
    """
    Build a deduped, searchable list of tickers from the local CSVs.
    Returns a DataFrame with columns: Ticker, Name, Category.
    """
    frames = []
    for path, category in [
        (os.path.join(_HERE, "Stocks.csv"), "Stock"),
        (os.path.join(_HERE, "ETFs.csv"), "ETF"),
    ]:
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if "Ticker" not in df.columns or "Stock Name" not in df.columns:
            continue
        df = df[["Ticker", "Stock Name"]].rename(columns={"Stock Name": "Name"})
        df["Category"] = category
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=["Ticker", "Name", "Category"])

    universe = pd.concat(frames, ignore_index=True)
    universe = universe.dropna(subset=["Ticker", "Name"])
    universe["Ticker"] = universe["Ticker"].astype(str).str.strip().str.upper()
    universe["Name"] = universe["Name"].astype(str).str.strip()
    # Drop the literal header row that snuck into a CSV
    universe = universe[universe["Ticker"] != "TICKER"]
    # Prefer ETF tag where the same ticker appears in both files (SPY, QQQ, ...).
    # "ETF" sorts before "Stock", so ascending=True puts ETF first.
    universe = universe.sort_values(["Ticker", "Category"], ascending=[True, True])
    universe = universe.drop_duplicates(subset=["Ticker"], keep="first")
    universe = universe.sort_values("Name", key=lambda s: s.str.lower()).reset_index(drop=True)
    return universe


def _format_picker_option(ticker, universe_df):
    """Render a dropdown option like 'AAPL — Apple Inc. (Stock)'."""
    if ticker == "__manual__":
        return "Type a ticker manually..."
    row = universe_df.loc[universe_df["Ticker"] == ticker]
    if row.empty:
        return ticker
    name = row.iloc[0]["Name"]
    category = row.iloc[0]["Category"]
    return f"{ticker} — {name} ({category})"


def ticker_picker(label, default_ticker, key_prefix, universe_df):
    """
    Searchable picker that defaults to a known ticker but lets users
    fall back to a manual text input for tickers not in the universe.
    """
    options = universe_df["Ticker"].tolist()
    if default_ticker not in options:
        options = [default_ticker] + options
    options = options + ["__manual__"]

    try:
        default_index = options.index(default_ticker)
    except ValueError:
        default_index = 0

    selection = st.sidebar.selectbox(
        label,
        options=options,
        index=default_index,
        key=f"{key_prefix}_select",
        format_func=lambda t: _format_picker_option(t, universe_df),
        help="Start typing a company name or ticker to search.",
    )

    if selection == "__manual__":
        return st.sidebar.text_input(
            f"{label} (custom ticker)",
            value=default_ticker,
            key=f"{key_prefix}_manual",
            help="Enter any Yahoo Finance ticker, e.g. NVDA, COIN, BRK-B.",
        ).strip().upper()

    return selection


@st.cache_data(ttl=24*3600)
@retry_request
def fetch_stock_info(ticker):
    stock = yf.Ticker(ticker)
    return stock.info

@st.cache_data(ttl=3600)
@retry_request
def fetch_stock_history(ticker, start_date):
    stock = yf.Ticker(ticker)
    return stock.history(start=start_date)

@st.cache_data(ttl=3600)
@retry_request
def fetch_stock_news(ticker):
    stock = yf.Ticker(ticker)
    return stock.news

@handle_exceptions
def get_stock_data(ticker, start_date):
    data = fetch_stock_history(ticker, start_date)
    if data is None or data.empty:
        return data
    data['Year'] = data.index.year
    return data


def adjust_start_date_to_stock_data(start_date, data):
    """
    Compare the input start date with the first available date in the stock data.
    Return the later date in the format of date_input (datetime.date).

    :param start_date: datetime.date - The desired start date for comparison.
    :param data: pd.DataFrame - The stock data with a datetime index.
    :return: datetime.date - The adjusted start date.
    """
    # Ensure start_date is a pd.Timestamp for compatibility
    start_date = pd.Timestamp(start_date)

    # Get the first available date in the DataFrame
    first_date_in_data = data.index.min()

    # Compare the dates and get the later one
    adjusted_start_date = max(start_date, first_date_in_data)

    # Return the adjusted date in the format of date_input (datetime.date)
    return adjusted_start_date.date()


def calculate_yearly_performance(data):
    """
    Calculate the yearly percentage change in closing prices
    from the first trading day to the last trading day of each year.

    :param data: DataFrame containing stock prices with a 'Close' column.
    :return: Series with yearly percentage returns.
    """
    if data is None or data.empty or 'Close' not in data.columns:
        return pd.Series(dtype=float)

    yearly_open = data['Close'].resample('Y').first()
    yearly_close = data['Close'].resample('Y').last()

    # Calculate the percentage difference between the first and last closing prices of each year
    yearly_returns = ((yearly_close - yearly_open) / yearly_open) * 100

    # Drop any potential NaN values (e.g., if there is only one year of data)
    yearly_returns = yearly_returns.dropna()

    return yearly_returns


@handle_exceptions
def display_stock_prices_chart(data1, data2, ticker1, ticker2):
    st.subheader(f"Stock Price History: {ticker1} vs {ticker2}")

    # Create traces for each stock
    trace1 = go.Scatter(
        x=data1.index,
        y=data1['Close'],
        mode='lines',
        name=ticker1,
        line=dict(color=STOCK1_COLOR),
        hovertemplate=f'<b>{ticker1}</b><br>'
                      f'<b>Date:</b> %{{x|%b %d, %Y}}<br>'
                      f'<b>Price:</b> $%{{y:.2f}}<extra></extra>'
    )

    trace2 = go.Scatter(
        x=data2.index,
        y=data2['Close'],
        mode='lines',
        name=ticker2,
        line=dict(color=STOCK2_COLOR),
        hovertemplate=f'<b>{ticker2}</b><br>'
                      f'<b>Date:</b> %{{x|%b %d, %Y}}<br>'
                      f'<b>Price:</b> $%{{y:.2f}}<extra></extra>'
    )

    # Create the layout for the chart
    layout = go.Layout(
        title=f'Stock Prices Over Time: {ticker1} vs {ticker2}',
        xaxis=dict(title='Year', tickformat='%Y'),
        yaxis=dict(title='Stock Price (USD)'),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='black',
            font=dict(
                size=14,
                color='black'
            )
        ),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    # Create the figure with the data and layout
    fig = go.Figure(data=[trace1, trace2], layout=layout)

    # Display the interactive chart
    st.plotly_chart(fig, use_container_width=True)


@handle_exceptions
def display_stock_prices_chart_normalized(data1, data2, ticker1, ticker2):
    st.subheader(f"Stock Price History Normalized: {ticker1} vs {ticker2}")

    # Normalize the stock prices to start at the same value
    start_price = min(data1['Close'].iloc[0], data2['Close'].iloc[0])
    data1['Normalized_Price'] = data1['Close'] / data1['Close'].iloc[0] * start_price
    data2['Normalized_Price'] = data2['Close'] / data2['Close'].iloc[0] * start_price

    # Create traces for each stock
    trace1 = go.Scatter(
        x=data1.index,
        y=data1['Normalized_Price'],
        mode='lines',
        name=ticker1,
        line=dict(color=STOCK1_COLOR),
        hovertemplate=f'<b>{ticker1}</b><br>'
                      f'<b>Date:</b> %{{x|%b %d, %Y}}<br>'
                      f'<b>Price:</b> $%{{y:.2f}}<extra></extra>'
    )

    trace2 = go.Scatter(
        x=data2.index,
        y=data2['Normalized_Price'],
        mode='lines',
        name=ticker2,
        line=dict(color=STOCK2_COLOR),
        hovertemplate=f'<b>{ticker2}</b><br>'
                      f'<b>Date:</b> %{{x|%b %d, %Y}}<br>'
                      f'<b>Price:</b> $%{{y:.2f}}<extra></extra>'
    )

    # Create the layout for the chart
    layout = go.Layout(
        title=f'Stock Prices Over Time Normalized: {ticker1} vs {ticker2}',
        xaxis=dict(title='Year', tickformat='%Y'),
        yaxis=dict(title='Normalized Stock Price (USD)'),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='black',
            font=dict(
                size=14,
                color='black'
            )
        ),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    # Create the figure with the data and layout
    fig = go.Figure(data=[trace1, trace2], layout=layout)

    # Display the interactive chart
    st.plotly_chart(fig, use_container_width=True)


# Calculate investment growth
def calculate_investment_growth(data, initial_investment=DEFAULT_INVESTMENT):
    if data is None or data.empty:
        return None
    initial_price = data['Close'].iloc[0]
    current_price = data['Close'].iloc[-1]
    return (current_price / initial_price) * initial_investment


@handle_exceptions
def display_yearly_performance_comparison(performance1, performance2, ticker1, ticker2):
    st.subheader(f"Yearly Performance Comparison: {ticker1} vs {ticker2}")

    # Create traces for each stock's yearly performance
    trace1 = go.Bar(
        x=performance1.index.year,
        y=performance1.values,
        name=ticker1,
        marker_color=STOCK1_COLOR,
        hovertemplate=f'<b>{ticker1}</b><br>'
                      f'<b>Year:</b> %{{x}}<br>'
                      f'<b>Return:</b> %{{y:.2f}}%<extra></extra>'
    )

    trace2 = go.Bar(
        x=performance2.index.year,
        y=performance2.values,
        name=ticker2,
        marker_color=STOCK2_COLOR,
        hovertemplate=f'<b>{ticker2}</b><br>'
                      f'<b>Year:</b> %{{x}}<br>'
                      f'<b>Return:</b> %{{y:.2f}}%<extra></extra>'
    )

    # Create the layout for the chart
    layout = go.Layout(
        title='Yearly Performance Comparison',
        xaxis=dict(title='Year', tickformat='%Y'),
        yaxis=dict(title='Yearly Return (%)'),
        barmode='group',
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='black',
            font=dict(
                size=14,
                color='black'
            )
        ),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    # Create the figure with the data and layout
    fig = go.Figure(data=[trace1, trace2], layout=layout)

    # Display the interactive chart
    st.plotly_chart(fig, use_container_width=True)


def display_results(ticker1, ticker2, performance1, performance2, data1, data2, start_date):
    try:
        if performance1 is None or performance2 is None or performance1.empty or performance2.empty:
            st.warning("Not enough yearly data to compare these tickers.")
            return

        # Align performances on years present in both
        common_years = performance1.index.intersection(performance2.index)
        performance1 = performance1.loc[common_years]
        performance2 = performance2.loc[common_years]

        # Scoreboard
        scores = (performance1 > performance2).astype(int).sum(), (performance2 > performance1).astype(int).sum()

        col1, col2 = st.columns(2)
        with col1:
             st.metric(label=f"{ticker1} Wins", value=int(scores[0]), delta=None)
        with col2:
             st.metric(label=f"{ticker2} Wins", value=int(scores[1]), delta=None)

        # Yearly comparison grid
        comparison_df = pd.DataFrame({
            'Year': performance1.index.year,
            ticker1: performance1.values,
            ticker2: performance2.values
        })

        comparison_df['Winner'] = comparison_df[[ticker1, ticker2]].idxmax(axis=1)

        # Format percentage values
        comparison_df[ticker1] = comparison_df[ticker1].apply(lambda x: f'{x:.2f}%')
        comparison_df[ticker2] = comparison_df[ticker2].apply(lambda x: f'{x:.2f}%')

        def colorize(val, column):
            if column == ticker1 or column == ticker2:
                color = 'green' if float(val[:-1]) > 0 else 'red'
                return f'background-color: {color}; color: white'
            elif column == 'Winner':
                return f'background-color: {STOCK1_COLOR}; color: white' if val == ticker1 else f'background-color: {STOCK2_COLOR}; color: white'
            return ''

        styled_df = comparison_df.style.applymap(lambda val: colorize(val, ticker1), subset=[ticker1]) \
            .applymap(lambda val: colorize(val, ticker2), subset=[ticker2]) \
            .applymap(lambda val: colorize(val, 'Winner'), subset=['Winner']) \
            .set_table_styles({
            ticker1: [{'selector': 'th', 'props': [('background-color', 'yellow'), ('color', 'black')]}],
            ticker2: [{'selector': 'th', 'props': [('background-color', 'lightblue'), ('color', 'black')]}],
            'Winner': [{'selector': 'th', 'props': [('background-color', 'gray'), ('color', 'white')]}],
            'Year': [{'selector': 'th', 'props': [('background-color', 'white'), ('color', 'black')]}]
        })

        st.write("#### Yearly Comparison Grid by percentage each year")
        st.dataframe(styled_df)

        # Download CSV
        csv = comparison_df.to_csv().encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name=f'{ticker1}_vs_{ticker2}_yearly_performance.csv',
            mime='text/csv',
        )

        display_stock_prices_chart_normalized(data1, data2, ticker1, ticker2)
        display_stock_prices_chart(data1, data2, ticker1, ticker2)

        # Calculate and display investment growth
        investment1 = calculate_investment_growth(data1)
        investment2 = calculate_investment_growth(data2)
        st.write("---")

        st.subheader(f"Investment Growth (Initial: ${DEFAULT_INVESTMENT})")
        col1, col2 = st.columns(2)
        with col1:
            if investment1 is not None:
                delta_pct1 = ((investment1 - DEFAULT_INVESTMENT) / DEFAULT_INVESTMENT) * 100
                st.metric(label=f"{ticker1} Value Today", value=f"${investment1:.2f}", delta=f"{delta_pct1:.2f}%")
            else:
                st.metric(label=f"{ticker1} Value Today", value="N/A")
        with col2:
            if investment2 is not None:
                delta_pct2 = ((investment2 - DEFAULT_INVESTMENT) / DEFAULT_INVESTMENT) * 100
                st.metric(label=f"{ticker2} Value Today", value=f"${investment2:.2f}", delta=f"{delta_pct2:.2f}%")
            else:
                st.metric(label=f"{ticker2} Value Today", value="N/A")

        st.write("---")

        display_yearly_performance_comparison(performance1, performance2, ticker1, ticker2)

    except Exception as e:
        st.error(f"Error displaying results: {e}")


def _fmt_money(value):
    if value is None:
        return "N/A"
    try:
        return f"${value:,}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_percent(value):
    # yfinance 1.x returns dividendYield already as a percent (e.g. 0.35 == 0.35%).
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _fmt_number(value, prefix="", suffix=""):
    if value is None:
        return "N/A"
    try:
        return f"{prefix}{float(value):.2f}{suffix}"
    except (TypeError, ValueError):
        return f"{prefix}{value}{suffix}"


@handle_exceptions
def display_side_by_side_info(ticker1, ticker2):
    st.subheader("General Information Comparison")

    col1, col2 = st.columns(2)

    info1 = fetch_stock_info(ticker1)
    info2 = fetch_stock_info(ticker2)

    def display_info_in_col(col, ticker, info):
        with col:
            st.markdown(f"### {ticker}")
            if info:
                st.write(f"**Company Name:** {info.get('longName') or 'N/A'}")
                st.write(f"**Sector:** {info.get('sector') or 'N/A'}")
                st.write(f"**Industry:** {info.get('industry') or 'N/A'}")
                st.write(f"**Market Cap:** {_fmt_money(info.get('marketCap'))}")
                st.write(f"**P/E Ratio:** {_fmt_number(info.get('forwardPE'))}")
                st.write(f"**Dividend Yield:** {_fmt_percent(info.get('dividendYield'))}")
                st.write(f"**52-Week High:** {_fmt_number(info.get('fiftyTwoWeekHigh'), prefix='$')}")
                st.write(f"**52-Week Low:** {_fmt_number(info.get('fiftyTwoWeekLow'), prefix='$')}")
            else:
                st.error(f"Could not fetch general information for {ticker}")

    display_info_in_col(col1, ticker1, info1)
    display_info_in_col(col2, ticker2, info2)


def get_name(ticker):
    try:
        info = fetch_stock_info(ticker)
        if info:
            return info.get('longName', ticker)
        return ticker
    except Exception:
        return ticker


def _extract_news_item(article):
    """Normalize news items across old (flat) and new (nested under 'content') yfinance shapes."""
    if not isinstance(article, dict):
        return None, None
    content = article.get('content', article)
    title = content.get('title') or article.get('title')
    link = None
    for key in ('canonicalUrl', 'clickThroughUrl'):
        val = content.get(key)
        if isinstance(val, dict) and val.get('url'):
            link = val['url']
            break
        if isinstance(val, str):
            link = val
            break
    link = link or article.get('link')
    return title, link


@handle_exceptions
def display_news(ticker):
    news = fetch_stock_news(ticker) or []
    with st.expander(f"Recent News for {ticker}"):
        if not news:
            st.write("_No recent news available._")
            return
        shown = 0
        for article in news:
            title, link = _extract_news_item(article)
            if not title:
                continue
            st.write(f"**{title}**")
            if link:
                st.write(f"[Read more]({link})")
            shown += 1
            if shown >= 5:
                break


def main():
    universe = load_ticker_universe()
    st.sidebar.caption(f"Searchable universe: {len(universe):,} stocks & ETFs")

    ticker1 = ticker_picker("First ticker", "AAPL", "ticker1", universe)
    ticker2 = ticker_picker("Second ticker", "MSFT", "ticker2", universe)

    start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2015-01-01"),
                                       help="Choose the starting date for comparison.")

    st.sidebar.write("#### Comparison Options")
    compare = st.sidebar.button("Compare Tickers")

    if not compare:
        st.title("Stock Performance Comparison")
        st.write("Compare the performance of two stock tickers over the last 10 years.")

    if compare:
        data1 = get_stock_data(ticker1, start_date)
        data2 = get_stock_data(ticker2, start_date)
        name1 = get_name(ticker1)
        name2 = get_name(ticker2)
        st.subheader(f"Comparing {name1} vs {name2}")

        missing = []
        if data1 is None or data1.empty:
            missing.append(ticker1)
        if data2 is None or data2.empty:
            missing.append(ticker2)
        if missing:
            st.error(f"Could not fetch price history for: {', '.join(missing)}. "
                     f"Check the ticker symbol(s) and try again.")
            return

        if not data1.empty and not data2.empty:
            performance1 = calculate_yearly_performance(data1)
            performance2 = calculate_yearly_performance(data2)

            display_results(ticker1, ticker2, performance1, performance2, data1, data2, start_date)

            st.write("---")
            display_side_by_side_info(ticker1, ticker2)
            st.write("---")
            display_news(ticker1)
            display_news(ticker2)
            st.markdown("""
            <hr style="margin-top: 50px;">
            <div style="text-align: center;">
                <p style="font-size: 14px;">
                Developed by <a href="https://github.com/Roialfassi" target="_blank">Roi Alfassi</a> |
                Powered by <a href="https://streamlit.io/" target="_blank">Streamlit</a> and 
                <a href="https://pypi.org/project/yfinance/" target="_blank">yFinance</a></p>
                <p style="font-size: 12px; color: grey;">© 2024 Roi Alfassi. All rights reserved.</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
