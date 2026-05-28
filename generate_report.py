import pandas as pd
import yfinance as yf

from main import calculate_yearly_performance, calculate_investment_growth

DEFAULT_INVESTMENT = 100


def load_stock_list(csv_path):
    """
    Load the list of stocks from a CSV file.

    :param csv_path: str - The file path to the CSV containing 'Ticker' and 'Stock Name'.
    :return: pd.DataFrame - A DataFrame containing the stock list.
    """
    try:
        stock_list = pd.read_csv(csv_path)
        if 'Ticker' not in stock_list.columns or 'Stock Name' not in stock_list.columns:
            raise ValueError("CSV must contain 'Ticker' and 'Stock Name' columns.")
        return stock_list
    except Exception as e:
        print(f"Error loading stock list: {e}")
        return pd.DataFrame()


def get_stock_data(ticker, start_date):
    """
    Fetch historical stock data starting from the given start date.
    Adjust the start date to the first available date if necessary.

    :param ticker: str - The stock ticker symbol.
    :param start_date: datetime.date or datetime.datetime - The desired start date for fetching data.
    :return: Tuple (DataFrame, pd.Timestamp) - The stock data and the adjusted start date.
    """
    stock = yf.Ticker(ticker)

    try:
        # Convert start_date to pd.Timestamp and make it timezone-aware if necessary
        start_date = pd.Timestamp(start_date)

        # Fetch the data from the desired start date
        data = stock.history(start=start_date)

        # Ensure that both start_date and the data index have the same timezone awareness
        if data.index.tz is not None:
            start_date = start_date.tz_localize(data.index.tz)

        # Check if data is available and get the actual start date of the data
        if not data.empty:
            actual_start_date = data.index.min()
            adjusted_start_date = max(start_date, actual_start_date)
        else:
            print(f"No data available for {ticker} from the requested start date.")
            return pd.DataFrame(), start_date

        data['Year'] = data.index.year
        return data, adjusted_start_date

    except Exception as e:
        print(f"An error occurred while fetching data for {ticker}: {e}")
        return pd.DataFrame(), start_date


def compare_stock_to_spy(stock_ticker, spy_ticker, start_date, years_to_compare):
    """
    Compare the stock to SPY over the last X years.

    :param stock_ticker: str - The stock ticker symbol.
    :param spy_ticker: str - The SPY ticker symbol.
    :param start_date: datetime.date - The start date for fetching data.
    :param years_to_compare: int - The number of years to compare.
    :return: dict - A dictionary with comparison results.
    """
    try:
        # Get data for the stock and SPY
        stock_data, adjusted_start_date = get_stock_data(stock_ticker, start_date)
        spy_data, _ = get_stock_data(spy_ticker, start_date)

        # Ensure we have enough data for comparison
        if stock_data.empty or spy_data.empty:
            return {
                'ticker': stock_ticker,
                'years_outperformed': 0,
                'investment_value': 0,
                'outperformed_spy': False
            }

        # Calculate yearly performance
        stock_yearly_perf = calculate_yearly_performance(stock_data)
        spy_yearly_perf = calculate_yearly_performance(spy_data)

        # Focus on the last X years
        stock_yearly_perf = stock_yearly_perf.tail(years_to_compare)
        spy_yearly_perf = spy_yearly_perf.loc[stock_yearly_perf.index]

        # Count the number of years the stock outperformed SPY
        years_outperformed = (stock_yearly_perf > spy_yearly_perf).sum()

        # Calculate investment growth for both the stock and SPY
        stock_investment_value = calculate_investment_growth(stock_data)
        spy_investment_value = calculate_investment_growth(spy_data)

        # Determine if the stock outperformed SPY in terms of investment value
        outperformed_spy = stock_investment_value > spy_investment_value

        return {
            'ticker': stock_ticker,
            'years_outperformed': years_outperformed,
            'investment_value': stock_investment_value,
            'outperformed_spy': outperformed_spy
        }

    except Exception as e:
        print(f"An error occurred during comparison for {stock_ticker}: {e}")
        return {
            'ticker': stock_ticker,
            'years_outperformed': 0,
            'investment_value': 0,
            'outperformed_spy': False
        }


def analyze_stocks(csv_path, spy_ticker, start_date, years_to_compare):
    """
    Analyze all stocks in the CSV and compare them against SPY.

    :param csv_path: str - Path to the CSV file containing the stock list.
    :param spy_ticker: str - The ticker for SPY (S&P 500).
    :param start_date: datetime.date - The start date for fetching data.
    :param years_to_compare: int - The number of years to compare.
    :return: pd.DataFrame - A DataFrame containing the analysis results.
    """
    stock_list = load_stock_list(csv_path)
    results = []

    if stock_list.empty:
        print("No valid stock data to analyze.")
        return pd.DataFrame()

    for _, row in stock_list.iterrows():
        result = compare_stock_to_spy(row['Ticker'], spy_ticker, start_date, years_to_compare)
        results.append(result)

    return pd.DataFrame(results)


# Example usage
csv_path = 'cryptoETF.csv'
spy_ticker = 'SPY'
start_date = pd.to_datetime("2019-01-01").date()
years_to_compare = 10

analysis_results = analyze_stocks(csv_path, spy_ticker, start_date, years_to_compare)

if not analysis_results.empty:
    # print(analysis_results)
    analysis_results.to_csv("analysis_results.csv", index = False)
else:
    print("No results to display.")
