```python
import streamlit as st
import pandas as pd
import math
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpInteger, value

st.set_page_config(page_title="Transport Route Optimizer", page_icon="🚛")
st.title("🚛 Transport Route Optimizer (Linear Programming)")

# Upload Excel file
uploaded_file = st.file_uploader("Upload your transport route Excel file", type=["xlsx"])

if uploaded_file:
    # Read routes data
    data = pd.read_excel(uploaded_file, sheet_name="Routes")
    st.success("✅ File loaded successfully!")
    st.dataframe(data)

    # User inputs
    fleet_size = st.number_input(
        "Enter available company fleet size (number of trucks)",
        min_value=1, value=10, step=1)
    work_days = st.number_input(
        "Enter number of working days per month", 
        min_value=1, max_value=31, value=26, step=1)

    # Build Linear Programming model
    model = LpProblem("Transport_Cost_Minimization", LpMinimize)

    # Decision variables: number of trucks, company trips, 3PL trips per route
    company_vars = {}
    pl3_vars = {}
    trucks_vars = {}
    
    for _, row in data.iterrows():
        route_key = (row['From'], row['To'])
        trucks_vars[route_key] = LpVariable(
            f"Trucks_{row['From']}_{row['To']}",
            lowBound=0, upBound=fleet_size, cat=LpInteger
        )
        company_vars[route_key] = LpVariable(
            f"CompanyTrips_{row['From']}_{row['To']}",
            lowBound=0, cat=LpInteger
        )
        pl3_vars[route_key] = LpVariable(
            f"PL3Trips_{row['From']}_{row['To']}",
            lowBound=0, cat=LpInteger
        )

    # Objective: minimize total cost (company + 3PL)
    model += lpSum(
        company_vars[(row['From'], row['To'])] * (row['Company_Cost'] + row['Return_Empty_Cost']) +
        pl3_vars[(row['From'], row['To'])] * float(row['3PL_Cost'])
        for _, row in data.iterrows()
    )

    # Constraint: total assigned trucks ≤ fleet size
    model += lpSum(trucks_vars[key] for key in trucks_vars) <= fleet_size, "Total_Truck_Limit"

    # Per-route constraints
    for _, row in data.iterrows():
        key = (row['From'], row['To'])
        demand = row['Monthly_Demand']
        duration = row['Trip_Duration_Days']
        max_trips_per_truck = math.floor(work_days / duration)

        # 1) Meet demand
        model += company_vars[key] + pl3_vars[key] >= demand, f"Demand_{row['From']}_{row['To']}"
        # 2) Cover high-demand routes (≥50% by company if demand >20)
        if demand > 20:
            model += company_vars[key] >= 0.5 * demand, f"HighDemand_{row['From']}_{row['To']}"
        # 3) Company trips limited by assigned trucks capacity
        model += company_vars[key] <= trucks_vars[key] * max_trips_per_truck, f"Capacity_{row['From']}_{row['To']}"

    # Solve model when user clicks
    if st.button("Run Optimization 🚀"):
        model.solve()

        # Collect and display results
        results = []
        for _, row in data.iterrows():
            key = (row['From'], row['To'])
            results.append({
                "From": row['From'],
                "To": row['To'],
                "Trucks_Assigned": int(trucks_vars[key].varValue),
                "Company_Trips": int(company_vars[key].varValue),
                "3PL_Trips": int(pl3_vars[key].varValue)
            })
        result_df = pd.DataFrame(results)

        st.subheader("📊 Optimization Results")
        st.dataframe(result_df)
        st.success(f"💰 Total Cost: SAR {value(model.objective):,.2f}")
else:
    st.info("📎 Please upload the Excel file 'Routes' sheet to begin.")
```
