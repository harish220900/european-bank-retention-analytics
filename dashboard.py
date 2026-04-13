import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="European Bank | Retention Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main { background: #f0f4f8; }
    
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 4px solid #1F4E79;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .metric-card.danger { border-left-color: #e53e3e; }
    .metric-card.warning { border-left-color: #dd6b20; }
    .metric-card.success { border-left-color: #276749; }
    .metric-card.info { border-left-color: #2B6CB0; }
    
    .metric-value { font-size: 2rem; font-weight: 700; color: #1A202C; line-height: 1.2; }
    .metric-label { font-size: 0.8rem; font-weight: 500; color: #718096; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
    .metric-delta { font-size: 0.85rem; color: #4A5568; margin-top: 4px; }
    
    .section-header {
        font-size: 1.3rem; font-weight: 700; color: #1F4E79;
        border-bottom: 2px solid #BEE3F8; padding-bottom: 8px;
        margin-bottom: 20px; margin-top: 8px;
    }
    
    .insight-box {
        background: #EBF8FF; border: 1px solid #BEE3F8;
        border-radius: 8px; padding: 14px 18px;
        font-size: 0.9rem; color: #2C5282; margin-bottom: 12px;
    }
    .insight-box.danger { background: #FFF5F5; border-color: #FED7D7; color: #742A2A; }
    .insight-box.success { background: #F0FFF4; border-color: #9AE6B4; color: #1C4532; }
    .insight-box.warning { background: #FFFAF0; border-color: #FBD38D; color: #7B341E; }
    
    .stSelectbox label, .stSlider label, .stMultiSelect label { font-weight: 600; color: #2D3748; }
    
    div[data-testid="stMetric"] {
        background: white; border-radius: 10px; padding: 16px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)

# ─── Load Data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # Load directly from GitHub raw URL — works on any server
    url = "https://raw.githubusercontent.com/harish220900/european-bank-retention-analytics/main/European_Bank.csv"
    df = pd.read_csv(url)
    return df
    
    # Engagement profiles
    df['EngagementProfile'] = 'Other'
    df.loc[(df.IsActiveMember==1) & (df.NumOfProducts>=2), 'EngagementProfile'] = 'Active Engaged'
    df.loc[(df.IsActiveMember==1) & (df.NumOfProducts==1), 'EngagementProfile'] = 'Active Low-Product'
    df.loc[(df.IsActiveMember==0) & (df.Balance>50000), 'EngagementProfile'] = 'Inactive High-Balance'
    df.loc[(df.IsActiveMember==0) & (df.NumOfProducts==1), 'EngagementProfile'] = 'Inactive Disengaged'
    
    # RSI
    df['RSI'] = (df.IsActiveMember*2 + df.NumOfProducts + df.HasCrCard + (df.Tenure>3).astype(int)).clip(1, 6)
    df['RSI_Label'] = df['RSI'].apply(lambda x: f"RSI {x}")
    
    # Age groups
    df['AgeGroup'] = pd.cut(df.Age, bins=[0,30,40,50,60,100], labels=['<30','30–40','40–50','50–60','60+'])
    
    # Balance segments
    df['BalanceSeg'] = 'Zero Balance'
    df.loc[df.Balance.between(1, 50000), 'BalanceSeg'] = '€1–50K'
    df.loc[df.Balance.between(50001, 100000), 'BalanceSeg'] = '€50K–100K'
    df.loc[df.Balance > 100000, 'BalanceSeg'] = '€100K+'
    
    # At-risk premium
    df['AtRisk'] = ((df.Balance > 100000) & (df.IsActiveMember == 0)).astype(int)
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏦 European Bank")
    st.markdown("**Retention Analytics Dashboard**")
    st.markdown("---")
    
    st.markdown("### 🔍 Filters")
    
    geo = st.multiselect("Geography", options=df.Geography.unique().tolist(), default=df.Geography.unique().tolist())
    gender = st.multiselect("Gender", options=df.Gender.unique().tolist(), default=df.Gender.unique().tolist())
    
    prod_range = st.slider("Number of Products", 1, 4, (1, 4))
    bal_range = st.slider("Balance Range (€)", 0, 250000, (0, 250000), step=5000, format="€%d")
    
    active_filter = st.selectbox("Membership Status", ["All", "Active Members Only", "Inactive Members Only"])
    
    st.markdown("---")
    st.markdown("**Dataset:** 10,000 customers")
    st.markdown("**Year:** 2025")
    st.markdown("**Geography:** France, Germany, Spain")

# ─── Apply Filters ────────────────────────────────────────────────────────────
dff = df[
    df.Geography.isin(geo) &
    df.Gender.isin(gender) &
    df.NumOfProducts.between(*prod_range) &
    df.Balance.between(*bal_range)
].copy()

if active_filter == "Active Members Only":
    dff = dff[dff.IsActiveMember == 1]
elif active_filter == "Inactive Members Only":
    dff = dff[dff.IsActiveMember == 0]

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='background: linear-gradient(135deg, #1F4E79 0%, #2B6CB0 100%); 
     border-radius: 16px; padding: 28px 36px; margin-bottom: 28px; color: white;'>
    <h1 style='margin:0; font-size:2rem; font-weight:700;'>🏦 Customer Engagement & Retention Analytics</h1>
    <p style='margin:8px 0 0 0; opacity:0.85; font-size:1rem;'>
        European Bank · Behavioral Churn Analysis · 2025 · N = {:,} customers (filtered)
    </p>
</div>
""".format(len(dff)), unsafe_allow_html=True)

# ─── KPI Row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

overall_churn = dff.Exited.mean() * 100
active_churn = dff[dff.IsActiveMember==1].Exited.mean() * 100
inactive_churn = dff[dff.IsActiveMember==0].Exited.mean() * 100
at_risk_count = dff[(dff.Balance > 100000) & (dff.IsActiveMember == 0)].shape[0]
two_prod_churn = dff[dff.NumOfProducts == 2].Exited.mean() * 100 if len(dff[dff.NumOfProducts==2]) > 0 else 0

k1.metric("Overall Churn Rate", f"{overall_churn:.1f}%", delta=f"{overall_churn-20.4:.1f}pp vs baseline")
k2.metric("Active Member Churn", f"{active_churn:.1f}%", delta="Lower is better")
k3.metric("Inactive Member Churn", f"{inactive_churn:.1f}%", delta=f"vs {active_churn:.1f}% active")
k4.metric("At-Risk Premium Customers", f"{at_risk_count:,}", delta="Balance >€100K, Inactive")
k5.metric("2-Product Churn (Optimal)", f"{two_prod_churn:.1f}%", delta="Target: all customers")

st.markdown("---")

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Engagement Overview",
    "📦 Product Utilization",
    "💰 Financial & Regional",
    "🎯 At-Risk Customer Detector",
    "📈 Retention Strength Scoring"
])

# ══════════════════════════════════════════════════════════════════
# TAB 1: ENGAGEMENT OVERVIEW
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Engagement vs Churn Overview</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Active vs Inactive Churn
        eng_data = dff.groupby('IsActiveMember')['Exited'].agg(['mean', 'count']).reset_index()
        eng_data['Label'] = eng_data['IsActiveMember'].map({0: 'Inactive', 1: 'Active'})
        eng_data['ChurnRate'] = eng_data['mean'] * 100
        
        fig = go.Figure(go.Bar(
            x=eng_data['Label'], y=eng_data['ChurnRate'],
            marker_color=['#e53e3e', '#276749'],
            text=[f"{v:.1f}%" for v in eng_data['ChurnRate']],
            textposition='outside',
            width=0.5
        ))
        fig.update_layout(
            title="Churn Rate: Active vs Inactive Members",
            yaxis_title="Churn Rate (%)", xaxis_title="",
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'),
            height=360, showlegend=False,
            title_font_size=14
        )
        fig.update_yaxes(gridcolor='#EDF2F7', range=[0, max(eng_data['ChurnRate'])*1.3])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Engagement Profile Churn
        ep_data = dff.groupby('EngagementProfile').agg(
            ChurnRate=('Exited', 'mean'),
            Count=('Exited', 'count')
        ).reset_index()
        ep_data['ChurnRate'] *= 100
        ep_data = ep_data.sort_values('ChurnRate', ascending=True)
        
        colors = {'Active Engaged': '#276749', 'Active Low-Product': '#2B6CB0',
                  'Inactive High-Balance': '#dd6b20', 'Inactive Disengaged': '#e53e3e', 'Other': '#718096'}
        
        fig2 = go.Figure(go.Bar(
            x=ep_data['ChurnRate'], y=ep_data['EngagementProfile'],
            orientation='h',
            marker_color=[colors.get(p, '#718096') for p in ep_data['EngagementProfile']],
            text=[f"{v:.1f}%  (n={c:,})" for v, c in zip(ep_data['ChurnRate'], ep_data['Count'])],
            textposition='outside'
        ))
        fig2.update_layout(
            title="Churn Rate by Engagement Profile",
            xaxis_title="Churn Rate (%)", yaxis_title="",
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=360,
            title_font_size=14, showlegend=False
        )
        fig2.update_xaxes(gridcolor='#EDF2F7', range=[0, max(ep_data['ChurnRate'])*1.3])
        st.plotly_chart(fig2, use_container_width=True)
    
    # Engagement profile volume + churn combined
    col3, col4 = st.columns(2)
    
    with col3:
        fig3 = px.pie(
            ep_data, values='Count', names='EngagementProfile',
            title="Customer Distribution by Engagement Profile",
            color='EngagementProfile',
            color_discrete_map=colors,
            hole=0.45
        )
        fig3.update_layout(font=dict(family='Inter'), height=340, title_font_size=14)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        # Age group churn
        age_data = dff.groupby('AgeGroup', observed=True)['Exited'].agg(['mean','count']).reset_index()
        age_data['ChurnRate'] = age_data['mean'] * 100
        
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=age_data['AgeGroup'].astype(str), y=age_data['ChurnRate'],
            marker_color=['#276749','#2B6CB0','#dd6b20','#e53e3e','#744210'],
            text=[f"{v:.1f}%" for v in age_data['ChurnRate']],
            textposition='outside'
        ))
        fig4.update_layout(
            title="Churn Rate by Age Group",
            yaxis_title="Churn Rate (%)", xaxis_title="Age Group",
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=340, showlegend=False,
            title_font_size=14
        )
        fig4.update_yaxes(gridcolor='#EDF2F7')
        st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown('<div class="insight-box">💡 <strong>Key Insight:</strong> Active members churn at 14.3% vs 26.9% for inactive — nearly 2x difference. The Inactive Disengaged segment shows 47.5% churn, almost 1-in-2 customers lost. Age group 50–60 is the most critical with 56.2% churn.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 2: PRODUCT UTILIZATION
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Product Utilization Impact on Churn</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        prod_data = dff.groupby('NumOfProducts')['Exited'].agg(['mean','count']).reset_index()
        prod_data['ChurnRate'] = prod_data['mean'] * 100
        
        bar_colors = ['#dd6b20' if v < 15 else ('#e53e3e' if v > 50 else '#2B6CB0') 
                      for v in prod_data['ChurnRate']]
        bar_colors[1] = '#276749'  # 2 products = green
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[f"{p} Product{'s' if p>1 else ''}" for p in prod_data['NumOfProducts']],
            y=prod_data['ChurnRate'],
            marker_color=bar_colors,
            text=[f"{v:.1f}%\n(n={c:,})" for v, c in zip(prod_data['ChurnRate'], prod_data['count'])],
            textposition='outside'
        ))
        fig.add_hline(y=overall_churn, line_dash="dash", line_color="#718096",
                      annotation_text=f"Portfolio Average {overall_churn:.1f}%")
        fig.update_layout(
            title="Churn Rate by Number of Products Held",
            yaxis_title="Churn Rate (%)", xaxis_title="",
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=380, showlegend=False,
            title_font_size=14
        )
        fig.update_yaxes(gridcolor='#EDF2F7', range=[0, 120])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Product count distribution by churn
        prod_churn_dist = dff.groupby(['NumOfProducts', 'Exited']).size().reset_index(name='Count')
        prod_churn_dist['Status'] = prod_churn_dist['Exited'].map({0: 'Retained', 1: 'Churned'})
        
        fig2 = px.bar(
            prod_churn_dist, x='NumOfProducts', y='Count', color='Status',
            barmode='stack', title="Customer Volume by Products & Churn Status",
            color_discrete_map={'Retained': '#2B6CB0', 'Churned': '#e53e3e'},
            labels={'NumOfProducts': 'Number of Products', 'Count': 'Customers'}
        )
        fig2.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=380, title_font_size=14
        )
        fig2.update_yaxes(gridcolor='#EDF2F7')
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Products × Active status heatmap
        hm_data = dff.groupby(['NumOfProducts', 'IsActiveMember'])['Exited'].mean().reset_index()
        hm_data['ChurnRate'] = (hm_data['Exited'] * 100).round(1)
        hm_pivot = hm_data.pivot(index='IsActiveMember', columns='NumOfProducts', values='ChurnRate')
        hm_pivot.index = ['Inactive', 'Active']
        
        fig3 = px.imshow(
            hm_pivot, text_auto=True, color_continuous_scale='RdYlGn_r',
            title="Churn Rate Heatmap: Products × Active Status",
            labels=dict(x="Number of Products", y="Member Status", color="Churn %"),
            aspect='auto'
        )
        fig3.update_layout(font=dict(family='Inter'), height=320, title_font_size=14)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        # Credit card vs churn
        cc_data = dff.groupby(['HasCrCard', 'IsActiveMember'])['Exited'].mean().reset_index()
        cc_data['ChurnRate'] = cc_data['Exited'] * 100
        cc_data['CC'] = cc_data['HasCrCard'].map({0: 'No Card', 1: 'Has Card'})
        cc_data['Active'] = cc_data['IsActiveMember'].map({0: 'Inactive', 1: 'Active'})
        
        fig4 = px.bar(
            cc_data, x='CC', y='ChurnRate', color='Active', barmode='group',
            title="Credit Card Ownership × Activity vs Churn",
            color_discrete_map={'Active': '#276749', 'Inactive': '#e53e3e'},
            labels={'CC': '', 'ChurnRate': 'Churn Rate (%)'}
        )
        fig4.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=320, title_font_size=14
        )
        fig4.update_yaxes(gridcolor='#EDF2F7')
        st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown('<div class="insight-box warning">⚠️ <strong>Critical Finding:</strong> 3–4 product customers show 83–100% churn — this is a product strategy failure, not a customer failure. Immediate audit of bundling practices required. The 2-product optimum represents a 72.6% churn reduction vs single-product customers.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 3: FINANCIAL & REGIONAL
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Financial Commitment & Geographic Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        geo_data = dff.groupby('Geography')['Exited'].agg(['mean','count']).reset_index()
        geo_data['ChurnRate'] = geo_data['mean'] * 100
        
        fig = px.bar(
            geo_data, x='Geography', y='ChurnRate',
            color='ChurnRate', color_continuous_scale='RdYlGn_r',
            title="Churn Rate by Geography",
            text=[f"{v:.1f}%" for v in geo_data['ChurnRate']],
            labels={'ChurnRate': 'Churn Rate (%)'}
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=360,
            showlegend=False, title_font_size=14
        )
        fig.update_yaxes(gridcolor='#EDF2F7', range=[0, 45])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        gen_data = dff.groupby('Gender')['Exited'].agg(['mean','count']).reset_index()
        gen_data['ChurnRate'] = gen_data['mean'] * 100
        
        fig2 = go.Figure(go.Bar(
            x=gen_data['Gender'], y=gen_data['ChurnRate'],
            marker_color=['#e07bb5', '#2B6CB0'],
            text=[f"{v:.1f}%\n(n={c:,})" for v, c in zip(gen_data['ChurnRate'], gen_data['count'])],
            textposition='outside', width=0.4
        ))
        fig2.update_layout(
            title="Churn Rate by Gender",
            yaxis_title="Churn Rate (%)", xaxis_title="",
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=360, showlegend=False,
            title_font_size=14
        )
        fig2.update_yaxes(gridcolor='#EDF2F7', range=[0, 35])
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Balance segment churn
        bal_order = ['Zero Balance', '€1–50K', '€50K–100K', '€100K+']
        bal_data = dff.groupby('BalanceSeg')['Exited'].agg(['mean','count']).reset_index()
        bal_data['ChurnRate'] = bal_data['mean'] * 100
        bal_data['BalanceSeg'] = pd.Categorical(bal_data['BalanceSeg'], categories=bal_order, ordered=True)
        bal_data = bal_data.sort_values('BalanceSeg')
        
        fig3 = go.Figure(go.Bar(
            x=bal_data['BalanceSeg'].astype(str), y=bal_data['ChurnRate'],
            marker_color=['#718096', '#2B6CB0', '#dd6b20', '#e53e3e'],
            text=[f"{v:.1f}%" for v in bal_data['ChurnRate']],
            textposition='outside'
        ))
        fig3.update_layout(
            title="Churn Rate by Balance Segment",
            yaxis_title="Churn Rate (%)", xaxis_title="Balance Segment",
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=340, showlegend=False,
            title_font_size=14
        )
        fig3.update_yaxes(gridcolor='#EDF2F7', range=[0, 40])
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        # Geography × Active heatmap
        geo_active = dff.groupby(['Geography', 'IsActiveMember'])['Exited'].mean().reset_index()
        geo_active['ChurnRate'] = (geo_active['Exited'] * 100).round(1)
        geo_pivot = geo_active.pivot(index='Geography', columns='IsActiveMember', values='ChurnRate')
        geo_pivot.columns = ['Inactive', 'Active']
        
        fig4 = px.imshow(
            geo_pivot, text_auto=True, color_continuous_scale='RdYlGn_r',
            title="Churn Heatmap: Geography × Activity",
            aspect='auto'
        )
        fig4.update_layout(font=dict(family='Inter'), height=340, title_font_size=14)
        st.plotly_chart(fig4, use_container_width=True)
    
    # Salary vs balance scatter
    st.markdown('<div class="section-header">Salary–Balance Relationship</div>', unsafe_allow_html=True)
    
    sample = dff.sample(min(2000, len(dff)), random_state=42)
    fig5 = px.scatter(
        sample, x='EstimatedSalary', y='Balance', color='Exited',
        color_discrete_map={0: '#2B6CB0', 1: '#e53e3e'},
        opacity=0.5, title="Salary vs Balance — Churned vs Retained",
        labels={'EstimatedSalary': 'Estimated Salary (€)', 'Balance': 'Account Balance (€)', 'Exited': 'Churned'},
        hover_data=['Geography', 'Age', 'NumOfProducts']
    )
    fig5.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='Inter'), height=400, title_font_size=14
    )
    fig5.update_xaxes(gridcolor='#EDF2F7')
    fig5.update_yaxes(gridcolor='#EDF2F7')
    st.plotly_chart(fig5, use_container_width=True)
    
    st.markdown('<div class="insight-box danger">🚨 <strong>Regional Alert:</strong> Germany churns at 32.4% — more than double France (16.2%) and Spain (16.7%). Female customers churn at 25.1% vs 16.5% for males. High-balance customers (€100K+) show elevated churn, especially when inactive.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 4: AT-RISK CUSTOMER DETECTOR
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">High-Value Disengaged Customer Detector</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="insight-box warning">
    🎯 <strong>Detector Settings:</strong> Adjust the thresholds below to identify at-risk premium customers 
    who are financially committed but behaviorally disengaged — the highest-priority retention targets.
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        min_balance = st.slider("Minimum Balance Threshold (€)", 0, 200000, 100000, step=10000, format="€%d")
    with c2:
        age_min, age_max = st.slider("Age Range", 18, 92, (40, 70))
    with c3:
        min_tenure = st.slider("Minimum Tenure (years)", 0, 10, 0)
    
    c4, c5 = st.columns(2)
    with c4:
        geo_filter = st.multiselect("Geography Filter", options=df.Geography.unique().tolist(), 
                                     default=df.Geography.unique().tolist(), key="atri_geo")
    with c5:
        include_active = st.checkbox("Include Active Members", value=False)
    
    # Build at-risk dataset
    mask = (
        (dff.Balance >= min_balance) &
        (dff.Age.between(age_min, age_max)) &
        (dff.Tenure >= min_tenure) &
        (dff.Geography.isin(geo_filter))
    )
    if not include_active:
        mask = mask & (dff.IsActiveMember == 0)
    
    at_risk_df = dff[mask].copy()
    
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("At-Risk Customers Found", f"{len(at_risk_df):,}")
    r2.metric("Avg Balance", f"€{at_risk_df.Balance.mean():,.0f}" if len(at_risk_df) > 0 else "N/A")
    r3.metric("Churn Rate in Segment", f"{at_risk_df.Exited.mean()*100:.1f}%" if len(at_risk_df) > 0 else "N/A")
    r4.metric("Already Churned", f"{at_risk_df.Exited.sum():,}" if len(at_risk_df) > 0 else "N/A")
    
    if len(at_risk_df) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            geo_breakdown = at_risk_df.groupby('Geography')['Exited'].agg(['mean','count']).reset_index()
            geo_breakdown['ChurnRate'] = geo_breakdown['mean'] * 100
            
            fig = px.bar(
                geo_breakdown, x='Geography', y='count', color='ChurnRate',
                color_continuous_scale='RdYlGn_r',
                title="At-Risk Customers by Geography",
                text=[f"{c:,}\n({r:.0f}% churn)" for c, r in zip(geo_breakdown['count'], geo_breakdown['ChurnRate'])],
                labels={'count': 'Customers', 'ChurnRate': 'Churn %'}
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(
                plot_bgcolor='white', paper_bgcolor='white',
                font=dict(family='Inter'), height=360, title_font_size=14
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            prod_ar = at_risk_df.groupby('NumOfProducts')['Exited'].agg(['mean','count']).reset_index()
            prod_ar['ChurnRate'] = prod_ar['mean'] * 100
            
            fig2 = px.pie(
                prod_ar, values='count', names='NumOfProducts',
                title="Product Distribution of At-Risk Customers",
                color_discrete_sequence=px.colors.sequential.Blues_r,
                hole=0.4
            )
            fig2.update_layout(font=dict(family='Inter'), height=360, title_font_size=14)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Customer table
        st.markdown("#### Top At-Risk Customer Records")
        display_cols = ['CustomerId', 'Geography', 'Gender', 'Age', 'Tenure', 'Balance', 
                         'NumOfProducts', 'IsActiveMember', 'EstimatedSalary', 'Exited', 'RSI']
        show_df = at_risk_df[display_cols].sort_values('Balance', ascending=False).head(50)
        show_df['Balance'] = show_df['Balance'].apply(lambda x: f"€{x:,.0f}")
        show_df['EstimatedSalary'] = show_df['EstimatedSalary'].apply(lambda x: f"€{x:,.0f}")
        show_df['IsActiveMember'] = show_df['IsActiveMember'].map({0: '❌ Inactive', 1: '✅ Active'})
        show_df['Exited'] = show_df['Exited'].map({0: 'Retained', 1: '🔴 Churned'})
        st.dataframe(show_df, use_container_width=True, height=400)
    else:
        st.info("No customers match the current filter criteria. Adjust the thresholds above.")

# ══════════════════════════════════════════════════════════════════
# TAB 5: RETENTION STRENGTH SCORING
# ══════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Relationship Strength Index (RSI) & Retention Scoring</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        rsi_data = dff.groupby('RSI')['Exited'].agg(['mean','count']).reset_index()
        rsi_data['ChurnRate'] = rsi_data['mean'] * 100
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=rsi_data['RSI'].astype(str),
            y=rsi_data['ChurnRate'],
            marker_color=['#d73027','#f46d43','#fdae61','#fee08b','#a6d96a','#1a9850'][:len(rsi_data)],
            text=[f"{v:.1f}%" for v in rsi_data['ChurnRate']],
            textposition='outside',
            name='Churn Rate'
        ))
        fig.add_hline(y=15, line_dash="dash", line_color="#276749",
                      annotation_text="15% — Target Threshold")
        fig.update_layout(
            title="Churn Rate by Relationship Strength Index (RSI)",
            xaxis_title="RSI Score (1=Weakest, 6=Strongest)",
            yaxis_title="Churn Rate (%)",
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=380,
            showlegend=False, title_font_size=14
        )
        fig.update_yaxes(gridcolor='#EDF2F7', range=[0, 45])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        rsi_vol = dff.groupby(['RSI', 'Exited']).size().reset_index(name='Count')
        rsi_vol['Status'] = rsi_vol['Exited'].map({0: 'Retained', 1: 'Churned'})
        
        fig2 = px.bar(
            rsi_vol, x='RSI', y='Count', color='Status', barmode='stack',
            title="Customer Volume by RSI Score",
            color_discrete_map={'Retained': '#2B6CB0', 'Churned': '#e53e3e'},
            labels={'RSI': 'RSI Score', 'Count': 'Customers'}
        )
        fig2.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=380, title_font_size=14
        )
        fig2.update_yaxes(gridcolor='#EDF2F7')
        st.plotly_chart(fig2, use_container_width=True)
    
    # RSI by geography
    col3, col4 = st.columns(2)
    
    with col3:
        rsi_geo = dff.groupby(['Geography', 'RSI'])['Exited'].mean().reset_index()
        rsi_geo['ChurnRate'] = rsi_geo['Exited'] * 100
        
        fig3 = px.line(
            rsi_geo, x='RSI', y='ChurnRate', color='Geography',
            title="RSI vs Churn Rate by Geography",
            markers=True,
            color_discrete_map={'France': '#2B6CB0', 'Germany': '#e53e3e', 'Spain': '#276749'},
            labels={'RSI': 'RSI Score', 'ChurnRate': 'Churn Rate (%)'}
        )
        fig3.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Inter'), height=360, title_font_size=14
        )
        fig3.update_yaxes(gridcolor='#EDF2F7')
        fig3.update_xaxes(gridcolor='#EDF2F7')
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        # RSI score calculator
        st.markdown("#### 🧮 RSI Score Calculator")
        st.markdown("Estimate a customer's churn risk by inputting their profile:")
        
        calc_active = st.selectbox("Active Member?", ["Yes", "No"], key="calc_active")
        calc_products = st.slider("Number of Products", 1, 4, 2, key="calc_prod")
        calc_cc = st.selectbox("Has Credit Card?", ["Yes", "No"], key="calc_cc")
        calc_tenure = st.slider("Tenure (years)", 0, 10, 3, key="calc_tenure")
        
        active_val = 1 if calc_active == "Yes" else 0
        cc_val = 1 if calc_cc == "Yes" else 0
        tenure_val = 1 if calc_tenure > 3 else 0
        
        rsi_score = min(active_val * 2 + calc_products + cc_val + tenure_val, 6)
        
        # Look up expected churn
        rsi_lookup = dff.groupby('RSI')['Exited'].mean()
        expected_churn = rsi_lookup.get(rsi_score, rsi_lookup.mean()) * 100
        
        risk_level = "🟢 Low Risk" if expected_churn < 15 else ("🟡 Medium Risk" if expected_churn < 25 else "🔴 High Risk")
        
        st.markdown(f"""
        <div style='background: {"#F0FFF4" if expected_churn < 15 else ("#FFFAF0" if expected_churn < 25 else "#FFF5F5")}; 
             border-radius: 12px; padding: 20px; margin-top: 12px; text-align: center;'>
            <div style='font-size: 0.85rem; color: #718096; margin-bottom: 4px;'>RELATIONSHIP STRENGTH INDEX</div>
            <div style='font-size: 3rem; font-weight: 700; color: #1A202C;'>{rsi_score}/6</div>
            <div style='font-size: 1.1rem; font-weight: 600; margin: 8px 0;'>{risk_level}</div>
            <div style='font-size: 1.5rem; font-weight: 700; color: {"#276749" if expected_churn < 15 else ("#dd6b20" if expected_churn < 25 else "#e53e3e")};'>
                Expected Churn: {expected_churn:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # KPI Summary Table
    st.markdown('<div class="section-header">KPI Summary Dashboard</div>', unsafe_allow_html=True)
    
    kpi_df = pd.DataFrame({
        'KPI': ['Engagement Retention Ratio', 'Product Depth Index', 'High-Balance Disengagement Rate',
                'Credit Card Stickiness Score', 'Relationship Strength Index (Avg)'],
        'Value': [
            f"{dff[dff.IsActiveMember==0].Exited.mean()/max(dff[dff.IsActiveMember==1].Exited.mean(),0.001):.2f}x",
            f"{(1 - dff[dff.NumOfProducts==2].Exited.mean()/max(dff[dff.NumOfProducts==1].Exited.mean(),0.001))*100:.1f}% reduction",
            f"{dff[(dff.Balance>100000)&(dff.IsActiveMember==0)].Exited.mean()*100:.1f}%",
            f"{abs(dff[dff.HasCrCard==1].Exited.mean() - dff[dff.HasCrCard==0].Exited.mean())*100:.1f}pp diff",
            f"{dff['RSI'].mean():.2f} / 6.0"
        ],
        'Status': ['⚠️ Active vs Inactive gap', '✅ Strong lever', '🔴 High priority', 'ℹ️ Minimal impact', '📊 Monitor'],
        'Recommendation': [
            'Launch activation campaigns targeting inactive members',
            'Cross-sell second product to all single-product customers',
            'Deploy premium re-engagement program immediately',
            'Credit card alone insufficient for retention — combine with activation',
            'Target RSI < 3 customers with bundled retention offers'
        ]
    })
    
    st.dataframe(kpi_df, use_container_width=True, hide_index=True)
    
    st.markdown('<div class="insight-box success">✅ <strong>Action Priority:</strong> Focus first on customers with RSI ≤ 2 (32%+ churn risk). Moving them to RSI 4+ requires just one engagement action + one product add — achievable with targeted outreach and reduces churn to ~16%.</div>', unsafe_allow_html=True)
