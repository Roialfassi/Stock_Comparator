# Stock Performance Comparison App

📈 **Stock Performance Comparison** is a Streamlit application that allows users to compare the historical performance of two stock tickers, including stocks, ETFs, or index funds. The app visualizes key metrics such as yearly returns, cumulative returns, and stock price history over the last 10 years (or since the latest existence of either stock). It also provides general information about the selected stocks, including market cap, sector, and more.

## Features

- **Yearly Performance Comparison**: Compare the yearly percentage returns of two stock tickers. The app highlights the better-performing stock each year and displays the results in a color-coded grid.
- **Cumulative Returns**: Visualize the cumulative returns of both tickers over the selected period.
- **Stock Price History**: View a line chart of the closing prices of both stocks over time.
- **General Information**: Access key details about each stock, such as market cap, sector, P/E ratio, and dividend yield.
- **Recent News**: Stay informed with the latest news related to the selected stock tickers.

## Installation

To run this app locally, you'll need to have Python installed. Follow these steps:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/roialfassi/stock-comparator.git
    cd stock-performance-comparison
    ```

2. **Install the required packages**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Streamlit app**:
    ```bash
    streamlit run main.py
    ```

## Usage

1. **Enter Stock Tickers**: Use the sidebar to input the ticker symbols of the two stocks you want to compare (e.g., `AAPL` for Apple and `MSFT` for Microsoft).
2. **Select Start Date**: Choose the starting date for the comparison.
3. **View Results**: Click the "Compare Tickers" button to view the comparison results, including:
   - Yearly performance
   - Cumulative returns
   - Stock price history
   - General information about each stock
   - Recent news

## Deployment

This app is deployed on Streamlit Community Cloud. You can access it directly via this link:

[https://your-username-streamlit-app.streamlit.app](https://your-username-streamlit-app.streamlit.app)

## Contributing

Contributions are welcome! If you have suggestions for new features or improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgements

- [Streamlit](https://streamlit.io/) - For providing an amazing platform to build and share data apps.
- [yFinance](https://pypi.org/project/yfinance/) - For making it easy to retrieve stock data.

## Contact

For any inquiries or feedback, feel free to reach out at [your-email@example.com](mailto:your-email@example.com).
