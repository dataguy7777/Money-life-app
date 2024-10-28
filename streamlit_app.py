import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go  # Updated for Plotly
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    filename='investment_simulator.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Set page configuration
st.set_page_config(
    page_title="Investment Wealth Simulator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title of the App
st.title("📈 Investment Wealth Simulator")

# Sidebar for user inputs
st.sidebar.header("Simulation Parameters")

# Function to get default portfolio allocations
def get_default_portfolio(region):
    if region == 'US':
        return {'Equities': 70, 'Bonds': 30}
    elif region == 'Europe':
        return {'Equities': 60, 'Bonds': 40}
    else:
        return {'Equities': 50, 'Bonds': 50}

# User selects region for default values
region = st.sidebar.selectbox("Select Region for Default Values", options=['US', 'Europe'])

# Default returns based on region
default_portfolio = get_default_portfolio(region)
default_equity_return = 7.0 if region == 'US' else 6.0  # Example default returns
default_bond_return = 3.0 if region == 'US' else 2.5
default_inflation = 2.0

# **Updated Input Fields with New Default Values**

# Monthly Savings Input
monthly_savings = st.sidebar.number_input(
    "Monthly Savings (€)", min_value=0, value=2000, step=100  # Changed default from 500 to 2000
)

# Starting Wealth Input
starting_wealth = st.sidebar.number_input(
    "Starting Wealth (€)", min_value=0.0, value=500000.0, step=1000.0  # Changed default from 10,000 to 500,000
)

equity_percent = st.sidebar.slider(
    "Equities Allocation (%)",
    min_value=0,
    max_value=100,
    value=default_portfolio['Equities'],
    step=1
)

bond_percent = 100 - equity_percent

annual_equity_return = st.sidebar.number_input(
    "Annual Return on Equities (%)", min_value=0.0, value=default_equity_return, step=0.1
)

annual_bond_return = st.sidebar.number_input(
    "Annual Return on Bonds (%)", min_value=0.0, value=default_bond_return, step=0.1
)

annual_inflation = st.sidebar.number_input(
    "Annual Inflation Rate (%)", min_value=0.0, value=default_inflation, step=0.1
)

simulation_years = st.sidebar.number_input(
    "Simulation Duration (Years)", min_value=1, max_value=50, value=25, step=1
)

# Calculate end date
start_date = datetime.today()
end_date = start_date + timedelta(days=simulation_years * 365)
st.sidebar.write(f"**Simulation Period:** {start_date.date()} to {end_date.date()}")

# Event management
st.sidebar.header("Manage Significant Expenses")

# Initialize session state for events
if 'events' not in st.session_state:
    st.session_state['events'] = []

# Function to add a new event
def add_event(name, amount, date):
    event = {'Name': name, 'Amount': amount, 'Date': date}
    st.session_state['events'].append(event)
    logging.info(f"Added event: {event}")

# Function to remove an event
def remove_event(index):
    event = st.session_state['events'].pop(index)
    logging.info(f"Removed event: {event}")

with st.sidebar.expander("Add New Expense"):
    event_name = st.text_input("Expense Name", value="House Purchase")
    event_amount = st.number_input("Expense Amount (€)", min_value=0.0, value=300000.0, step=1000.0)
    event_date = st.date_input("Expense Date", value=(start_date + timedelta(days=365*5)).date())
    if st.button("Add Expense"):
        if event_date < start_date.date():
            st.sidebar.error("Expense date cannot be in the past.")
        else:
            add_event(event_name, event_amount, event_date)
            st.sidebar.success(f"Added expense: {event_name} on {event_date}")
            logging.info(f"User added expense: {event_name}, Amount: {event_amount}, Date: {event_date}")

# Display current events
if st.session_state['events']:
    st.sidebar.subheader("Current Expenses")
    for idx, event in enumerate(st.session_state['events']):
        col1, col2, col3, col4 = st.sidebar.columns([3, 2, 2, 1])
        col1.write(event['Name'])
        col2.write(f"€{event['Amount']:,.2f}")
        col3.write(event['Date'].strftime("%Y-%m-%d"))
        if col4.button("Remove", key=idx):
            remove_event(idx)
            st.sidebar.success(f"Removed expense: {event['Name']}")
else:
    st.sidebar.write("No significant expenses added.")

# Function to simulate wealth over time
@st.cache_data
def simulate_wealth(
    starting_wealth,
    monthly_saving,
    equity_pct,
    bond_pct,
    equity_return,
    bond_return,
    inflation,
    start_date,
    end_date,
    events
):
    logging.info("Starting wealth simulation.")
    
    # Convert annual returns to monthly
    monthly_equity_return = (1 + equity_return / 100) ** (1/12) - 1
    monthly_bond_return = (1 + bond_return / 100) ** (1/12) - 1
    monthly_inflation = (1 + inflation / 100) ** (1/12) - 1
    
    # Create a date range
    dates = pd.date_range(start=start_date, end=end_date, freq='M')
    wealth = []
    total_wealth = starting_wealth  # Initialize with starting wealth
    
    # Sort events by date
    sorted_events = sorted(events, key=lambda x: x['Date'])
    
    event_idx = 0  # Pointer to events
    
    for current_date in dates:
        # Apply monthly savings
        total_wealth += monthly_saving
        logging.debug(f"{current_date.date()}: Added monthly savings. Total wealth: {total_wealth:.2f}")
        
        # Apply investment returns
        total_equity = total_wealth * (equity_pct / 100)
        total_bond = total_wealth * (bond_pct / 100)
        equity_growth = total_equity * monthly_equity_return
        bond_growth = total_bond * monthly_bond_return
        total_wealth += equity_growth + bond_growth
        logging.debug(f"{current_date.date()}: Applied returns. Equity growth: {equity_growth:.2f}, Bond growth: {bond_growth:.2f}, Total wealth: {total_wealth:.2f}")
        
        # Subtract expenses if any
        while (event_idx < len(sorted_events)) and (sorted_events[event_idx]['Date'] <= current_date.date()):
            expense = sorted_events[event_idx]
            total_wealth -= expense['Amount']
            logging.info(f"{current_date.date()}: Subtracted expense {expense['Name']} of €{expense['Amount']:.2f}. Total wealth: {total_wealth:.2f}")
            event_idx += 1
        
        # Adjust for inflation
        total_wealth /= (1 + monthly_inflation)
        logging.debug(f"{current_date.date()}: Adjusted for inflation. Total wealth: {total_wealth:.2f}")
        
        wealth.append(total_wealth)
    
    df = pd.DataFrame({
        'Date': dates,
        'Wealth (€)': wealth
    })
    
    logging.info("Wealth simulation completed.")
    return df

# Run simulation
df_wealth = simulate_wealth(
    starting_wealth=starting_wealth,  # Pass starting wealth
    monthly_saving=monthly_savings,
    equity_pct=equity_percent,
    bond_pct=bond_percent,
    equity_return=annual_equity_return,
    bond_return=annual_bond_return,
    inflation=annual_inflation,
    start_date=start_date,
    end_date=end_date,
    events=st.session_state['events']
)

# Display simulation results
st.subheader("Wealth Over Time")

# **Updated Visualization with Plotly**
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df_wealth['Date'],
        y=df_wealth['Wealth (€)'],
        mode='lines',
        name='Total Wealth',
        line=dict(color='blue')
    )
)

fig.update_layout(
    title="Wealth Accumulation Over Time",
    xaxis_title="Date",
    yaxis_title="Wealth (€)",
    template='plotly_white',
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

# Display final wealth
final_wealth = df_wealth['Wealth (€)'].iloc[-1]
st.write(f"**Final Wealth after {simulation_years} years:** €{final_wealth:,.2f}")

# Display data in a table
with st.expander("View Detailed Wealth Data"):
    st.dataframe(df_wealth.style.format({"Wealth (€)": "{:,.2f}"}))

# Logging user completion
logging.info("User completed simulation.")