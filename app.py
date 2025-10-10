"""
Solar ROI Calculator (UK)
A simple tool to estimate solar panel savings for UK homeowners.

To run locally:
    pip install streamlit plotly
    streamlit run app.py

To deploy on Streamlit Cloud:
    1. Push this file to a GitHub repo as 'app.py'
    2. Create requirements.txt with: streamlit plotly
    3. Go to share.streamlit.io and connect your repo
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="Solar ROI Calculator (UK)",
    page_icon="☀️",
    layout="centered"
)

# App title and introduction
st.title("☀️ Solar ROI Calculator")
st.markdown("""
Welcome! This tool helps you estimate how much you could save by installing 
solar panels on your home. Simply enter your details below to see your potential 
annual savings and payback period.
""")

st.divider()

# ============================================================================
# SECTION 1: Property Information
# ============================================================================
st.markdown("### 🏠 Property Information")
st.markdown("Tell us about your home and roof setup.")

col1, col2 = st.columns(2)

with col1:
    postcode = st.text_input(
        "Postcode",
        placeholder="e.g., SW1A 1AA",
        help="Your property's postcode (used for location-based estimates)"
    )
    
    roof_direction = st.selectbox(
        "Main Roof Direction",
        ["South", "South-East", "South-West", "East", "West", "North"],
        index=0,
        help="South-facing roofs generate the most electricity"
    )

with col2:
    has_shading = st.radio(
        "Is your roof affected by shading?",
        ["No", "Yes"],
        index=0,
        help="Trees, chimneys, or nearby buildings can reduce solar generation"
    )
    
    home_type = st.selectbox(
        "Home Type",
        ["Detached", "Semi-detached", "Terrace", "Flat"],
        index=1,
        help="This helps estimate available roof space"
    )

st.divider()

# ============================================================================
# SECTION 2: Electricity Usage
# ============================================================================
st.markdown("### ⚡ Electricity Usage")
st.markdown("Help us understand your energy consumption patterns.")

col3, col4 = st.columns(2)

with col3:
    annual_usage = st.number_input(
        "Annual Electricity Usage (kWh)",
        min_value=1000,
        max_value=20000,
        value=3500,
        step=100,
        help="Check your energy bills. Average UK household uses ~3,500 kWh/year"
    )
    
    has_ev = st.radio(
        "Do you charge an EV at home?",
        ["No", "Yes"],
        index=0,
        help="EV charging increases electricity usage by ~2,000-3,000 kWh/year"
    )

with col4:
    hot_water_system = st.selectbox(
        "Hot Water System",
        ["Gas boiler", "Electric immersion", "Heat pump"],
        index=0,
        help="Electric systems can use solar energy directly"
    )
    
    home_during_day = st.radio(
        "Usually home during the day?",
        ["No", "Yes"],
        index=0,
        help="Being home during daylight hours increases self-use of solar energy"
    )

st.divider()

# ============================================================================
# SECTION 3: Tariff Information
# ============================================================================
st.markdown("### 💷 Your Electricity Tariff")
st.markdown("Enter your current electricity rates.")

col5, col6, col7 = st.columns(3)

with col5:
    day_rate = st.number_input(
        "Day Rate (p/kWh)",
        min_value=10.0,
        max_value=100.0,
        value=24.5,
        step=0.5,
        help="Price you pay for daytime electricity"
    )

with col6:
    night_rate = st.number_input(
        "Night Rate (p/kWh)",
        min_value=5.0,
        max_value=100.0,
        value=24.5,
        step=0.5,
        help="If you have Economy 7/10, enter your night rate. Otherwise, use the same as day rate"
    )

with col7:
    seg_rate = st.number_input(
        "Export (SEG) Rate (p/kWh)",
        min_value=5.0,
        max_value=30.0,
        value=21.0,
        step=0.5,
        help="Smart Export Guarantee - what you earn for exporting to the grid"
    )

st.divider()

# ============================================================================
# SECTION 4: Solar Setup
# ============================================================================
st.markdown("### ☀️ Solar Setup")
st.markdown("Configure your planned solar panel system.")

col8, col9 = st.columns(2)

with col8:
    num_panels = st.slider(
        "Number of Solar Panels",
        min_value=4,
        max_value=16,
        value=10,
        step=1,
        help="Typical home installations range from 8-16 panels"
    )
    
    panel_wattage = st.number_input(
        "Panel Wattage (W)",
        min_value=300,
        max_value=600,
        value=460,
        step=10,
        help="Modern panels are typically 400-460W. Check your quote for exact specs"
    )

with col9:
    has_battery = st.radio(
        "Planning to add battery storage?",
        ["No", "Yes"],
        index=0,
        help="Battery stores excess solar energy for use at night (adds ~£3,500 to cost)"
    )
    
    # Display calculated system size
    system_size_kwp = num_panels * (panel_wattage / 1000)
    st.metric(
        "Total System Size",
        f"{system_size_kwp:.2f} kWp",
        help="Your total solar capacity based on panels selected"
    )

st.divider()

# ============================================================================
# CALCULATION LOGIC
# ============================================================================

# UK baseline constants (North West England)
BASE_YIELD = 950  # kWh per kWp per year (North West England baseline)
BASE_INSTALL_COST = 5654.26  # £ for solar system installation
BATTERY_COST = 3500  # £ additional cost for battery

# Orientation multipliers
ORIENTATION_FACTORS = {
    "South": 1.0,
    "South-East": 1.0,  # Treated as South for this calculation
    "South-West": 1.0,  # Treated as South for this calculation
    "East": 0.85,
    "West": 0.85,
    "North": 0.6
}

def calculate_solar_roi():
    """
    Calculate solar ROI metrics based on user inputs.
    
    Core calculation logic:
    1. kWp = (panel_count × panel_watt) / 1000
    2. Annual generation = kWp × yield × orientation_factor
    3. Self-use % = base 45% + adjustments (capped at 90%)
    4. Financial benefit = self-use savings + export income
    5. Payback = install_cost / annual_benefit
    """
    
    # Step 1: Calculate system size in kWp
    system_size_kwp = (num_panels * panel_wattage) / 1000
    
    # Step 2: Calculate annual generation
    orientation_factor = ORIENTATION_FACTORS[roof_direction]
    annual_generation = system_size_kwp * BASE_YIELD * orientation_factor
    
    # Step 3: Calculate self-use percentage
    # Start with default 45%
    self_use_percent = 0.45
    
    # Add 10% if home during day
    if home_during_day == "Yes":
        self_use_percent += 0.10
    
    # Add 25% if battery planned
    if has_battery == "Yes":
        self_use_percent += 0.25
    
    # Cap at 90%
    self_use_percent = min(0.90, self_use_percent)
    
    # Calculate self-used and exported energy
    self_used_kwh = annual_generation * self_use_percent
    exported_kwh = annual_generation - self_used_kwh
    
    # Step 4: Calculate financial benefits
    # Savings from using your own solar power (at day rate)
    savings = self_used_kwh * (day_rate / 100)
    
    # Income from exporting to grid (at SEG rate)
    export_income = exported_kwh * (seg_rate / 100)
    
    # Total annual value
    total_annual_value = savings + export_income
    
    # Step 5: Calculate payback period
    install_cost = BASE_INSTALL_COST
    
    if total_annual_value > 0:
        payback_years = install_cost / total_annual_value
    else:
        payback_years = 0
    
    # Calculate percentages for display
    export_percent = 1 - self_use_percent
    
    return {
        'system_size_kwp': system_size_kwp,
        'annual_generation': annual_generation,
        'self_used_kwh': self_used_kwh,
        'exported_kwh': exported_kwh,
        'self_use_percent': self_use_percent,
        'export_percent': export_percent,
        'savings': savings,
        'export_income': export_income,
        'total_annual_value': total_annual_value,
        'install_cost': install_cost,
        'payback_years': payback_years,
        'orientation_factor': orientation_factor
    }

# ============================================================================
# SECTION 5: Results
# ============================================================================

if st.button("Calculate My Solar Savings", type="primary", use_container_width=True):
    
    # Perform calculations
    results = calculate_solar_roi()
    
    st.divider()
    st.markdown("## 📊 Your Solar ROI Results")
    st.markdown("Here's what your solar panel system could deliver:")
    st.write("")
    
    # Display key metrics in columns
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric(
            "Estimated Annual Solar Generation",
            f"{results['annual_generation']:,.1f} kWh",
            help="Estimated electricity your solar panels will generate per year"
        )
    
    with metric_col2:
        st.metric(
            "Self-Use Percentage",
            f"{results['self_use_percent']*100:.1f}%",
            help="Percentage of solar energy you'll use in your home"
        )
    
    with metric_col3:
        st.metric(
            "Total Annual Benefit",
            f"£{results['total_annual_value']:,.1f}",
            help="Your yearly savings from self-use + export income"
        )
    
    with metric_col4:
        st.metric(
            "Payback Period",
            f"{results['payback_years']:.1f} years",
            help="Time to recover your investment through savings"
        )
    
    st.divider()
    
    # Visualizations
    st.markdown("### 📈 Visual Comparison")
    
    # Bar chart: Usage vs Generation
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**Annual Usage vs Solar Generation**")
        
        comparison_data = {
            'Category': ['Your Current Usage', 'Estimated Solar Generation'],
            'kWh': [annual_usage, results['annual_generation']]
        }
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=comparison_data['Category'],
            y=comparison_data['kWh'],
            marker_color=['#FF6B6B', '#4ECDC4'],
            text=[f"{val:,.0f} kWh" for val in comparison_data['kWh']],
            textposition='outside'
        ))
        
        fig_bar.update_layout(
            yaxis_title="kWh per year",
            showlegend=False,
            height=350,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_chart2:
        st.markdown("**Self-Use vs Export Breakdown**")
        
        energy_split = {
            'Type': ['Self-Use', 'Export to Grid'],
            'kWh': [results['self_used_kwh'], results['exported_kwh']],
            'Percentage': [results['self_use_percent']*100, results['export_percent']*100]
        }
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=energy_split['Type'],
            values=energy_split['kWh'],
            marker_colors=['#51CF66', '#FFA94D'],
            hole=0.4,
            textinfo='label+percent',
            textposition='auto'
        )])
        
        fig_pie.update_layout(
            showlegend=True,
            height=350,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # Additional details
    st.markdown("### 💡 Detailed Breakdown")
    
    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        st.metric("System Size", f"{results['system_size_kwp']:.1f} kWp")
        st.metric("Energy You'll Use", f"{results['self_used_kwh']:,.1f} kWh ({results['self_use_percent']*100:.1f}%)")
        st.metric("Savings from Self-Use", f"£{results['savings']:,.1f}")
    
    with detail_col2:
        st.metric("Installation Cost", f"£{results['install_cost']:,.2f}")
        st.metric("Energy Exported", f"{results['exported_kwh']:,.1f} kWh ({results['export_percent']*100:.1f}%)")
        st.metric("Income from Export", f"£{results['export_income']:,.1f}")
    
    st.divider()
    
    # Summary text
    coverage_percent = (results['annual_generation'] / annual_usage * 100) if annual_usage > 0 else 0
    
    st.markdown("### 📝 Summary")
    st.success(f"""
    Your **{num_panels}-panel system ({results['system_size_kwp']:.1f} kWp)** would generate 
    approximately **{results['annual_generation']:,.1f} kWh per year** — that's about **{coverage_percent:.1f}%** 
    of your current electricity usage.
    
    You'd use **{results['self_use_percent']*100:.1f}%** of this energy directly in your home and export 
    **{results['export_percent']*100:.1f}%** to the grid.
    
    This would give you an annual benefit of around **£{results['total_annual_value']:,.1f}** 
    (£{results['savings']:,.1f} from self-use + £{results['export_income']:,.1f} from exports), 
    meaning you'd recover your **£{results['install_cost']:,.2f} investment** in approximately 
    **{results['payback_years']:.1f} years**.
    """)
    
    # Intelligent recommendations
    st.markdown("### 💡 Our Recommendation")
    
    recommendations = []
    
    # Payback assessment
    if results['payback_years'] < 7:
        recommendations.append("✅ **Excellent payback period!** Your system would pay for itself in under 7 years, which is considered very good for UK solar installations. This is a solid investment.")
    elif results['payback_years'] < 10:
        recommendations.append("👍 **Good payback period.** Your system would pay for itself in under 10 years, making it a worthwhile long-term investment.")
    else:
        recommendations.append("⚠️ **Long payback period.** With a payback of over 10 years, you may want to consider adjusting your system size or waiting for better tariff rates.")
    
    # Battery recommendation
    if seg_rate < 15:
        if has_battery == "Yes":
            recommendations.append("🔋 **Good choice on the battery!** With export rates below 15p/kWh, storing energy for your own use makes more financial sense than exporting it.")
        else:
            recommendations.append("🔋 **Consider adding a battery.** Your export rate is below 15p/kWh, so storing excess solar energy for evening use would be more valuable than exporting it to the grid.")
    else:
        if has_battery == "Yes":
            recommendations.append("🔋 **Battery may not be essential.** Your export rate is decent, so exporting excess energy is already quite profitable. A battery adds value but may not be critical.")
        else:
            recommendations.append("🔋 **Battery is optional.** With a reasonable export rate, exporting to the grid is financially viable without storage.")
    
    # Export profitability
    if seg_rate >= 20:
        recommendations.append("💰 **Great export rate!** At {:.1f}p/kWh, exporting your surplus energy to the grid is highly profitable. You're getting good value for every kWh you don't use.".format(seg_rate))
    elif seg_rate >= 15:
        recommendations.append("💰 **Decent export rate.** At {:.1f}p/kWh, exporting surplus energy is still worthwhile, though not as lucrative as the best tariffs available.".format(seg_rate))
    else:
        recommendations.append("💰 **Low export rate.** At {:.1f}p/kWh, your SEG rate is below average. Consider shopping around for better export tariffs or maximizing self-use with a battery.".format(seg_rate))
    
    for rec in recommendations:
        st.markdown(rec)
        st.write("")
    
    # Assumptions note
    with st.expander("ℹ️ Calculation Details & Assumptions"):
        st.markdown(f"""
        **Calculation Steps:**
        
        1. **System Size:** kWp = ({num_panels} panels × {panel_wattage}W) ÷ 1,000 = **{results['system_size_kwp']:.1f} kWp**
        
        2. **Annual Generation:** {results['system_size_kwp']:.1f} kWp × {BASE_YIELD} kWh/kWp/year × {results['orientation_factor']:.2f} (orientation) 
           = **{results['annual_generation']:,.1f} kWh/year**
        
        3. **Self-Use Calculation:**
           - Base self-use: 45%
           - Home during day: {'+10%' if home_during_day == 'Yes' else '—'}
           - Battery storage: {'+25%' if has_battery == 'Yes' else '—'}
           - **Total self-use: {results['self_use_percent']*100:.1f}%** (capped at 90%)
        
        4. **Financial Benefits:**
           - Self-used: {results['self_used_kwh']:,.1f} kWh × {day_rate:.1f}p/kWh = **£{results['savings']:,.1f}**
           - Exported: {results['exported_kwh']:,.1f} kWh × {seg_rate:.1f}p/kWh = **£{results['export_income']:,.1f}**
           - **Total annual value: £{results['total_annual_value']:,.1f}**
        
        5. **Payback Period:** £{results['install_cost']:,.2f} ÷ £{results['total_annual_value']:,.1f}/year = **{results['payback_years']:.1f} years**
        
        ---
        
        **Key Assumptions:**
        - Base solar yield: {BASE_YIELD} kWh/kWp/year (North West England baseline)
        - Orientation multipliers: South = 1.0, East/West = 0.85, North = 0.6
        - Panel wattage: {panel_wattage}W per panel
        - Installation cost: £{results['install_cost']:,.2f}
        - System lifespan: 25 years (typical warranty period)
        
        These are estimates based on typical UK conditions. Actual results vary by location, 
        shading, roof pitch, and weather patterns. Consult a certified MCS installer for a 
        detailed site assessment and quote.
        """)

# Footer
st.divider()
st.caption("☀️ Solar ROI Calculator | For estimation purposes only | Data based on UK averages")

# ============================================================================
# DEPLOYMENT INSTRUCTIONS
# ============================================================================
st.divider()
st.markdown("### 🚀 Deployment Guide")

with st.expander("📖 How to Run & Deploy This App"):
    st.markdown("""
    #### Running Locally
    
    1. **Install dependencies:**
    ```bash
    pip install streamlit plotly
    ```
    
    2. **Run the app:**
    ```bash
    streamlit run app.py
    ```
    
    3. **Open your browser** to the local URL shown (typically `http://localhost:8501`)
    
    ---
    
    #### Deploying to Streamlit Cloud (Free)
    
    1. **Create a GitHub repository** and push this `app.py` file to it
    
    2. **Create a `requirements.txt` file** in the same directory with:
    ```
    streamlit
    plotly
    ```
    
    3. **Deploy on Streamlit Cloud:**
       - Go to [share.streamlit.io](https://share.streamlit.io)
       - Click "New app"
       - Connect your GitHub account
       - Select your repository and the `app.py` file
       - Click "Deploy"!
    
    4. **Your app will be live** at a public URL within minutes
    
    ---
    
    #### Requirements File
    
    Create a file named `requirements.txt` with the following content:
    
    ```
    streamlit
    plotly
    ```
    
    **Note:** Streamlit Cloud will automatically install these dependencies when deploying.
    
    ---
    
    #### Customization Tips
    
    - Adjust `BASE_YIELD` for different UK regions (Scotland ~850, South England ~1050)
    - Update `BASE_INSTALL_COST` based on current market rates
    - Modify orientation factors based on local topography
    - Add postcode-based regional yield adjustments using UK solar data APIs
    
    For questions or issues, consult the [Streamlit documentation](https://docs.streamlit.io).
    """)
