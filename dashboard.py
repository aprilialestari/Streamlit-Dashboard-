import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

sns.set(style='dark')

# Data Preparation
def load_data():
    day_df = pd.read_csv("dashboard/day.csv")
    hour_df = pd.read_csv("dashboard/hour.csv")

    # Convert datetime
    day_df['dteday'] = pd.to_datetime(day_df['dteday'])
    hour_df['dteday'] = pd.to_datetime(hour_df['dteday'])
    return day_df, hour_df

    def create_daily_rentals_df(df):
        daily_df = df.resample('D', on='dteday').agg({
            'cnt': 'sum',
            'casual': 'sum',
            'registered': 'sum'
        }).reset_index()
        return daily_df

def create_weather_analysis_df(df):
    weather_df = df.groupby('weathersit').agg({
        'cnt': ['mean', 'min', 'max'],
        'casual': 'mean',
        'registered': 'mean'
    }).reset_index()
    weather_df.columns = ['weathersit', 'avg_cnt', 'min_cnt', 'max_cnt', 'casual', 'registered']
    return weather_df

    # Data Validation
def validate_data(df):
    # Validasi konsistensi holiday-workingday
    inconsistency = df[(df['holiday'] == 1) & (df['workingday'] == 1)]
    if not inconsistency.empty:
        st.warning(f"Terdapat {len(inconsistency)} data tidak konsisten (hari libur tapi tercatat sebagai workingday)")

# Load data
day_df, hour_df = load_data()
validate_data(day_df)

# Streamlit Dashboard
st.title("Bike Sharing Dashboard")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2972/2972185.png", width=100)
    
    min_date = day_df['dteday'].min()
    max_date = day_df['dteday'].max()

    start_date, end_date = st.date_input(
    label='Rentang Tanggal',
    min_value=min_date,
    max_value=max_date,
    value=[min_date, max_date]
    )
    
    selected_weather = st.multiselect(
        'Kondisi Cuaca',
        options=sorted(day_df['weathersit'].unique()),
        default=sorted(day_df['weathersit'].unique()),
        format_func=lambda x: {1: 'Cerah', 2: 'Berawan', 3: 'Hujan/Salju'}.get(x, 'Unknown')
    )

    # Filter data
filtered_day_df = day_df[
    (day_df['dteday'] >= pd.to_datetime(start_date)) &
    (day_df['dteday'] <= pd.to_datetime(end_date)) &
    (day_df['weathersit'].isin(selected_weather))
]

# Main Dashboard
st.title('Analisis Bike Sharing 🚴')

# Key Metrics
col1, col2, col3 = st.columns(3)
with col1:
    total_rentals = filtered_day_df['cnt'].sum()
    st.metric("Total Penyewaan", value=f"{total_rentals:,}")

with col2:
    workingday_rain = filtered_day_df[(filtered_day_df['workingday'] == 1) & (filtered_day_df['weathersit'] == 3)]['cnt'].mean()
    st.metric("Rata-rata Sewa Hari Kerja Hujan", value=f"{workingday_rain:,.0f}")

with col3:
    holiday_diff = day_df[day_df['holiday'] == 1]['cnt'].mean() - day_df[day_df['holiday'] == 0]['cnt'].mean()
    st.metric("Selisih Sewa Hari Libur vs Biasa", value=f"{holiday_diff:,.0f}")

   # Visualization Section
# Tren Harian
st.subheader("Tren Harian Penyewaan Sepeda")
daily_rentals_df = filtered_day_df[['dteday', 'cnt']].set_index('dteday').resample('D').sum().reset_index()
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(daily_rentals_df['dteday'], daily_rentals_df['cnt'], color='#1f77b4')
ax.set_xlabel("Tanggal")
ax.set_ylabel("Jumlah Penyewaan")
ax.grid(True)
st.pyplot(fig) 



# Analisis Cuaca
st.subheader("Dampak Kondisi Cuaca pada Penyewaan")
weather_df = create_weather_analysis_df(filtered_day_df)
fig, ax = plt.subplots()
sns.barplot(
    x='weathersit', 
    y='avg_cnt', 
    data=weather_df,
    palette='Blues',
    order=sorted(day_df['weathersit'].unique()))
ax.set_xticklabels(['Cerah', 'Berawan', 'Hujan/Salju'])
ax.set_xlabel("Kondisi Cuaca")
ax.set_ylabel("Rata-rata Penyewaan")
st.pyplot(fig)



# Analisis Outlier
st.subheader("Distribusi Kelembaban dan Kecepatan Angin")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

sns.boxplot(y=day_df['hum'], ax=axes[0], color='lightblue')
axes[0].set_title('Kelembaban (hum)')
axes[0].set_ylabel('Persentase Kelembaban')

sns.boxplot(y=day_df['windspeed'], ax=axes[1], color='salmon')
axes[1].set_title('Kecepatan Angin (windspeed)')
axes[1].set_ylabel('Kecepatan Angin')
st.pyplot(fig)


# Analisis Hari Libur
st.subheader("Perbandingan Sewa Hari Libur vs Biasa")
holiday_df = day_df.groupby('holiday').agg({'cnt': 'mean'}).reset_index()
fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(
    x='holiday',
    y='cnt',
    data=holiday_df,
    palette=['#1f77b4', '#ff7f0e'])
ax.set_xticklabels(['Hari Biasa', 'Hari Libur'])
ax.set_xlabel("Tanggal Libur")
ax.set_ylabel("Rata-rata Penyewaan")
st.pyplot(fig)

# Data Validation
st.header("Validasi Data")
cols = st.columns(3)

with cols[0]:
    st.write("#### Cek Data")
    st.metric("Total Hari Libur", day_df['holiday'].sum())
    st.metric("Missing Values (Day)", day_df.isnull().sum().sum())

with cols[1]:
    st.write("#### Konsistensi")
    st.metric("Kategori Cuaca Unik", len(day_df['weathersit'].unique()))
    st.metric("Missing Values (Hour)", hour_df.isnull().sum().sum())

with cols[2]:
    st.write("#### Statistik Deskriptif")
    st.write(f"Total Hari Kerja: {day_df['workingday'].sum()}")
    st.write(f"Rentang Temperatur: {day_df['temp'].min():.2f} - {day_df['temp'].max():.2f}")

st.caption('Analisis oleh: Aprilia Lestari')