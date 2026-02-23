import streamlit as st
import anthropic
import base64
import json
import numpy_financial as npf
import pandas as pd
from io import BytesIO
from datetime import datetime

# ─── Page Config ───
st.set_page_config(
    page_title="Multifamily OM Analyzer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    /* Global */
    .stApp { background-color: #F7F8FA; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #3B7DD8 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        margin: 0; font-size: 1.8rem; font-weight: 700; color: white;
    }
    .main-header p {
        margin: 0.3rem 0 0 0; font-size: 0.95rem; opacity: 0.8; color: #B0C4DE;
    }

    /* Upload area */
    .upload-zone {
        background: white;
        border: 2px dashed #3B7DD8;
        border-radius: 16px;
        padding: 3rem 2rem;
        text-align: center;
        margin: 1rem 0;
    }

    /* KPI Cards */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border-left: 4px solid #3B7DD8;
        height: 100%;
    }
    .kpi-value {
        font-size: 1.4rem; font-weight: 700; color: #1B2A4A;
        margin: 0;
    }
    .kpi-label {
        font-size: 0.75rem; color: #888; text-transform: uppercase;
        letter-spacing: 0.5px; margin: 0.3rem 0 0 0;
    }

    /* Section headers */
    .section-header {
        font-size: 1.3rem; font-weight: 700; color: #1B2A4A;
        border-bottom: 3px solid #3B7DD8;
        padding-bottom: 0.5rem; margin: 1.5rem 0 1rem 0;
    }

    .subsection-header {
        font-size: 1rem; font-weight: 600; color: #2C3E6B;
        margin: 1rem 0 0.5rem 0;
    }

    /* SWOT */
    .swot-box {
        border-radius: 10px; padding: 1rem;
        min-height: 150px; color: white;
    }
    .swot-strength { background: linear-gradient(135deg, #2E7D32, #43A047); }
    .swot-weakness { background: linear-gradient(135deg, #C62828, #E53935); }
    .swot-opportunity { background: linear-gradient(135deg, #1565C0, #42A5F5); }
    .swot-threat { background: linear-gradient(135deg, #E65100, #FB8C00); }
    .swot-box h4 { margin: 0 0 0.5rem 0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9; }
    .swot-box li { font-size: 0.82rem; margin-bottom: 0.3rem; line-height: 1.4; }

    /* Info cards */
    .info-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }

    /* Red flag */
    .red-flag {
        background: #FFF3E0;
        border-left: 4px solid #E65100;
        padding: 0.5rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.3rem 0;
        font-size: 0.85rem;
    }

    /* Status badge */
    .status-processing {
        background: #E8F0FE; color: #1565C0;
        padding: 0.5rem 1rem; border-radius: 8px;
        font-weight: 600; text-align: center;
    }

    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Table styling */
    .dataframe { font-size: 0.85rem !important; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a senior commercial real estate analyst specializing in multifamily acquisitions. You are analyzing an Offering Memorandum (OM) for a multifamily property. Your job is to extract every relevant data point and perform qualitative analysis.

Return your analysis as a single valid JSON object with the following structure. If a field cannot be determined from the OM, use null. Do NOT guess or fabricate numbers — only extract what is explicitly stated or clearly calculable from stated figures.

{
  "page_1_overview": {
    "property_summary": {
      "property_name": "",
      "address": "",
      "city": "",
      "state": "",
      "zip": "",
      "county": "",
      "submarket": "",
      "year_built": null,
      "year_renovated": null,
      "total_units": null,
      "total_sf": null,
      "average_unit_sf": null,
      "property_type": "",
      "construction_type": "",
      "number_of_buildings": null,
      "number_of_stories": null,
      "parking_spaces": null,
      "lot_size_acres": null
    },
    "description": "Write a 3-4 sentence executive summary of the property and the investment opportunity as presented in the OM.",
    "key_features": [
      "List 8-12 key selling points, amenities, and differentiators mentioned in the OM"
    ],
    "kpis": {
      "asking_price": null,
      "price_per_unit": null,
      "price_per_sf": null,
      "current_occupancy_pct": null,
      "average_rent_per_unit": null,
      "average_rent_psf": null,
      "walt_years": null,
      "in_place_noi": null,
      "pro_forma_noi": null,
      "in_place_cap_rate": null,
      "pro_forma_cap_rate": null,
      "grm": null,
      "operating_expense_ratio": null
    },
    "deal_transparency_report": {
      "data_completeness_score": "Rate 1-10 how complete the OM data is",
      "missing_data_points": ["List any critical data points NOT provided in the OM"],
      "red_flags": ["List any assumptions, projections, or claims that seem aggressive, unrealistic, or warrant scrutiny"],
      "assumptions_to_verify": ["List assumptions the broker has made that an investor should independently verify"],
      "data_quality_notes": "Any observations about the quality, consistency, or recency of the data presented"
    },
    "swot_analysis": {
      "strengths": ["3-5 strengths based on OM data"],
      "weaknesses": ["3-5 weaknesses or risks identified"],
      "opportunities": ["3-5 value-add or upside opportunities"],
      "threats": ["3-5 external threats or market risks"]
    }
  },
  "page_2_financials": {
    "income": {
      "gross_potential_rent": null,
      "loss_to_lease": null,
      "vacancy_loss": null,
      "concessions": null,
      "bad_debt": null,
      "effective_gross_income": null,
      "other_income": null,
      "other_income_breakdown": {},
      "total_gross_income": null
    },
    "expenses": {
      "total_operating_expenses": null,
      "expense_breakdown": {
        "real_estate_taxes": null,
        "insurance": null,
        "utilities": null,
        "repairs_and_maintenance": null,
        "management_fee": null,
        "management_fee_pct": null,
        "payroll": null,
        "general_and_admin": null,
        "marketing": null,
        "contract_services": null,
        "reserves_per_unit": null,
        "total_reserves": null,
        "other_expenses": null
      },
      "expense_per_unit": null,
      "expense_per_sf": null
    },
    "noi": {
      "in_place_noi": null,
      "pro_forma_noi": null,
      "noi_per_unit": null
    },
    "broker_assumptions": {
      "rent_growth_pct": null,
      "expense_growth_pct": null,
      "vacancy_assumption_pct": null,
      "cap_rate_assumption": null,
      "exit_cap_rate": null,
      "hold_period_years": null
    },
    "capital_expenditures": {
      "total_capex_budget": null,
      "capex_per_unit": null,
      "capex_breakdown": {},
      "renovation_details": ""
    },
    "debt_assumptions_from_om": {
      "loan_amount": null,
      "ltv_pct": null,
      "interest_rate_pct": null,
      "amortization_years": null,
      "loan_term_years": null,
      "interest_only_period_years": null,
      "annual_debt_service": null
    },
    "historical_financials": {
      "t12_noi": null,
      "t3_noi": null,
      "year_over_year_noi_trend": [],
      "historical_occupancy_trend": [],
      "historical_revenue": [],
      "historical_expenses": []
    }
  },
  "page_3_lease_analysis": {
    "unit_mix": [
      {
        "unit_type": "e.g. 1BR/1BA",
        "count": null,
        "avg_sf": null,
        "avg_rent": null,
        "avg_rent_psf": null,
        "market_rent": null,
        "market_rent_psf": null,
        "loss_to_lease_pct": null
      }
    ],
    "occupancy": {
      "current_occupancy_pct": null,
      "physical_vacancy_units": null,
      "economic_occupancy_pct": null,
      "average_occupancy_12mo": null
    },
    "lease_expiration_schedule": [
      {
        "period": "e.g. Month-to-Month, Q1 2025, etc.",
        "units_expiring": null,
        "pct_of_total": null,
        "sf_expiring": null,
        "rent_at_risk": null
      }
    ],
    "recent_lease_activity": {
      "recent_new_leases": [],
      "recent_renewals": [],
      "average_lease_term_months": null,
      "concession_trends": ""
    },
    "lease_abstraction": {
      "standard_lease_term_months": null,
      "typical_escalation_structure": "",
      "pet_policy": "",
      "tenant_improvement_allowance": null,
      "notable_lease_provisions": []
    },
    "rent_roll_summary": {
      "total_monthly_rent": null,
      "total_annual_rent": null,
      "highest_rent_unit": null,
      "lowest_rent_unit": null,
      "median_rent": null,
      "rent_distribution_notes": ""
    }
  },
  "page_4_market_analysis": {
    "market_overview": {
      "msa": "",
      "population": null,
      "population_growth_pct": null,
      "median_household_income": null,
      "income_growth_pct": null,
      "unemployment_rate_pct": null,
      "major_employers": [],
      "economic_drivers": ""
    },
    "submarket_overview": {
      "submarket_name": "",
      "submarket_vacancy_pct": null,
      "submarket_avg_rent": null,
      "submarket_rent_growth_pct": null,
      "submarket_inventory_units": null,
      "pipeline_under_construction_units": null,
      "absorption_trend": ""
    },
    "rent_comps": [
      {
        "property_name": "",
        "distance_miles": null,
        "year_built": null,
        "total_units": null,
        "occupancy_pct": null,
        "avg_rent": null,
        "avg_rent_psf": null,
        "amenities_notes": ""
      }
    ],
    "sales_comps": [
      {
        "property_name": "",
        "sale_date": "",
        "sale_price": null,
        "price_per_unit": null,
        "cap_rate": null,
        "total_units": null,
        "year_built": null
      }
    ],
    "location_highlights": {
      "walk_score": null,
      "transit_score": null,
      "nearby_amenities": [],
      "school_ratings": "",
      "proximity_highlights": []
    }
  },
  "page_5_broker_assumptions": {
    "investment_highlights_as_stated": [
      "List the key investment highlights exactly as the broker presents them"
    ],
    "value_add_strategy_as_stated": "",
    "broker_pro_forma_assumptions": {
      "rent_premiums_after_renovation": null,
      "target_occupancy_pct": null,
      "projected_rent_growth_annual_pct": null,
      "projected_expense_growth_annual_pct": null,
      "projected_noi_year_1": null,
      "projected_noi_stabilized": null,
      "projected_cap_rate_exit": null,
      "projected_hold_period": null,
      "projected_irr": null,
      "projected_equity_multiple": null
    },
    "broker_credibility_assessment": "Assess whether the broker's projections seem reasonable, aggressive, or conservative based on the market data and comps provided in the OM.",
    "assumptions_vs_actuals_gaps": [
      "List specific gaps between the broker's forward-looking assumptions and the actual historical or current performance data in the OM"
    ],
    "broker_contact": {
      "brokerage_firm": "",
      "lead_broker": "",
      "phone": "",
      "email": ""
    }
  }
}

IMPORTANT INSTRUCTIONS:
- Extract ONLY data that is explicitly stated in the OM or directly calculable from stated figures.
- For any field you cannot determine, use null.
- All dollar amounts should be numbers (not strings), without dollar signs or commas.
- All percentages should be expressed as decimals (e.g., 95% = 0.95).
- The SWOT analysis and transparency report should reflect YOUR expert assessment, not just parrot the broker's language.
- If the OM contains a T-12 (trailing 12-month) financial statement, extract those line items into historical_financials.
- If the OM provides a unit mix table, extract every row into the unit_mix array.
- For lease expiration, capture whatever granularity the OM provides.
- For rent and sales comps, extract all that are provided.
- Return ONLY the JSON object. No markdown, no commentary, no code fences."""


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCIAL MODEL
# ═══════════════════════════════════════════════════════════════════════════════

def build_cash_flow_model(extracted, scenario="base"):
    fin = extracted.get("page_2_financials", {})
    kpis = extracted.get("page_1_overview", {}).get("kpis", {})
    broker = fin.get("broker_assumptions", {})

    purchase_price = kpis.get("asking_price") or 0
    noi_year0 = fin.get("noi", {}).get("in_place_noi") or fin.get("noi", {}).get("pro_forma_noi") or kpis.get("in_place_noi") or 0
    debt = fin.get("debt_assumptions_from_om", {})
    ltv = debt.get("ltv_pct") or 0.65
    interest_rate = debt.get("interest_rate_pct") or 0.065
    amort_years = debt.get("amortization_years") or 30
    io_period = debt.get("interest_only_period_years") or 0
    capex_total = fin.get("capital_expenditures", {}).get("total_capex_budget") or 0

    scenarios = {
        "base": {
            "rent_growth": broker.get("rent_growth_pct") or 0.03,
            "expense_growth": broker.get("expense_growth_pct") or 0.02,
            "exit_cap": broker.get("exit_cap_rate") or (kpis.get("in_place_cap_rate") or 0.055) + 0.001,
            "vacancy": broker.get("vacancy_assumption_pct") or 0.05,
        },
        "upside": {
            "rent_growth": (broker.get("rent_growth_pct") or 0.03) + 0.01,
            "expense_growth": (broker.get("expense_growth_pct") or 0.02) - 0.005,
            "exit_cap": (broker.get("exit_cap_rate") or 0.055) - 0.0025,
            "vacancy": (broker.get("vacancy_assumption_pct") or 0.05) - 0.02,
        },
        "downside": {
            "rent_growth": (broker.get("rent_growth_pct") or 0.03) - 0.01,
            "expense_growth": (broker.get("expense_growth_pct") or 0.02) + 0.01,
            "exit_cap": (broker.get("exit_cap_rate") or 0.055) + 0.005,
            "vacancy": (broker.get("vacancy_assumption_pct") or 0.05) + 0.03,
        },
    }

    s = scenarios[scenario]
    loan_amount = purchase_price * ltv
    equity = purchase_price - loan_amount + capex_total

    if interest_rate > 0 and loan_amount > 0:
        monthly_rate = interest_rate / 12
        n_payments = amort_years * 12
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
        annual_debt_service = monthly_payment * 12
        io_annual_debt_service = loan_amount * interest_rate
    else:
        annual_debt_service = 0
        io_annual_debt_service = 0

    loan_balance = loan_amount
    loan_schedule = []
    cash_flows = []
    noi = noi_year0

    for year in range(0, 11):
        if year == 0:
            cash_flows.append({
                "Year": 0, "NOI": 0, "Yield": 0, "CapEx": -capex_total,
                "CF Pre-Debt": -capex_total, "Debt Service": 0, "DSCR": 0,
                "CF Post-Debt": -capex_total, "Sale Proceeds": 0,
                "Loan Repayment": 0, "Levered CF": -equity, "CoC": 0,
            })
            loan_schedule.append({"Year": 0, "Beg Balance": 0, "Interest": 0, "Principal": 0, "End Balance": loan_amount})
            continue

        noi = noi * (1 + s["rent_growth"]) if year > 1 else noi_year0
        year_capex = (capex_total / 2) if capex_total > 0 and year <= 2 else 0
        ds = io_annual_debt_service if year <= io_period else annual_debt_service
        year_interest = loan_balance * interest_rate
        year_principal = 0 if year <= io_period else ds - year_interest
        new_balance = loan_balance - year_principal
        loan_schedule.append({"Year": year, "Beg Balance": round(loan_balance), "Interest": round(year_interest), "Principal": round(year_principal), "End Balance": round(new_balance)})
        loan_balance = new_balance

        dscr = noi / ds if ds > 0 else 0
        cf_before_debt = noi - year_capex
        cf_after_debt = cf_before_debt - ds
        net_sale = 0
        loan_repay = 0
        if year == 10:
            exit_value = noi * (1 + s["rent_growth"]) / s["exit_cap"]
            net_sale = exit_value * 0.98
            loan_repay = -loan_balance

        levered_cf = cf_after_debt + net_sale + loan_repay if year == 10 else cf_after_debt
        coc = cf_after_debt / equity if equity > 0 else 0

        cash_flows.append({
            "Year": year, "NOI": round(noi), "Yield": round(noi / purchase_price, 4) if purchase_price > 0 else 0,
            "CapEx": round(-year_capex), "CF Pre-Debt": round(cf_before_debt),
            "Debt Service": round(-ds), "DSCR": round(dscr, 2),
            "CF Post-Debt": round(cf_after_debt), "Sale Proceeds": round(net_sale),
            "Loan Repayment": round(loan_repay), "Levered CF": round(levered_cf),
            "CoC": round(coc, 4),
        })

    levered_cfs = [cf["Levered CF"] for cf in cash_flows]
    levered_cfs[0] = -equity
    try:
        irr = npf.irr(levered_cfs)
    except:
        irr = None

    total_distributions = sum(cf["Levered CF"] for cf in cash_flows[1:])
    equity_multiple = (equity + total_distributions) / equity if equity > 0 else 0

    # Sensitivity
    exit_cap_adjustments = [-0.01, -0.005, 0, 0.005, 0.01]
    rent_growth_adjustments = [-0.02, -0.01, 0, 0.01, 0.02]
    irr_sensitivity = []
    for ec_adj in exit_cap_adjustments:
        row = {"Exit Cap": f"{(s['exit_cap'] + ec_adj)*100:.1f}%"}
        for rg_adj in rent_growth_adjustments:
            test_noi_s = noi_year0
            test_balance = loan_amount
            test_cfs = [-equity]
            for y in range(1, 11):
                test_noi_s = test_noi_s * (1 + s["rent_growth"] + rg_adj) if y > 1 else noi_year0
                yc = (capex_total / 2) if capex_total > 0 and y <= 2 else 0
                ds_y = io_annual_debt_service if y <= io_period else annual_debt_service
                yi = test_balance * interest_rate
                yp = 0 if y <= io_period else ds_y - yi
                test_balance -= yp
                cf_ = test_noi_s - yc - ds_y
                if y == 10:
                    ev = test_noi_s * (1 + s["rent_growth"] + rg_adj) / (s["exit_cap"] + ec_adj)
                    test_cfs.append(cf_ + ev * 0.98 - test_balance)
                else:
                    test_cfs.append(cf_)
            try:
                t_irr = round(npf.irr(test_cfs) * 100, 1)
            except:
                t_irr = None
            row[f"RG {(s['rent_growth'] + rg_adj)*100:.1f}%"] = t_irr
        irr_sensitivity.append(row)

    # Scenario returns by LTV
    equity_scenarios = []
    for ltv_test in [0.50, 0.55, 0.60, 0.65, 0.70, 0.75]:
        test_loan = purchase_price * ltv_test
        test_equity = purchase_price - test_loan + capex_total
        if interest_rate > 0 and test_loan > 0:
            mr = interest_rate / 12
            np_ = amort_years * 12
            mp = test_loan * (mr * (1 + mr)**np_) / ((1 + mr)**np_ - 1)
            test_ds = mp * 12
        else:
            test_ds = 0
        test_coc = (noi_year0 - test_ds) / test_equity if test_equity > 0 else 0
        t_noi = noi_year0
        t_bal = test_loan
        test_cfs_s = [-test_equity]
        for y in range(1, 11):
            t_noi = t_noi * (1 + s["rent_growth"]) if y > 1 else noi_year0
            yc = (capex_total / 2) if capex_total > 0 and y <= 2 else 0
            yi = t_bal * interest_rate
            yp = test_ds - yi
            t_bal -= yp
            cf_ = t_noi - yc - test_ds
            if y == 10:
                ev = t_noi * (1 + s["rent_growth"]) / s["exit_cap"]
                test_cfs_s.append(cf_ + ev * 0.98 - t_bal)
            else:
                test_cfs_s.append(cf_)
        try:
            t_irr = npf.irr(test_cfs_s)
        except:
            t_irr = None
        t_total = sum(test_cfs_s[1:])
        t_mult = (test_equity + t_total) / test_equity if test_equity > 0 else 0
        equity_scenarios.append({
            "LTV": f"{ltv_test*100:.0f}%", "Equity": f"${test_equity:,.0f}",
            "CoC Yr1": f"{test_coc*100:.1f}%", "Net Profit": f"${(t_total - test_equity):,.0f}",
            "IRR": f"{t_irr*100:.1f}%" if t_irr else "N/A", "Multiple": f"{t_mult:.2f}x",
        })

    return {
        "scenario": scenario, "assumptions": s,
        "purchase_price": purchase_price, "equity": round(equity),
        "loan_amount": round(loan_amount), "annual_ds": round(annual_debt_service),
        "cash_flows": cash_flows, "irr": irr, "equity_multiple": round(equity_multiple, 2),
        "net_profit": round(total_distributions - equity),
        "irr_sensitivity": irr_sensitivity, "equity_scenarios": equity_scenarios,
        "loan_schedule": loan_schedule,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def fmt_d(val):
    if val is None: return "N/A"
    if abs(val) >= 1_000_000: return f"${val/1_000_000:,.1f}M"
    return f"${val:,.0f}"

def fmt_p(val):
    if val is None: return "N/A"
    return f"{val*100:.1f}%"

def render_kpi(label, value):
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-value">{value}</p>
        <p class="kpi-label">{label}</p>
    </div>
    """, unsafe_allow_html=True)

def render_swot_box(title, items, css_class):
    items_html = "".join([f"<li>{item}</li>" for item in items]) if items else "<li>N/A</li>"
    st.markdown(f"""
    <div class="swot-box {css_class}">
        <h4>{title}</h4>
        <ul style="padding-left: 1.2rem; margin: 0;">{items_html}</ul>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_om(pdf_bytes):
   client = anthropic.Anthropic(api_key=st.secrets.get("ANTHROPIC_API_KEY", None))
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                {"type": "text", "text": "Analyze this Offering Memorandum and return the structured JSON as specified."},
            ],
        }],
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0]

    return json.loads(response_text)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div class="main-header">
    <h1>🏢 Multifamily OM Analyzer</h1>
    <p>Upload an Offering Memorandum and get instant investment analysis</p>
</div>
""", unsafe_allow_html=True)

# Session state
if "extracted" not in st.session_state:
    st.session_state.extracted = None
if "models" not in st.session_state:
    st.session_state.models = None

# ─── Upload Section ───
if st.session_state.extracted is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Drop your Offering Memorandum here",
            type=["pdf"],
            label_visibility="visible",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_file:
            with st.status("Analyzing your OM...", expanded=True) as status:
                st.write("📤 Sending PDF to Claude for extraction...")
                try:
                    extracted = extract_om(uploaded_file.read())
                    st.write("✅ Data extracted successfully")

                    st.write("📊 Running financial models...")
                    models = {
                        "base": build_cash_flow_model(extracted, "base"),
                        "upside": build_cash_flow_model(extracted, "upside"),
                        "downside": build_cash_flow_model(extracted, "downside"),
                    }
                    st.write("✅ All scenarios calculated")

                    st.session_state.extracted = extracted
                    st.session_state.models = models
                    status.update(label="Analysis complete!", state="complete")
                    st.rerun()

                except json.JSONDecodeError:
                    st.error("Failed to parse Claude's response. The OM may be too complex or in an unusual format. Try again.")
                except anthropic.AuthenticationError:
                    st.error("Invalid API key. Check your ANTHROPIC_API_KEY.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

else:
    # ─── We have data — show the analysis ───
    extracted = st.session_state.extracted
    models = st.session_state.models

    overview = extracted.get("page_1_overview", {})
    prop = overview.get("property_summary", {})
    kpis = overview.get("kpis", {})
    swot = overview.get("swot_analysis", {})
    transparency = overview.get("deal_transparency_report", {})

    # Sidebar: reset button
    with st.sidebar:
        st.markdown("### Options")
        if st.button("🔄 Analyze New OM", use_container_width=True):
            st.session_state.extracted = None
            st.session_state.models = None
            st.rerun()

        st.markdown("---")
        # Download JSON
        json_str = json.dumps({"extracted": extracted, "models": {k: {kk: vv for kk, vv in v.items() if kk != "assumptions"} for k, v in models.items()}}, indent=2, default=str)
        st.download_button("📥 Download Raw JSON", json_str, file_name="om_analysis.json", mime="application/json", use_container_width=True)

    # ─── Tabs for 5 pages ───
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overview", "💰 Financials", "📄 Lease Analysis", "🏙️ Market", "🤝 Broker Assumptions"
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1: OVERVIEW
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tab1:
        st.markdown(f'<div class="section-header">{prop.get("property_name", "Property Overview")}</div>', unsafe_allow_html=True)

        # Property details
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            **Address:** {prop.get('address', 'N/A')}, {prop.get('city', '')}, {prop.get('state', '')} {prop.get('zip', '')}
            **Year Built:** {prop.get('year_built', 'N/A')} | **Renovated:** {prop.get('year_renovated', 'N/A')}
            **Type:** {prop.get('property_type', 'N/A')} | **Construction:** {prop.get('construction_type', 'N/A')}
            """)
        with c2:
            st.markdown(f"""
            **Total Units:** {prop.get('total_units', 'N/A')} | **Total SF:** {f"{prop.get('total_sf'):,.0f}" if prop.get('total_sf') else 'N/A'}
            **Buildings:** {prop.get('number_of_buildings', 'N/A')} | **Stories:** {prop.get('number_of_stories', 'N/A')}
            **Parking:** {prop.get('parking_spaces', 'N/A')} | **Lot:** {prop.get('lot_size_acres', 'N/A')} acres
            """)

        # Executive Summary
        desc = overview.get("description", "")
        if desc:
            st.info(desc)

        # KPIs
        st.markdown('<div class="subsection-header">Key Performance Indicators</div>', unsafe_allow_html=True)
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1: render_kpi("Asking Price", fmt_d(kpis.get('asking_price')))
        with k2: render_kpi("Price/Unit", fmt_d(kpis.get('price_per_unit')))
        with k3: render_kpi("Occupancy", fmt_p(kpis.get('current_occupancy_pct')))
        with k4: render_kpi("In-Place NOI", fmt_d(kpis.get('in_place_noi')))
        with k5: render_kpi("Cap Rate", fmt_p(kpis.get('in_place_cap_rate')))
        with k6: render_kpi("Avg Rent/SF", f"${kpis.get('average_rent_psf', 0):.2f}" if kpis.get('average_rent_psf') else "N/A")

        st.markdown("")

        # Key Features
        features = overview.get("key_features", [])
        if features:
            with st.expander("🔑 Key Features", expanded=True):
                for f in features:
                    st.markdown(f"- {f}")

        # SWOT
        st.markdown('<div class="subsection-header">SWOT Analysis</div>', unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        with s1: render_swot_box("Strengths", swot.get("strengths", []), "swot-strength")
        with s2: render_swot_box("Weaknesses", swot.get("weaknesses", []), "swot-weakness")
        with s3: render_swot_box("Opportunities", swot.get("opportunities", []), "swot-opportunity")
        with s4: render_swot_box("Threats", swot.get("threats", []), "swot-threat")

        st.markdown("")

        # Transparency Report
        with st.expander("🔍 Deal Transparency Report", expanded=True):
            score = transparency.get("data_completeness_score", "N/A")
            st.markdown(f"**Data Completeness:** {score}/10")

            flags = transparency.get("red_flags", [])
            if flags:
                st.markdown("**Red Flags:**")
                for flag in flags:
                    st.markdown(f'<div class="red-flag">🚩 {flag}</div>', unsafe_allow_html=True)

            verify = transparency.get("assumptions_to_verify", [])
            if verify:
                st.markdown("**Assumptions to Verify:**")
                for v in verify:
                    st.markdown(f"- ❓ {v}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 2: FINANCIALS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tab2:
        st.markdown('<div class="section-header">Financial Analysis</div>', unsafe_allow_html=True)

        # Scenario selector
        scenario = st.radio("Select Scenario", ["base", "upside", "downside"], horizontal=True, index=0)
        m = models[scenario]

        # Top metrics
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1: render_kpi("Purchase Price", fmt_d(m['purchase_price']))
        with m2: render_kpi("Equity", fmt_d(m['equity']))
        with m3: render_kpi("Loan", fmt_d(m['loan_amount']))
        with m4: render_kpi("IRR", f"{m['irr']*100:.1f}%" if m['irr'] else "N/A")
        with m5: render_kpi("Eq Multiple", f"{m['equity_multiple']:.2f}x")
        with m6: render_kpi("Net Profit", fmt_d(m['net_profit']))

        st.markdown("")

        # Assumptions
        with st.expander("📐 Scenario Assumptions"):
            a1, a2, a3, a4 = st.columns(4)
            with a1: st.metric("Rent Growth", f"{m['assumptions']['rent_growth']*100:.1f}%")
            with a2: st.metric("Expense Growth", f"{m['assumptions']['expense_growth']*100:.1f}%")
            with a3: st.metric("Exit Cap Rate", f"{m['assumptions']['exit_cap']*100:.2f}%")
            with a4: st.metric("Vacancy", f"{m['assumptions']['vacancy']*100:.1f}%")

        # Scenario Comparison
        st.markdown('<div class="subsection-header">Scenario Comparison</div>', unsafe_allow_html=True)
        comp_data = {
            "Metric": ["IRR", "Equity Multiple", "Net Profit"],
            "🔴 Downside": [
                f"{models['downside']['irr']*100:.1f}%" if models['downside']['irr'] else "N/A",
                f"{models['downside']['equity_multiple']:.2f}x",
                fmt_d(models['downside']['net_profit']),
            ],
            "📊 Base Case": [
                f"{models['base']['irr']*100:.1f}%" if models['base']['irr'] else "N/A",
                f"{models['base']['equity_multiple']:.2f}x",
                fmt_d(models['base']['net_profit']),
            ],
            "🟢 Upside": [
                f"{models['upside']['irr']*100:.1f}%" if models['upside']['irr'] else "N/A",
                f"{models['upside']['equity_multiple']:.2f}x",
                fmt_d(models['upside']['net_profit']),
            ],
        }
        st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

        # Cash Flow Table
        st.markdown('<div class="subsection-header">10-Year Cash Flow Projection</div>', unsafe_allow_html=True)
        cf_df = pd.DataFrame(m["cash_flows"])
        display_cf = cf_df.copy()
        for col in ["NOI", "CapEx", "CF Pre-Debt", "Debt Service", "CF Post-Debt", "Sale Proceeds", "Loan Repayment", "Levered CF"]:
            if col in display_cf.columns:
                display_cf[col] = display_cf[col].apply(lambda x: fmt_d(x) if x != 0 else "—")
        display_cf["Yield"] = display_cf["Yield"].apply(lambda x: f"{x*100:.1f}%" if x else "—")
        display_cf["DSCR"] = display_cf["DSCR"].apply(lambda x: f"{x:.2f}x" if x else "—")
        display_cf["CoC"] = display_cf["CoC"].apply(lambda x: f"{x*100:.1f}%" if x else "—")
        st.dataframe(display_cf, use_container_width=True, hide_index=True)

        # Scenario Returns by LTV
        st.markdown('<div class="subsection-header">Scenario Returns by Leverage</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(m["equity_scenarios"]), use_container_width=True, hide_index=True)

        # IRR Sensitivity
        st.markdown('<div class="subsection-header">IRR Sensitivity (Exit Cap vs Rent Growth)</div>', unsafe_allow_html=True)
        sens_df = pd.DataFrame(m["irr_sensitivity"])
        st.dataframe(sens_df, use_container_width=True, hide_index=True)

        # Loan Schedule
        with st.expander("🏦 Annual Loan Summary"):
            loan_df = pd.DataFrame(m["loan_schedule"])
            for col in ["Beg Balance", "Interest", "Principal", "End Balance"]:
                loan_df[col] = loan_df[col].apply(lambda x: fmt_d(x))
            st.dataframe(loan_df, use_container_width=True, hide_index=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 3: LEASE ANALYSIS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tab3:
        st.markdown('<div class="section-header">Lease Analysis</div>', unsafe_allow_html=True)
        lease = extracted.get("page_3_lease_analysis", {})

        # Unit Mix
        unit_mix = lease.get("unit_mix", [])
        if unit_mix:
            st.markdown('<div class="subsection-header">Unit Mix</div>', unsafe_allow_html=True)
            um_df = pd.DataFrame(unit_mix)
            um_df.columns = [c.replace("_", " ").title() for c in um_df.columns]
            st.dataframe(um_df, use_container_width=True, hide_index=True)

        # Occupancy
        occ = lease.get("occupancy", {})
        if occ:
            st.markdown('<div class="subsection-header">Occupancy</div>', unsafe_allow_html=True)
            o1, o2, o3, o4 = st.columns(4)
            with o1: render_kpi("Current", fmt_p(occ.get('current_occupancy_pct')))
            with o2: render_kpi("Vacant Units", str(occ.get('physical_vacancy_units', 'N/A')))
            with o3: render_kpi("Economic", fmt_p(occ.get('economic_occupancy_pct')))
            with o4: render_kpi("12-Mo Avg", fmt_p(occ.get('average_occupancy_12mo')))

        st.markdown("")

        # Lease Expiration
        les = lease.get("lease_expiration_schedule", [])
        if les:
            st.markdown('<div class="subsection-header">Lease Expiration Schedule</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(les), use_container_width=True, hide_index=True)

        # Lease Abstraction
        la = lease.get("lease_abstraction", {})
        if la:
            with st.expander("📋 Lease Abstraction", expanded=True):
                st.markdown(f"""
                **Standard Term:** {la.get('standard_lease_term_months', 'N/A')} months |
                **Escalation:** {la.get('typical_escalation_structure', 'N/A')} |
                **Pet Policy:** {la.get('pet_policy', 'N/A')}
                """)
                provisions = la.get("notable_lease_provisions", [])
                if provisions:
                    for p in provisions:
                        st.markdown(f"- {p}")

        # Rent Roll
        rr = lease.get("rent_roll_summary", {})
        if rr:
            st.markdown('<div class="subsection-header">Rent Roll Summary</div>', unsafe_allow_html=True)
            r1, r2, r3, r4, r5 = st.columns(5)
            with r1: render_kpi("Monthly Total", fmt_d(rr.get('total_monthly_rent')))
            with r2: render_kpi("Annual Total", fmt_d(rr.get('total_annual_rent')))
            with r3: render_kpi("Highest Unit", fmt_d(rr.get('highest_rent_unit')))
            with r4: render_kpi("Lowest Unit", fmt_d(rr.get('lowest_rent_unit')))
            with r5: render_kpi("Median Rent", fmt_d(rr.get('median_rent')))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 4: MARKET
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tab4:
        st.markdown('<div class="section-header">Market Analysis</div>', unsafe_allow_html=True)
        market = extracted.get("page_4_market_analysis", {})

        mo = market.get("market_overview", {})
        if mo:
            st.markdown('<div class="subsection-header">Market Overview</div>', unsafe_allow_html=True)
            mk1, mk2, mk3, mk4 = st.columns(4)
            with mk1: render_kpi("MSA", mo.get('msa', 'N/A'))
            with mk2: render_kpi("Population", f"{mo.get('population'):,.0f}" if mo.get('population') else "N/A")
            with mk3: render_kpi("Med HH Income", fmt_d(mo.get('median_household_income')))
            with mk4: render_kpi("Unemployment", fmt_p(mo.get('unemployment_rate_pct')))

            st.markdown("")
            employers = mo.get("major_employers", [])
            if employers:
                st.markdown(f"**Major Employers:** {', '.join(employers)}")
            drivers = mo.get("economic_drivers", "")
            if drivers:
                st.markdown(f"**Economic Drivers:** {drivers}")

        sub = market.get("submarket_overview", {})
        if sub:
            st.markdown(f'<div class="subsection-header">Submarket: {sub.get("submarket_name", "N/A")}</div>', unsafe_allow_html=True)
            sb1, sb2, sb3, sb4 = st.columns(4)
            with sb1: render_kpi("Vacancy", fmt_p(sub.get('submarket_vacancy_pct')))
            with sb2: render_kpi("Avg Rent", fmt_d(sub.get('submarket_avg_rent')))
            with sb3: render_kpi("Rent Growth", fmt_p(sub.get('submarket_rent_growth_pct')))
            with sb4: render_kpi("Pipeline", f"{sub.get('pipeline_under_construction_units'):,.0f}" if sub.get('pipeline_under_construction_units') else "N/A")

        st.markdown("")

        comps = market.get("rent_comps", [])
        if comps:
            st.markdown('<div class="subsection-header">Rent Comps</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(comps), use_container_width=True, hide_index=True)

        scomps = market.get("sales_comps", [])
        if scomps:
            st.markdown('<div class="subsection-header">Sales Comps</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(scomps), use_container_width=True, hide_index=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 5: BROKER ASSUMPTIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tab5:
        st.markdown('<div class="section-header">Broker Assumptions & Assessment</div>', unsafe_allow_html=True)
        bp = extracted.get("page_5_broker_assumptions", {})

        highlights = bp.get("investment_highlights_as_stated", [])
        if highlights:
            with st.expander("💡 Investment Highlights (as stated by broker)", expanded=True):
                for h in highlights:
                    st.markdown(f"- {h}")

        vas = bp.get("value_add_strategy_as_stated", "")
        if vas:
            st.markdown('<div class="subsection-header">Value-Add Strategy</div>', unsafe_allow_html=True)
            st.info(vas)

        bpf = bp.get("broker_pro_forma_assumptions", {})
        if bpf:
            st.markdown('<div class="subsection-header">Broker Pro Forma Assumptions</div>', unsafe_allow_html=True)
            bp1, bp2, bp3, bp4 = st.columns(4)
            with bp1:
                render_kpi("Rent Premium", fmt_d(bpf.get('rent_premiums_after_renovation')))
                render_kpi("Year 1 NOI", fmt_d(bpf.get('projected_noi_year_1')))
            with bp2:
                render_kpi("Target Occ", fmt_p(bpf.get('target_occupancy_pct')))
                render_kpi("Stabilized NOI", fmt_d(bpf.get('projected_noi_stabilized')))
            with bp3:
                render_kpi("Rent Growth", fmt_p(bpf.get('projected_rent_growth_annual_pct')))
                render_kpi("Exit Cap", fmt_p(bpf.get('projected_cap_rate_exit')))
            with bp4:
                render_kpi("Projected IRR", fmt_p(bpf.get('projected_irr')))
                render_kpi("Eq Multiple", f"{bpf.get('projected_equity_multiple'):.2f}x" if bpf.get('projected_equity_multiple') else "N/A")

        st.markdown("")

        cred = bp.get("broker_credibility_assessment", "")
        if cred:
            st.markdown('<div class="subsection-header">Credibility Assessment</div>', unsafe_allow_html=True)
            st.warning(cred)

        gaps = bp.get("assumptions_vs_actuals_gaps", [])
        if gaps:
            st.markdown('<div class="subsection-header">Assumptions vs. Actuals Gaps</div>', unsafe_allow_html=True)
            for g in gaps:
                st.markdown(f'<div class="red-flag">⚠️ {g}</div>', unsafe_allow_html=True)

        contact = bp.get("broker_contact", {})
        if contact and contact.get("brokerage_firm"):
            st.markdown('<div class="subsection-header">Broker Contact</div>', unsafe_allow_html=True)
            st.markdown(f"""
            **Firm:** {contact.get('brokerage_firm', 'N/A')} |
            **Broker:** {contact.get('lead_broker', 'N/A')} |
            **Phone:** {contact.get('phone', 'N/A')} |
            **Email:** {contact.get('email', 'N/A')}
            """)
