"""
Solar ROI Calculator (UK)
A simple tool to estimate solar panel savings for UK homeowners.

To run locally:
    pip install streamlit plotly pandas
    streamlit run app.py

To deploy on Streamlit Cloud:
    1. Push this file to a GitHub repo as 'app.py'
    2. Create requirements.txt with: streamlit plotly pandas
    3. Create data/region_yield.csv with regional yield data
    4. Create data/suppliers.csv with supplier SEG rate data
    5. Go to share.streamlit.io and connect your repo
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import re
import os

# Page configuration
st.set_page_config(
    page_title="Solar ROI Calculator (UK)",
    page_icon="☀️",
    layout="centered"
)

# ============================================================================
# CONSTANTS
# ============================================================================

# UK baseline constants
BASE_YIELD = 950  # kWh per kWp per year (fallback if region not found)
BASE_INSTALL_COST = 5654.26  # £ for solar system installation
BATTERY_COST = 3500  # £ additional cost for battery

# Orientation multipliers
ORIENTATION_FACTORS = {
    "South": 1.0,
    "South-East": 0.95,
    "South-West": 0.95,
    "East": 0.85,
    "West": 0.85,
    "North-East": 0.70,
    "North-West": 0.70,
    "North": 0.6
}

# ============================================================================
# HELPER FUNCTIONS - DEFINED FIRST
# ============================================================================

@st.cache_data
def load_regional_yields():
    """Load regional yield data from CSV file."""
    csv_path = "data/region_yield.csv"
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return df
        except Exception as e:
            st.warning(f"Could not load regional yield data: {e}")
            return None
    else:
        return None

def get_regional_yield(postcode):
    """
    Extract postcode prefix and look up regional yield.
    Returns tuple: (region_name, yield_value)
    """
    if not postcode or postcode.strip() == "":
        return "UK Average", BASE_YIELD
    
    postcode_clean = postcode.strip().upper().replace(" ", "")
    match = re.match(r'^([A-Z]{1,2})', postcode_clean)
    
    if not match:
        return "UK Average", BASE_YIELD
    
    prefix = match.group(1)
    regional_df = load_regional_yields()
    
    if regional_df is None:
        return "UK Average", BASE_YIELD
    
    result = regional_df[regional_df['prefix'] == prefix]
    
    if not result.empty:
        region = result.iloc[0]['region']
        yield_val = result.iloc[0]['yield']
        return region, int(yield_val)
    else:
        return "UK Average", BASE_YIELD

@st.cache_data
def load_supplier_data():
    """Load energy supplier SEG rate data from CSV file."""
    csv_path = "data/suppliers.csv"
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return df
        except Exception as e:
            st.warning(f"Could not load supplier data: {e}")
            return None
    else:
        return None

def get_seg_rate_for_supplier(supplier_name):
    """
    Look up SEG rate for a given supplier.
    Returns SEG rate as float.
    """
    supplier_df = load_supplier_data()
    
    if supplier_df is None:
        return 21.0
    
    result = supplier_df[supplier_df['supplier'] == supplier_name]
    
    if not result.empty:
        return float(result.iloc[0]['seg_rate'])
    else:
        return 21.0

@st.cache_data
def load_home_type_data():
    """Load home type panel recommendations from CSV file."""
    csv_path = "data/home_type_panels.csv"
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return df
        except Exception as e:
            st.warning(f"Could not load home type data: {e}")
            return None
    else:
        return None

def get_min_panels_for_home_type(home_type):
    """
    Look up minimum recommended panels for a home type.
    Returns min_panels as int.
    """
    home_type_df = load_home_type_data()
    
    if home_type_df is None:
        return 8  # Default fallback
    
    result = home_type_df[home_type_df['home_type'] == home_type]
    
    if not result.empty:
        return int(result.iloc[0]['min_panels'])
    else:
        return 8  # Default fallback

# ============================================================================
# APP UI STARTS HERE
# ============================================================================

# App title and introduction
# DEVELOPER NOTE: This header block sets the brand tone and emotional entry point.
# Can be used for A/B testing different copy variants to optimize engagement.
# Current version prioritizes economic and personal-benefit framing over climate 
# messaging for broader appeal across different user motivations.
# Tone refinement: Removed "cleaner energy" reference to maintain purely economic focus.
st.title("☀️ Welcome to the Solar Revolution")
st.markdown("""
**Discover how much you could save—and earn—by switching to solar power.**

Join thousands of UK homeowners **reducing their energy bills** and achieving **energy independence**. 
This is your first step toward more affordable energy for your home.
""")

st.divider()

# ============================================================================
# SECTION 1: Property Information
# ============================================================================
st.markdown("### 🏠 Property Information")
st.markdown("Tell us about your home and roof setup.")

# Postcode input at the top
postcode = st.text_input(
    "Postcode",
    placeholder="e.g., M1 1AA, EH1 1AA, BN1 1AA",
    help="Enter your postcode to get region-specific solar yield estimates",
    key="postcode_input"
)

# Get regional yield based on postcode
region_name, regional_yield = get_regional_yield(postcode)

# Display regional information
if postcode and postcode.strip() != "":
    st.info(f"📍 **Your area:** {region_name} ({regional_yield} kWh/kWh per year)")
else:
    st.info(f"📍 Enter your postcode above for region-specific estimates (default: {BASE_YIELD} kWh/kWp per year)")

st.write("")

col1, col2 = st.columns(2)

with col1:
    roof_direction = st.selectbox(
        "Main Roof Direction",
        ["South", "South-East", "South-West", "East", "West", "North-East", "North-West", "North"],
        index=0,
        help="South-facing roofs generate the most electricity"
    )
    
    # Get orientation factor and show performance caption
    orientation_factor = ORIENTATION_FACTORS[roof_direction]
    
    if roof_direction == "South":
        performance_text = "☀️ Perfect! South-facing roofs get optimal solar generation."
    else:
        performance_pct = int(orientation_factor * 100)
        performance_text = f"☀️ Roof faces {roof_direction} — about {performance_pct}% of ideal south-facing performance."
    
    st.caption(performance_text)
    
    # Google Maps satellite view link
    if postcode and postcode.strip() != "":
        postcode_encoded = postcode.strip().replace(" ", "+")
        # t=k for satellite/hybrid view, z=20 for zoom level
        maps_url = f"https://maps.google.com/?q={postcode_encoded}&t=k&z=20"
        
        st.markdown(
            f'🔍 <a href="{maps_url}" target="_blank">View your roof on Google Maps</a>',
            unsafe_allow_html=True
        )

with col2:
    has_shading = st.radio(
        "Is your roof affected by shading?",
        ["No", "Yes"],
        index=0,
        help="Trees, chimneys, or nearby buildings can reduce solar generation"
    )

st.write("")

# Load home type data for dropdown
home_type_df = load_home_type_data()

if home_type_df is not None:
    home_type_list = home_type_df['home_type'].tolist()
else:
    home_type_list = ["Flat / Small home", "Terrace", "Semi-detached", "Detached", "Bungalow"]

home_type = st.selectbox(
    "Home Type",
    home_type_list,
    index=2,  # Default to Semi-detached
    help="This helps estimate appropriate system size for your property"
)

# Get minimum panels for selected home type
min_panels_for_type = get_min_panels_for_home_type(home_type)

# Show home type notes if available
if home_type_df is not None:
    home_info = home_type_df[home_type_df['home_type'] == home_type]
    if not home_info.empty:
        notes = home_info.iloc[0]['notes']
        typical_kwp = home_info.iloc[0]['typical_kwp']
        st.caption(f"ℹ️ {home_type}: {notes} (typical: {typical_kwp} kWp)")

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

# Load supplier data
supplier_df = load_supplier_data()

# Create supplier options
if supplier_df is not None:
    supplier_list = ["Select your supplier..."] + supplier_df['supplier'].tolist() + ["Other / Don't know"]
else:
    supplier_list = ["Select your supplier...", "Other / Don't know"]

# Supplier selection
selected_supplier = st.selectbox(
    "Your Energy Supplier",
    supplier_list,
    index=0,
    help="Select your supplier to auto-fill the export (SEG) rate",
    key="supplier_select"
)

# Get SEG rate for selected supplier
if selected_supplier == "Other / Don't know":
    supplier_seg_rate = 4.0  # Minimum guaranteed SEG rate
    st.caption("ℹ️ Using minimum guaranteed SEG rate of 4p/kWh. Check with your supplier for actual rate.")
elif selected_supplier != "Select your supplier...":
    supplier_seg_rate = get_seg_rate_for_supplier(selected_supplier)
    
    # Show supplier notes if available
    if supplier_df is not None:
        supplier_info = supplier_df[supplier_df['supplier'] == selected_supplier]
        if not supplier_info.empty:
            notes = supplier_info.iloc[0]['notes']
            st.caption(f"ℹ️ {selected_supplier}: {notes}")
else:
    supplier_seg_rate = 21.0  # Default if no selection made yet

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
        min_value=4.0,
        max_value=30.0,
        value=supplier_seg_rate,
        step=0.5,
        help="Smart Export Guarantee - what you earn for exporting to the grid. Auto-filled from your supplier selection, but you can edit it."
    )

# Display current SEG rate confirmation
if selected_supplier != "Select your supplier..." and selected_supplier != "Other / Don't know":
    st.success(f"✓ Using {selected_supplier}'s SEG rate: {seg_rate}p/kWh (editable above)")

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
        max_value=24,
        value=min_panels_for_type,
        step=1,
        help=f"Recommended minimum for {home_type}: {min_panels_for_type} panels. Adjust based on your roof space."
    )
    
    panel_wattage = st.number_input(
        "Panel Wattage (W)",
        min_value=300,
        max_value=600,
        value=460,
        step=10,
        help="Modern panels are typically 400-460W. Check your quote for exact specs"
    )
    
    # Calculate and display system size
    estimated_kwp = (num_panels * panel_wattage) / 1000
    st.caption(f"💡 Estimated system size: **{estimated_kwp:.1f} kWp** based on {num_panels} panels for a {home_type.lower()}.")

with col9:
    has_battery = st.radio(
        "Planning to add battery storage?",
        ["No", "Yes"],
        index=0,
        help="Battery stores excess solar energy for use at night (adds ~£3,500 to cost)"
    )

st.divider()

# ============================================================================
# CALCULATION LOGIC
# ============================================================================

def calculate_solar_roi():
    """
    Calculate solar ROI metrics based on user inputs.
    """
    
    # Step 1: Calculate system size in kWp
    system_size_kwp = (num_panels * panel_wattage) / 1000
    
    # Step 2: Calculate annual generation using regional yield
    orientation_factor = ORIENTATION_FACTORS[roof_direction]
    annual_generation = system_size_kwp * regional_yield * orientation_factor
    
    # Step 3: Calculate self-use percentage
    self_use_percent = 0.45
    
    if home_during_day == "Yes":
        self_use_percent += 0.10
    
    if has_battery == "Yes":
        self_use_percent += 0.25
    
    self_use_percent = min(0.90, self_use_percent)
    
    # Calculate self-used and exported energy
    self_used_kwh = annual_generation * self_use_percent
    exported_kwh = annual_generation - self_used_kwh
    
    # Step 4: Calculate financial benefits
    savings = self_used_kwh * (day_rate / 100)
    export_income = exported_kwh * (seg_rate / 100)
    total_annual_value = savings + export_income
    
    # Step 5: Calculate payback period
    install_cost = BASE_INSTALL_COST
    
    if total_annual_value > 0:
        payback_years = install_cost / total_annual_value
    else:
        payback_years = 0
    
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
        'orientation_factor': orientation_factor,
        'regional_yield': regional_yield,
        'region_name': region_name
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
            "Annual Generation",
            f"{results['annual_generation']:,.0f} kWh",
            help="Estimated electricity your solar panels will generate per year"
        )
    
    with metric_col2:
        st.metric(
            "Self-Use %",
            f"{results['self_use_percent']*100:.0f}%",
            help="Percentage of solar energy you'll use in your home"
        )
    
    with metric_col3:
        st.metric(
            "Annual Benefit",
            f"£{results['total_annual_value']:,.0f}",
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
        
        2. **Annual Generation:** {results['system_size_kwp']:.1f} kWp × {results['regional_yield']} kWh/kWp/year × {results['orientation_factor']:.2f} (orientation) 
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
        - Regional solar yield: {results['regional_yield']} kWh/kWp/year ({results['region_name']})
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
