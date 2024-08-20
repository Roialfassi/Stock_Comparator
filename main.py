import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objs as go

# Set page configuration
st.set_page_config(
    page_title="Stock Performance Comparison",
    page_icon="📈",
    # layout="wide",  # This makes the view wider
    initial_sidebar_state="expanded"
)

# Constants for colors
STOCK1_COLOR = "blue"
STOCK2_COLOR = "#ffae21"
DEFAULT_INVESTMENT = 100


# Exception handling function
def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # st.error(f"An error occurred: {e}")
            return None

    return wrapper


@handle_exceptions
def get_stock_data(ticker, start_date):
    stock = yf.Ticker(ticker)
    data = stock.history(start=start_date)
    data['Year'] = data.index.year
    return data


@handle_exceptions
def calculate_yearly_performance(data):
    yearly_returns = data['Close'].resample('Y').ffill().pct_change().dropna() * 100
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
    start_price = min(data1['Close'][0], data2['Close'][0])
    data1['Normalized_Price'] = data1['Close'] / data1['Close'][0] * start_price
    data2['Normalized_Price'] = data2['Close'] / data2['Close'][0] * start_price

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
@handle_exceptions
def calculate_investment_growth(data, initial_investment=DEFAULT_INVESTMENT):
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

        st.write("### Yearly Comparison Grid by percentage each year")
        st.write(styled_df)
        display_stock_prices_chart_normalized(data1, data2, ticker1, ticker2)
        display_stock_prices_chart(data1, data2, ticker1, ticker2)

        # Calculate and display investment growth
        investment1 = calculate_investment_growth(data1)
        investment2 = calculate_investment_growth(data2)
        st.write("---")
        st.markdown(
            f"If you invested **100** dollars in **{ticker1}** at **{start_date}** , you would have **{investment1:.2f}** dollars today.")
        st.markdown(
            f"If you invested **100** dollars in **{ticker2}** at **{start_date}** , you would have  **{investment2:.2f}** dollars today.")
        st.write("---")

        # Plotting yearly performance
        # fig, ax = plt.subplots(figsize=(10, 5))
        # ax.plot(performance1.index.year, performance1.values, label=ticker1, color=STOCK1_COLOR, marker='o')
        # ax.plot(performance2.index.year, performance2.values, label=ticker2, color=STOCK2_COLOR, marker='o')
        # ax.set_title('Yearly Performance Comparison')
        # ax.set_xlabel('Year')
        # ax.set_ylabel('Yearly Return (%)')
        # ax.legend()
        # st.pyplot(fig)
        display_yearly_performance_comparison(performance1, performance2, ticker1, ticker2)



    except Exception as e:
        st.error(f"Error displaying results: {e}")


@handle_exceptions
def display_general_info(ticker):
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


@handle_exceptions
def display_news(ticker):
    stock = yf.Ticker(ticker)
    news = stock.news
    st.subheader(f"Recent News for {ticker}")
    for article in news[:5]:
        st.write(f"**{article['title']}**")
        st.write(f"[Read more]({article['link']})")


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

            display_results(ticker1, ticker2, performance1, performance2, data1, data2, start_date)

            st.write("---")
            display_general_info(ticker1)
            st.write("---")
            display_general_info(ticker2)
            st.write("---")
            display_news(ticker1)
            st.write("---")
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
