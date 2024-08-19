import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(
    page_title="Stock Performance Comparison",
    page_icon="📈",
    # layout="wide",  # This makes the view wider
    initial_sidebar_state="expanded"
)

stock1_color = "blue"
stock2_color = "#ffae21"


def get_stock_data(ticker, start_date):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date)
        data['Year'] = data.index.year
        return data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()


def calculate_yearly_performance(data):
    try:
        yearly_returns = data['Close'].resample('Y').ffill().pct_change().dropna() * 100
        return yearly_returns
    except Exception as e:
        st.error(f"Error calculating yearly performance: {e}")
        return pd.Series()


def display_stock_prices_chart(data1, data2, ticker1, ticker2):
    try:
        st.subheader(f"Stock Price History: {ticker1} vs {ticker2}")

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(data1.index, data1['Close'], label=ticker1, color=stock1_color)
        ax.plot(data2.index, data2['Close'], label=ticker2, color=stock2_color)

        ax.set_title('Stock Prices Over Time')
        ax.set_xlabel('Year')
        ax.set_ylabel('Stock Price (USD)')
        ax.legend()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error displaying stock prices chart: {e}")


def display_results(ticker1, ticker2, performance1, performance2, data1, data2):
    try:
        # st.subheader(f"Performance Comparison: {ticker1} vs {ticker2}")

        # Display stock prices chart        # Scoreboard
        scores = (performance1 > performance2).astype(int).sum(), (performance2 > performance1).astype(int).sum()
        st.write(f"### Scoreboard: {ticker1} {scores[0]} - {ticker2} {scores[1]}")

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
                return f'background-color: {stock1_color}; color: white' if val == ticker1 else f'background-color: {stock2_color}; color: white'
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

        st.write("### Yearly Comparison Grid by percentage each year")
        st.write(styled_df)
        display_stock_prices_chart(data1, data2, ticker1, ticker2)

        # Plotting yearly performance
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(performance1.index.year, performance1.values, label=ticker1, color=stock1_color, marker='o')
        ax.plot(performance2.index.year, performance2.values, label=ticker2, color=stock2_color, marker='o')
        ax.set_title('Yearly Performance Comparison')
        ax.set_xlabel('Year')
        ax.set_ylabel('Yearly Return (%)')
        ax.legend()
        st.pyplot(fig)


    except Exception as e:
        st.error(f"Error displaying results: {e}")


def display_general_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        st.subheader(f"General Information for {ticker}")
        st.write(f"**Company Name:** {info.get('longName', 'N/A')}")
        st.write(f"**Sector:** {info.get('sector', 'N/A')}")
        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
        st.write(f"**Market Cap:** ${info.get('marketCap', 'N/A'):,}")
        st.write(f"**P/E Ratio:** {info.get('forwardPE', 'N/A')}")
        st.write(f"**Dividend Yield:** {info.get('dividendYield', 'N/A') * 100:.2f}%")
        st.write(f"**52-Week High:** ${info.get('fiftyTwoWeekHigh', 'N/A')}")
        st.write(f"**52-Week Low:** ${info.get('fiftyTwoWeekLow', 'N/A')}")
    except Exception as e:
        st.error(f"Error displaying general information for {ticker}: {e}")


def display_news(ticker):
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        st.subheader(f"Recent News for {ticker}")
        for article in news[:5]:
            st.write(f"**{article['title']}**")
            st.write(f"[Read more]({article['link']})")
    except Exception as e:
        st.error(f"Error displaying news for {ticker}: {e}")


def main():
    ticker1 = st.sidebar.text_input("Enter the first ticker", "AAPL",
                                    help="Input the ticker symbol of the first stock/ETF.")
    ticker2 = st.sidebar.text_input("Enter the second ticker", "MSFT",
                                    help="Input the ticker symbol of the second stock/ETF.")
    start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2014-01-01"),
                                       help="Choose the starting date for comparison.")

    st.sidebar.write("### Comparison Options")
    compare = st.sidebar.button("Compare Tickers")

    if not compare:
        st.title("Stock Performance Comparison")
        st.write("Compare the performance of two stock tickers over the last 10 years.")

    if compare:
        st.header(f"Comparing {ticker1} vs {ticker2}")
        # st.write("---")

        data1 = get_stock_data(ticker1, start_date)
        data2 = get_stock_data(ticker2, start_date)

        if not data1.empty and not data2.empty:
            performance1 = calculate_yearly_performance(data1)
            performance2 = calculate_yearly_performance(data2)

            display_results(ticker1, ticker2, performance1, performance2, data1, data2)

            st.write("---")
            display_general_info(ticker1)
            st.write("---")
            display_general_info(ticker2)
            st.write("---")
            display_news(ticker1)
            st.write("---")
            display_news(ticker2)


if __name__ == "__main__":
    main()
