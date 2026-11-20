"""Hand-written content for the synthetic bank: organization, taxonomies and risk concepts.

Each RiskConcept is one underlying risk. The generator decides which concepts appear in
ERM, in IA, in both (a true cross-source match) or twice in ERM (a within-ERM duplicate),
and writes each source's item in that source's own voice. ERM writes RCSA-style risk
statements; IA writes audit-universe style entries. The same concept never produces the
same sentence in two items, so matching has to work from meaning, not copy.

All institution, people, vendor and system names come from names/*.txt (INV-9).
"""
from dataclasses import dataclass, field

SEGMENTS = [
    "Consumer Banking", "Commercial Banking", "Wealth Management", "Treasury & Markets",
    "Operations", "Technology", "Corporate Functions",
]

# business unit -> segment
BUSINESS_UNITS = {
    "Retail Branch Network": "Consumer Banking",
    "Consumer Lending": "Consumer Banking",
    "Card Services": "Consumer Banking",
    "Commercial Lending": "Commercial Banking",
    "Treasury Management Services": "Commercial Banking",
    "Private Wealth Advisory": "Wealth Management",
    "Corporate Treasury": "Treasury & Markets",
    "Payment Operations": "Operations",
    "Deposit Operations": "Operations",
    "Enterprise Technology": "Technology",
    "Finance": "Corporate Functions",
    "Compliance": "Corporate Functions",
}

# auditable entity -> owning business unit (INV-2: exactly one)
AUDITABLE_ENTITIES = {
    "Commercial Loan Origination": "Commercial Lending",
    "Consumer Mortgage Lending": "Consumer Lending",
    "Wire Transfer Operations": "Payment Operations",
    "ACH Operations": "Payment Operations",
    "Deposit Account Servicing": "Deposit Operations",
    "BSA/AML Program": "Compliance",
    "Treasury ALM": "Corporate Treasury",
    "Liquidity Management": "Corporate Treasury",
    "Identity & Access Management": "Enterprise Technology",
    "General Ledger & Financial Close": "Finance",
    "Customer Complaints Management": "Retail Branch Network",
    "Card Disputes": "Card Services",
    "New Product Approval": "Compliance",
    "Third-Party Risk Management": "Finance",
    "Wealth Client Onboarding": "Private Wealth Advisory",
}

# process -> (auditable entity that performs it, systems it runs on)
PROCESSES = {
    "Loan application intake": ("Commercial Loan Origination", ["Halbrook Loan Origination"]),
    "Credit underwriting and approval": ("Commercial Loan Origination", ["Halbrook Loan Origination"]),
    "Mortgage underwriting": ("Consumer Mortgage Lending", ["Halbrook Loan Origination"]),
    "Wire initiation and release": ("Wire Transfer Operations", ["Brisance Wire Manager", "Corvessa Core Banking"]),
    "ACH file origination": ("ACH Operations", ["Quorvane Payments Hub"]),
    "Manual account adjustments": ("Deposit Account Servicing", ["Corvessa Core Banking"]),
    "Payment suspense reconciliation": ("General Ledger & Financial Close", ["Velistra General Ledger", "Quorvane Payments Hub"]),
    "Transaction monitoring alert review": ("BSA/AML Program", ["Merrow AML Monitor", "Tessaly Case Manager"]),
    "Customer due diligence": ("BSA/AML Program", ["Corvessa Core Banking"]),
    "User access provisioning": ("Identity & Access Management", ["Okrin Identity Gateway"]),
    "Access recertification": ("Identity & Access Management", ["Okrin Identity Gateway"]),
    "Interest rate risk measurement": ("Treasury ALM", ["Pellmark ALM", "Ylvara Data Warehouse"]),
    "Contingency funding planning": ("Liquidity Management", ["Pellmark ALM"]),
    "Complaint intake and resolution": ("Customer Complaints Management", ["Tessaly Case Manager"]),
    "Card dispute processing": ("Card Disputes", ["Corvessa Core Banking", "Tessaly Case Manager"]),
    "New product review": ("New Product Approval", []),
    "Vendor onboarding": ("Third-Party Risk Management", []),
    "Wealth client onboarding": ("Wealth Client Onboarding", ["Corvessa Core Banking"]),
}

# system -> (vendor, criticality)
SYSTEMS = {
    "Corvessa Core Banking": ("Quorvane Systems", "High"),
    "Halbrook Loan Origination": ("Halbrook Data", "High"),
    "Pellmark ALM": ("Merrow Analytics", "Medium"),
    "Quorvane Payments Hub": ("Quorvane Systems", "High"),
    "Brisance Wire Manager": ("Velistra Software", "High"),
    "Ylvara Data Warehouse": ("Okrin Technologies", "Medium"),
    "Merrow AML Monitor": ("Merrow Analytics", "High"),
    "Okrin Identity Gateway": ("Okrin Technologies", "High"),
    "Velistra General Ledger": ("Velistra Software", "High"),
    "Tessaly Case Manager": ("Tessaly Labs", "Medium"),
}

# regulation -> citation, in priority order (a smaller --count REGULATION keeps the first N)
REGULATIONS = {
    "Bank Secrecy Act": "31 U.S.C. 5311 et seq.",
    "Sarbanes-Oxley Act Section 404": "15 U.S.C. 7262",
    "Regulation E (Electronic Fund Transfers)": "12 CFR Part 1005",
    "Gramm-Leach-Bliley Act": "15 U.S.C. 6801 et seq.",
    "OFAC Regulations": "31 CFR Chapter V",
    "Interagency Guidance on Third-Party Relationships": "88 FR 37920",
    "OCC Heightened Standards": "12 CFR Part 30, Appendix D",
    "Interagency Policy Statement on Funding and Liquidity Risk Management": "75 FR 13656",
    "Regulation Z (Truth in Lending)": "12 CFR Part 1026",
    "Interagency Appraisal and Evaluation Guidelines": "75 FR 77450",
    "UCC Article 4A (Funds Transfers)": "UCC Article 4A",
    "Nacha Operating Rules": "Nacha Operating Rules",
    "Dodd-Frank UDAAP Provisions": "12 U.S.C. 5531",
}

# ERM taxonomy (Basel-style), thin branch for the sample: (L1, L2, L3) paths.
ERM_TAXONOMY = [
    ("Credit", "Credit Risk Management", "Underwriting & Origination"),
    ("Market", "Interest Rate Risk", "Banking Book IRR"),
    ("Liquidity", "Funding Liquidity", "Contingency Funding"),
    ("Operational", "Process & Execution", "Transaction Processing"),
    ("Operational", "Technology", "Access & Identity"),
    ("Compliance", "Regulatory Compliance", "BSA/AML"),
    ("Strategic", "Business Strategy", "New Products & Initiatives"),
    ("Reputational", "Stakeholder Risk", "Customer Complaints"),
]

# IA legacy taxonomy: (L1, L2, L3) paths.
IA_TAXONOMY = [
    ("Lending", "Commercial Lending", "Loan Origination"),
    ("Treasury", "Asset/Liability Management", "Interest Rate & Liquidity"),
    ("Operations", "Payments", "Wire & ACH"),
    ("Regulatory Compliance", "Financial Crimes", "AML Monitoring"),
    ("Information Technology", "IT General Controls", "Access Management"),
    ("Customer", "Complaints", "Complaint Handling"),
    ("Corporate Governance", "Governance Oversight", "Project & Change Governance"),
]

# True mapping of each IA node (by level and name) to an ERM node (level, name), or None
# for unmapped. Never deeper than the IA node. Uneven on purpose: level mismatches
# (IA L2 -> ERM L1, IA L3 -> ERM L2) and a whole IA branch with no ERM home.
IA_TO_ERM = {
    (1, "Lending"): (1, "Credit"),
    (1, "Treasury"): (1, "Market"),
    (1, "Operations"): (1, "Operational"),
    (1, "Regulatory Compliance"): (1, "Compliance"),
    (1, "Information Technology"): (1, "Operational"),
    (1, "Customer"): (1, "Reputational"),
    (1, "Corporate Governance"): None,
    (2, "Commercial Lending"): (2, "Credit Risk Management"),
    (2, "Asset/Liability Management"): (1, "Market"),
    (2, "Payments"): (2, "Process & Execution"),
    (2, "Financial Crimes"): (2, "Regulatory Compliance"),
    (2, "IT General Controls"): (2, "Technology"),
    (2, "Complaints"): (2, "Stakeholder Risk"),
    (2, "Governance Oversight"): None,
    (3, "Loan Origination"): (3, "Underwriting & Origination"),
    (3, "Interest Rate & Liquidity"): (2, "Interest Rate Risk"),
    (3, "Wire & ACH"): (3, "Transaction Processing"),
    (3, "AML Monitoring"): (3, "BSA/AML"),
    (3, "Access Management"): (3, "Access & Identity"),
    (3, "Complaint Handling"): (2, "Stakeholder Risk"),
    (3, "Project & Change Governance"): None,
}


@dataclass(frozen=True)
class ControlConcept:
    erm_title: str
    erm: str            # ERM RCSA: one brief sentence
    ia_title: str
    ia: str             # IA RCM: detailed, several sentences
    control_type: str   # Preventive / Detective
    nature: str         # Manual / Automated / IT-dependent manual
    frequency: str
    systems: list = field(default_factory=list)
    regulation: str | None = None
    finding: str = ""   # how a test of this control fails, used for issues


@dataclass(frozen=True)
class RiskConcept:
    key: str
    erm_l3: str         # true ERM home (L3 name)
    ia_l3: str          # where IA files it (L3 name)
    rating: str         # inherent rating: High / Medium / Low
    entities: list      # auditable entities exposed to it
    erm_title: str
    erm: str            # clause for "Risk that ..."
    alt_title: str      # second ERM phrasing, used by within-ERM duplicates
    alt: str
    cause: str
    impact: str
    ia_title: str
    ia_focus: str
    control: ControlConcept


def _c(*args, **kwargs) -> ControlConcept:
    return ControlConcept(*args, **kwargs)


RISK_CONCEPTS = [
    RiskConcept(
        "uw_authority", "Underwriting & Origination", "Loan Origination", "High",
        ["Commercial Loan Origination"],
        "Credit approvals outside delegated authority",
        "loans are approved above the approver's delegated lending authority",
        "Approval limit breaches in commercial lending",
        "commercial credits close without the second signature required above the house limit",
        "manual overrides in the origination workflow",
        "unapproved credit exposure and higher loss severity",
        "Lending authority not enforced at approval",
        "approval matrix setup, override log, approvals above $5 million",
        _c("Lending authority hard-stop",
           "Origination system blocks booking when the approver's limit is exceeded.",
           "Approval matrix validation in loan origination system",
           "Halbrook Loan Origination compares the approver's delegated authority to the approval matrix "
           "before a loan can be booked. Overrides route to Credit Administration, which reviews the override "
           "log weekly and escalates unapproved items to the Chief Credit Officer.",
           "Preventive", "Automated", "Per transaction", ["Halbrook Loan Origination"],
           "OCC Heightened Standards",
           "The approval matrix was not updated after the March limit change; 3 of 40 sampled loans were "
           "approved above authority."),
    ),
    RiskConcept(
        "uw_collateral", "Underwriting & Origination", "Loan Origination", "Medium",
        ["Commercial Loan Origination", "Consumer Mortgage Lending"],
        "Inaccurate collateral valuation at origination",
        "collateral values used in underwriting are stale or unsupported by an independent appraisal",
        "Appraisal quality gaps",
        "appraisals are accepted without review of the appraiser's independence or comparable sales",
        "appraisal ordering handled by the loan officer",
        "understated loss given default",
        "Appraisal review and independence",
        "appraisal ordering process, review checklist, aged valuations",
        _c("Independent appraisal review",
           "Appraisals are reviewed by the valuation unit before closing.",
           "Valuation unit review of third-party appraisals",
           "The valuation unit orders appraisals through an approved panel and completes a review checklist "
           "covering comparable sales, appraiser independence and value support before the loan closes. "
           "Valuations older than 120 days are re-ordered.",
           "Detective", "Manual", "Per transaction", ["Halbrook Loan Origination"],
           "Interagency Appraisal and Evaluation Guidelines",
           "The review checklist was missing for 5 of 30 sampled closings, and two appraisals were ordered "
           "directly by the loan officer."),
    ),
    RiskConcept(
        "uw_income", "Underwriting & Origination", "Loan Origination", "Medium",
        ["Consumer Mortgage Lending"],
        "Borrower income not verified",
        "consumer loans are underwritten on stated income that is never verified",
        "Income documentation exceptions",
        "mortgage files close with missing tax returns or pay stubs",
        "exception tracking that relies on spreadsheets",
        "early payment defaults and repurchase demands",
        "Income verification in consumer underwriting",
        "file documentation checklist, exception aging, early payment defaults",
        _c("Income verification checklist",
           "Underwriters confirm income documents before approval.",
           "Pre-closing documentation checklist with exception tracking",
           "Underwriters complete the income verification checklist in Halbrook Loan Origination, and the "
           "system will not issue a clear-to-close until each item is received or an exception is approved "
           "by the underwriting manager. Open exceptions are reported weekly.",
           "Preventive", "IT-dependent manual", "Per transaction", ["Halbrook Loan Origination"],
           "Regulation Z (Truth in Lending)",
           "Exceptions were approved by the processing team rather than the underwriting manager for 4 of "
           "25 sampled files."),
    ),
    RiskConcept(
        "irr_model", "Banking Book IRR", "Interest Rate & Liquidity", "High",
        ["Treasury ALM"],
        "Interest rate risk model mis-specification",
        "the ALM model misstates earnings sensitivity because deposit assumptions are outdated",
        "Stale deposit beta assumptions",
        "deposit repricing betas used for earnings-at-risk have not been recalibrated since rates moved",
        "the lack of an annual assumption review",
        "hedging decisions based on misleading rate sensitivity",
        "ALM model assumptions and validation",
        "assumption governance, back-testing, model validation findings",
        _c("Annual ALM assumption approval",
           "ALCO approves key ALM assumptions each year.",
           "Assumption review and back-testing for the ALM model",
           "Treasury back-tests deposit betas and prepayment speeds in Pellmark ALM each quarter and presents "
           "variances above tolerance to ALCO. ALCO approves the assumption set annually, and Model Risk "
           "validates the model every two years.",
           "Detective", "Manual", "Quarterly", ["Pellmark ALM"], None,
           "Deposit betas were last recalibrated 26 months ago, and quarterly back-testing was not presented "
           "to ALCO in two quarters."),
    ),
    RiskConcept(
        "irr_limits", "Banking Book IRR", "Interest Rate & Liquidity", "Medium",
        ["Treasury ALM"],
        "Breach of interest rate risk limits",
        "economic value of equity sensitivity exceeds board limits without escalation",
        "EVE limit monitoring gaps",
        "limit breaches under rate shocks are identified late and never reported to the board",
        "manual compilation of the limit report",
        "unmanaged exposure to rising rates",
        "IRR limit monitoring and escalation",
        "limit framework, breach reporting, ALCO minutes",
        _c("Monthly IRR limit monitoring",
           "Treasury reports EVE and NII sensitivity against limits monthly.",
           "Limit breach escalation to ALCO and the Board Risk Committee",
           "Treasury produces the monthly rate shock report from Pellmark ALM and compares each scenario to "
           "board-approved limits. Breaches are escalated to ALCO within five business days and to the Board "
           "Risk Committee at its next meeting with a remediation plan.",
           "Detective", "IT-dependent manual", "Monthly", ["Pellmark ALM", "Ylvara Data Warehouse"], None,
           "A +300 bp EVE limit breach in June was reported to ALCO 19 days late and never reached the Board "
           "Risk Committee."),
    ),
    RiskConcept(
        "cfp_test", "Contingency Funding", "Interest Rate & Liquidity", "High",
        ["Liquidity Management"],
        "Contingency funding plan not executable",
        "contingency funding sources cannot be drawn in the time the plan assumes",
        "Untested contingent funding lines",
        "borrowing capacity at the Federal Home Loan Bank and the discount window has not been tested",
        "operational testing that is skipped when markets are calm",
        "a liquidity shortfall during a deposit run",
        "Contingency funding plan testing",
        "test results, collateral pledging, discount window readiness",
        _c("Annual contingency funding test",
           "Treasury tests access to contingent funding lines each year.",
           "Operational test of FHLB and discount window draws",
           "Treasury performs an annual small-dollar draw on each contingent funding source, confirms pledged "
           "collateral values with the lender and records the time to funds. Results and any failed steps "
           "are reported to ALCO with owners and dates.",
           "Detective", "Manual", "Annual", ["Pellmark ALM"],
           "Interagency Policy Statement on Funding and Liquidity Risk Management",
           "No test draw on the discount window was performed in 2024, and collateral schedules were nine "
           "months old."),
    ),
    RiskConcept(
        "cfp_stress", "Contingency Funding", "Interest Rate & Liquidity", "Medium",
        ["Liquidity Management", "Treasury ALM"],
        "Liquidity stress testing understates outflows",
        "stress scenarios assume deposit runoff far below recent industry experience",
        "Mild runoff assumptions in liquidity stress tests",
        "uninsured deposit outflow rates in the stress model are lower than in recent peer failures",
        "scenario design that was not refreshed after the 2023 bank failures",
        "an overstated survival horizon",
        "Liquidity stress scenario design",
        "scenario severity, uninsured deposit concentration, deposit assumptions shared with the ALM model",
        _c("Liquidity stress scenario review",
           "ALCO reviews stress scenarios annually.",
           "Annual challenge of liquidity stress assumptions",
           "Treasury compares runoff assumptions to recent stress events and to uninsured deposit "
           "concentration, documents the rationale for each rate, and obtains challenge from Market Risk "
           "before ALCO approval.",
           "Detective", "Manual", "Annual", ["Pellmark ALM"],
           "Interagency Policy Statement on Funding and Liquidity Risk Management",
           "Runoff assumptions for uninsured commercial deposits were unchanged since 2021 and had no "
           "second-line challenge."),
    ),
    RiskConcept(
        "wire_fraud", "Transaction Processing", "Wire & ACH", "High",
        ["Wire Transfer Operations"],
        "Fraudulent wire transfers",
        "outgoing wires are released on instructions from a compromised customer email",
        "Business email compromise payment fraud",
        "payment instructions changed by an impostor are executed without independent confirmation",
        "callback verification skipped under cut-off pressure",
        "unrecoverable funds and customer reimbursement",
        "Wire callback verification",
        "callback logs, high-value wires, changed beneficiary instructions",
        _c("Wire callback verification",
           "Wires above threshold are confirmed by callback before release.",
           "Independent callback to a number on file before wire release",
           "For outgoing wires above $25,000 or to a new beneficiary, operations staff call the customer at "
           "the number on file in Corvessa Core Banking, not the number on the request, and record the call "
           "in Brisance Wire Manager. The wire cannot be released until a second operator approves the "
           "callback record.",
           "Preventive", "IT-dependent manual", "Per transaction",
           ["Brisance Wire Manager", "Corvessa Core Banking"], "UCC Article 4A (Funds Transfers)",
           "Callback records were missing for 6 of 45 sampled wires, and four were released by the operator "
           "who logged the callback."),
    ),
    RiskConcept(
        "ach_fraud", "Transaction Processing", "Wire & ACH", "High",
        ["ACH Operations"],
        "Unauthorized ACH originations",
        "originated ACH files contain debits the account holder never authorized",
        "ACH origination exposure limits",
        "commercial originators exceed their approved exposure limit without review",
        "exposure limits that are set once and never monitored",
        "returned entries and losses when the originator cannot cover them",
        "ACH origination limits and file review",
        "originator exposure limits, return rates, file release approvals, callback verification of changed instructions",
        _c("ACH exposure limit monitoring",
           "Originator exposure is checked against approved limits daily.",
           "Daily ACH exposure check and dual file release",
           "Quorvane Payments Hub suspends any ACH file that would take an originator over its approved "
           "exposure limit. Payment Operations reviews suspended files and needs a second approver to "
           "release them; return rates above 0.5% trigger an originator review.",
           "Preventive", "Automated", "Daily", ["Quorvane Payments Hub"], "Nacha Operating Rules",
           "Exposure limits for 7 of 20 sampled originators had not been reviewed in over two years."),
    ),
    RiskConcept(
        "recon_breaks", "Transaction Processing", "Wire & ACH", "Medium",
        ["General Ledger & Financial Close", "ACH Operations"],
        "Unreconciled payment suspense balances",
        "aged items in payment suspense accounts are not researched or cleared",
        "Suspense account aging",
        "suspense balances age past 30 days without escalation",
        "reconciliation ownership split between operations and finance",
        "misstated balances and undetected losses",
        "Payment suspense reconciliation",
        "reconciliation sign-off, aged items, write-off approvals",
        _c("Daily suspense reconciliation",
           "Payment suspense accounts are reconciled daily.",
           "Daily reconciliation of payment suspense with aged-item escalation",
           "Payment Operations reconciles each suspense account to Velistra General Ledger daily. Items older "
           "than 15 days are escalated to the operations manager and items older than 30 days to the "
           "Controller; write-offs need Controller approval.",
           "Detective", "IT-dependent manual", "Daily",
           ["Velistra General Ledger", "Quorvane Payments Hub"], "Sarbanes-Oxley Act Section 404",
           "Twelve suspense items more than 60 days old, totalling $418,000, had no escalation evidence."),
    ),
    RiskConcept(
        "txn_errors", "Transaction Processing", "Wire & ACH", "Low",
        ["Deposit Account Servicing"],
        "Manual posting errors",
        "payments keyed by hand post with the wrong amount or to the wrong account",
        "Unreviewed manual adjustments",
        "manual adjustments to customer accounts are entered without maker-checker review",
        "high volumes of exceptions processed by hand",
        "customer harm and operational losses",
        "Manual adjustment review",
        "maker-checker evidence, adjustment volumes, error rates",
        _c("Maker-checker on manual postings",
           "Manual postings need a second reviewer.",
           "Dual control on manual account adjustments",
           "Adjustments above $1,000 entered in Corvessa Core Banking are held until a second user approves "
           "them, and the system prevents the same user from entering and approving. Deposit Operations "
           "reviews a daily report of approved adjustments.",
           "Preventive", "Automated", "Per transaction", ["Corvessa Core Banking"],
           "Regulation E (Electronic Fund Transfers)",
           "The dual-control threshold was raised to $10,000 without change approval."),
    ),
    RiskConcept(
        "acc_provision", "Access & Identity", "Access Management", "High",
        ["Identity & Access Management"],
        "Excessive user access to critical systems",
        "users hold access beyond what their role requires in critical applications",
        "Access provisioning without role approval",
        "new access is granted on email requests with no manager or application owner approval",
        "role definitions that are not maintained",
        "unauthorized transactions and data exposure",
        "User access provisioning",
        "access request approvals, role design, removal of access that is no longer needed after role changes",
        _c("Role-based access provisioning",
           "Access is granted through approved role requests.",
           "Manager and application owner approval of access requests",
           "Access to in-scope applications is requested through Okrin Identity Gateway, which routes each "
           "request to the user's manager and the application owner. Provisioning runs only after both "
           "approvals, requests outside the role catalogue need Information Security sign-off, and access is "
           "removed automatically when a user changes role.",
           "Preventive", "Automated", "Per transaction", ["Okrin Identity Gateway"],
           "Gramm-Leach-Bliley Act",
           "Fourteen accounts in Velistra General Ledger were provisioned directly by administrators, "
           "bypassing the approval workflow."),
    ),
    RiskConcept(
        "acc_recert", "Access & Identity", "Access Management", "Medium",
        ["Identity & Access Management"],
        "Inappropriate access not removed",
        "access that is no longer needed stays active after role changes",
        "Ineffective user access recertification",
        "managers approve quarterly access reviews wholesale without revoking unneeded entitlements",
        "review packs that are too large to assess",
        "segregation of duties conflicts and fraud opportunity",
        "Periodic access recertification",
        "review completeness, revocation timeliness, SoD conflicts",
        _c("Quarterly access recertification",
           "Managers recertify user access quarterly.",
           "Quarterly recertification with revocation tracking",
           "Okrin Identity Gateway issues quarterly recertification campaigns for critical applications. "
           "Managers must certify or revoke each entitlement, revocations are completed within five business "
           "days, and Information Security reports incomplete campaigns to the Technology Risk Committee.",
           "Detective", "IT-dependent manual", "Quarterly",
           ["Okrin Identity Gateway", "Corvessa Core Banking"], "Sarbanes-Oxley Act Section 404",
           "The second-quarter campaign for Corvessa Core Banking closed with 22% of entitlements "
           "uncertified, and nine revocations took more than 30 days."),
    ),
    RiskConcept(
        "acc_privileged", "Access & Identity", "Access Management", "High",
        ["Identity & Access Management", "General Ledger & Financial Close"],
        "Unmonitored privileged access",
        "administrator accounts are used without logging or independent review",
        "Shared administrator credentials",
        "privileged credentials are shared among support staff and never rotated",
        "legacy applications that do not support individual admin accounts",
        "undetected changes to production data",
        "Privileged access management",
        "admin account inventory, session logging, password vaulting",
        _c("Privileged session review",
           "Privileged activity is logged and reviewed.",
           "Vaulted admin credentials with monthly session log review",
           "Administrator credentials are checked out from the password vault for each session and rotated "
           "afterwards. Information Security reviews privileged session logs for Velistra General Ledger and "
           "Corvessa Core Banking monthly and investigates any activity without a linked change ticket.",
           "Detective", "IT-dependent manual", "Monthly",
           ["Okrin Identity Gateway", "Velistra General Ledger", "Corvessa Core Banking"],
           "Sarbanes-Oxley Act Section 404",
           "Three generic administrator accounts on Velistra General Ledger were not vaulted, and session "
           "logs went unreviewed for four months."),
    ),
    RiskConcept(
        "aml_monitoring", "BSA/AML", "AML Monitoring", "High",
        ["BSA/AML Program"],
        "Ineffective transaction monitoring",
        "suspicious activity goes undetected because monitoring scenarios are poorly tuned",
        "Transaction monitoring coverage gaps",
        "new products and channels are not mapped to any monitoring scenario",
        "scenario thresholds not tuned since the system was implemented",
        "missed suspicious activity reports and regulatory action",
        "AML scenario tuning and coverage",
        "scenario inventory, above- and below-the-line testing, product mapping",
        _c("Annual scenario tuning",
           "BSA Compliance tunes monitoring scenarios annually.",
           "Above- and below-the-line testing of monitoring scenarios",
           "BSA Compliance runs above- and below-the-line testing on each Merrow AML Monitor scenario every "
           "year and maps every product and channel to at least one scenario. Threshold changes are approved "
           "by the BSA Officer and validated by Model Risk.",
           "Detective", "IT-dependent manual", "Annual", ["Merrow AML Monitor", "Ylvara Data Warehouse"],
           "Bank Secrecy Act",
           "Remote deposit capture was not mapped to any scenario, and below-the-line testing was skipped "
           "for 5 of 18 scenarios."),
    ),
    RiskConcept(
        "aml_alerts", "BSA/AML", "AML Monitoring", "High",
        ["BSA/AML Program"],
        "Alert backlog in AML investigations",
        "monitoring alerts are not dispositioned within required timeframes",
        "Late suspicious activity reporting",
        "SARs are filed after the 30-day deadline because cases sit in queue",
        "investigator staffing below alert volumes",
        "late SAR filings and enforcement risk",
        "Alert disposition timeliness",
        "alert aging, case quality, SAR filing timelines",
        _c("Alert aging monitoring",
           "Alert aging is reported to the BSA Officer weekly.",
           "Weekly alert aging report with escalation and QA sampling",
           "Tessaly Case Manager produces a weekly aging report of open alerts and cases. Alerts older than "
           "30 days are escalated to the BSA Officer, and the quality assurance team re-performs a 5% sample "
           "of closed alerts each month.",
           "Detective", "IT-dependent manual", "Weekly", ["Tessaly Case Manager", "Merrow AML Monitor"],
           "Bank Secrecy Act",
           "1,240 alerts were older than 30 days at quarter end, and QA sampling was suspended for two "
           "months."),
    ),
    RiskConcept(
        "aml_cdd", "BSA/AML", "AML Monitoring", "Medium",
        ["BSA/AML Program", "Wealth Client Onboarding"],
        "Incomplete customer due diligence",
        "beneficial ownership information is missing for legal entity customers",
        "Customer risk rating errors",
        "customer risk ratings are not refreshed when ownership or activity changes",
        "onboarding checklists completed after accounts are opened",
        "high-risk customers monitored as low risk",
        "Beneficial ownership and CDD refresh",
        "beneficial ownership certification, risk rating refresh, monitoring scenarios applied to high-risk customers",
        _c("Beneficial ownership certification",
           "Beneficial ownership is collected at account opening.",
           "Account activation hold until beneficial ownership is certified",
           "Corvessa Core Banking will not activate a legal entity account until the beneficial ownership "
           "certification fields are complete and verified by the onboarding team. Customer risk ratings are "
           "recalculated nightly from ownership and activity data.",
           "Preventive", "Automated", "Per transaction", ["Corvessa Core Banking"], "Bank Secrecy Act",
           "Seven legal entity accounts were activated through a manual override with no BSA approval."),
    ),
    RiskConcept(
        "aml_sanctions", "BSA/AML", "AML Monitoring", "High",
        ["BSA/AML Program", "Wire Transfer Operations"],
        "Sanctions screening failures",
        "payments to sanctioned parties are not stopped by screening",
        "Sanctions list update delays",
        "screening lists in the payment system lag official updates by several days",
        "manual upload of list updates",
        "sanctions violations and penalties",
        "Sanctions screening of payments",
        "list update timeliness, fuzzy-match settings, hit disposition",
        _c("Real-time payment sanctions screening",
           "Payments are screened against sanctions lists before release.",
           "Automated sanctions screening with same-day list updates",
           "Brisance Wire Manager screens every outgoing and incoming wire against the sanctions list before "
           "release. List updates load automatically on the day they are published, and Compliance documents "
           "its review of every potential match before the payment is released or blocked.",
           "Preventive", "Automated", "Per transaction", ["Brisance Wire Manager", "Quorvane Payments Hub"],
           "OFAC Regulations",
           "List updates were loaded by hand two to four days late in 5 of 12 sampled weeks."),
    ),
    RiskConcept(
        "npi_approval", "New Products & Initiatives", "Project & Change Governance", "Medium",
        ["New Product Approval"],
        "Products launched without risk assessment",
        "new products go live before compliance and operational risk reviews are complete",
        "Bypassed new product approval",
        "product changes are labelled minor to avoid the new product committee",
        "unclear criteria for what counts as a new product",
        "unmanaged compliance and operational exposures",
        "New product approval governance",
        "committee approvals, risk assessments, post-implementation reviews",
        _c("New product committee approval",
           "The New Product Committee approves launches.",
           "Committee sign-off with completed risk assessments before launch",
           "Product owners submit a risk assessment signed by Compliance, Operational Risk and Information "
           "Security to the New Product Committee. Launch is blocked until the committee approves, and a "
           "post-implementation review is completed within six months.",
           "Preventive", "Manual", "Per event", [], "OCC Heightened Standards",
           "Two product changes launched as minor changes without committee review or a risk assessment."),
    ),
    RiskConcept(
        "npi_thirdparty", "New Products & Initiatives", "Project & Change Governance", "High",
        ["Third-Party Risk Management", "New Product Approval"],
        "Fintech partner risk not assessed",
        "fintech partnerships launch without due diligence on the partner's compliance program",
        "Third-party due diligence gaps",
        "critical vendors are onboarded before security and financial reviews are finished",
        "business sponsors negotiating contracts before third-party risk management is engaged",
        "consumer harm and regulatory criticism attributed to the bank",
        "Third-party onboarding due diligence",
        "due diligence packages, criticality ratings, contract clauses",
        _c("Third-party due diligence before contract",
           "Third-party risk management completes due diligence before contracts are signed.",
           "Contract signature hold until third-party due diligence is complete",
           "Procurement will not execute a contract with a critical or high-risk third party until the "
           "third-party risk team records a completed due diligence package, including security, financial "
           "and compliance reviews, and assigns a criticality rating.",
           "Preventive", "Manual", "Per event", [], "Interagency Guidance on Third-Party Relationships",
           "Four critical vendors were onboarded with due diligence still open, and one had no SOC 2 "
           "report."),
    ),
    RiskConcept(
        "cmp_handling", "Customer Complaints", "Complaint Handling", "Medium",
        ["Customer Complaints Management"],
        "Complaints not captured or resolved",
        "customer complaints received in branches are not logged or resolved on time",
        "Untracked branch complaints",
        "verbal complaints in branches never reach the complaint system",
        "the lack of a single intake channel for complaints",
        "unaddressed customer harm and UDAAP exposure",
        "Complaint intake and resolution",
        "intake channels, resolution timeliness, regulator complaints",
        _c("Complaint resolution tracking",
           "Complaints are logged and tracked to resolution.",
           "Central complaint log with 15-day resolution tracking",
           "All complaints, including verbal branch complaints, are logged in Tessaly Case Manager within "
           "one business day. Complaints open longer than 15 days are escalated to the Complaints Manager and "
           "reported monthly to the Compliance Committee.",
           "Detective", "IT-dependent manual", "Daily", ["Tessaly Case Manager"],
           "Dodd-Frank UDAAP Provisions",
           "Branch complaints were logged an average of nine days after receipt, and 31 complaints passed "
           "15 days without escalation."),
    ),
    RiskConcept(
        "cmp_rootcause", "Customer Complaints", "Complaint Handling", "Low",
        ["Customer Complaints Management", "Card Disputes"],
        "Complaint trends not analyzed",
        "recurring complaint themes are not analyzed for root causes",
        "Weak complaint root cause analysis",
        "complaint data is reported as counts without identifying systemic issues",
        "complaint categories that are too broad",
        "repeat customer harm and reputational damage",
        "Complaint trend analysis",
        "categorization, root cause reviews, management reporting",
        _c("Quarterly complaint trend review",
           "Compliance reviews complaint trends quarterly.",
           "Quarterly root cause analysis of complaint themes",
           "Compliance analyzes complaint data from Tessaly Case Manager each quarter by product, channel and "
           "theme, assigns a root cause owner to any theme above threshold, and tracks corrective actions to "
           "closure.",
           "Detective", "Manual", "Quarterly", ["Tessaly Case Manager", "Ylvara Data Warehouse"],
           "Dodd-Frank UDAAP Provisions",
           "No root cause owner was assigned for the two largest card complaint themes."),
    ),
]

# Templates. ERM writes RCSA risk statements; IA writes audit-universe entries.
ERM_RISK_TEMPLATES = [
    "Risk that {phrase} due to {cause}, resulting in {impact}.",
    "{Impact} may occur if {phrase}. Primary driver: {cause}.",
]
IA_RISK_TEMPLATES = [
    "{area}: {title}. Review scope: {focus}.",
    "{title} ({area}; audit focus: {focus}).",
]

ISSUE_SOURCES = ["IA", "Regulator", "Self-identified", "2nd line"]
ISSUE_TEMPLATES = {
    "IA": ("{ia_title} not operating as designed", "{finding}"),
    "Regulator": ("MRA: {erm_title} weaknesses", "Examiners found that {finding_lc}"),
    "Self-identified": ("Self-identified gap: {erm_title}", "Management identified that {finding_lc}"),
    "2nd line": ("2LOD review: {erm_title}", "Second-line testing found that {finding_lc}"),
}
AUDIT_RATINGS = ["Satisfactory", "Needs Improvement", "Unsatisfactory"]
RATINGS = ["High", "Medium", "Low"]
