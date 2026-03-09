import streamlit as st
import anthropic
import base64
import json
import numpy_financial as npf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Multifamily OM Analyzer", page_icon="🏢", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    .stApp { background-color: #F7F8FA; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp p, .stApp span, .stApp li, .stApp div, .stApp label { color: #2D2D2D; }
    .stTabs [data-baseweb="tab-list"] { gap: 0px; background-color: #1B2A4A; border-radius: 10px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { color: rgba(255,255,255,1) !important; -webkit-text-fill-color: white !important; font-weight: 600 !important; font-size: 0.9rem !important; padding: 0.6rem 1.2rem !important; border-radius: 8px !important; background-color: transparent !important; }
    .stTabs [data-baseweb="tab"]:hover { color: white !important; background-color: rgba(255,255,255,0.1) !important; }
    .stTabs [aria-selected="true"] { color: white !important; background-color: #3B7DD8 !important; }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }
    [data-testid="stExpander"] summary { color: #1B2A4A !important; font-weight: 600 !important; background-color: #F0F4F8 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] p, [data-testid="stExpander"] [data-testid="stExpanderDetails"] li, [data-testid="stExpander"] [data-testid="stExpanderDetails"] span, [data-testid="stExpander"] [data-testid="stExpanderDetails"] div { color: #2D2D2D !important; }
    [data-testid="stAlert"] p, [data-testid="stAlert"] span, [data-testid="stAlert"] div { color: #2D2D2D !important; }
    .main-header { background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #3B7DD8 100%); padding: 2rem 2.5rem; border-radius: 16px; margin-bottom: 1.5rem; }
    .main-header, .main-header * { color: white !important; -webkit-text-fill-color: white !important; }
    .main-header p { color: #B0C4DE !important; -webkit-text-fill-color: #B0C4DE !important; margin: 0.3rem 0 0 0; font-size: 0.95rem; }
    .main-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
    [data-testid="stMarkdownContainer"] .main-header h1 { color: white !important; -webkit-text-fill-color: white !important; }
    .upload-zone { background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #3B7DD8 100%); border: 2px dashed rgba(255,255,255,0.4); border-radius: 16px; padding: 3rem 2rem; text-align: center; margin: 1rem 0; }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] div, [data-testid="stFileUploader"] small { color: #2D2D2D !important; }
    [data-testid="stFileUploaderDropzone"] { background: transparent !important; border-color: rgba(255,255,255,0.3) !important; }
    [data-testid="stFileUploaderDropzone"] *, [data-testid="stFileUploaderDropzoneInstructions"] * { color: #2D2D2D !important; }    [data-testid="stFileUploader"] button, [data-testid="stFileUploaderDropzone"] button { color: white !important; border-color: rgba(255,255,255,0.6) !important; background-color: rgba(255,255,255,0.15) !important; }
    [data-testid="stFileUploader"] button:hover { background-color: rgba(255,255,255,0.3) !important; }
    [data-testid="stFileUploader"] svg, [data-testid="stFileUploaderDropzone"] svg { fill: #2D2D2D !important; stroke: #2D2D2D !important; color: #2D2D2D !important; }
    [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p { color: white !important; }
    section[data-testid="stFileUploadDropzone"] * { color: white !important; }
    .kpi-card { background: white; border-radius: 12px; padding: 1.2rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-left: 4px solid #3B7DD8; margin-bottom: 0.5rem; }
    .kpi-value { font-size: 1.4rem; font-weight: 700; color: #1B2A4A !important; margin: 0; }
    .kpi-label { font-size: 0.75rem; color: #666 !important; text-transform: uppercase; letter-spacing: 0.5px; margin: 0.3rem 0 0 0; }
    .section-header { font-size: 1.3rem; font-weight: 700; color: #1B2A4A !important; border-bottom: 3px solid #3B7DD8; padding-bottom: 0.5rem; margin: 1.5rem 0 1rem 0; }
    .subsection-header { font-size: 1rem; font-weight: 600; color: #2C3E6B !important; margin: 1rem 0 0.5rem 0; }
    .prop-detail-box { background: white; border-radius: 12px; padding: 1.2rem 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 1rem; font-size: 0.9rem; color: #2D2D2D !important; line-height: 1.8; }
    .prop-detail-box strong { color: #1B2A4A !important; }
    .swot-box { border-radius: 10px; padding: 1rem; min-height: 150px; }
    .swot-box, .swot-box * { color: white !important; }
    .swot-strength { background: linear-gradient(135deg, #2E7D32, #43A047); }
    .swot-weakness { background: linear-gradient(135deg, #C62828, #E53935); }
    .swot-opportunity { background: linear-gradient(135deg, #1565C0, #42A5F5); }
    .swot-threat { background: linear-gradient(135deg, #E65100, #FB8C00); }
    .swot-box h4 { margin: 0 0 0.5rem 0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }
    .swot-box li { font-size: 0.82rem; margin-bottom: 0.3rem; line-height: 1.4; }
    .red-flag { background: #FFF3E0; border-left: 4px solid #E65100; padding: 0.5rem 1rem; border-radius: 0 8px 8px 0; margin: 0.3rem 0; font-size: 0.85rem; color: #3E2723 !important; }
    .assumptions-box { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 1rem; border: 2px solid #E8EDF4; }
    .verdict-yes { background: linear-gradient(135deg, #1B5E20, #2E7D32); border-radius: 16px; padding: 1.5rem 2rem; margin: 1rem 0; }
    .verdict-yes * { color: white !important; }
    .verdict-yes h2 { margin: 0 0 0.5rem 0; font-size: 1.4rem; }
    .verdict-yes p { margin: 0; font-size: 0.9rem; line-height: 1.5; opacity: 0.95; }
    .verdict-no { background: linear-gradient(135deg, #B71C1C, #C62828); border-radius: 16px; padding: 1.5rem 2rem; margin: 1rem 0; }
    .verdict-no * { color: white !important; }
    .verdict-no h2 { margin: 0 0 0.5rem 0; font-size: 1.4rem; }
    .verdict-no p { margin: 0; font-size: 0.9rem; line-height: 1.5; opacity: 0.95; }
    .verdict-maybe { background: linear-gradient(135deg, #E65100, #F57C00); border-radius: 16px; padding: 1.5rem 2rem; margin: 1rem 0; }
    .verdict-maybe * { color: white !important; }
    .verdict-maybe h2 { margin: 0 0 0.5rem 0; font-size: 1.4rem; }
    .verdict-maybe p { margin: 0; font-size: 0.9rem; line-height: 1.5; opacity: 0.95; }
    .deal-card { background: white; border-radius: 12px; padding: 1.2rem 1.5rem; box-shadow: 0 2px 6px rgba(0,0,0,0.1); margin-bottom: 1rem; border-top: 4px solid #3B7DD8; }
    .deal-card h3 { color: #1B2A4A !important; margin: 0 0 0.5rem 0; font-size: 1.1rem; }
    .deal-card p { color: #2D2D2D !important; font-size: 0.88rem; line-height: 1.5; margin: 0.3rem 0; }
    .deal-card .deal-price { font-size: 1.3rem; font-weight: 700; color: #3B7DD8 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}
    .dataframe { font-size: 0.85rem !important; }
    .stMarkdown p, .stMarkdown li, .stMarkdown span { color: #2D2D2D !important; }
    .stMarkdown strong { color: #1B2A4A !important; }
    [data-testid="stNumberInput"] label { color: #2D2D2D !important; font-weight: 500 !important; }
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """You are a senior commercial real estate analyst specializing in multifamily acquisitions. Analyze the Offering Memorandum and return a single valid JSON object. If a field cannot be determined, use null. Do NOT guess — only extract what is explicitly stated or calculable.

{
  "page_1_overview": {
    "property_summary": {"property_name":"","address":"","city":"","state":"","zip":"","county":"","submarket":"","year_built":null,"year_renovated":null,"total_units":null,"total_sf":null,"average_unit_sf":null,"property_type":"","construction_type":"","number_of_buildings":null,"number_of_stories":null,"parking_spaces":null,"lot_size_acres":null},
    "description": "3-4 sentence executive summary",
    "key_features": ["8-12 key selling points"],
    "kpis": {"asking_price":null,"price_per_unit":null,"price_per_sf":null,"current_occupancy_pct":null,"average_rent_per_unit":null,"average_rent_psf":null,"walt_years":null,"in_place_noi":null,"pro_forma_noi":null,"in_place_cap_rate":null,"pro_forma_cap_rate":null,"grm":null,"operating_expense_ratio":null},
    "deal_transparency_report": {"data_completeness_score":"1-10","missing_data_points":[],"red_flags":[],"assumptions_to_verify":[],"data_quality_notes":""},
    "swot_analysis": {"strengths":[],"weaknesses":[],"opportunities":[],"threats":[]},
    "deal_verdict": {
      "recommendation": "YES or NO or MAYBE",
      "confidence": "Rate 1-10 how confident you are in this recommendation given the available data",
      "summary": "2-3 sentence explanation of why you recommend yes/no/maybe. Be direct and specific. Reference key numbers.",
      "key_positives": ["Top 3 reasons to do this deal"],
      "key_concerns": ["Top 3 reasons to be cautious"],
      "conditions": "If MAYBE or YES with caveats, what conditions would need to be met"
    },
    "deal_ideas": [
      {
        "deal_name": "Conservative Offer",
        "offer_price": null,
        "offer_per_unit": null,
        "strategy": "Describe the deal structure and strategy in 2-3 sentences. Reference specific data gaps, missed assumptions, or leverage points from the OM that justify the lower price.",
        "key_terms": "Key terms to propose (e.g., seller financing, inspection contingency, closing timeline)",
        "expected_cap_rate": null,
        "expected_irr": "Rough estimate",
        "rationale": "Why this deal makes sense — what OM weaknesses or data gaps justify this price"
      },
      {
        "deal_name": "Moderate Offer",
        "offer_price": null,
        "offer_per_unit": null,
        "strategy": "A balanced offer that accounts for some upside but protects against identified risks",
        "key_terms": "",
        "expected_cap_rate": null,
        "expected_irr": "",
        "rationale": "Why this is a fair middle-ground price"
      },
      {
        "deal_name": "Aggressive Offer",
        "offer_price": null,
        "offer_per_unit": null,
        "strategy": "Closest to asking price, for when you believe in the upside story",
        "key_terms": "",
        "expected_cap_rate": null,
        "expected_irr": "",
        "rationale": "Why you might pay near asking — what upside justifies it"
      }
    ]
  },
  "page_2_financials": {
    "income": {"gross_potential_rent":null,"loss_to_lease":null,"vacancy_loss":null,"concessions":null,"bad_debt":null,"effective_gross_income":null,"other_income":null,"other_income_breakdown":{},"total_gross_income":null},
    "expenses": {"total_operating_expenses":null,"expense_breakdown":{"real_estate_taxes":null,"insurance":null,"utilities":null,"repairs_and_maintenance":null,"management_fee":null,"management_fee_pct":null,"payroll":null,"general_and_admin":null,"marketing":null,"contract_services":null,"reserves_per_unit":null,"total_reserves":null,"other_expenses":null},"expense_per_unit":null,"expense_per_sf":null},
    "noi": {"in_place_noi":null,"pro_forma_noi":null,"noi_per_unit":null},
    "broker_assumptions": {"rent_growth_pct":null,"expense_growth_pct":null,"vacancy_assumption_pct":null,"cap_rate_assumption":null,"exit_cap_rate":null,"hold_period_years":null},
    "capital_expenditures": {"total_capex_budget":null,"capex_per_unit":null,"capex_breakdown":{},"renovation_details":""},
    "debt_assumptions_from_om": {"loan_amount":null,"ltv_pct":null,"interest_rate_pct":null,"amortization_years":null,"loan_term_years":null,"interest_only_period_years":null,"annual_debt_service":null},
    "historical_financials": {"t12_noi":null,"t3_noi":null,"year_over_year_noi_trend":[],"historical_occupancy_trend":[],"historical_revenue":[],"historical_expenses":[]}
  },
  "page_3_lease_analysis": {
    "unit_mix": [{"unit_type":"","count":null,"avg_sf":null,"avg_rent":null,"avg_rent_psf":null,"market_rent":null,"market_rent_psf":null,"loss_to_lease_pct":null}],
    "occupancy": {"current_occupancy_pct":null,"physical_vacancy_units":null,"economic_occupancy_pct":null,"average_occupancy_12mo":null},
    "lease_expiration_schedule": [{"period":"","units_expiring":null,"pct_of_total":null,"sf_expiring":null,"rent_at_risk":null}],
    "recent_lease_activity": {"recent_new_leases":[],"recent_renewals":[],"average_lease_term_months":null,"concession_trends":""},
    "lease_abstraction": {"standard_lease_term_months":null,"typical_escalation_structure":"","pet_policy":"","tenant_improvement_allowance":null,"notable_lease_provisions":[]},
    "rent_roll_summary": {"total_monthly_rent":null,"total_annual_rent":null,"highest_rent_unit":null,"lowest_rent_unit":null,"median_rent":null,"rent_distribution_notes":""}
  },
  "page_4_market_analysis": {
    "market_overview": {"msa":"","population":null,"population_growth_pct":null,"median_household_income":null,"income_growth_pct":null,"unemployment_rate_pct":null,"major_employers":[],"economic_drivers":""},
    "submarket_overview": {"submarket_name":"","submarket_vacancy_pct":null,"submarket_avg_rent":null,"submarket_rent_growth_pct":null,"submarket_inventory_units":null,"pipeline_under_construction_units":null,"absorption_trend":""},
    "rent_comps": [{"property_name":"","distance_miles":null,"year_built":null,"total_units":null,"occupancy_pct":null,"avg_rent":null,"avg_rent_psf":null,"amenities_notes":""}],
    "sales_comps": [{"property_name":"","sale_date":"","sale_price":null,"price_per_unit":null,"cap_rate":null,"total_units":null,"year_built":null}],
    "location_highlights": {"walk_score":null,"transit_score":null,"nearby_amenities":[],"school_ratings":"","proximity_highlights":[]}
  },
  "page_5_broker_assumptions": {
    "investment_highlights_as_stated": [],
    "value_add_strategy_as_stated": "",
    "broker_pro_forma_assumptions": {"rent_premiums_after_renovation":null,"target_occupancy_pct":null,"projected_rent_growth_annual_pct":null,"projected_expense_growth_annual_pct":null,"projected_noi_year_1":null,"projected_noi_stabilized":null,"projected_cap_rate_exit":null,"projected_hold_period":null,"projected_irr":null,"projected_equity_multiple":null},
    "broker_credibility_assessment": "",
    "assumptions_vs_actuals_gaps": [],
    "broker_contact": {"brokerage_firm":"","lead_broker":"","phone":"","email":""}
  }
}

IMPORTANT:
- All dollar amounts as numbers. All percentages as decimals (95%=0.95).
- SWOT and transparency = YOUR expert assessment, not the broker's language.
- For deal_verdict: Give a direct YES, NO, or MAYBE recommendation. Be honest and bold. Reference specific numbers. It is okay to not have all the info — give your best assessment with what you have.
- For deal_ideas: Create 3 distinct offers at different price points. The Conservative offer should be 10-20% below asking, Moderate 5-10% below, Aggressive within 5% of asking. Reference specific OM weaknesses, data gaps, or missed assumptions that justify each price. Include specific dollar amounts.
- Return ONLY JSON. No markdown, no commentary, no code fences."""

def build_cash_flow_model(extracted, scenario="base", overrides=None):
    fin = extracted.get("page_2_financials", {}); kpis = extracted.get("page_1_overview", {}).get("kpis", {}); broker = fin.get("broker_assumptions", {}); ov = overrides or {}
    purchase_price = kpis.get("asking_price") or 0; noi_year0 = fin.get("noi", {}).get("in_place_noi") or fin.get("noi", {}).get("pro_forma_noi") or kpis.get("in_place_noi") or 0
    debt = fin.get("debt_assumptions_from_om", {}); occupancy = ov.get("occupancy", kpis.get("current_occupancy_pct") or 0.95); interest_rate = ov.get("interest_rate", debt.get("interest_rate_pct") or 0.065)
    capex_total = ov.get("renovation_budget", fin.get("capital_expenditures", {}).get("total_capex_budget") or 0); ltv = ov.get("ltv", debt.get("ltv_pct") or 0.65)
    monthly_rent = ov.get("monthly_rent", kpis.get("average_rent_per_unit") or 0); amort_years = debt.get("amortization_years") or 30; io_period = debt.get("interest_only_period_years") or 0
    total_units = extracted.get("page_1_overview", {}).get("property_summary", {}).get("total_units") or 1
    if "monthly_rent" in ov and monthly_rent > 0:
        gross_rent = monthly_rent * total_units * 12 * occupancy; expenses = fin.get("expenses", {}).get("total_operating_expenses")
        if not expenses: expenses = gross_rent * 0.40
        noi_year0 = gross_rent - expenses
    scenarios = {
        "base": {"rent_growth": broker.get("rent_growth_pct") or 0.03, "expense_growth": broker.get("expense_growth_pct") or 0.02, "exit_cap": broker.get("exit_cap_rate") or (kpis.get("in_place_cap_rate") or 0.055) + 0.001, "vacancy": 1.0 - occupancy},
        "upside": {"rent_growth": (broker.get("rent_growth_pct") or 0.03) + 0.01, "expense_growth": (broker.get("expense_growth_pct") or 0.02) - 0.005, "exit_cap": (broker.get("exit_cap_rate") or 0.055) - 0.0025, "vacancy": max(0, (1.0 - occupancy) - 0.02)},
        "downside": {"rent_growth": (broker.get("rent_growth_pct") or 0.03) - 0.01, "expense_growth": (broker.get("expense_growth_pct") or 0.02) + 0.01, "exit_cap": (broker.get("exit_cap_rate") or 0.055) + 0.005, "vacancy": (1.0 - occupancy) + 0.03},
    }
    s = scenarios[scenario]; loan_amount = purchase_price * ltv; equity = purchase_price - loan_amount + capex_total
    if interest_rate > 0 and loan_amount > 0:
        mr = interest_rate / 12; np_ = amort_years * 12; mp = loan_amount * (mr * (1 + mr)**np_) / ((1 + mr)**np_ - 1); annual_ds = mp * 12; io_ds = loan_amount * interest_rate
    else: annual_ds = 0; io_ds = 0
    lb = loan_amount; ls = []; cfs = []; noi = noi_year0
    for yr in range(0, 11):
        if yr == 0:
            cfs.append({"Year":0,"NOI":0,"Yield":0,"CapEx":-capex_total,"CF Pre-Debt":-capex_total,"Debt Service":0,"DSCR":0,"CF Post-Debt":-capex_total,"Sale Proceeds":0,"Loan Repayment":0,"Levered CF":-equity,"CoC":0})
            ls.append({"Year":0,"Beg Balance":0,"Interest":0,"Principal":0,"End Balance":loan_amount}); continue
        noi = noi * (1 + s["rent_growth"]) if yr > 1 else noi_year0; yc = (capex_total / 2) if capex_total > 0 and yr <= 2 else 0
        ds = io_ds if yr <= io_period else annual_ds; yi = lb * interest_rate; yp = 0 if yr <= io_period else ds - yi; nb = lb - yp
        ls.append({"Year":yr,"Beg Balance":round(lb),"Interest":round(yi),"Principal":round(yp),"End Balance":round(nb)}); lb = nb
        dscr = noi / ds if ds > 0 else 0; cfbd = noi - yc; cfad = cfbd - ds; ns = 0; lr = 0
        if yr == 10: ev = noi * (1 + s["rent_growth"]) / s["exit_cap"]; ns = ev * 0.98; lr = -lb
        lcf = cfad + ns + lr if yr == 10 else cfad; coc = cfad / equity if equity > 0 else 0
        cfs.append({"Year":yr,"NOI":round(noi),"Yield":round(noi/purchase_price,4) if purchase_price>0 else 0,"CapEx":round(-yc),"CF Pre-Debt":round(cfbd),"Debt Service":round(-ds),"DSCR":round(dscr,2),"CF Post-Debt":round(cfad),"Sale Proceeds":round(ns),"Loan Repayment":round(lr),"Levered CF":round(lcf),"CoC":round(coc,4)})
    lcfs = [c["Levered CF"] for c in cfs]; lcfs[0] = -equity
    try: irr = npf.irr(lcfs)
    except: irr = None
    td = sum(c["Levered CF"] for c in cfs[1:]); em = (equity + td) / equity if equity > 0 else 0
    eca = [-0.01,-0.005,0,0.005,0.01]; rga = [-0.02,-0.01,0,0.01,0.02]; sens = []
    for ec in eca:
        row = {"Exit Cap": f"{(s['exit_cap']+ec)*100:.1f}%"}
        for rg in rga:
            tn=noi_year0; tb=loan_amount; tc=[-equity]
            for y in range(1,11):
                tn=tn*(1+s["rent_growth"]+rg) if y>1 else noi_year0; yc2=(capex_total/2) if capex_total>0 and y<=2 else 0; dy=io_ds if y<=io_period else annual_ds; yi2=tb*interest_rate; yp2=0 if y<=io_period else dy-yi2; tb-=yp2; cf_=tn-yc2-dy
                if y==10: ev2=tn*(1+s["rent_growth"]+rg)/(s["exit_cap"]+ec); tc.append(cf_+ev2*0.98-tb)
                else: tc.append(cf_)
            try: ti=round(npf.irr(tc)*100,1)
            except: ti=None
            row[f"RG {(s['rent_growth']+rg)*100:.1f}%"]=ti
        sens.append(row)
    es = []
    for lt in [0.50,0.55,0.60,0.65,0.70,0.75]:
        tl=purchase_price*lt; te=purchase_price-tl+capex_total
        if interest_rate>0 and tl>0: mr2=interest_rate/12; np2=amort_years*12; mp2=tl*(mr2*(1+mr2)**np2)/((1+mr2)**np2-1); tds=mp2*12
        else: tds=0
        tc2=(noi_year0-tds)/te if te>0 else 0; tn2=noi_year0; tb2=tl; tcs=[-te]
        for y in range(1,11):
            tn2=tn2*(1+s["rent_growth"]) if y>1 else noi_year0; yc3=(capex_total/2) if capex_total>0 and y<=2 else 0; yi3=tb2*interest_rate; yp3=tds-yi3; tb2-=yp3; cf2=tn2-yc3-tds
            if y==10: ev3=tn2*(1+s["rent_growth"])/s["exit_cap"]; tcs.append(cf2+ev3*0.98-tb2)
            else: tcs.append(cf2)
        try: ti2=npf.irr(tcs)
        except: ti2=None
        tt=sum(tcs[1:]); tm=(te+tt)/te if te>0 else 0
        es.append({"LTV":f"{lt*100:.0f}%","Equity":f"${te:,.0f}","CoC Yr1":f"{tc2*100:.1f}%","Net Profit":f"${(tt-te):,.0f}","IRR":f"{ti2*100:.1f}%" if ti2 else "N/A","Multiple":f"{tm:.2f}x"})
    return {"scenario":scenario,"assumptions":s,"purchase_price":purchase_price,"equity":round(equity),"loan_amount":round(loan_amount),"annual_ds":round(annual_ds),"cash_flows":cfs,"irr":irr,"equity_multiple":round(em,2),"net_profit":round(td-equity),"irr_sensitivity":sens,"equity_scenarios":es,"loan_schedule":ls}

def fmt_d(v):
    if v is None: return "N/A"
    if abs(v)>=1e6: return f"${v/1e6:,.1f}M"
    return f"${v:,.0f}"
def fmt_p(v):
    if v is None: return "N/A"
    return f"{v*100:.1f}%"
def render_kpi(l,v): st.markdown(f'<div class="kpi-card"><p class="kpi-value">{v}</p><p class="kpi-label">{l}</p></div>',unsafe_allow_html=True)
def render_swot(t,items,c):
    ih="".join([f"<li>{i}</li>" for i in items]) if items else "<li>N/A</li>"
    st.markdown(f'<div class="swot-box {c}"><h4>{t}</h4><ul style="padding-left:1.2rem;margin:0;">{ih}</ul></div>',unsafe_allow_html=True)

def extract_om(pdf_bytes):
    import fitz
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    if len(text) > 100000:
        text = text[:100000]
    msg = client.messages.create(model="claude-sonnet-4-5-20250929",max_tokens=16000,system=SYSTEM_PROMPT,messages=[{"role":"user","content":[{"type":"text","text":"Here is the text extracted from an Offering Memorandum. Analyze it and return the structured JSON.\n\n" + text}]}])
    txt = msg.content[0].text.strip()
    if txt.startswith("```"):
        txt = txt.split("\n",1)[1]
        txt = txt.rsplit("```",1)[0]
    return json.loads(txt)

st.markdown('<div class="main-header"><h1>🏢 Multifamily OM Analyzer</h1><p>Upload an Offering Memorandum and get instant investment analysis</p></div>',unsafe_allow_html=True)
if "extracted" not in st.session_state: st.session_state.extracted=None
if "models" not in st.session_state: st.session_state.models=None

if st.session_state.extracted is None:
    c1,c2,c3=st.columns([1,2,1])
    with c2:
        uf=st.file_uploader("Drop your Offering Memorandum here",type=["pdf"],label_visibility="visible")
        if uf:
            with st.status("Analyzing your OM...",expanded=True) as status:
                st.write("📤 Sending PDF to Claude..."); 
                try:
                    ext=extract_om(uf.read()); st.write("✅ Data extracted"); st.write("📊 Running models...")
                    mods={"base":build_cash_flow_model(ext,"base"),"upside":build_cash_flow_model(ext,"upside"),"downside":build_cash_flow_model(ext,"downside")}
                    st.session_state.extracted=ext; st.session_state.models=mods; status.update(label="Complete!",state="complete"); st.rerun()
                except json.JSONDecodeError: st.error("Failed to parse response. Try again.")
                except anthropic.AuthenticationError: st.error("Invalid API key.")
                except Exception as e: st.error(f"Error: {e}")
else:
    ext=st.session_state.extracted; mods=st.session_state.models
    ov=ext.get("page_1_overview",{}); prop=ov.get("property_summary",{}); kpis=ov.get("kpis",{}); swot=ov.get("swot_analysis",{}); tr=ov.get("deal_transparency_report",{}); fin=ext.get("page_2_financials",{})
    with st.sidebar:
        if st.button("🔄 Analyze New OM",use_container_width=True): st.session_state.extracted=None; st.session_state.models=None; st.rerun()
        st.markdown("---")
        st.markdown("---")
        st.download_button("📥 Download JSON (reload later)",json.dumps({"extracted":ext},indent=2,default=str),file_name="om_analysis.json",mime="application/json",use_container_width=True)
        try:
            from fpdf import FPDF
            import io
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 12, prop.get("property_name", "Property Analysis"), ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, f"Generated {datetime.now().strftime('%B %d, %Y')}", ln=True)
            pdf.ln(5)
            verdict = ov.get("deal_verdict", {})
            rec = verdict.get("recommendation", "N/A")
            conf = verdict.get("confidence", "?")
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, f"DEAL VERDICT: {rec} (Confidence: {conf}/10)", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, verdict.get("summary", ""))
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Why to do it:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for p in verdict.get("key_positives", []):
                pdf.multi_cell(0, 5, f"  + {p}")
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Why to be cautious:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for c in verdict.get("key_concerns", []):
                pdf.multi_cell(0, 5, f"  - {c}")
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Deal Ideas", ln=True)
            for deal in ov.get("deal_ideas", []):
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 7, deal.get("deal_name", ""), ln=True)
                pdf.set_font("Helvetica", "", 9)
                price = deal.get("offer_price")
                pdf.cell(0, 5, f"Offer: {fmt_d(price) if price else 'See rationale'}", ln=True)
                pdf.multi_cell(0, 5, f"Strategy: {deal.get('strategy', 'N/A')}")
                pdf.multi_cell(0, 5, f"Rationale: {deal.get('rationale', '')}")
                pdf.ln(3)
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Property Overview", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for key, val in prop.items():
                pdf.cell(90, 5, key.replace("_", " ").title())
                pdf.cell(0, 5, str(val) if val else "N/A", ln=True)
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Key Metrics", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for key, val in kpis.items():
                pdf.cell(90, 5, key.replace("_", " ").title())
                if val is not None:
                    if "pct" in key or "rate" in key or "ratio" in key:
                        pdf.cell(0, 5, fmt_p(val), ln=True)
                    elif "price" in key or "noi" in key or "rent" in key or "income" in key:
                        pdf.cell(0, 5, fmt_d(val), ln=True)
                    else:
                        pdf.cell(0, 5, str(val), ln=True)
                else:
                    pdf.cell(0, 5, "N/A", ln=True)
            pdf.ln(5)
            desc = ov.get("description", "")
            if desc:
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, "Executive Summary", ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 5, desc)
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Key Features", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for f in ov.get("key_features", []):
                pdf.multi_cell(0, 5, f"  * {f}")
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "SWOT Analysis", ln=True)
            swot_data = ov.get("swot_analysis", {})
            for cat in ["strengths", "weaknesses", "opportunities", "threats"]:
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 7, cat.title(), ln=True)
                pdf.set_font("Helvetica", "", 9)
                for item in swot_data.get(cat, []):
                    pdf.multi_cell(0, 5, f"  - {item}")
                pdf.ln(2)
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Deal Transparency Report", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, f"Data Completeness: {tr.get('data_completeness_score', 'N/A')}/10", ln=True)
            for flag in tr.get("red_flags", []):
                pdf.multi_cell(0, 5, f"  RED FLAG: {flag}")
            for v in tr.get("assumptions_to_verify", []):
                pdf.multi_cell(0, 5, f"  VERIFY: {v}")
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "10-Year Cash Flow (Base Case)", ln=True)
            pdf.set_font("Helvetica", "B", 7)
            cf_headers = ["Year", "NOI", "CapEx", "Debt Svc", "CF Post-Debt", "DSCR", "CoC"]
            col_w = 24
            for h in cf_headers:
                pdf.cell(col_w, 5, h)
            pdf.ln()
            pdf.set_font("Helvetica", "", 7)
            for cf in mods["base"]["cash_flows"]:
                pdf.cell(col_w, 4, str(cf["Year"]))
                pdf.cell(col_w, 4, fmt_d(cf["NOI"]) if cf["NOI"] else "-")
                pdf.cell(col_w, 4, fmt_d(cf["CapEx"]) if cf["CapEx"] else "-")
                pdf.cell(col_w, 4, fmt_d(cf["Debt Service"]) if cf["Debt Service"] else "-")
                pdf.cell(col_w, 4, fmt_d(cf["CF Post-Debt"]) if cf["CF Post-Debt"] else "-")
                pdf.cell(col_w, 4, f"{cf['DSCR']:.2f}x" if cf["DSCR"] else "-")
                pdf.cell(col_w, 4, f"{cf['CoC']*100:.1f}%" if cf["CoC"] else "-")
                pdf.ln()
                pdf.ln(5)
            mb = mods["base"]
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Return Summary", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(90, 5, "IRR"); pdf.cell(0, 5, f"{mb['irr']*100:.1f}%" if mb['irr'] else "N/A", ln=True)
            pdf.cell(90, 5, "Equity Multiple"); pdf.cell(0, 5, f"{mb['equity_multiple']:.2f}x", ln=True)
            pdf.cell(90, 5, "Net Profit"); pdf.cell(0, 5, fmt_d(mb['net_profit']), ln=True)
            pdf_bytes = pdf.output()
            st.download_button("📄 Download PDF Report", pdf_bytes, file_name=f"om_report_{prop.get('property_name','property').replace(' ','_')}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as e:
            st.caption(f"PDF export error: {e}")
    t1,t2,t3,t4,t5=st.tabs(["📋 Overview","💰 Financials","📄 Lease Analysis","🏙️ Market","🤝 Broker Assumptions"])

    with t1:
        st.markdown(f'<div class="section-header">{prop.get("property_name","Property")}</div>',unsafe_allow_html=True)

        # ═══ DEAL VERDICT ═══
        verdict = ov.get("deal_verdict", {})
        rec = verdict.get("recommendation", "").upper().strip()
        conf = verdict.get("confidence", "?")
        summary = verdict.get("summary", "")
        if rec == "YES":
            st.markdown(f'<div class="verdict-yes"><h2>✅ VERDICT: DO THIS DEAL</h2><p><strong>Confidence: {conf}/10</strong></p><p>{summary}</p></div>', unsafe_allow_html=True)
        elif rec == "NO":
            st.markdown(f'<div class="verdict-no"><h2>❌ VERDICT: PASS ON THIS DEAL</h2><p><strong>Confidence: {conf}/10</strong></p><p>{summary}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-maybe"><h2>⚠️ VERDICT: PROCEED WITH CAUTION</h2><p><strong>Confidence: {conf}/10</strong></p><p>{summary}</p></div>', unsafe_allow_html=True)

        vc1, vc2 = st.columns(2)
        positives = verdict.get("key_positives", [])
        concerns = verdict.get("key_concerns", [])
        with vc1:
            if positives:
                st.markdown("**Why to do it:**")
                for p in positives: st.markdown(f"🟢 {p}")
        with vc2:
            if concerns:
                st.markdown("**Why to be cautious:**")
                for c in concerns: st.markdown(f"🔴 {c}")
        conditions = verdict.get("conditions", "")
        if conditions and conditions != "null":
            st.markdown(f"**Conditions:** {conditions}")
        st.markdown("")

        # ═══ DEAL IDEAS ═══
        deals = ov.get("deal_ideas", [])
        if deals:
            st.markdown('<div class="subsection-header">💡 Deal Ideas — 3 Offers to Consider</div>', unsafe_allow_html=True)
            dc1, dc2, dc3 = st.columns(3)
            cols = [dc1, dc2, dc3]
            colors = ["#2E7D32", "#1565C0", "#E65100"]
            for i, deal in enumerate(deals[:3]):
                with cols[i]:
                    price = deal.get("offer_price")
                    ppu = deal.get("offer_per_unit")
                    price_str = fmt_d(price) if price else "See rationale"
                    ppu_str = f"({fmt_d(ppu)}/unit)" if ppu else ""
                    ecap = deal.get("expected_cap_rate")
                    ecap_str = fmt_p(ecap) if ecap else "N/A"
                    eirr = deal.get("expected_irr", "N/A")
                    st.markdown(f'''<div class="deal-card" style="border-top-color: {colors[i]};">
                        <h3>{deal.get("deal_name", f"Deal {i+1}")}</h3>
                        <p class="deal-price">{price_str} {ppu_str}</p>
                        <p><strong>Cap Rate:</strong> {ecap_str} | <strong>Est. IRR:</strong> {eirr}</p>
                        <p><strong>Strategy:</strong> {deal.get("strategy", "N/A")}</p>
                        <p><strong>Key Terms:</strong> {deal.get("key_terms", "N/A")}</p>
                        <p style="font-size:0.82rem; color:#666 !important; margin-top:0.5rem;"><em>{deal.get("rationale", "")}</em></p>
                    </div>''', unsafe_allow_html=True)
            st.markdown("")

        # ═══ PROPERTY DETAILS ═══
        c1,c2=st.columns(2)
        with c1: st.markdown(f'<div class="prop-detail-box"><strong>Address:</strong> {prop.get("address","N/A")}, {prop.get("city","")}, {prop.get("state","")} {prop.get("zip","")}<br><strong>Year Built:</strong> {prop.get("year_built","N/A")} | <strong>Renovated:</strong> {prop.get("year_renovated","N/A")}<br><strong>Type:</strong> {prop.get("property_type","N/A")} | <strong>Construction:</strong> {prop.get("construction_type","N/A")}</div>',unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="prop-detail-box"><strong>Units:</strong> {prop.get("total_units","N/A")} | <strong>Total SF:</strong> {f"{prop.get(chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(115)+chr(102)):,.0f}" if prop.get("total_sf") else "N/A"}<br><strong>Buildings:</strong> {prop.get("number_of_buildings","N/A")} | <strong>Stories:</strong> {prop.get("number_of_stories","N/A")}<br><strong>Parking:</strong> {prop.get("parking_spaces","N/A")} | <strong>Lot:</strong> {prop.get("lot_size_acres","N/A")} acres</div>',unsafe_allow_html=True)
        d=ov.get("description","")
        if d: st.info(d)
        st.markdown('<div class="subsection-header">Key Performance Indicators</div>',unsafe_allow_html=True)
        k1,k2,k3,k4,k5,k6=st.columns(6)
        with k1: render_kpi("Asking Price",fmt_d(kpis.get('asking_price')))
        with k2: render_kpi("Price/Unit",fmt_d(kpis.get('price_per_unit')))
        with k3: render_kpi("Occupancy",fmt_p(kpis.get('current_occupancy_pct')))
        with k4: render_kpi("In-Place NOI",fmt_d(kpis.get('in_place_noi')))
        with k5: render_kpi("Cap Rate",fmt_p(kpis.get('in_place_cap_rate')))
        with k6: render_kpi("Avg Rent/SF",f"${kpis.get('average_rent_psf',0):.2f}" if kpis.get('average_rent_psf') else "N/A")
        st.markdown("")
        ft=ov.get("key_features",[])
        if ft:
            st.markdown('<div class="subsection-header">🔑 Key Features</div>',unsafe_allow_html=True)
            fc=st.columns(2); h=len(ft)//2+len(ft)%2
            with fc[0]:
                for f in ft[:h]: st.markdown(f"✅ {f}")
            with fc[1]:
                for f in ft[h:]: st.markdown(f"✅ {f}")
        st.markdown('<div class="subsection-header">SWOT Analysis</div>',unsafe_allow_html=True)
        s1,s2,s3,s4=st.columns(4)
        with s1: render_swot("Strengths",swot.get("strengths",[]),"swot-strength")
        with s2: render_swot("Weaknesses",swot.get("weaknesses",[]),"swot-weakness")
        with s3: render_swot("Opportunities",swot.get("opportunities",[]),"swot-opportunity")
        with s4: render_swot("Threats",swot.get("threats",[]),"swot-threat")
        st.markdown(""); st.markdown('<div class="subsection-header">🔍 Deal Transparency Report</div>',unsafe_allow_html=True)
        st.markdown(f"**Data Completeness:** {tr.get('data_completeness_score','N/A')}/10")
        qn=tr.get("data_quality_notes","")
        if qn: st.markdown(f"**Data Quality:** {qn}")
        for fl in tr.get("red_flags",[]): st.markdown(f'<div class="red-flag">🚩 {fl}</div>',unsafe_allow_html=True)
        for v in tr.get("assumptions_to_verify",[]): st.markdown(f"❓ {v}")
        for mi in tr.get("missing_data_points",[]): st.markdown(f"📭 {mi}")

    with t2:
        st.markdown('<div class="section-header">Financial Analysis</div>',unsafe_allow_html=True)
        st.markdown('<div class="subsection-header">⚙️ Model Assumptions — Adjust & Recalculate</div>',unsafe_allow_html=True)
        st.markdown('<div class="assumptions-box">',unsafe_allow_html=True)
        debt=fin.get("debt_assumptions_from_om",{}); exb=fin.get("expenses",{}).get("expense_breakdown",{})
        ac1,ac2,ac3=st.columns(3)
        with ac1:
            io=st.number_input("Occupancy %",50.0,100.0,float((kpis.get("current_occupancy_pct") or 0.95)*100),0.5)/100.0
            ii=st.number_input("Interest Rate %",0.0,15.0,float((debt.get("interest_rate_pct") or 0.065)*100),0.125)/100.0
        with ac2:
            ir=st.number_input("Renovation Budget ($)",0,10000000,int(fin.get("capital_expenditures",{}).get("total_capex_budget") or 0),10000)
            im=st.number_input("Management Fee %",0.0,15.0,float((exb.get("management_fee_pct") or 0.05)*100),0.5)/100.0
        with ac3:
            il=st.number_input("Loan-to-Value %",0.0,90.0,float((debt.get("ltv_pct") or 0.65)*100),1.0)/100.0
            ire=st.number_input("Avg Monthly Rent/Unit ($)",0,20000,int(kpis.get("average_rent_per_unit") or 0),25)
        st.markdown('</div>',unsafe_allow_html=True)
        ovr={"occupancy":io,"interest_rate":ii,"renovation_budget":ir,"management_fee_pct":im,"ltv":il,"monthly_rent":ire}
        mb=build_cash_flow_model(ext,"base",ovr); mu=build_cash_flow_model(ext,"upside",ovr); md=build_cash_flow_model(ext,"downside",ovr)
        cm={"base":mb,"upside":mu,"downside":md}
        sc=st.radio("Scenario",["base","upside","downside"],horizontal=True); m=cm[sc]
        m1,m2,m3,m4,m5,m6=st.columns(6)
        with m1: render_kpi("Purchase Price",fmt_d(m['purchase_price']))
        with m2: render_kpi("Equity",fmt_d(m['equity']))
        with m3: render_kpi("Loan",fmt_d(m['loan_amount']))
        with m4: render_kpi("IRR",f"{m['irr']*100:.1f}%" if m['irr'] else "N/A")
        with m5: render_kpi("Eq Multiple",f"{m['equity_multiple']:.2f}x")
        with m6: render_kpi("Net Profit",fmt_d(m['net_profit']))
        st.markdown(""); st.markdown('<div class="subsection-header">Scenario Comparison</div>',unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({"Metric":["IRR","Equity Multiple","Net Profit"],"🔴 Downside":[f"{md['irr']*100:.1f}%" if md['irr'] else "N/A",f"{md['equity_multiple']:.2f}x",fmt_d(md['net_profit'])],"📊 Base":[f"{mb['irr']*100:.1f}%" if mb['irr'] else "N/A",f"{mb['equity_multiple']:.2f}x",fmt_d(mb['net_profit'])],"🟢 Upside":[f"{mu['irr']*100:.1f}%" if mu['irr'] else "N/A",f"{mu['equity_multiple']:.2f}x",fmt_d(mu['net_profit'])]}),use_container_width=True,hide_index=True)
        st.markdown('<div class="subsection-header">10-Year Cash Flow</div>',unsafe_allow_html=True)
        df=pd.DataFrame(m["cash_flows"]).copy()
        for c in ["NOI","CapEx","CF Pre-Debt","Debt Service","CF Post-Debt","Sale Proceeds","Loan Repayment","Levered CF"]:
            if c in df.columns: df[c]=df[c].apply(lambda x: fmt_d(x) if x!=0 else "—")
        df["Yield"]=df["Yield"].apply(lambda x: f"{x*100:.1f}%" if x else "—"); df["DSCR"]=df["DSCR"].apply(lambda x: f"{x:.2f}x" if x else "—"); df["CoC"]=df["CoC"].apply(lambda x: f"{x*100:.1f}%" if x else "—")
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.markdown('<div class="subsection-header">Returns by Leverage</div>',unsafe_allow_html=True); st.dataframe(pd.DataFrame(m["equity_scenarios"]),use_container_width=True,hide_index=True)
        st.markdown('<div class="subsection-header">IRR Sensitivity</div>',unsafe_allow_html=True); st.dataframe(pd.DataFrame(m["irr_sensitivity"]),use_container_width=True,hide_index=True)
        st.markdown('<div class="subsection-header">🏦 Loan Summary</div>',unsafe_allow_html=True)
        ld=pd.DataFrame(m["loan_schedule"])
        for c in ["Beg Balance","Interest","Principal","End Balance"]: ld[c]=ld[c].apply(lambda x: fmt_d(x))
        st.dataframe(ld,use_container_width=True,hide_index=True)

    with t3:
        st.markdown('<div class="section-header">Lease Analysis</div>',unsafe_allow_html=True); le=ext.get("page_3_lease_analysis",{})
        um=le.get("unit_mix",[])
        if um: st.markdown('<div class="subsection-header">Unit Mix</div>',unsafe_allow_html=True); ud=pd.DataFrame(um); ud.columns=[c.replace("_"," ").title() for c in ud.columns]; st.dataframe(ud,use_container_width=True,hide_index=True)
        oc=le.get("occupancy",{})
        if oc:
            st.markdown('<div class="subsection-header">Occupancy</div>',unsafe_allow_html=True)
            o1,o2,o3,o4=st.columns(4)
            with o1: render_kpi("Current",fmt_p(oc.get('current_occupancy_pct')))
            with o2: render_kpi("Vacant",str(oc.get('physical_vacancy_units','N/A')))
            with o3: render_kpi("Economic",fmt_p(oc.get('economic_occupancy_pct')))
            with o4: render_kpi("12-Mo Avg",fmt_p(oc.get('average_occupancy_12mo')))
        les=le.get("lease_expiration_schedule",[])
        if les: st.markdown(""); st.markdown('<div class="subsection-header">Lease Expiration</div>',unsafe_allow_html=True); st.dataframe(pd.DataFrame(les),use_container_width=True,hide_index=True)
        la=le.get("lease_abstraction",{})
        if la:
            st.markdown('<div class="subsection-header">📋 Lease Abstraction</div>',unsafe_allow_html=True)
            st.markdown(f"**Term:** {la.get('standard_lease_term_months','N/A')} mo | **Escalation:** {la.get('typical_escalation_structure','N/A')} | **Pets:** {la.get('pet_policy','N/A')}")
            for p in la.get("notable_lease_provisions",[]): st.markdown(f"- {p}")
        rr=le.get("rent_roll_summary",{})
        if rr:
            st.markdown('<div class="subsection-header">Rent Roll</div>',unsafe_allow_html=True)
            r1,r2,r3,r4,r5=st.columns(5)
            with r1: render_kpi("Monthly",fmt_d(rr.get('total_monthly_rent')))
            with r2: render_kpi("Annual",fmt_d(rr.get('total_annual_rent')))
            with r3: render_kpi("Highest",fmt_d(rr.get('highest_rent_unit')))
            with r4: render_kpi("Lowest",fmt_d(rr.get('lowest_rent_unit')))
            with r5: render_kpi("Median",fmt_d(rr.get('median_rent')))

    with t4:
        st.markdown('<div class="section-header">Market Analysis</div>',unsafe_allow_html=True); mkt=ext.get("page_4_market_analysis",{})
        mo=mkt.get("market_overview",{})
        if mo:
            st.markdown('<div class="subsection-header">Market Overview</div>',unsafe_allow_html=True)
            mk1,mk2,mk3,mk4=st.columns(4)
            with mk1: render_kpi("MSA",mo.get('msa','N/A'))
            with mk2: render_kpi("Population",f"{mo.get('population'):,.0f}" if mo.get('population') else "N/A")
            with mk3: render_kpi("Med Income",fmt_d(mo.get('median_household_income')))
            with mk4: render_kpi("Unemployment",fmt_p(mo.get('unemployment_rate_pct')))
            st.markdown(""); emp=mo.get("major_employers",[])
            if emp: st.markdown(f"**Major Employers:** {', '.join(emp)}")
        sub=mkt.get("submarket_overview",{})
        if sub:
            st.markdown(f'<div class="subsection-header">Submarket: {sub.get("submarket_name","N/A")}</div>',unsafe_allow_html=True)
            sb1,sb2,sb3,sb4=st.columns(4)
            with sb1: render_kpi("Vacancy",fmt_p(sub.get('submarket_vacancy_pct')))
            with sb2: render_kpi("Avg Rent",fmt_d(sub.get('submarket_avg_rent')))
            with sb3: render_kpi("Rent Growth",fmt_p(sub.get('submarket_rent_growth_pct')))
            with sb4: render_kpi("Pipeline",f"{sub.get('pipeline_under_construction_units'):,.0f}" if sub.get('pipeline_under_construction_units') else "N/A")
        st.markdown("")
        cp=mkt.get("rent_comps",[])
        if cp: st.markdown('<div class="subsection-header">Rent Comps</div>',unsafe_allow_html=True); st.dataframe(pd.DataFrame(cp),use_container_width=True,hide_index=True)
        sc2=mkt.get("sales_comps",[])
        if sc2: st.markdown('<div class="subsection-header">Sales Comps</div>',unsafe_allow_html=True); st.dataframe(pd.DataFrame(sc2),use_container_width=True,hide_index=True)

    with t5:
        st.markdown('<div class="section-header">Broker Assumptions</div>',unsafe_allow_html=True); bp=ext.get("page_5_broker_assumptions",{})
        hl=bp.get("investment_highlights_as_stated",[])
        if hl:
            st.markdown('<div class="subsection-header">💡 Investment Highlights (broker stated)</div>',unsafe_allow_html=True)
            for h in hl: st.markdown(f"- {h}")
        vs=bp.get("value_add_strategy_as_stated","")
        if vs: st.markdown('<div class="subsection-header">Value-Add Strategy</div>',unsafe_allow_html=True); st.info(vs)
        bpf=bp.get("broker_pro_forma_assumptions",{})
        if bpf:
            st.markdown('<div class="subsection-header">Broker Pro Forma</div>',unsafe_allow_html=True)
            b1,b2,b3,b4=st.columns(4)
            with b1: render_kpi("Rent Premium",fmt_d(bpf.get('rent_premiums_after_renovation'))); render_kpi("Yr 1 NOI",fmt_d(bpf.get('projected_noi_year_1')))
            with b2: render_kpi("Target Occ",fmt_p(bpf.get('target_occupancy_pct'))); render_kpi("Stab NOI",fmt_d(bpf.get('projected_noi_stabilized')))
            with b3: render_kpi("Rent Growth",fmt_p(bpf.get('projected_rent_growth_annual_pct'))); render_kpi("Exit Cap",fmt_p(bpf.get('projected_cap_rate_exit')))
            with b4: render_kpi("Proj IRR",fmt_p(bpf.get('projected_irr'))); render_kpi("Eq Mult",f"{bpf.get('projected_equity_multiple'):.2f}x" if bpf.get('projected_equity_multiple') else "N/A")
        st.markdown("")
        cr=bp.get("broker_credibility_assessment","")
        if cr: st.markdown('<div class="subsection-header">Credibility Assessment</div>',unsafe_allow_html=True); st.markdown(f'<div class="prop-detail-box">{cr}</div>',unsafe_allow_html=True)
        gp=bp.get("assumptions_vs_actuals_gaps",[])
        if gp:
            st.markdown('<div class="subsection-header">Assumptions vs Actuals Gaps</div>',unsafe_allow_html=True)
            for g in gp: st.markdown(f'<div class="red-flag">⚠️ {g}</div>',unsafe_allow_html=True)
        ct=bp.get("broker_contact",{})
        if ct and ct.get("brokerage_firm"): st.markdown(f"**Firm:** {ct.get('brokerage_firm','N/A')} | **Broker:** {ct.get('lead_broker','N/A')} | **Phone:** {ct.get('phone','N/A')}")
