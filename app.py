import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
import locale

# Set Vietnamese locale
try:
    locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'vi_VN')
    except:
        pass

# Đường dẫn file CSV
CSV_PATH = r"D:\python project\Trực quan hóa dữ liệu dự đoán\predictions_hanoi_10d_from_30_4.csv"

# Đọc dữ liệu mẫu để lấy các trường và giá trị
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH)
    df['time'] = pd.to_datetime(df['time'])
    df['date'] = df['time'].dt.date
    df['hour'] = df['time'].dt.hour
    df['month'] = df['time'].dt.month
    df['year'] = df['time'].dt.year
    df['day_name'] = df['time'].dt.strftime('%A')  # Tên ngày trong tuần
    df['month_name'] = df['time'].dt.strftime('%B')  # Tên tháng
    df['t2m'] = (df['t2m'] - 273)  # Đổi nhiệt độ K -> C
    return df

df = load_data()

st.markdown('<h1 style="color:white;background-color:#b22234;padding:10px 0 10px 20px;border-radius:5px;">Trực quan hoá dữ liệu</h1>', unsafe_allow_html=True)
st.markdown('<hr style="border:2px solid #daa520;">', unsafe_allow_html=True)

# Chọn khoảng thời gian
time_period = st.selectbox('Chọn khoảng thời gian', ['Ngày', 'Tháng', 'Năm'])

if time_period == 'Ngày':
    dates = sorted(df['date'].unique())
    date_format = lambda x: x.strftime('%d/%m/%Y')  # Format: DD/MM/YYYY
    selected_date = st.selectbox('Chọn ngày', dates, format_func=date_format)
    filtered_df = df[df['date'] == selected_date]
    st.write(f"Ngày đã chọn: {selected_date.strftime('%d/%m/%Y')} ({df[df['date'] == selected_date]['day_name'].iloc[0]})")
elif time_period == 'Tháng':
    years = sorted(df['year'].unique())
    selected_year = st.selectbox('Chọn năm', years)
    months = sorted(df[df['year'] == selected_year]['month'].unique())
    month_names = [datetime(selected_year, m, 1).strftime('%B') for m in months]
    selected_month = st.selectbox('Chọn tháng', months, format_func=lambda x: datetime(selected_year, x, 1).strftime('%B'))
    filtered_df = df[(df['year'] == selected_year) & (df['month'] == selected_month)]
    st.write(f"Tháng đã chọn: {datetime(selected_year, selected_month, 1).strftime('%B/%Y')}")
else:  # Năm
    years = sorted(df['year'].unique())
    selected_year = st.selectbox('Chọn năm', years)
    filtered_df = df[df['year'] == selected_year]
    st.write(f"Năm đã chọn: {selected_year}")

# Chọn vĩ độ và kinh độ
latitude_min, latitude_max = float(df['latitude'].min()), float(df['latitude'].max())
longitude_min, longitude_max = float(df['longitude'].min()), float(df['longitude'].max())

selected_latitude = st.slider('Chọn vĩ độ (latitude)', min_value=latitude_min, max_value=latitude_max, value=float(filtered_df['latitude'].iloc[0]), step=0.25, format="%.2f")
selected_longitude = st.slider('Chọn kinh độ (longitude)', min_value=longitude_min, max_value=longitude_max, value=float(filtered_df['longitude'].iloc[0]), step=0.25, format="%.2f")

# Chọn trường dữ liệu để vẽ
data_fields = [
    'u10', 'v10', 'd2m', 't2m', 'msl', 'meanSea', 'sst', 'sp'
]
selected_field = st.selectbox('Chọn trường dữ liệu', data_fields)

# Lọc dữ liệu theo vị trí đã chọn
df_point = filtered_df[(filtered_df['latitude'] == selected_latitude) & (filtered_df['longitude'] == selected_longitude)]

# Vẽ biểu đồ đường
def plot_line_chart(df, field):
    fig, ax = plt.subplots(figsize=(12, 5))
    if time_period == 'Ngày':
        x_data = df['hour']
        x_label = 'Giờ trong ngày'
    else:
        x_data = df['date']
        x_label = 'Ngày'
    ax.plot(x_data, df[field], marker='o', color='b')
    ax.set_xlabel(x_label)
    ax.set_ylabel(field)
    ax.set_title(f'{field} Trend')
    ax.grid(True)
    plt.xticks(rotation=45)
    return fig

if not df_point.empty:
    st.pyplot(plot_line_chart(df_point, selected_field))
else:
    st.warning('Không có dữ liệu cho vị trí này trong khoảng thời gian đã chọn.')

# Tính toán thống kê theo khoảng thời gian
if time_period == 'Ngày':
    stats_df = df_point.copy()
    x_col = 'hour'
    x_label = 'Giờ'
elif time_period == 'Tháng':
    stats_df = filtered_df.groupby('date').agg({
        't2m': ['max', 'min'],
        'd2m': ['max', 'min'],
        'msl': 'mean',
        'meanSea': 'mean',
        'sst': 'mean',
        'sp': 'mean',
        'total_precipitation_6hr': 'sum'
    }).reset_index()
    stats_df.columns = ['Date', 'MaxTemp', 'MinTemp', 'MaxDew', 'MinDew', 'MeanMSL', 'MeanMeanSea', 'MeanSST', 'MeanSP', 'TotalPrecip']
    stats_df['TempDiff'] = stats_df['MaxTemp'] - stats_df['MinTemp']
    x_col = 'Date'
    x_label = 'Ngày'
else:  # Năm
    stats_df = filtered_df.groupby('month').agg({
        't2m': ['max', 'min'],
        'd2m': ['max', 'min'],
        'msl': 'mean',
        'meanSea': 'mean',
        'sst': 'mean',
        'sp': 'mean',
        'total_precipitation_6hr': 'sum'
    }).reset_index()
    stats_df.columns = ['Month', 'MaxTemp', 'MinTemp', 'MaxDew', 'MinDew', 'MeanMSL', 'MeanMeanSea', 'MeanSST', 'MeanSP', 'TotalPrecip']
    stats_df['TempDiff'] = stats_df['MaxTemp'] - stats_df['MinTemp']
    x_col = 'Month'
    x_label = 'Tháng'

# Đặt lại tên cột cho dễ hiểu
if time_period != 'Ngày':
    stats_df = stats_df.rename(columns={
        't2m_max': 'MaxTemp',
        't2m_min': 'MinTemp',
        'd2m_max': 'MaxDew',
        'd2m_min': 'MinDew',
        'msl_mean': 'MeanMSL',
        'meanSea_mean': 'MeanMeanSea',
        'sst_mean': 'MeanSST',
        'sp_mean': 'MeanSP'
    })

# Biểu đồ nhiệt độ
def plot_temperature_chart(data):
    fig, ax = plt.subplots(figsize=(12, 5))
    x_data = data[x_col]
    if 'MaxTemp' in data.columns and 'MinTemp' in data.columns:
        ax.plot(x_data, data['MaxTemp'], marker='o', color='red', label='Nhiệt độ cao nhất')
        ax.plot(x_data, data['MinTemp'], marker='o', color='blue', label='Nhiệt độ thấp nhất')
    if 'TempDiff' in data.columns:
        ax.plot(x_data, data['TempDiff'], marker='o', color='green', label='Chênh lệch nhiệt độ')
    ax.set_xlabel(x_label)
    ax.set_ylabel('Nhiệt độ (°C)')
    ax.set_title('Phân tích nhiệt độ')
    ax.legend()
    ax.grid(True)
    plt.xticks(rotation=45)
    return fig

# Biểu đồ lượng mưa
def plot_precipitation_chart(data):
    fig, ax = plt.subplots(figsize=(12, 5))
    x_data = data[x_col] if 'x_col' in globals() else data['hour']
    if 'TotalPrecip' in data.columns:
        ax.bar(x_data, data['TotalPrecip'], color='blue', label='Tổng lượng mưa')
        ax.set_ylabel('Lượng mưa (mm)')
    else:
        ax.bar(x_data, [0]*len(x_data), color='blue', label='Không có dữ liệu lượng mưa')
        ax.set_ylabel('Lượng mưa (mm)')
    ax.set_xlabel(x_label)
    ax.set_title('Phân tích lượng mưa')
    ax.legend()
    ax.grid(True)
    plt.xticks(rotation=45)
    return fig

# Hiển thị biểu đồ
st.markdown("### Biểu đồ Nhiệt độ")
st.pyplot(plot_temperature_chart(stats_df))

st.markdown("### Biểu đồ Lượng mưa")
st.pyplot(plot_precipitation_chart(stats_df))

# Hiển thị thống k

