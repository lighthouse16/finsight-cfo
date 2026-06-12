import os
import csv
import math
from typing import Optional
from app.models.advisory import PdEstimateResponse, PdFactorContribution

def _load_and_train_dataset() -> tuple[float, float, float, float, str, str]:
    # Look for dataset file in various locations
    paths = [
        "historical_default_dataset.csv",
        "backend/historical_default_dataset.csv",
        "demo_data/historical_default_dataset.csv",
        "backend/demo_data/historical_default_dataset.csv",
        "../historical_default_dataset.csv",
        "../demo_data/historical_default_dataset.csv"
    ]
    
    dataset_path = None
    for p in paths:
        if os.path.exists(p):
            dataset_path = p
            break
            
    if not dataset_path:
        # Fallback to default baseline coefficients
        return (
            -1.5, -2.0, 3.0, -4.0, 
            "indicative_readiness_index",
            "This is a deterministic logistic-style proxy for demonstration purposes only. It is not a calibrated production probability-of-default (PD) model. Indicative readiness index fallback is active."
        )
        
    # Read CSV records
    try:
        records = []
        with open(dataset_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dscr_val = float(row.get("dscr", 1.0))
                debt_ratio_val = float(row.get("debt_ratio", 0.5))
                margin_val = float(row.get("margin", 0.1))
                defaulted_val = int(row.get("defaulted", 0))
                records.append((dscr_val, debt_ratio_val, margin_val, defaulted_val))
                
        # Validate dataset size
        if len(records) < 5:
            raise ValueError("Dataset too small for calibration.")
            
        y_values = [r[3] for r in records]
        if sum(y_values) == 0 or sum(y_values) == len(records):
            raise ValueError("Dataset must contain both defaulted and non-defaulted samples.")
            
        # Fit logistic regression using gradient descent in pure Python
        b0 = -1.5
        b1 = -2.0
        b2 = 3.0
        b3 = -4.0
        
        lr = 0.05
        epochs = 1000
        N = len(records)
        
        for _ in range(epochs):
            g0, g1, g2, g3 = 0.0, 0.0, 0.0, 0.0
            for dscr_v, debt_v, marg_v, def_v in records:
                z = b0 + b1 * dscr_v + b2 * debt_v + b3 * marg_v
                # Sigmoid
                p = 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, z))))
                diff = p - def_v
                g0 += diff
                g1 += diff * dscr_v
                g2 += diff * debt_v
                g3 += diff * marg_v
                
            b0 -= lr * (g0 / N)
            b1 -= lr * (g1 / N)
            b2 -= lr * (g2 / N)
            b3 -= lr * (g3 / N)
            
        # Validate calibrated coefficients signs:
        # Higher DSCR should lower default probability (b1 < 0)
        # Higher Debt Ratio should increase default probability (b2 > 0)
        if b1 > 0 or b2 < 0:
            raise ValueError("Calibrated coefficients did not pass sign validation checks (DSCR coefficient must be negative, Debt Ratio coefficient must be positive).")
            
        disclaimer = (
            f"This model has been statistically calibrated using logistic regression baseline on '{os.path.basename(dataset_path)}'. "
            f"Fitted parameters: Intercept={b0:.2f}, DSCR={b1:.2f}, DebtRatio={b2:.2f}, Margin={b3:.2f}. "
            "No formal borrower approval/decline decisions are implied."
        )
        return b0, b1, b2, b3, "calibrated", disclaimer
        
    except Exception as e:
        # Fallback with warning in the disclaimer
        return (
            -1.5, -2.0, 3.0, -4.0,
            "indicative_readiness_index",
            f"Deterministic fallback active. Failed to calibrate model: {str(e)}"
        )

class ICalibratedPdModel:
    """
    Interface/Placeholder for future calibrated Probability of Default (PD) model.
    To be implemented when historical default data becomes available for calibration.
    """
    def calibrate(self, historical_data: list) -> None:
        raise NotImplementedError("Calibration requires historical default data and is not implemented.")

    def predict_calibrated_pd(self, features: dict) -> float:
        raise NotImplementedError("Predicting calibrated PD is not implemented. Use uncalibrated proxy.")

def calculate_pd(
    company_id: str,
    dscr: Optional[float],
    debt_ratio: Optional[float],
    margin: Optional[float],
    cdi_collateral_hkd: float = 0.0
) -> PdEstimateResponse:
    """
    Calculates a logistic-style Probability of Default (PD) score
    for BOCHK challenge Phase 3 advisory context, calibrated dynamically
    if a dataset is provided.
    
    Formula:
    Z = β0 + β1(DSCR) + β2(DebtRatio) + β3(Margin) + β4(CDI_Collateral_Adjustment)
    PD = 1 / (1 + e^-Z)
    """
    
    # Load coefficients (either calibrated or baseline fallback)
    b0, b1, b2, b3, cal_status, disclaimer = _load_and_train_dataset()
    
    # Defaults if missing to prevent math errors
    safe_dscr = dscr if dscr is not None and not math.isnan(dscr) else 1.0
    safe_debt_ratio = debt_ratio if debt_ratio is not None and not math.isnan(debt_ratio) else 0.5
    safe_margin = margin if margin is not None and not math.isnan(margin) else 0.1
    
    # CDI Collateral acts as a risk mitigant:
    # every 1M HKD in collateral lowers Z by 0.1
    b4_effect = -0.1 * (cdi_collateral_hkd / 1_000_000.0)
    
    # Factor contributions
    z_b0 = b0
    z_dscr = b1 * safe_dscr
    z_debt = b2 * safe_debt_ratio
    z_margin = b3 * safe_margin
    z_cdi = b4_effect
    
    z_score = z_b0 + z_dscr + z_debt + z_margin + z_cdi
    
    # Cap Z to avoid overflow
    z_score_capped = max(-10.0, min(10.0, z_score))
    
    pd_raw = 1.0 / (1.0 + math.exp(-z_score_capped))
    
    # Map to tiers A-E
    if pd_raw < 0.02:
        tier = "Planning Tier A (Excellent)"
    elif pd_raw < 0.05:
        tier = "Planning Tier B (Good)"
    elif pd_raw < 0.10:
        tier = "Planning Tier C (Adequate)"
    elif pd_raw < 0.20:
        tier = "Planning Tier D (Elevated)"
    else:
        tier = "Planning Tier E (High Risk)"
        
    # Map to 0-100 score (lower PD = higher score)
    score_100 = int(max(0, min(100, 100 - (pd_raw * 200))))
    
    factors = [
        PdFactorContribution(factor="Base Intercept", value=1.0, contribution=z_b0),
        PdFactorContribution(factor="DSCR", value=safe_dscr, contribution=z_dscr),
        PdFactorContribution(factor="Debt Ratio", value=safe_debt_ratio, contribution=z_debt),
        PdFactorContribution(factor="Operating Margin", value=safe_margin, contribution=z_margin),
        PdFactorContribution(factor="CDI Alternative Collateral mitigant", value=cdi_collateral_hkd, contribution=z_cdi)
    ]
    
    pd_assumptions = [
        "Base intercept represents long-run baseline default expectation.",
        "DSCR coefficients imply higher coverage capacity reduces probability of default.",
        "Debt ratio coefficient implies higher leverage increases probability of default.",
        "Operating margin coefficient implies higher operating profitability reduces default probability.",
        "CDI collateral acts as a linear credit mitigant to lower default probability score."
    ]
    
    pd_limitations = [
        "Not calibrated to historical default data.",
        "Not a formal credit decision."
    ]
    
    pd_data_quality = {
        "dscr_available": dscr is not None,
        "debt_ratio_available": debt_ratio is not None,
        "margin_available": margin is not None,
        "cdi_collateral_used": cdi_collateral_hkd > 0
    }
    
    confidence_band = "medium" if (dscr is not None and debt_ratio is not None and margin is not None) else "low"
    return PdEstimateResponse(
        company_id=company_id,
        z_score=z_score,
        probability_default=pd_raw,
        tier=tier,
        score=score_100,
        factor_contributions=factors,
        disclaimer=disclaimer,
        calibration_status=cal_status,
        model_version="1.0.0",
        model_type="indicative_pd_proxy",
        assumptions=pd_assumptions,
        limitations=pd_limitations,
        data_quality=pd_data_quality,
        confidence_band=confidence_band
    )

