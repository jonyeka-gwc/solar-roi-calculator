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
    5. Create data/home_type_panels.csv with home type recommendations
    6. Go to share.streamlit.io and connect your repo
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import re
import os
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="Solar ROI Calculator (UK)",
    page_icon="☀️",
    layout="centered"
)

# ============================================================================
# USEBERRY INTEGRATION TOGGLE
# ============================================================================
# DEVELOPER NOTE: Toggle for Useberry Live URL tracking during usability testing
# Set to True for user testing sessions, False for production
enable_useberry = True  # Change to False to disable tracking

# ============================================================================
# CONSTANTS
# ============================================================================

# UK baseline constants
BASE_YIELD = 950  # kWh per kWp per year (fallback if region not found)

# DEVELOPER NOTE: Installation cost model - Option 1 (Linear Scaling)
# Future evolution: Consider tiered costs (economies of scale), regional adjustments,
# or more granular breakdowns (inverter size, mounting systems, labor rates by region)
FIXED_COST = 2500  # £ baseline (scaffolding, inverter, labor)
COST_PER_PANEL = 350  # £ variable cost per panel

# DEVELOPER NOTE: Battery constants - current model uses 5kWh as standard
# Future expandability: capacity tiers (5kWh/10kWh), degradation modeling,
# smart charging integration, multiple battery configurations
BATTERY_COST = 4000  # £ additional cost for 5kWh battery storage
BATTERY_CAPACITY = 5  # kWh storage capacity
BATTERY_SELF_USE_BOOST = 0.25  # 25% increase in self-use when battery included

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
# DEVELOPER NOTE: This section focuses on the physical characteristics of the building itself
# (location, roof orientation, environmental factors) - not the solar system being designed.
st.markdown("### 🏠 Property Information")
st.markdown("Tell us about your home and roof characteristics.")

# Postcode input
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
    st.info(f"📍 **Your area:** {region_name} ({regional_yield} kWh/kWp per year)")
else:
    st.info(f"📍 Enter your postcode above for region-specific estimates (default: {BASE_YIELD} kWh/kWp per year)")

st.write("")

# Roof characteristics (moved back from Solar Setup)
col_roof1, col_roof2 = st.columns(2)

with col_roof1:
    # Start with no selection to encourage active participation
    roof_options = ["Select your roof direction", "South", "South-East", "South-West", "East", "West", "North-East", "North-West", "North"]
    
    roof_direction_raw = st.selectbox(
        "Main Roof Direction",
        roof_options,
        index=0,
        help="South-facing roofs generate the most electricity",
        key="roof_direction_select"
    )
    
    # DEVELOPER NOTE: Text-only compass guide for MVP. Consider visual compass overlay in future.
    st.caption("🧭 North ↑ | East → | South ↓ | West ←")
    
    # Google Maps satellite view link
    if postcode and postcode.strip() != "":
        postcode_encoded = postcode.strip().replace(" ", "+")
        maps_url = f"https://maps.google.com/?q={postcode_encoded}&t=k&z=20"
        
        st.markdown(
            f'🔍 <a href="{maps_url}" target="_blank">View your roof on Google Maps</a>',
            unsafe_allow_html=True
        )
        st.caption("💡 Tip: On Google Maps, north is always at the top — south is at the bottom.")

with col_roof2:
    has_shading = st.radio(
        "Is your roof affected by shading?",
        ["No", "Yes"],
        index=0,
        help="Trees, chimneys, or nearby buildings can reduce solar generation",
        key="shading_radio"
    )
    st.caption("Shading from trees or nearby buildings can reduce efficiency by 5–20%.")

# DEVELOPER NOTE: Dynamic feedback appears only after direction selection
# This creates a reactive "moment of insight" rather than static text
if roof_direction_raw != "Select your roof direction":
    roof_direction = roof_direction_raw
    
    # Get orientation factor
    orientation_factor = ORIENTATION_FACTORS[roof_direction]
    
    # Provide contextual feedback based on selection
    if roof_direction == "South":
        st.success("☀️ Perfect! South-facing roofs get optimal solar generation.")
    elif roof_direction in ["East", "West"]:
        st.info("☀️ Great! East- or west-facing roofs still capture most sunlight.")
    elif roof_direction == "North":
        st.warning("⚠️ North-facing roofs typically generate less energy.")
    else:
        st.info("☀️ Good choice — most directions still generate plenty of energy.")
else:
    # Default to South for calculations if not selected
    roof_direction = "South"
    orientation_factor = ORIENTATION_FACTORS[roof_direction]

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
# DEVELOPER NOTE: Tariff section reordered for MVP usability testing
# User flow clarity: Supplier first → SEG rate → Day/Night rates
# Mirrors typical energy bill structure for familiarity
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

# SEG rate input (moved up before day/night rates)
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

st.write("")

# Instructional caption for clarity
st.caption("💡 You can find your day and night rates on your latest energy bill.")

col5, col6 = st.columns(2)

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

st.divider()

# ============================================================================
# SECTION 4: Solar Setup
# ============================================================================
# DEVELOPER NOTE: This section focuses on designing the solar system itself
# (home type determines sizing, then panels, wattage, battery). Property vs system distinction.
st.markdown("### ☀️ Solar Setup")
st.markdown("Now let's configure your solar panel system.")

# Home type selection (moved from Property Information)
# DEVELOPER NOTE: Home type moved here because it directly influences system sizing
home_type_df = load_home_type_data()

if home_type_df is not None:
    home_type_list = ["Select your home type"] + home_type_df['home_type'].tolist()
else:
    home_type_list = ["Select your home type", "Flat / Small home", "Terrace", "Semi-detached", "Detached", "Bungalow"]

home_type_raw = st.selectbox(
    "Home Type",
    home_type_list,
    index=0,
    help="This determines the recommended system size for your property",
    key="home_type_select"
)

# Check if home type is selected
if home_type_raw == "Select your home type":
    home_type_selected = False
    home_type = "Semi-detached"  # Fallback for calculations
    min_panels_for_type = 8  # Default
    st.info("👆 Please select your home type to see recommended panel count")
else:
    home_type_selected = True
    home_type = home_type_raw
    min_panels_for_type = get_min_panels_for_home_type(home_type)
    
    # Show home type notes if available
    if home_type_df is not None:
        home_info = home_type_df[home_type_df['home_type'] == home_type]
        if not home_info.empty:
            notes = home_info.iloc[0]['notes']
            typical_kwp = home_info.iloc[0]['typical_kwp']
            st.caption(f"ℹ️ {home_type}: {notes} (typical: {typical_kwp} kWp)")

st.write("")

# Panel configuration
col8, col9 = st.columns(2)

with col8:
    # DEVELOPER NOTE: Panel count depends on home type selection
    # Disabled until home type chosen to make dependency clear
    if home_type_selected:
        num_panels = st.slider(
            "Number of Solar Panels",
            min_value=4,
            max_value=24,
            value=min_panels_for_type,
            step=1,
            help=f"Recommended minimum for {home_type}: {min_panels_for_type} panels. Adjust based on your roof space.",
            key="panel_count_slider"
        )
    else:
        # Show disabled state when no home type selected
        st.slider(
            "Number of Solar Panels",
            min_value=4,
            max_value=24,
            value=0,
            step=1,
            disabled=True,
            help="Select your home type above to enable this field",
            key="panel_count_slider_disabled"
        )
        num_panels = 0
    
    # Caption explaining the connection
    if home_type_selected:
        st.caption("💡 Your roof direction affects how much sunlight the panels receive.")
    
    # Panel wattage always active (advanced users may know their specs)
    panel_wattage = st.number_input(
        "Panel Wattage (W)",
        min_value=300,
        max_value=600,
        value=460,
        step=10,
        help="Modern panels are typically 400-460W. Check your quote for exact specs"
    )
    
    # Calculate and display system size
    if home_type_selected and num_panels > 0:
        estimated_kwp = (num_panels * panel_wattage) / 1000
        st.caption(f"Estimated system size: **{estimated_kwp:.1f} kWp** based on {num_panels} panels for a {home_type.lower()}.")
    elif not home_type_selected:
        st.caption("Select home type to see system size estimate")

with col9:
    has_battery = st.radio(
        "Would you like to include a home battery?",
        ["No", "Yes"],
        index=0,
        help="Store excess solar energy for use during evenings and cloudy days"
    )
    
    if has_battery == "Yes":
        st.caption(f"🔋 Adding {BATTERY_CAPACITY}kWh battery storage - stores daytime solar energy for evening use, reducing grid reliance.")
    else:
        st.caption("💡 Batteries store solar energy for use when the sun isn't shining, increasing your energy independence.")

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
    
    # Step 2: Calculate annual generation using regional yield, orientation, and shading
    orientation_factor = ORIENTATION_FACTORS[roof_direction]
    shading_factor = 0.9 if has_shading == "Yes" else 1.0
    annual_generation = system_size_kwp * regional_yield * orientation_factor * shading_factor
    
    # Step 3: Calculate self-use percentage
    # DEVELOPER NOTE: Battery significantly increases self-use by storing excess daytime generation
    self_use_percent = 0.45
    
    if home_during_day == "Yes":
        self_use_percent += 0.10
    
    if has_battery == "Yes":
        self_use_percent += BATTERY_SELF_USE_BOOST  # 25% boost with battery
    
    self_use_percent = min(0.90, self_use_percent)
    
    # Calculate self-used and exported energy
    self_used_kwh = annual_generation * self_use_percent
    exported_kwh = annual_generation - self_used_kwh
    
    # Step 4: Calculate financial benefits
    savings = self_used_kwh * (day_rate / 100)
    export_income = exported_kwh * (seg_rate / 100)
    total_annual_value = savings + export_income
    
    # Step 5: Calculate installation cost (scaled by panel count)
    # DEVELOPER NOTE: Linear cost model - fixed baseline + per-panel variable cost
    panel_install_cost = FIXED_COST + (num_panels * COST_PER_PANEL)
    battery_install_cost = BATTERY_COST if has_battery == "Yes" else 0
    install_cost = panel_install_cost + battery_install_cost
    
    # Step 6: Calculate payback period
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
        'panel_install_cost': panel_install_cost,
        'battery_install_cost': battery_install_cost,
        'payback_years': payback_years,
        'orientation_factor': orientation_factor,
        'shading_factor': shading_factor,
        'regional_yield': regional_yield,
        'region_name': region_name
    }

# ============================================================================
# SECTION 5: Results
# ============================================================================

if st.button("Calculate My Solar Savings", type="primary", use_container_width=True):
    
    # Perform calculations
    results = calculate_solar_roi()
    
    # DEVELOPER NOTE: Auto-scroll to results for mobile UX - critical for visibility
    # Users on mobile need to see results immediately after clicking calculate button
    # Using HTML anchor + JavaScript for cross-platform scroll behavior
    st.markdown('<div id="results-section"></div>', unsafe_allow_html=True)
    st.markdown("""
        <script>
            document.getElementById('results-section').scrollIntoView({behavior: 'smooth', block: 'start'});
        </script>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("## ☀️ Your Solar Savings")
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
        st.metric("Energy You'll Use", f"{results['self_used_kwh']:,.0f} kWh ({results['self_use_percent']*100:.0f}%)")
        st.metric("Savings from Self-Use", f"£{results['savings']:,.0f}")
    
    with detail_col2:
        st.metric("Installation Cost", f"£{results['install_cost']:,.0f}")
        if results['battery_install_cost'] > 0:
            st.caption(f"💰 Panels: £{results['panel_install_cost']:,.0f} + Battery: £{results['battery_install_cost']:,.0f}")
        else:
            st.caption(f"💰 Estimated installation cost (UK national average)")
        st.metric("Energy Exported", f"{results['exported_kwh']:,.0f} kWh ({results['export_percent']*100:.0f}%)")
        st.metric("Income from Export", f"£{results['export_income']:,.0f}")
    
    st.divider()
    
    # Summary text
    coverage_percent = (results['annual_generation'] / annual_usage * 100) if annual_usage > 0 else 0
    
    st.markdown("### 📝 Summary")
    
    # Build summary text dynamically
    summary_parts = []
    
    summary_parts.append(f"""
    Your **{num_panels}-panel system ({results['system_size_kwp']:.1f} kWp)** would generate 
    approximately **{results['annual_generation']:,.0f} kWh per year** — that's about **{coverage_percent:.0f}%** 
    of your current electricity usage.
    """)
    
    if has_battery == "Yes":
        summary_parts.append(f"""
    With a **{BATTERY_CAPACITY}kWh battery**, you'd use **{results['self_use_percent']*100:.0f}%** of your solar energy 
    directly in your home (storing excess for evenings) and export **{results['export_percent']*100:.0f}%** to the grid.
    """)
    else:
        summary_parts.append(f"""
    You'd use **{results['self_use_percent']*100:.0f}%** of this energy directly in your home and export 
    **{results['export_percent']*100:.0f}%** to the grid.
    """)
    
    summary_parts.append(f"""
    This would give you an annual benefit of around **£{results['total_annual_value']:,.0f}** 
    (£{results['savings']:,.0f} from self-use + £{results['export_income']:,.0f} from exports).
    """)
    
    summary_parts.append(f"""
    💰 **Estimated installation cost: £{results['install_cost']:,.0f}** (UK national average - 
    £{results['panel_install_cost']:,.0f} for panels{'+ £' + str(results['battery_install_cost']) + ' for battery' if has_battery == 'Yes' else ''})
    
    You'd recover your investment in approximately **{results['payback_years']:.1f} years**.
    """)
    
    st.success("".join(summary_parts))
    
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
            recommendations.append(f"🔋 **Excellent choice on the battery!** With export rates below 15p/kWh, storing energy for your own use (at {day_rate:.1f}p/kWh value) makes much more financial sense than exporting it. Your {BATTERY_CAPACITY}kWh battery will maximize your savings.")
        else:
            recommendations.append(f"🔋 **Strongly consider adding a battery.** Your export rate is only {seg_rate:.1f}p/kWh, but your grid electricity costs {day_rate:.1f}p/kWh. A {BATTERY_CAPACITY}kWh battery (£{BATTERY_COST:,}) would let you store excess daytime solar for evening use, significantly improving your return.")
    else:
        if has_battery == "Yes":
            recommendations.append(f"🔋 **Battery adds value.** With a decent {seg_rate:.1f}p export rate, you're already getting good returns from exporting. Your {BATTERY_CAPACITY}kWh battery will boost self-use from {(results['self_use_percent']-BATTERY_SELF_USE_BOOST)*100:.0f}% to {results['self_use_percent']*100:.0f}%, further reducing grid reliance.")
        else:
            recommendations.append(f"🔋 **Battery is optional.** With a {seg_rate:.1f}p export rate, exporting to the grid is already quite profitable. A battery would increase self-use but may not dramatically improve payback given your good export terms.")
    
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
        
        2. **Annual Generation:** 
           - Base: {results['system_size_kwp']:.1f} kWp × {results['regional_yield']} kWh/kWp/year = {results['system_size_kwp'] * results['regional_yield']:,.0f} kWh
           - Orientation factor: × {results['orientation_factor']:.2f} ({roof_direction})
           - Shading factor: × {results['shading_factor']:.1f} ({'yes' if has_shading == 'Yes' else 'no shading'})
           - **Final: {results['annual_generation']:,.0f} kWh/year**
        
        3. **Self-Use Calculation:**
           - Base self-use: 45%
           - Home during day: {'+10%' if home_during_day == 'Yes' else '—'}
           - Battery storage: {f'+{BATTERY_SELF_USE_BOOST*100:.0f}%' if has_battery == 'Yes' else '—'}
           - **Total self-use: {results['self_use_percent']*100:.0f}%** (capped at 90%)
        
        4. **Financial Benefits:**
           - Self-used: {results['self_used_kwh']:,.0f} kWh × {day_rate:.1f}p/kWh = **£{results['savings']:,.0f}**
           - Exported: {results['exported_kwh']:,.0f} kWh × {seg_rate:.1f}p/kWh = **£{results['export_income']:,.0f}**
           - **Total annual value: £{results['total_annual_value']:,.0f}**
        
        5. **Installation Cost:**
           - Fixed costs: £{FIXED_COST:,} (scaffolding, inverter, labor)
           - Panel costs: {num_panels} panels × £{COST_PER_PANEL} = £{num_panels * COST_PER_PANEL:,}
           - Battery: {'£' + str(BATTERY_COST) + f' ({BATTERY_CAPACITY}kWh)' if has_battery == 'Yes' else '—'}
           - **Total: £{results['install_cost']:,.0f}**
        
        6. **Payback Period:** £{results['install_cost']:,.0f} ÷ £{results['total_annual_value']:,.0f}/year = **{results['payback_years']:.1f} years**
        
        ---
        
        **Key Assumptions:**
        - Regional solar yield: {results['regional_yield']} kWh/kWp/year ({results['region_name']})
        - Orientation multipliers: South = 1.0, SE/SW = 0.95, E/W = 0.85, NE/NW = 0.70, North = 0.6
        - Shading impact: 10% reduction if present
        - Panel wattage: {panel_wattage}W per panel
        - Installation costs: £{FIXED_COST:,} fixed + £{COST_PER_PANEL}/panel (UK national average)
        - Battery: {BATTERY_CAPACITY}kWh capacity, £{BATTERY_COST:,}, +{BATTERY_SELF_USE_BOOST*100:.0f}% self-use boost
        - System lifespan: 25 years (typical warranty period)
        
        These are estimates based on typical UK conditions. Actual results vary by location, 
        shading, roof pitch, weather patterns, and installer quotes. Consult a certified MCS 
        installer for a detailed site assessment and accurate pricing.
        """)

# Footer
st.divider()
st.caption("☀️ Solar ROI Calculator | For estimation purposes only | Data based on UK averages")

# ============================================================================
# USEBERRY INTEGRATION FOR USER TESTING
# ============================================================================
# DEVELOPER NOTE: Useberry integration for user testing (toggleable via enable_useberry variable)
# This script records user sessions during usability testing. Placed at bottom to avoid
# delaying page load. Has no visual or functional side effects - purely passive analytics.
# Disable in production by setting enable_useberry = False at top of file.

if enable_useberry:
    components.html(
        """
        <script type="text/javascript" src="https://api.useberry.com/integrations/liveUrl/scripts/useberryScript.js"></script>
        """,
        height=0,
        width=0
    )
