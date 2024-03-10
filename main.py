import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import time
from pybit.unified_trading import HTTP

def fetch_and_analyze_crypto_price(symbol, hours_ago=48, resolution='15', window_size=8):
    """
    Fetches cryptocurrency price data, converts it to a DataFrame, and calculates the rolling standard deviation of returns.

    Parameters:
    - symbol (str): The symbol for the cryptocurrency (e.g., 'BTCUSDT').
    - hours_ago (int): How many hours ago to fetch data for.
    - resolution (str): The resolution of the kline data.
    - window_size (int): The window size for calculating rolling standard deviation.

    Returns:
    - DataFrame: A DataFrame with the original kline data.
    """
    try:
        session = HTTP(testnet=False)
        current_time_ms = int(time.time() * 1000)
        start_time_ms = current_time_ms - (hours_ago * 3600 * 1000)

        response = session.get_kline(
            category='spot',
            symbol=symbol,
            interval=resolution,
            start=start_time_ms,
            end=current_time_ms
        )
        if 'result' in response and 'list' in response['result']:
            kline_data = response['result']['list']
            df = pd.DataFrame(kline_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Quote Asset Volume'])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
            df = df.iloc[::-1]
            df.set_index('Timestamp', inplace=True)
            df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
            df['Returns'] = df['Close'].pct_change()
            df['Rolling_Std_4h'] = df['Returns'].rolling(window=window_size).std()
        else:
            raise ValueError("No data returned from API.")
    except Exception as e:
        raise ValueError(f"Error fetching data for {symbol}: {e}")


    return df
def main():
    st.title('Rolling Standard Deviation of Top 20 Cryptocurrencies')
    top_20_cryptos = ['ETHUSDT', 'MNTUSDT', 'SOLUSDT', 'GALAUSDT', 'XRPUSDT', 'APEXUSDT', 'DOGEUSDT', 'PEPEUSDT', 'WLDUSDT', 'FLOKIUSDT', 'MATICUSDT', 'AGIUSDT', 'BNBUSDT', 'AGIXUSDT', 'FETUSDT', 'NEARUSDT', 'BONKUSDT', 'PYTHUSDT', 'MAVIAUSDT']
    
    if 'cryptos' not in st.session_state:
        st.session_state.cryptos = top_20_cryptos

    new_crypto = st.text_input('Type a new cryptocurrency symbol to add (e.g., BTCUSDT):')

    if st.button('Add Cryptocurrency'):
        if new_crypto and new_crypto not in st.session_state.cryptos:
            st.session_state.cryptos.append(new_crypto)
            st.success(f'Added {new_crypto} to the list!')

    included_cryptos = st.multiselect("Choose cryptocurrencies to include:", st.session_state.cryptos, st.session_state.cryptos)

    if st.button('Reload Data'):
        fetch_data_and_plot(included_cryptos)



def fetch_data_and_plot(symbols):
    result = {}
    dfs = {}
    for symbol in symbols:
        try:
            df = fetch_and_analyze_crypto_price(symbol)
            last_rolling_std = df['Rolling_Std_4h'].iloc[-1]
            if not pd.isna(last_rolling_std):
                result[symbol] = last_rolling_std
                dfs[symbol] = df
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {e}")
    
    if result:
        plot_data(result)
        plot_rolling_std_vs_time(dfs)
    else:
        st.error("No data available to display.")

def plot_data(data):
    df_plot = pd.DataFrame(list(data.items()), columns=['Symbol', 'Rolling_Std_4h'])
    df_plot.sort_values(by='Rolling_Std_4h', ascending=False, inplace=True)
    max_std = df_plot['Rolling_Std_4h'].max()
    min_std = df_plot['Rolling_Std_4h'].min()
    df_plot['Color'] = (df_plot['Rolling_Std_4h'] - min_std) / (max_std - min_std)

    fig = px.bar(df_plot, x='Symbol', y='Rolling_Std_4h', color='Color',
                 color_continuous_scale=['green', 'yellow', 'red'],
                 labels={'Rolling_Std_4h': 'Last 4H Rolling Std Dev'},
                 title='Rolling Standard Deviation of Returns (Last 4H)')
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

def plot_rolling_std_vs_time(dfs):
    for symbol, df in dfs.items():
        fig = px.line(df.reset_index(), x='Timestamp', y='Rolling_Std_4h', title=f'Rolling Std Dev Over Time for {symbol}')
        fig.update_layout(xaxis_title='Time', yaxis_title='Rolling Std Dev (4H)')
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
