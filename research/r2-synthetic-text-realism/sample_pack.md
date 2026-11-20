# Sample pack: Cedar Prairie Bancorp (synthetic)

This is a small slice of the generated bank (about 15 rows per entity) for one question: **do these records read like a real US regional bank's ERM and Internal Audit data?** Judge the wording and attributes of the rows. Population sizes, ratios and taxonomy breadth are set later (children b-e), so they are not under review here.

Risks, controls and issues show two versions of each description: **templated** (built from hand-written phrases) and **AI-written** (generated once with Claude and committed). Pick one.

## Your review

Mark each entity type realistic (yes / no) and add notes. Record the verdict and text choice in `research/r2-synthetic-text-realism/decision.md`.

| entity type | realistic? | notes |
|---|---|---|
| segment |  |  |
| business_unit |  |  |
| auditable_entity |  |  |
| process |  |  |
| system |  |  |
| person |  |  |
| regulation |  |  |
| taxonomy_node_erm |  |  |
| taxonomy_node_ia |  |  |
| risk_erm |  |  |
| risk_ia |  |  |
| control_erm |  |  |
| control_ia |  |  |
| audit |  |  |
| issue |  |  |

**Text choice (templated / AI):** ____

## Name lists

Every institution, person, vendor and system name comes from these lists (INV-9). Check that none resembles a real institution or product.

**institution:** Cedar Prairie Bancorp

**first_names:** Adaeze; Alma; Anders; Beatriz; Callum; Corinne; Darnell; Delphine; Emeka; Fiona; Gideon; Harriet; Ines; Joaquin; Keziah; Lorenzo; Marisol; Nikhil; Odette; Priya; Quentin; Rosalind; Soren; Tamsin; Ulric; Valeria; Wendell; Ximena; Yusuf; Zelda

**last_names:** Abernathy; Achterberg; Balogun; Castellanos; Delacroix; Eastwick; Fairbanks; Galloway; Haddad; Ishikawa; Jaramillo; Kowalczyk; Lindqvist; Mbeki; Nakamura; Okonkwo; Pellegrino; Quinlan; Rasmussen; Szabo; Thackeray; Uriarte; Vasquez; Whitcombe; Yamamoto; Zielinski; Ferreira; Okafor; Brannigan; Holloway

**titles:** Chief Credit Officer; Credit Administration Manager; Senior Underwriter; Valuation Manager; Treasurer; ALM Manager; Head of Payment Operations; Wire Room Supervisor; ACH Operations Manager; Deposit Operations Manager; Controller; BSA Officer; AML Investigations Manager; Sanctions Compliance Manager; Information Security Manager; Identity and Access Lead; Complaints Manager; New Product Program Manager; Third-Party Risk Manager; Operational Risk Manager

**systems:** Corvessa Core Banking; Halbrook Loan Origination; Pellmark ALM; Quorvane Payments Hub; Brisance Wire Manager; Ylvara Data Warehouse; Merrow AML Monitor; Okrin Identity Gateway; Velistra General Ledger; Tessaly Case Manager

**vendors:** Quorvane Systems; Halbrook Data; Merrow Analytics; Velistra Software; Okrin Technologies; Tessaly Labs

**regulations:** Bank Secrecy Act; Sarbanes-Oxley Act Section 404; Regulation E (Electronic Fund Transfers); Gramm-Leach-Bliley Act; OFAC Regulations; Interagency Guidance on Third-Party Relationships; OCC Heightened Standards; Interagency Policy Statement on Funding and Liquidity Risk Management; Regulation Z (Truth in Lending); Interagency Appraisal and Evaluation Guidelines; UCC Article 4A (Funds Transfers); Nacha Operating Rules; Dodd-Frank UDAAP Provisions

## Entities

### segment

| segment_id | name |
|---|---|
| SEG-20 | Corporate Functions |
| SEG-32 | Consumer Banking |
| SEG-34 | Technology |
| SEG-55 | Operations |
| SEG-71 | Wealth Management |
| SEG-78 | Treasury & Markets |
| SEG-80 | Commercial Banking |

### business_unit

| business_unit_id | name |
|---|---|
| BU-215 | Compliance |
| BU-223 | Commercial Lending |
| BU-266 | Payment Operations |
| BU-272 | Card Services |
| BU-313 | Enterprise Technology |
| BU-549 | Treasury Management Services |
| BU-586 | Consumer Lending |
| BU-662 | Retail Branch Network |
| BU-767 | Corporate Treasury |
| BU-931 | Deposit Operations |
| BU-951 | Private Wealth Advisory |
| BU-990 | Finance |

### auditable_entity

| auditable_entity_id | name |
|---|---|
| AE-153 | Consumer Mortgage Lending |
| AE-165 | Commercial Loan Origination |
| AE-352 | Customer Complaints Management |
| AE-384 | Card Disputes |
| AE-400 | Liquidity Management |
| AE-457 | Third-Party Risk Management |
| AE-518 | General Ledger & Financial Close |
| AE-587 | Wealth Client Onboarding |
| AE-604 | ACH Operations |
| AE-755 | Identity & Access Management |
| AE-762 | Wire Transfer Operations |
| AE-855 | Deposit Account Servicing |
| AE-882 | New Product Approval |
| AE-929 | BSA/AML Program |
| AE-976 | Treasury ALM |

### process

| process_id | name |
|---|---|
| PRC-154 | User access provisioning |
| PRC-188 | Customer due diligence |
| PRC-192 | Complaint intake and resolution |
| PRC-299 | Loan application intake |
| PRC-302 | Mortgage underwriting |
| PRC-330 | Interest rate risk measurement |
| PRC-407 | Manual account adjustments |
| PRC-533 | Wealth client onboarding |
| PRC-568 | Contingency funding planning |
| PRC-597 | New product review |
| PRC-630 | Payment suspense reconciliation |
| PRC-677 | Wire initiation and release |
| PRC-768 | Vendor onboarding |
| PRC-797 | Card dispute processing |
| PRC-815 | Credit underwriting and approval |
| PRC-869 | Transaction monitoring alert review |
| PRC-954 | Access recertification |
| PRC-991 | ACH file origination |

### system

| system_id | name | vendor | criticality |
|---|---|---|---|
| SYS-100 | Tessaly Case Manager | Tessaly Labs | Medium |
| SYS-170 | Merrow AML Monitor | Merrow Analytics | High |
| SYS-253 | Pellmark ALM | Merrow Analytics | Medium |
| SYS-254 | Corvessa Core Banking | Quorvane Systems | High |
| SYS-526 | Ylvara Data Warehouse | Okrin Technologies | Medium |
| SYS-533 | Quorvane Payments Hub | Quorvane Systems | High |
| SYS-772 | Halbrook Loan Origination | Halbrook Data | High |
| SYS-879 | Okrin Identity Gateway | Okrin Technologies | High |
| SYS-931 | Velistra General Ledger | Velistra Software | High |
| SYS-960 | Brisance Wire Manager | Velistra Software | High |

### person

| person_id | name | title |
|---|---|---|
| P-1271 | Harriet Quinlan | New Product Program Manager |
| P-1280 | Corinne Yamamoto | Sanctions Compliance Manager |
| P-1562 | Soren Okonkwo | Wire Room Supervisor |
| P-1755 | Corinne Galloway | Valuation Manager |
| P-1969 | Adaeze Eastwick | BSA Officer |
| P-2333 | Marisol Rasmussen | Treasurer |
| P-3275 | Rosalind Zielinski | ALM Manager |
| P-3378 | Adaeze Nakamura | Identity and Access Lead |
| P-3407 | Rosalind Galloway | AML Investigations Manager |
| P-4486 | Corinne Uriarte | Operational Risk Manager |
| P-4682 | Valeria Szabo | Controller |
| P-5614 | Delphine Pellegrino | Deposit Operations Manager |
| P-5896 | Rosalind Holloway | Information Security Manager |
| P-6147 | Zelda Lindqvist | Head of Payment Operations |
| P-6828 | Adaeze Galloway | Third-Party Risk Manager |
| P-6848 | Alma Rasmussen | Senior Underwriter |
| P-6927 | Yusuf Whitcombe | Credit Administration Manager |
| P-7171 | Joaquin Yamamoto | ACH Operations Manager |
| P-8293 | Corinne Nakamura | Chief Credit Officer |
| P-9676 | Corinne Abernathy | Complaints Manager |

### regulation

| regulation_id | name | citation |
|---|---|---|
| REG-249 | Interagency Guidance on Third-Party Relationships | 88 FR 37920 |
| REG-542 | Bank Secrecy Act | 31 U.S.C. 5311 et seq. |
| REG-589 | OCC Heightened Standards | 12 CFR Part 30, Appendix D |
| REG-642 | Gramm-Leach-Bliley Act | 15 U.S.C. 6801 et seq. |
| REG-693 | Interagency Policy Statement on Funding and Liquidity Risk Management | 75 FR 13656 |
| REG-787 | Regulation E (Electronic Fund Transfers) | 12 CFR Part 1005 |
| REG-852 | OFAC Regulations | 31 CFR Chapter V |
| REG-935 | Sarbanes-Oxley Act Section 404 | 15 U.S.C. 7262 |

### taxonomy_node_erm

| taxonomy_node_id | level | name |
|---|---|---|
| ERMT-149 | 2 | Regulatory Compliance |
| ERMT-173 | 1 | Operational |
| ERMT-428 | 2 | Funding Liquidity |
| ERMT-510 | 2 | Technology |
| ERMT-543 | 2 | Business Strategy |
| ERMT-562 | 3 | Customer Complaints |
| ERMT-600 | 1 | Compliance |
| ERMT-618 | 1 | Liquidity |
| ERMT-637 | 3 | New Products & Initiatives |
| ERMT-641 | 2 | Credit Risk Management |
| ERMT-668 | 3 | Access & Identity |
| ERMT-679 | 1 | Credit |
| ERMT-734 | 2 | Interest Rate Risk |
| ERMT-751 | 3 | Contingency Funding |
| ERMT-820 | 3 | Banking Book IRR |
| ERMT-863 | 3 | Underwriting & Origination |
| ERMT-866 | 1 | Reputational |
| ERMT-887 | 1 | Strategic |
| ERMT-897 | 3 | Transaction Processing |
| ERMT-927 | 3 | BSA/AML |
| ERMT-943 | 2 | Process & Execution |
| ERMT-953 | 1 | Market |
| ERMT-955 | 2 | Stakeholder Risk |

### taxonomy_node_ia

| taxonomy_node_id | level | name |
|---|---|---|
| IAT-103 | 1 | Operations |
| IAT-112 | 2 | IT General Controls |
| IAT-271 | 3 | Loan Origination |
| IAT-297 | 1 | Customer |
| IAT-355 | 2 | Payments |
| IAT-374 | 2 | Asset/Liability Management |
| IAT-391 | 3 | Project & Change Governance |
| IAT-439 | 2 | Commercial Lending |
| IAT-449 | 2 | Complaints |
| IAT-475 | 3 | Interest Rate & Liquidity |
| IAT-529 | 3 | Complaint Handling |
| IAT-544 | 1 | Corporate Governance |
| IAT-548 | 3 | AML Monitoring |
| IAT-610 | 3 | Wire & ACH |
| IAT-674 | 1 | Lending |
| IAT-696 | 3 | Access Management |
| IAT-729 | 2 | Governance Oversight |
| IAT-767 | 1 | Information Technology |
| IAT-889 | 1 | Regulatory Compliance |
| IAT-922 | 1 | Treasury |
| IAT-968 | 2 | Financial Crimes |

### risk_erm

| risk_id | title | description (templated) | description (AI) | inherent_rating |
|---|---|---|---|---|
| ERM-R1240 | Complaint trends not analyzed | Repeat customer harm and reputational damage may occur if recurring complaint themes are not analyzed for root causes. Primary driver: complaint categories that are too broad. | Because complaint categories are defined too broadly to separate distinct issues, recurring complaint themes may go unanalyzed for root cause, which could allow the same customer harm to repeat and expose the bank to reputational damage. | Low |
| ERM-R1512 | Unreconciled payment suspense balances | Misstated balances and undetected losses may occur if aged items in payment suspense accounts are not researched or cleared. Primary driver: reconciliation ownership split between operations and finance. | Because responsibility for reconciling payment suspense accounts is split between operations and finance, aged items may go unresearched and uncleared. This could leave balances misstated and allow losses to go undetected. | Medium |
| ERM-R1647 | Unauthorized ACH originations | Returned entries and losses when the originator cannot cover them may occur if originated ACH files contain debits the account holder never authorized. Primary driver: exposure limits that are set once and never monitored. | Because originator exposure limits are set once at onboarding and never monitored afterward, originated ACH files may carry debits the account holder never authorized. When the originator cannot cover the resulting returned entries, the bank absorbs the losses. | High |
| ERM-R1782 | Unmonitored privileged access | Risk that administrator accounts are used without logging or independent review due to legacy applications that do not support individual admin accounts, resulting in undetected changes to production data. | Because several legacy applications cannot support individual administrator accounts, privileged access is exercised through shared credentials that are neither logged nor subject to independent review. Changes made to production data through these accounts could therefore go undetected, impairing the integrity of records relied on for operations and reporting. | High |
| ERM-R1809 | Inappropriate access not removed | Segregation of duties conflicts and fraud opportunity may occur if access that is no longer needed stays active after role changes. Primary driver: review packs that are too large to assess. | Because periodic access review packs are too large for reviewers to assess meaningfully, entitlements that are no longer needed after an employee changes roles may stay active instead of being removed. This could create SoD conflicts and an opportunity for fraud through unauthorized processing or concealment of transactions. | Medium |
| ERM-R2069 | Alert backlog in AML investigations | Late SAR filings and enforcement risk may occur if monitoring alerts are not dispositioned within required timeframes. Primary driver: investigator staffing below alert volumes. | Because investigator staffing has not kept pace with alert volumes, monitoring alerts may age beyond the required timeframes for disposition and accumulate into an investigation backlog. Any resulting late SAR filings would expose the bank to regulatory criticism and enforcement risk. | High |
| ERM-R2184 | Sanctions screening failures | Risk that payments to sanctioned parties are not stopped by screening due to manual upload of list updates, resulting in sanctions violations and penalties. | Because sanctions list updates are uploaded to the screening process manually, a missed, late or incomplete upload could leave screening running against outdated lists, so payments to sanctioned parties are not stopped. The bank would then be exposed to sanctions violations, regulatory penalties and related remediation costs. | High |
| ERM-R2580 | Excessive user access to critical systems | Risk that users hold access beyond what their role requires in critical applications due to role definitions that are not maintained, resulting in unauthorized transactions and data exposure. | Because role definitions in critical applications are not kept current, users may accumulate access beyond what their job functions require. This could allow unauthorized transactions to be processed and sensitive data to be exposed. | High |
| ERM-R2689 | Contingency funding plan not executable | A liquidity shortfall during a deposit run may occur if contingency funding sources cannot be drawn in the time the plan assumes. Primary driver: operational testing that is skipped when markets are calm. | Because operational draw-down testing of contingency funding sources tends to be deferred when markets are calm, those sources may not be accessible within the timeframes the contingency funding plan assumes, resulting in a liquidity shortfall if the bank experiences a deposit run. | High |
| ERM-R3450 | Fintech partner risk not assessed | Consumer harm and regulatory criticism attributed to the bank may occur if fintech partnerships launch without due diligence on the partner's compliance program. Primary driver: business sponsors negotiating contracts before third-party risk management is engaged. | Because business sponsors often negotiate fintech partnership contracts before third-party risk management is engaged, a partnership may launch without due diligence on the partner's compliance program, exposing customers to harm and the bank to regulatory criticism attributed to it. | High |
| ERM-R3459 | Stale deposit beta assumptions | Risk that deposit repricing betas used for earnings-at-risk have not been recalibrated since rates moved due to the lack of an annual assumption review, resulting in hedging decisions based on misleading rate sensitivity. | Because no annual review of deposit assumptions is in place, the repricing betas that drive the earnings-at-risk measure have not been recalibrated since the shift in market rates and may no longer reflect actual depositor behavior. Interest rate sensitivity could therefore be misstated, leading to hedging decisions that rest on a distorted view of earnings exposure and leave the bank under- or over-hedged. | High |
| ERM-R3603 | Interest rate risk model mis-specification | Hedging decisions based on misleading rate sensitivity may occur if the ALM model misstates earnings sensitivity because deposit assumptions are outdated. Primary driver: the lack of an annual assumption review. | Because deposit assumptions are not subject to an annual review and have become outdated, the ALM model may misstate earnings sensitivity to rate changes. Treasury and ALCO could then base hedging decisions on misleading rate sensitivity results, leaving the bank inappropriately hedged against interest rate movements. | High |
| ERM-R4055 | Borrower income not verified | Risk that consumer loans are underwritten on stated income that is never verified due to exception tracking that relies on spreadsheets, resulting in early payment defaults and repurchase demands. | Because underwriting exceptions for missing income documentation are tracked in spreadsheets rather than within a controlled workflow, consumer loans may be approved and funded on borrower-stated income that is never subsequently verified. This could lead to elevated early payment defaults and repurchase demands from loan purchasers. | Medium |
| ERM-R4131 | Complaints not captured or resolved | Risk that customer complaints received in branches are not logged or resolved on time due to the lack of a single intake channel for complaints, resulting in unaddressed customer harm and UDAAP exposure. | Because branches have no single intake channel for customer complaints, complaints received in person or by phone at the branch level may never be logged or may not be resolved within required timeframes. This could leave customer harm unaddressed and increase the bank's UDAAP exposure. | Medium |
| ERM-R4982 | Fraudulent wire transfers | Unrecoverable funds and customer reimbursement may occur if outgoing wires are released on instructions from a compromised customer email. Primary driver: callback verification skipped under cut-off pressure. | When staff skip callback verification to meet same-day cut-off times, outgoing wires may be released on payment instructions received from a compromised customer email account. Funds sent this way are often unrecoverable once credited to the beneficiary institution, which leaves the bank exposed to reimbursing the customer for the loss. | High |

### risk_ia

| risk_id | title | description (templated) | description (AI) | inherent_rating |
|---|---|---|---|---|
| IAR-5050 | Complaint intake and resolution | Complaint Handling: Complaint intake and resolution. Review scope: intake channels, resolution timeliness, regulator complaints. | Complaint handling, covering intake and resolution of customer complaints. The audit evaluates how complaints are captured across intake channels, whether resolution is timely, and how complaints received through regulators are tracked and answered. | Medium |
| IAR-5150 | Sanctions screening of payments | AML Monitoring: Sanctions screening of payments. Review scope: list update timeliness, fuzzy-match settings, hit disposition. | This AML monitoring entry covers the screening of payment transactions against sanctions lists. The audit tests whether list updates are loaded promptly, whether fuzzy-match settings are calibrated and governed appropriately, and whether screening hits are dispositioned accurately and on time with adequate supporting evidence. | High |
| IAR-5246 | User access provisioning | User access provisioning (Access Management; audit focus: access request approvals, role design, removal of access that is no longer needed after role changes). | User access provisioning is part of the Access Management risk area. The audit evaluates whether access requests are properly approved before being granted, whether roles are designed so they confer only appropriate entitlements, and whether access that is no longer needed is removed promptly after an employee changes roles. | Medium |
| IAR-5757 | AML scenario tuning and coverage | AML scenario tuning and coverage (AML Monitoring; audit focus: scenario inventory, above- and below-the-line testing, product mapping). | AML transaction monitoring scenario tuning and coverage is a risk area in AML monitoring that covers whether detection scenarios are calibrated and cover the bank's products. The audit tests completeness of the scenario inventory, reviews above-the-line and below-the-line threshold testing that supports tuning decisions, and checks that product and transaction types map to at least one active scenario. | Medium |
| IAR-6108 | Contingency funding plan testing | Interest Rate & Liquidity: Contingency funding plan testing. Review scope: test results, collateral pledging, discount window readiness. | Under interest rate and liquidity risk, this entry covers testing of the contingency funding plan. The audit reviews plan test results and the handling of any noted exceptions, the adequacy and documentation of collateral pledged to secure contingent funding sources, and Treasury's operational readiness to access the Federal Reserve discount window on short notice. | High |
| IAR-6267 | Appraisal review and independence | Loan Origination: Appraisal review and independence. Review scope: appraisal ordering process, review checklist, aged valuations. | Appraisal review and independence sits within the loan origination risk area and addresses the risk that collateral valuations are improperly influenced or inadequately reviewed. The audit evaluates how appraisals are ordered and kept separate from production staff, tests completion of the appraisal review checklist, and identifies aged valuations relied on beyond acceptable timeframes. | Medium |
| IAR-6295 | New product approval governance | Project & Change Governance: New product approval governance. Review scope: committee approvals, risk assessments, post-implementation reviews. | New product approval governance falls within the project and change governance risk area. The audit examines how the New Product Committee approves proposals and whether risk assessments are completed and documented before launch. It also tests whether post-implementation reviews are performed and their findings tracked to resolution. | Medium |
| IAR-6395 | Periodic access recertification | Periodic access recertification (Access Management; audit focus: review completeness, revocation timeliness, SoD conflicts). | Periodic access recertification falls within the access management risk area and covers the recurring review of user entitlements by system and business owners. The audit evaluates whether reviews are complete across all in-scope users and applications, whether access flagged for removal is revoked in a timely manner, and whether SoD conflicts are identified and resolved or formally accepted. | Medium |
| IAR-6788 | Wire callback verification | Wire & ACH: Wire callback verification. Review scope: callback logs, high-value wires, changed beneficiary instructions. | Wire and ACH risk area covering wire callback verification, where the audit tests whether callbacks are performed and documented before release by examining callback logs, with particular attention to high-value wires and to requests involving changed beneficiary instructions. | High |
| IAR-6809 | Payment suspense reconciliation | Payment suspense reconciliation (Wire & ACH; audit focus: reconciliation sign-off, aged items, write-off approvals). | Payment suspense reconciliation covers the wire and ACH suspense accounts where unmatched or unapplied payments are held until cleared. The audit tests whether each reconciliation is reviewed and signed off on time, whether aged items are tracked and escalated, and whether write-offs receive appropriate approval before posting. | Medium |
| IAR-7771 | Lending authority not enforced at approval | Loan Origination: Lending authority not enforced at approval. Review scope: approval matrix setup, override log, approvals above $5 million. | This loan origination risk area covers the possibility that credit approvals proceed without enforcement of the lending authority assigned to the approver. The audit tests how the approval matrix is configured, reviews the override log for exceptions and their justification, and examines all approvals above $5 million to confirm each one was granted at the appropriate authority level. | High |
| IAR-8634 | Liquidity stress scenario design | Interest Rate & Liquidity: Liquidity stress scenario design. Review scope: scenario severity, uninsured deposit concentration, deposit assumptions shared with the ALM model. | Liquidity stress scenario design falls within the interest rate and liquidity risk area and covers how Treasury builds and calibrates the stress scenarios used to test funding resilience. The audit assesses whether scenario severity is adequately challenging, whether concentrations of uninsured deposits are reflected in projected outflows, and whether the deposit assumptions shared with the ALM model are consistent, documented and supported. | Medium |
| IAR-8862 | Complaint trend analysis | Complaint trend analysis (Complaint Handling; audit focus: categorization, root cause reviews, management reporting). | Complaint trend analysis falls within the complaint handling risk area and covers how complaints are categorized, whether root cause reviews are completed for recurring issues, and the accuracy of management reporting on trends. Audit work tests a sample of logged complaints for correct coding and traces reported trend figures back to source records maintained under the Complaints Manager. | Medium |
| IAR-8993 | Beneficial ownership and CDD refresh | AML Monitoring: Beneficial ownership and CDD refresh. Review scope: beneficial ownership certification, risk rating refresh, monitoring scenarios applied to high-risk customers. | Beneficial ownership and CDD refresh falls within the AML monitoring risk area and covers how the bank obtains and maintains beneficial ownership certifications and refreshes customer risk ratings on schedule. The audit also tests whether the monitoring scenarios applied to high-risk customers are assigned correctly and keep running after a rating changes. | Medium |
| IAR-9035 | ALM model assumptions and validation | ALM model assumptions and validation (Interest Rate & Liquidity; audit focus: assumption governance, back-testing, model validation findings). | Within the interest rate and liquidity risk area, ALM model assumptions and validation covers how the bank sets, approves and documents the behavioral and market assumptions that drive its ALM modeling. The audit examines assumption governance, the back-testing of model outputs against actual results, and whether findings from model validation are tracked and resolved on time. | Medium |

### control_erm

| control_id | title | description (templated) | description (AI) | control_type | nature | frequency | key_control |
|---|---|---|---|---|---|---|---|
| ERM-C1134 | Role-based access provisioning | Access is granted through approved role requests. | User access to systems is provisioned only on the basis of approved role-based requests. | Preventive | Automated | Per transaction | Y |
| ERM-C1643 | Real-time payment sanctions screening | Payments are screened against sanctions lists before release. | Payment Operations screens each outgoing payment against applicable sanctions lists in real time and releases it only after screening is complete. | Preventive | Automated | Per transaction | Y |
| ERM-C1862 | Annual ALM assumption approval | ALCO approves key ALM assumptions each year. | On an annual basis, ALCO reviews and approves the key assumptions used in ALM modeling. | Detective | Manual | Quarterly | Y |
| ERM-C2315 | Privileged session review | Privileged activity is logged and reviewed. | Activity performed under privileged access is captured in logs and periodically reviewed by Information Security. | Detective | IT-dependent manual | Monthly | Y |
| ERM-C2452 | Wire callback verification | Wires above threshold are confirmed by callback before release. | Payment Operations confirms each wire exceeding the established threshold through a callback to the customer before the wire is released. | Preventive | IT-dependent manual | Per transaction | Y |
| ERM-C2539 | Complaint resolution tracking | Complaints are logged and tracked to resolution. | Customer complaints are captured in a central log and monitored by the Complaints Manager until each one is resolved and closed. | Detective | IT-dependent manual | Daily | N |
| ERM-C2606 | Daily suspense reconciliation | Payment suspense accounts are reconciled daily. | Payment Operations reconciles the payment suspense accounts each business day so that unresolved items get identified and cleared on time. | Detective | IT-dependent manual | Daily | N |
| ERM-C2968 | Alert aging monitoring | Alert aging is reported to the BSA Officer weekly. | The BSA Officer receives a weekly report on the aging of open AML alerts. | Detective | IT-dependent manual | Weekly | Y |
| ERM-C3229 | Third-party due diligence before contract | Third-party risk management completes due diligence before contracts are signed. | Before any contract is executed, third-party risk management performs due diligence on the prospective vendor. | Preventive | Manual | Per event | Y |
| ERM-C3233 | Annual contingency funding test | Treasury tests access to contingent funding lines each year. | On an annual basis, Treasury performs a test to confirm the bank can access its contingent funding lines. | Detective | Manual | Annual | Y |
| ERM-C3325 | ACH exposure limit monitoring | Originator exposure is checked against approved limits daily. | Each business day, Payment Operations compares ACH originator exposure against approved limits. | Preventive | Automated | Daily | Y |
| ERM-C3478 | Maker-checker on manual postings | Manual postings need a second reviewer. | Each manual posting is reviewed and approved by a second person, independent of the preparer, before it takes effect. | Preventive | Automated | Per transaction | N |
| ERM-C3504 | Quarterly access recertification | Managers recertify user access quarterly. | Each quarter, managers review and recertify the access held by users on their teams. | Detective | IT-dependent manual | Quarterly | N |
| ERM-C3862 | Income verification checklist | Underwriters confirm income documents before approval. | Before any loan is approved, underwriters review and confirm the borrower's income documentation against the verification checklist. | Preventive | IT-dependent manual | Per transaction | N |
| ERM-C4997 | Quarterly complaint trend review | Compliance reviews complaint trends quarterly. | Each quarter, Compliance reviews customer complaint trends to identify recurring issues and emerging risks. | Detective | Manual | Quarterly | N |

### control_ia

| control_id | title | description (templated) | description (AI) | control_type | nature | frequency | key_control |
|---|---|---|---|---|---|---|---|
| IAC-5044 | Operational test of FHLB and discount window draws | Treasury performs an annual small-dollar draw on each contingent funding source, confirms pledged collateral values with the lender and records the time to funds. Results and any failed steps are reported to ALCO with owners and dates. | Once each year, Treasury executes a small-dollar test draw against every contingent funding source, including the FHLB advance line and the Federal Reserve discount window, to confirm the facilities work in practice. During each draw, Treasury reconciles its record of pledged collateral values to the values confirmed by the lender and logs the elapsed time from request to receipt of funds. Treasury then presents the test results to ALCO, including any step that failed, with a named owner and target completion date for each remediation item. Evidence retained includes draw confirmations, lender collateral statements, the time-to-funds log and the ALCO minutes and presentation. | Detective | Manual | Annual | Y |
| IAC-5069 | Assumption review and back-testing for the ALM model | Treasury back-tests deposit betas and prepayment speeds in Pellmark ALM each quarter and presents variances above tolerance to ALCO. ALCO approves the assumption set annually, and Model Risk validates the model every two years. | Each quarter, Treasury compares the deposit beta and prepayment speed assumptions in Pellmark ALM against actual observed results, and any variance that exceeds the established tolerance is reported to ALCO with an explanation of its cause and any proposed assumption change. Evidence retained for this step includes the quarterly back-testing workpaper and the ALCO meeting package and minutes that reflect the variance discussion. On an annual basis, ALCO reviews and approves the full assumption set, with approval documented in the ALCO minutes. Model Risk performs an independent validation of the model every two years, and the resulting validation report and any findings are retained as evidence. | Detective | Manual | Quarterly | Y |
| IAC-5164 | Independent callback to a number on file before wire release | For outgoing wires above $25,000 or to a new beneficiary, operations staff call the customer at the number on file in Corvessa Core Banking, not the number on the request, and record the call in Brisance Wire Manager. The wire cannot be released until a second operator approves the callback record. | Before any outgoing wire exceeding $25,000, or any wire to a beneficiary not previously paid, is released, operations staff place an independent callback to the customer using the telephone number on file in Corvessa Core Banking rather than any number supplied with the wire request. The operator logs the callback in Brisance Wire Manager, noting the date and time, the number dialed, the individual reached and confirmation of the beneficiary and amount details. Release is blocked in Brisance Wire Manager until a second operator reviews and approves the callback record, so the performer and approver are always different people. The callback log entry and the second operator's approval are retained in Brisance Wire Manager as evidence of control performance for each qualifying wire. | Preventive | IT-dependent manual | Per transaction | N |
| IAC-5300 | Manager and application owner approval of access requests | Access to in-scope applications is requested through Okrin Identity Gateway, which routes each request to the user's manager and the application owner. Provisioning runs only after both approvals, requests outside the role catalogue need Information Security sign-off, and access is removed automatically when a user changes role. | For each request for access to an in-scope application, the user's manager and the application owner review and approve it through Okrin Identity Gateway before any access is granted. The gateway routes every submitted request to both approvers and holds provisioning until both approvals are recorded. Requests for access that falls outside the role catalogue also need sign-off from Information Security before they can proceed. When a user changes role, the gateway removes their existing access automatically, and the request, approval and removal history it retains for each user serves as evidence of the control's operation. | Preventive | Automated | Per transaction | Y |
| IAC-6349 | Committee sign-off with completed risk assessments before launch | Product owners submit a risk assessment signed by Compliance, Operational Risk and Information Security to the New Product Committee. Launch is blocked until the committee approves, and a post-implementation review is completed within six months. | Before any new product or material product change goes live, the product owner presents the New Product Committee with a completed risk assessment that carries sign-off from Compliance, Operational Risk and Information Security. The committee reviews the package at its scheduled meeting, and no launch may proceed until the committee has recorded its approval in the meeting minutes. Within six months after go-live, a post-implementation review is performed and its results are reported back to the committee. Retained evidence consists of the signed risk assessment, the committee minutes documenting approval and the launch date, and the completed post-implementation review, all kept in the committee's product file. | Preventive | Manual | Per event | Y |
| IAC-6482 | Automated sanctions screening with same-day list updates | Brisance Wire Manager screens every outgoing and incoming wire against the sanctions list before release. List updates load automatically on the day they are published, and Compliance documents its review of every potential match before the payment is released or blocked. | Before any wire is released, Brisance Wire Manager automatically screens each incoming and outgoing transfer against the sanctions list, and list updates load into the system on the same day they are published. Any potential match holds the payment in queue until Compliance reviews it, records the disposition, and either releases or blocks the wire. Evidence retained for testing includes the system log of list update load dates and, for each potential match, the documented Compliance review showing the reviewer, the rationale and the final release or block decision. | Preventive | Automated | Per transaction | Y |
| IAC-6591 | Quarterly root cause analysis of complaint themes | Compliance analyzes complaint data from Tessaly Case Manager each quarter by product, channel and theme, assigns a root cause owner to any theme above threshold, and tracks corrective actions to closure. | Each quarter, Compliance extracts complaint data from Tessaly Case Manager and analyzes volumes and trends by product, channel and theme to find emerging or recurring issues. When a theme exceeds the established threshold, Compliance assigns a root cause owner who must investigate the underlying cause and propose corrective actions. Compliance then tracks each corrective action to closure, following up on open items in later quarterly cycles until they are resolved. Evidence retained includes the quarterly analysis workpaper with the Tessaly Case Manager extract, documented owner assignments for above-threshold themes, and the corrective action tracking log showing status and closure dates. | Detective | Manual | Quarterly | Y |
| IAC-6630 | Valuation unit review of third-party appraisals | The valuation unit orders appraisals through an approved panel and completes a review checklist covering comparable sales, appraiser independence and value support before the loan closes. Valuations older than 120 days are re-ordered. | Before each loan closes, valuation unit staff order the third-party appraisal from the approved appraiser panel and review the completed report against a standard review checklist. The checklist confirms that comparable sales are relevant and adequately adjusted, that the appraiser is independent of the borrower and the loan production function, and that the concluded value is supported. Any valuation dated more than 120 days before the closing date is re-ordered rather than relied upon. The signed and dated checklist, the appraisal report and any re-order request are kept in the loan file as evidence of performance. | Detective | Manual | Per transaction | Y |
| IAC-6907 | Above- and below-the-line testing of monitoring scenarios | BSA Compliance runs above- and below-the-line testing on each Merrow AML Monitor scenario every year and maps every product and channel to at least one scenario. Threshold changes are approved by the BSA Officer and validated by Model Risk. | Each year, BSA Compliance performs above- and below-the-line testing on every scenario configured in Merrow AML Monitor, sampling alerted and non-alerted activity around current thresholds to judge whether each threshold is still set appropriately. As part of the same annual review, the team confirms that every product and channel offered by the bank maps to at least one active scenario and updates the coverage mapping to reflect any gaps or changes. Any resulting threshold adjustment requires BSA Officer approval and independent validation by Model Risk before it is implemented in production. Evidence retained includes the testing workpapers and sample results, the signed product and channel coverage map, the BSA Officer's documented approval, and the Model Risk validation memo for each threshold change. | Detective | IT-dependent manual | Annual | Y |
| IAC-7297 | Approval matrix validation in loan origination system | Halbrook Loan Origination compares the approver's delegated authority to the approval matrix before a loan can be booked. Overrides route to Credit Administration, which reviews the override log weekly and escalates unapproved items to the Chief Credit Officer. | Before any loan can move to booking, Halbrook Loan Origination automatically checks the assigned approver's delegated lending authority against the approval matrix and blocks booking when the requested amount or terms fall outside that authority. Any override of this check is routed to Credit Administration. Each week, Credit Administration reviews the system override log, confirms that every override carries a documented approval, and escalates any item lacking one to the Chief Credit Officer for resolution. Retained evidence includes the system-generated override log, the reviewer's sign-off on each weekly review, and the escalation correspondence sent to the Chief Credit Officer along with its disposition. | Preventive | Automated | Per transaction | Y |
| IAC-7714 | Quarterly recertification with revocation tracking | Okrin Identity Gateway issues quarterly recertification campaigns for critical applications. Managers must certify or revoke each entitlement, revocations are completed within five business days, and Information Security reports incomplete campaigns to the Technology Risk Committee. | Each quarter, Information Security launches a recertification campaign in Okrin Identity Gateway that covers every entitlement on the critical applications in scope. The responsible manager reviews each assigned entitlement and either certifies that access is still needed or marks it for revocation, and Information Security removes any revoked access within five business days of the manager's decision. At campaign close, Information Security identifies campaigns with uncertified items and reports them to the Technology Risk Committee. Retained evidence includes the campaign completion export from Okrin Identity Gateway with each reviewer's decision and timestamp, the revocation completion dates measured against the five-day standard, and the committee materials showing the incomplete-campaign report. | Detective | IT-dependent manual | Quarterly | N |
| IAC-8141 | Account activation hold until beneficial ownership is certified | Corvessa Core Banking will not activate a legal entity account until the beneficial ownership certification fields are complete and verified by the onboarding team. Customer risk ratings are recalculated nightly from ownership and activity data. | Corvessa Core Banking applies a system hold that prevents activation of any new legal entity account until every beneficial ownership certification field has been populated and marked as verified by the onboarding team. This preventive control operates automatically at the point of account opening, so an account cannot be released to transact while any required certification field remains blank or unverified. Separately, customer risk ratings are recalculated in a nightly batch using current ownership and account activity data. Evidence retained includes the system configuration settings for the activation hold, the record of onboarding verification for each certified account, and the nightly batch logs for the risk rating recalculation. | Preventive | Automated | Per transaction | N |
| IAC-8207 | Central complaint log with 15-day resolution tracking | All complaints, including verbal branch complaints, are logged in Tessaly Case Manager within one business day. Complaints open longer than 15 days are escalated to the Complaints Manager and reported monthly to the Compliance Committee. | Branch and contact center staff enter every customer complaint into Tessaly Case Manager no later than one business day after receipt, and this includes complaints customers raise verbally at a branch. The Complaints Manager is alerted whenever a case stays unresolved for more than 15 days and works it to closure. Each month the Complaints Manager prepares an aging report from Tessaly Case Manager covering these escalated items and presents it to the Compliance Committee. Evidence retained consists of the case records with intake timestamps, the escalation history, and the monthly report together with Compliance Committee minutes. | Detective | IT-dependent manual | Daily | Y |
| IAC-8814 | Daily reconciliation of payment suspense with aged-item escalation | Payment Operations reconciles each suspense account to Velistra General Ledger daily. Items older than 15 days are escalated to the operations manager and items older than 30 days to the Controller; write-offs need Controller approval. | Each business day, Payment Operations staff reconcile the balance of every payment suspense account to Velistra General Ledger and identify the open items that make up any difference. Open items aged beyond 15 days are escalated to the operations manager for follow-up, and items aged beyond 30 days are escalated to the Controller. No suspense item may be written off without Controller approval. The completed daily reconciliation, the aged-item listing with escalation notes, and the approved write-off requests are retained as evidence of performance and review. | Detective | IT-dependent manual | Daily | Y |
| IAC-8897 | Annual challenge of liquidity stress assumptions | Treasury compares runoff assumptions to recent stress events and to uninsured deposit concentration, documents the rationale for each rate, and obtains challenge from Market Risk before ALCO approval. | Once a year, Treasury reviews the deposit runoff assumptions used in liquidity stress testing against recent stress events and the bank's current concentration of uninsured deposits. For each runoff rate, Treasury writes a rationale explaining why the rate was kept or changed in light of that comparison. Market Risk independently challenges the assumptions and rationale before the package goes to ALCO for approval. Evidence retained includes the comparison workpaper, the rate-by-rate rationale, Market Risk's written challenge and Treasury's responses, and the ALCO minutes recording approval. | Detective | Manual | Annual | Y |

### audit

| audit_id | title | audit_year | start_date | end_date | rating |
|---|---|---|---|---|---|
| AUD-117 | Card Disputes and Wealth Client Onboarding Audit 2023 | 2023 | 2023-09-08 | 2023-11-06 | Satisfactory |
| AUD-164 | BSA/AML Program and Customer Complaints Management Audit 2024 | 2024 | 2024-05-28 | 2024-07-08 | Needs Improvement |
| AUD-212 | Liquidity Management and Wire Transfer Operations Audit 2023 | 2023 | 2023-06-22 | 2023-08-08 | Unsatisfactory |
| AUD-257 | Consumer Mortgage Lending and Customer Complaints Management Audit 2025 | 2025 | 2025-05-06 | 2025-06-18 | Needs Improvement |
| AUD-711 | Liquidity Management Audit 2025 | 2025 | 2025-09-22 | 2025-10-30 | Needs Improvement |
| AUD-759 | BSA/AML Program Audit 2024 | 2024 | 2024-01-21 | 2024-03-16 | Needs Improvement |

### issue

| issue_id | title | description (templated) | description (AI) | source | rating | opened_date | closed_date |
|---|---|---|---|---|---|---|---|
| ISS-1283 | Account activation hold until beneficial ownership is certified not operating as designed | Seven legal entity accounts were activated through a manual override with no BSA approval. | Internal Audit found that the hold meant to keep legal entity accounts inactive until beneficial ownership certification is complete is not working as designed. Seven legal entity accounts were activated by manual override of the hold, and none had BSA approval for the override. Because these accounts became available for use without the required certification sign-off, the control's purpose was defeated in each case. | IA | Medium | 2023-11-18 |  |
| ISS-2285 | MRA: Annual contingency funding test weaknesses | Examiners found that no test draw on the discount window was performed in 2024, and collateral schedules were nine months old. | Examiners determined that Treasury did not execute a test draw on the Federal Reserve discount window at any point during 2024 as part of the annual contingency funding test. Collateral schedules supporting the contingency funding plan were also found to be nine months out of date at the time of review, which limits the bank's ability to rely on pledged collateral values under stress. | Regulator | Medium | 2024-08-30 |  |
| ISS-2861 | Self-identified gap: Third-party due diligence before contract | Management identified that four critical vendors were onboarded with due diligence still open, and one had no SOC 2 report. | During a review of the vendor inventory, management found that four vendors rated as critical had been onboarded and placed into service before their due diligence reviews were closed. For one of these four, no SOC 2 report had been obtained at the time of onboarding, so the bank had no independent assurance over that vendor's control environment. | Self-identified | Medium | 2025-04-30 | 2025-10-17 |
| ISS-4014 | Central complaint log with 15-day resolution tracking not operating as designed | Branch complaints were logged an average of nine days after receipt, and 31 complaints passed 15 days without escalation. | Internal Audit found that complaints received at branches were entered into the central complaint log an average of nine days after receipt, which leaves little of the 15-day resolution window for tracking and follow-up. Within the review population, 31 complaints exceeded 15 days with no escalation to the Complaints Manager, so the log's resolution tracking is not functioning as intended. | IA | High | 2024-07-25 | 2024-11-30 |
| ISS-4077 | 2LOD review: Third-party due diligence before contract | Second-line testing found that four critical vendors were onboarded with due diligence still open, and one had no SOC 2 report. | During second-line testing of third-party onboarding, we found that four vendors classified as critical had been approved and onboarded before their due diligence was complete, with open items still outstanding at contract execution. For one of the four, no SOC 2 report had been obtained or reviewed before onboarding, and nothing in the file showed that a compensating assessment of the vendor's control environment had been performed. | 2nd line | High | 2023-11-08 | 2023-12-30 |
| ISS-4080 | Operational test of FHLB and discount window draws not operating as designed | No test draw on the discount window was performed in 2024, and collateral schedules were nine months old. | Internal Audit found that Treasury did not execute a test draw on the discount window at any point during 2024, so the bank could not show that the operational steps to access this contingent funding source work as designed. The collateral schedules supporting the draw process were nine months old at the time of review and did not reflect current pledged positions. | IA | Medium | 2025-11-04 |  |
| ISS-4180 | Self-identified gap: Privileged session review | Management identified that three generic administrator accounts on Velistra General Ledger were not vaulted, and session logs went unreviewed for four months. | During a self-assessment of privileged access, management found that three generic administrator accounts on Velistra General Ledger had never been placed in the credential vault. Privileged session logs for these accounts also received no review for four months, so administrative activity on the ledger went unmonitored during that period. | Self-identified | Low | 2023-07-30 | 2023-10-19 |
| ISS-4944 | Above- and below-the-line testing of monitoring scenarios not operating as designed | Remote deposit capture was not mapped to any scenario, and below-the-line testing was skipped for 5 of 18 scenarios. | Internal Audit found that remote deposit capture transactions were not mapped to any transaction monitoring scenario, so activity through that channel was not subject to automated surveillance. Above- and below-the-line threshold testing was also incomplete: below-the-line testing was not performed for 5 of the 18 scenarios in production during the review period, and no documented rationale or approved exception supported the omission. | IA | Medium | 2024-03-16 |  |
| ISS-5149 | MRA: Role-based access provisioning weaknesses | Examiners found that fourteen accounts in Velistra General Ledger were provisioned directly by administrators, bypassing the approval workflow. | Examination testing of user access in Velistra General Ledger identified fourteen accounts that administrators had provisioned directly, outside the established approval workflow. No documented business-line or role-based approval existed for these accounts at the time access was granted, indicating that the provisioning control can be bypassed by personnel holding administrative privileges. | Regulator | High | 2023-01-17 | 2023-07-16 |
| ISS-6172 | Operational test of FHLB and discount window draws not operating as designed | No test draw on the discount window was performed in 2024, and collateral schedules were nine months old. | Internal Audit found that Treasury did not execute a test draw on the discount window at any point during 2024, leaving the bank's ability to access contingent funding through that channel unvalidated. In addition, the collateral schedules supporting FHLB and discount window borrowing capacity had last been updated nine months before the review, so reported availability could not be relied upon for liquidity planning. | IA | Low | 2023-08-21 | 2024-01-21 |
| ISS-7325 | MRA: Complaint resolution tracking weaknesses | Examiners found that branch complaints were logged an average of nine days after receipt, and 31 complaints passed 15 days without escalation. | Our review of complaint handling found that complaints received at branches were not entered into the tracking process promptly, with an average lag of nine days between receipt and logging. In addition, 31 complaints remained open beyond 15 days with no evidence of escalation. These conditions limit management's ability to monitor complaint resolution timeliness and to identify potential UDAAP concerns. | Regulator | Medium | 2023-08-14 |  |
| ISS-8558 | 2LOD review: Third-party due diligence before contract | Second-line testing found that four critical vendors were onboarded with due diligence still open, and one had no SOC 2 report. | During second line testing of third-party onboarding, four vendors rated critical were found to have been onboarded and placed under contract while their due diligence remained open. For one of these vendors, no SOC 2 report had been obtained at the time of review, so the control environment of a critical service provider was not assessed before the relationship began. | 2nd line | High | 2024-02-10 |  |
| ISS-8602 | Central complaint log with 15-day resolution tracking not operating as designed | Branch complaints were logged an average of nine days after receipt, and 31 complaints passed 15 days without escalation. | Internal Audit found that complaints received at branches were entered into the central complaint log an average of nine days after receipt, which leaves little of the 15-day resolution window for tracking and follow-up. In the population reviewed, 31 complaints remained open beyond 15 days with no escalation recorded, so the log's resolution tracking is not working as intended. | IA | High | 2024-07-13 |  |
| ISS-8888 | Account activation hold until beneficial ownership is certified not operating as designed | Seven legal entity accounts were activated through a manual override with no BSA approval. | Internal Audit found that the control holding legal entity accounts from activation until beneficial ownership certification is complete did not operate as designed. Seven legal entity accounts were activated through a manual override of the hold, and none of the seven had BSA approval for the override. | IA | Low | 2023-11-06 |  |
| ISS-9449 | Above- and below-the-line testing of monitoring scenarios not operating as designed | Remote deposit capture was not mapped to any scenario, and below-the-line testing was skipped for 5 of 18 scenarios. | Internal Audit found that above- and below-the-line testing of transaction monitoring scenarios is not operating as designed. Remote deposit capture activity has not been mapped to any monitoring scenario, so those transactions fall outside automated surveillance. In addition, the required below-the-line testing was not performed for 5 of the 18 scenarios in the current scenario inventory, leaving thresholds for those scenarios unvalidated. | IA | Medium | 2024-03-21 |  |

## How things connect

Each relationship file, with names in place of IDs.

<details><summary>audit_covered_auditable_entity (10 rows)</summary>

| audit_id | auditable_entity_id |
|---|---|
| Card Disputes and Wealth Client Onboarding Audit 2023 (AUD-117) | Card Disputes (AE-384) |
| Card Disputes and Wealth Client Onboarding Audit 2023 (AUD-117) | Wealth Client Onboarding (AE-587) |
| BSA/AML Program and Customer Complaints Management Audit 2024 (AUD-164) | Customer Complaints Management (AE-352) |
| BSA/AML Program and Customer Complaints Management Audit 2024 (AUD-164) | BSA/AML Program (AE-929) |
| Liquidity Management and Wire Transfer Operations Audit 2023 (AUD-212) | Liquidity Management (AE-400) |
| Liquidity Management and Wire Transfer Operations Audit 2023 (AUD-212) | Wire Transfer Operations (AE-762) |
| Consumer Mortgage Lending and Customer Complaints Management Audit 2025 (AUD-257) | Consumer Mortgage Lending (AE-153) |
| Consumer Mortgage Lending and Customer Complaints Management Audit 2025 (AUD-257) | Customer Complaints Management (AE-352) |
| Liquidity Management Audit 2025 (AUD-711) | Liquidity Management (AE-400) |
| BSA/AML Program Audit 2024 (AUD-759) | BSA/AML Program (AE-929) |

</details>

<details><summary>audit_raised_issue (8 rows)</summary>

| audit_id | issue_id |
|---|---|
| Card Disputes and Wealth Client Onboarding Audit 2023 (AUD-117) | Account activation hold until beneficial ownership is certified not operating as designed (ISS-1283) |
| Card Disputes and Wealth Client Onboarding Audit 2023 (AUD-117) | Account activation hold until beneficial ownership is certified not operating as designed (ISS-8888) |
| BSA/AML Program and Customer Complaints Management Audit 2024 (AUD-164) | Central complaint log with 15-day resolution tracking not operating as designed (ISS-4014) |
| BSA/AML Program and Customer Complaints Management Audit 2024 (AUD-164) | Central complaint log with 15-day resolution tracking not operating as designed (ISS-8602) |
| Liquidity Management and Wire Transfer Operations Audit 2023 (AUD-212) | Operational test of FHLB and discount window draws not operating as designed (ISS-6172) |
| Liquidity Management Audit 2025 (AUD-711) | Operational test of FHLB and discount window draws not operating as designed (ISS-4080) |
| BSA/AML Program Audit 2024 (AUD-759) | Above- and below-the-line testing of monitoring scenarios not operating as designed (ISS-4944) |
| BSA/AML Program Audit 2024 (AUD-759) | Above- and below-the-line testing of monitoring scenarios not operating as designed (ISS-9449) |

</details>

<details><summary>audit_tested_control_ia (19 rows)</summary>

| audit_id | control_id |
|---|---|
| Card Disputes and Wealth Client Onboarding Audit 2023 (AUD-117) | Quarterly root cause analysis of complaint themes (IAC-6591) |
| Card Disputes and Wealth Client Onboarding Audit 2023 (AUD-117) | Account activation hold until beneficial ownership is certified (IAC-8141) |
| BSA/AML Program and Customer Complaints Management Audit 2024 (AUD-164) | Automated sanctions screening with same-day list updates (IAC-6482) |
| BSA/AML Program and Customer Complaints Management Audit 2024 (AUD-164) | Quarterly root cause analysis of complaint themes (IAC-6591) |
| BSA/AML Program and Customer Complaints Management Audit 2024 (AUD-164) | Above- and below-the-line testing of monitoring scenarios (IAC-6907) |
| BSA/AML Program and Customer Complaints Management Audit 2024 (AUD-164) | Account activation hold until beneficial ownership is certified (IAC-8141) |
| BSA/AML Program and Customer Complaints Management Audit 2024 (AUD-164) | Central complaint log with 15-day resolution tracking (IAC-8207) |
| Liquidity Management and Wire Transfer Operations Audit 2023 (AUD-212) | Operational test of FHLB and discount window draws (IAC-5044) |
| Liquidity Management and Wire Transfer Operations Audit 2023 (AUD-212) | Independent callback to a number on file before wire release (IAC-5164) |
| Liquidity Management and Wire Transfer Operations Audit 2023 (AUD-212) | Automated sanctions screening with same-day list updates (IAC-6482) |
| Liquidity Management and Wire Transfer Operations Audit 2023 (AUD-212) | Annual challenge of liquidity stress assumptions (IAC-8897) |
| Consumer Mortgage Lending and Customer Complaints Management Audit 2025 (AUD-257) | Quarterly root cause analysis of complaint themes (IAC-6591) |
| Consumer Mortgage Lending and Customer Complaints Management Audit 2025 (AUD-257) | Valuation unit review of third-party appraisals (IAC-6630) |
| Consumer Mortgage Lending and Customer Complaints Management Audit 2025 (AUD-257) | Central complaint log with 15-day resolution tracking (IAC-8207) |
| Liquidity Management Audit 2025 (AUD-711) | Operational test of FHLB and discount window draws (IAC-5044) |
| Liquidity Management Audit 2025 (AUD-711) | Annual challenge of liquidity stress assumptions (IAC-8897) |
| BSA/AML Program Audit 2024 (AUD-759) | Automated sanctions screening with same-day list updates (IAC-6482) |
| BSA/AML Program Audit 2024 (AUD-759) | Above- and below-the-line testing of monitoring scenarios (IAC-6907) |
| BSA/AML Program Audit 2024 (AUD-759) | Account activation hold until beneficial ownership is certified (IAC-8141) |

</details>

<details><summary>auditable_entity_exposed_to_risk_erm (20 rows)</summary>

| auditable_entity_id | risk_id |
|---|---|
| Consumer Mortgage Lending (AE-153) | Borrower income not verified (ERM-R4055) |
| Customer Complaints Management (AE-352) | Complaint trends not analyzed (ERM-R1240) |
| Customer Complaints Management (AE-352) | Complaints not captured or resolved (ERM-R4131) |
| Card Disputes (AE-384) | Complaint trends not analyzed (ERM-R1240) |
| Liquidity Management (AE-400) | Contingency funding plan not executable (ERM-R2689) |
| Third-Party Risk Management (AE-457) | Fintech partner risk not assessed (ERM-R3450) |
| General Ledger & Financial Close (AE-518) | Unreconciled payment suspense balances (ERM-R1512) |
| General Ledger & Financial Close (AE-518) | Unmonitored privileged access (ERM-R1782) |
| ACH Operations (AE-604) | Unreconciled payment suspense balances (ERM-R1512) |
| ACH Operations (AE-604) | Unauthorized ACH originations (ERM-R1647) |
| Identity & Access Management (AE-755) | Unmonitored privileged access (ERM-R1782) |
| Identity & Access Management (AE-755) | Inappropriate access not removed (ERM-R1809) |
| Identity & Access Management (AE-755) | Excessive user access to critical systems (ERM-R2580) |
| Wire Transfer Operations (AE-762) | Sanctions screening failures (ERM-R2184) |
| Wire Transfer Operations (AE-762) | Fraudulent wire transfers (ERM-R4982) |
| New Product Approval (AE-882) | Fintech partner risk not assessed (ERM-R3450) |
| BSA/AML Program (AE-929) | Alert backlog in AML investigations (ERM-R2069) |
| BSA/AML Program (AE-929) | Sanctions screening failures (ERM-R2184) |
| Treasury ALM (AE-976) | Stale deposit beta assumptions (ERM-R3459) |
| Treasury ALM (AE-976) | Interest rate risk model mis-specification (ERM-R3603) |

</details>

<details><summary>auditable_entity_exposed_to_risk_ia (21 rows)</summary>

| auditable_entity_id | risk_id |
|---|---|
| Consumer Mortgage Lending (AE-153) | Appraisal review and independence (IAR-6267) |
| Commercial Loan Origination (AE-165) | Appraisal review and independence (IAR-6267) |
| Commercial Loan Origination (AE-165) | Lending authority not enforced at approval (IAR-7771) |
| Customer Complaints Management (AE-352) | Complaint intake and resolution (IAR-5050) |
| Customer Complaints Management (AE-352) | Complaint trend analysis (IAR-8862) |
| Card Disputes (AE-384) | Complaint trend analysis (IAR-8862) |
| Liquidity Management (AE-400) | Contingency funding plan testing (IAR-6108) |
| Liquidity Management (AE-400) | Liquidity stress scenario design (IAR-8634) |
| General Ledger & Financial Close (AE-518) | Payment suspense reconciliation (IAR-6809) |
| Wealth Client Onboarding (AE-587) | Beneficial ownership and CDD refresh (IAR-8993) |
| ACH Operations (AE-604) | Payment suspense reconciliation (IAR-6809) |
| Identity & Access Management (AE-755) | User access provisioning (IAR-5246) |
| Identity & Access Management (AE-755) | Periodic access recertification (IAR-6395) |
| Wire Transfer Operations (AE-762) | Sanctions screening of payments (IAR-5150) |
| Wire Transfer Operations (AE-762) | Wire callback verification (IAR-6788) |
| New Product Approval (AE-882) | New product approval governance (IAR-6295) |
| BSA/AML Program (AE-929) | Sanctions screening of payments (IAR-5150) |
| BSA/AML Program (AE-929) | AML scenario tuning and coverage (IAR-5757) |
| BSA/AML Program (AE-929) | Beneficial ownership and CDD refresh (IAR-8993) |
| Treasury ALM (AE-976) | Liquidity stress scenario design (IAR-8634) |
| Treasury ALM (AE-976) | ALM model assumptions and validation (IAR-9035) |

</details>

<details><summary>auditable_entity_performs_process (18 rows)</summary>

| auditable_entity_id | process_id |
|---|---|
| Consumer Mortgage Lending (AE-153) | Mortgage underwriting (PRC-302) |
| Commercial Loan Origination (AE-165) | Loan application intake (PRC-299) |
| Commercial Loan Origination (AE-165) | Credit underwriting and approval (PRC-815) |
| Customer Complaints Management (AE-352) | Complaint intake and resolution (PRC-192) |
| Card Disputes (AE-384) | Card dispute processing (PRC-797) |
| Liquidity Management (AE-400) | Contingency funding planning (PRC-568) |
| Third-Party Risk Management (AE-457) | Vendor onboarding (PRC-768) |
| General Ledger & Financial Close (AE-518) | Payment suspense reconciliation (PRC-630) |
| Wealth Client Onboarding (AE-587) | Wealth client onboarding (PRC-533) |
| ACH Operations (AE-604) | ACH file origination (PRC-991) |
| Identity & Access Management (AE-755) | User access provisioning (PRC-154) |
| Identity & Access Management (AE-755) | Access recertification (PRC-954) |
| Wire Transfer Operations (AE-762) | Wire initiation and release (PRC-677) |
| Deposit Account Servicing (AE-855) | Manual account adjustments (PRC-407) |
| New Product Approval (AE-882) | New product review (PRC-597) |
| BSA/AML Program (AE-929) | Customer due diligence (PRC-188) |
| BSA/AML Program (AE-929) | Transaction monitoring alert review (PRC-869) |
| Treasury ALM (AE-976) | Interest rate risk measurement (PRC-330) |

</details>

<details><summary>business_unit_owns_auditable_entity (15 rows)</summary>

| business_unit_id | auditable_entity_id |
|---|---|
| Compliance (BU-215) | New Product Approval (AE-882) |
| Compliance (BU-215) | BSA/AML Program (AE-929) |
| Commercial Lending (BU-223) | Commercial Loan Origination (AE-165) |
| Payment Operations (BU-266) | ACH Operations (AE-604) |
| Payment Operations (BU-266) | Wire Transfer Operations (AE-762) |
| Card Services (BU-272) | Card Disputes (AE-384) |
| Enterprise Technology (BU-313) | Identity & Access Management (AE-755) |
| Consumer Lending (BU-586) | Consumer Mortgage Lending (AE-153) |
| Retail Branch Network (BU-662) | Customer Complaints Management (AE-352) |
| Corporate Treasury (BU-767) | Liquidity Management (AE-400) |
| Corporate Treasury (BU-767) | Treasury ALM (AE-976) |
| Deposit Operations (BU-931) | Deposit Account Servicing (AE-855) |
| Private Wealth Advisory (BU-951) | Wealth Client Onboarding (AE-587) |
| Finance (BU-990) | Third-Party Risk Management (AE-457) |
| Finance (BU-990) | General Ledger & Financial Close (AE-518) |

</details>

<details><summary>control_depends_on_system_erm (22 rows)</summary>

| control_id | system_id |
|---|---|
| Role-based access provisioning (ERM-C1134) | Okrin Identity Gateway (SYS-879) |
| Real-time payment sanctions screening (ERM-C1643) | Quorvane Payments Hub (SYS-533) |
| Real-time payment sanctions screening (ERM-C1643) | Brisance Wire Manager (SYS-960) |
| Annual ALM assumption approval (ERM-C1862) | Pellmark ALM (SYS-253) |
| Privileged session review (ERM-C2315) | Corvessa Core Banking (SYS-254) |
| Privileged session review (ERM-C2315) | Okrin Identity Gateway (SYS-879) |
| Privileged session review (ERM-C2315) | Velistra General Ledger (SYS-931) |
| Wire callback verification (ERM-C2452) | Corvessa Core Banking (SYS-254) |
| Wire callback verification (ERM-C2452) | Brisance Wire Manager (SYS-960) |
| Complaint resolution tracking (ERM-C2539) | Tessaly Case Manager (SYS-100) |
| Daily suspense reconciliation (ERM-C2606) | Quorvane Payments Hub (SYS-533) |
| Daily suspense reconciliation (ERM-C2606) | Velistra General Ledger (SYS-931) |
| Alert aging monitoring (ERM-C2968) | Tessaly Case Manager (SYS-100) |
| Alert aging monitoring (ERM-C2968) | Merrow AML Monitor (SYS-170) |
| Annual contingency funding test (ERM-C3233) | Pellmark ALM (SYS-253) |
| ACH exposure limit monitoring (ERM-C3325) | Quorvane Payments Hub (SYS-533) |
| Maker-checker on manual postings (ERM-C3478) | Corvessa Core Banking (SYS-254) |
| Quarterly access recertification (ERM-C3504) | Corvessa Core Banking (SYS-254) |
| Quarterly access recertification (ERM-C3504) | Okrin Identity Gateway (SYS-879) |
| Income verification checklist (ERM-C3862) | Halbrook Loan Origination (SYS-772) |
| Quarterly complaint trend review (ERM-C4997) | Tessaly Case Manager (SYS-100) |
| Quarterly complaint trend review (ERM-C4997) | Ylvara Data Warehouse (SYS-526) |

</details>

<details><summary>control_depends_on_system_ia (20 rows)</summary>

| control_id | system_id |
|---|---|
| Operational test of FHLB and discount window draws (IAC-5044) | Pellmark ALM (SYS-253) |
| Assumption review and back-testing for the ALM model (IAC-5069) | Pellmark ALM (SYS-253) |
| Independent callback to a number on file before wire release (IAC-5164) | Corvessa Core Banking (SYS-254) |
| Independent callback to a number on file before wire release (IAC-5164) | Brisance Wire Manager (SYS-960) |
| Manager and application owner approval of access requests (IAC-5300) | Okrin Identity Gateway (SYS-879) |
| Automated sanctions screening with same-day list updates (IAC-6482) | Quorvane Payments Hub (SYS-533) |
| Automated sanctions screening with same-day list updates (IAC-6482) | Brisance Wire Manager (SYS-960) |
| Quarterly root cause analysis of complaint themes (IAC-6591) | Tessaly Case Manager (SYS-100) |
| Quarterly root cause analysis of complaint themes (IAC-6591) | Ylvara Data Warehouse (SYS-526) |
| Valuation unit review of third-party appraisals (IAC-6630) | Halbrook Loan Origination (SYS-772) |
| Above- and below-the-line testing of monitoring scenarios (IAC-6907) | Merrow AML Monitor (SYS-170) |
| Above- and below-the-line testing of monitoring scenarios (IAC-6907) | Ylvara Data Warehouse (SYS-526) |
| Approval matrix validation in loan origination system (IAC-7297) | Halbrook Loan Origination (SYS-772) |
| Quarterly recertification with revocation tracking (IAC-7714) | Corvessa Core Banking (SYS-254) |
| Quarterly recertification with revocation tracking (IAC-7714) | Okrin Identity Gateway (SYS-879) |
| Account activation hold until beneficial ownership is certified (IAC-8141) | Corvessa Core Banking (SYS-254) |
| Central complaint log with 15-day resolution tracking (IAC-8207) | Tessaly Case Manager (SYS-100) |
| Daily reconciliation of payment suspense with aged-item escalation (IAC-8814) | Quorvane Payments Hub (SYS-533) |
| Daily reconciliation of payment suspense with aged-item escalation (IAC-8814) | Velistra General Ledger (SYS-931) |
| Annual challenge of liquidity stress assumptions (IAC-8897) | Pellmark ALM (SYS-253) |

</details>

<details><summary>control_mitigates_risk_erm (15 rows)</summary>

| control_id | risk_id |
|---|---|
| Role-based access provisioning (ERM-C1134) | Excessive user access to critical systems (ERM-R2580) |
| Real-time payment sanctions screening (ERM-C1643) | Sanctions screening failures (ERM-R2184) |
| Annual ALM assumption approval (ERM-C1862) | Stale deposit beta assumptions (ERM-R3459) |
| Annual ALM assumption approval (ERM-C1862) | Interest rate risk model mis-specification (ERM-R3603) |
| Privileged session review (ERM-C2315) | Unmonitored privileged access (ERM-R1782) |
| Wire callback verification (ERM-C2452) | Fraudulent wire transfers (ERM-R4982) |
| Complaint resolution tracking (ERM-C2539) | Complaints not captured or resolved (ERM-R4131) |
| Daily suspense reconciliation (ERM-C2606) | Unreconciled payment suspense balances (ERM-R1512) |
| Alert aging monitoring (ERM-C2968) | Alert backlog in AML investigations (ERM-R2069) |
| Third-party due diligence before contract (ERM-C3229) | Fintech partner risk not assessed (ERM-R3450) |
| Annual contingency funding test (ERM-C3233) | Contingency funding plan not executable (ERM-R2689) |
| ACH exposure limit monitoring (ERM-C3325) | Unauthorized ACH originations (ERM-R1647) |
| Quarterly access recertification (ERM-C3504) | Inappropriate access not removed (ERM-R1809) |
| Income verification checklist (ERM-C3862) | Borrower income not verified (ERM-R4055) |
| Quarterly complaint trend review (ERM-C4997) | Complaint trends not analyzed (ERM-R1240) |

</details>

<details><summary>control_mitigates_risk_ia (15 rows)</summary>

| control_id | risk_id |
|---|---|
| Operational test of FHLB and discount window draws (IAC-5044) | Contingency funding plan testing (IAR-6108) |
| Assumption review and back-testing for the ALM model (IAC-5069) | ALM model assumptions and validation (IAR-9035) |
| Independent callback to a number on file before wire release (IAC-5164) | Wire callback verification (IAR-6788) |
| Manager and application owner approval of access requests (IAC-5300) | User access provisioning (IAR-5246) |
| Committee sign-off with completed risk assessments before launch (IAC-6349) | New product approval governance (IAR-6295) |
| Automated sanctions screening with same-day list updates (IAC-6482) | Sanctions screening of payments (IAR-5150) |
| Quarterly root cause analysis of complaint themes (IAC-6591) | Complaint trend analysis (IAR-8862) |
| Valuation unit review of third-party appraisals (IAC-6630) | Appraisal review and independence (IAR-6267) |
| Above- and below-the-line testing of monitoring scenarios (IAC-6907) | AML scenario tuning and coverage (IAR-5757) |
| Approval matrix validation in loan origination system (IAC-7297) | Lending authority not enforced at approval (IAR-7771) |
| Quarterly recertification with revocation tracking (IAC-7714) | Periodic access recertification (IAR-6395) |
| Account activation hold until beneficial ownership is certified (IAC-8141) | Beneficial ownership and CDD refresh (IAR-8993) |
| Central complaint log with 15-day resolution tracking (IAC-8207) | Complaint intake and resolution (IAR-5050) |
| Daily reconciliation of payment suspense with aged-item escalation (IAC-8814) | Payment suspense reconciliation (IAR-6809) |
| Annual challenge of liquidity stress assumptions (IAC-8897) | Liquidity stress scenario design (IAR-8634) |

</details>

<details><summary>control_owned_by_person_erm (15 rows)</summary>

| control_id | person_id |
|---|---|
| Role-based access provisioning (ERM-C1134) | Corinne Galloway (P-1755) |
| Real-time payment sanctions screening (ERM-C1643) | Rosalind Holloway (P-5896) |
| Annual ALM assumption approval (ERM-C1862) | Corinne Galloway (P-1755) |
| Privileged session review (ERM-C2315) | Yusuf Whitcombe (P-6927) |
| Wire callback verification (ERM-C2452) | Adaeze Nakamura (P-3378) |
| Complaint resolution tracking (ERM-C2539) | Harriet Quinlan (P-1271) |
| Daily suspense reconciliation (ERM-C2606) | Corinne Abernathy (P-9676) |
| Alert aging monitoring (ERM-C2968) | Rosalind Zielinski (P-3275) |
| Third-party due diligence before contract (ERM-C3229) | Rosalind Zielinski (P-3275) |
| Annual contingency funding test (ERM-C3233) | Corinne Abernathy (P-9676) |
| ACH exposure limit monitoring (ERM-C3325) | Corinne Nakamura (P-8293) |
| Maker-checker on manual postings (ERM-C3478) | Corinne Galloway (P-1755) |
| Quarterly access recertification (ERM-C3504) | Rosalind Galloway (P-3407) |
| Income verification checklist (ERM-C3862) | Alma Rasmussen (P-6848) |
| Quarterly complaint trend review (ERM-C4997) | Adaeze Nakamura (P-3378) |

</details>

<details><summary>control_owned_by_person_ia (15 rows)</summary>

| control_id | person_id |
|---|---|
| Operational test of FHLB and discount window draws (IAC-5044) | Adaeze Eastwick (P-1969) |
| Assumption review and back-testing for the ALM model (IAC-5069) | Corinne Nakamura (P-8293) |
| Independent callback to a number on file before wire release (IAC-5164) | Zelda Lindqvist (P-6147) |
| Manager and application owner approval of access requests (IAC-5300) | Yusuf Whitcombe (P-6927) |
| Committee sign-off with completed risk assessments before launch (IAC-6349) | Corinne Galloway (P-1755) |
| Automated sanctions screening with same-day list updates (IAC-6482) | Yusuf Whitcombe (P-6927) |
| Quarterly root cause analysis of complaint themes (IAC-6591) | Valeria Szabo (P-4682) |
| Valuation unit review of third-party appraisals (IAC-6630) | Corinne Yamamoto (P-1280) |
| Above- and below-the-line testing of monitoring scenarios (IAC-6907) | Adaeze Galloway (P-6828) |
| Approval matrix validation in loan origination system (IAC-7297) | Adaeze Nakamura (P-3378) |
| Quarterly recertification with revocation tracking (IAC-7714) | Alma Rasmussen (P-6848) |
| Account activation hold until beneficial ownership is certified (IAC-8141) | Corinne Nakamura (P-8293) |
| Central complaint log with 15-day resolution tracking (IAC-8207) | Valeria Szabo (P-4682) |
| Daily reconciliation of payment suspense with aged-item escalation (IAC-8814) | Rosalind Zielinski (P-3275) |
| Annual challenge of liquidity stress assumptions (IAC-8897) | Corinne Uriarte (P-4486) |

</details>

<details><summary>issue_against_control_erm (7 rows)</summary>

| issue_id | control_id |
|---|---|
| MRA: Annual contingency funding test weaknesses (ISS-2285) | Annual contingency funding test (ERM-C3233) |
| Self-identified gap: Third-party due diligence before contract (ISS-2861) | Third-party due diligence before contract (ERM-C3229) |
| 2LOD review: Third-party due diligence before contract (ISS-4077) | Third-party due diligence before contract (ERM-C3229) |
| Self-identified gap: Privileged session review (ISS-4180) | Privileged session review (ERM-C2315) |
| MRA: Role-based access provisioning weaknesses (ISS-5149) | Role-based access provisioning (ERM-C1134) |
| MRA: Complaint resolution tracking weaknesses (ISS-7325) | Complaint resolution tracking (ERM-C2539) |
| 2LOD review: Third-party due diligence before contract (ISS-8558) | Third-party due diligence before contract (ERM-C3229) |

</details>

<details><summary>issue_against_control_ia (8 rows)</summary>

| issue_id | control_id |
|---|---|
| Account activation hold until beneficial ownership is certified not operating as designed (ISS-1283) | Account activation hold until beneficial ownership is certified (IAC-8141) |
| Central complaint log with 15-day resolution tracking not operating as designed (ISS-4014) | Central complaint log with 15-day resolution tracking (IAC-8207) |
| Operational test of FHLB and discount window draws not operating as designed (ISS-4080) | Operational test of FHLB and discount window draws (IAC-5044) |
| Above- and below-the-line testing of monitoring scenarios not operating as designed (ISS-4944) | Above- and below-the-line testing of monitoring scenarios (IAC-6907) |
| Operational test of FHLB and discount window draws not operating as designed (ISS-6172) | Operational test of FHLB and discount window draws (IAC-5044) |
| Central complaint log with 15-day resolution tracking not operating as designed (ISS-8602) | Central complaint log with 15-day resolution tracking (IAC-8207) |
| Account activation hold until beneficial ownership is certified not operating as designed (ISS-8888) | Account activation hold until beneficial ownership is certified (IAC-8141) |
| Above- and below-the-line testing of monitoring scenarios not operating as designed (ISS-9449) | Above- and below-the-line testing of monitoring scenarios (IAC-6907) |

</details>

<details><summary>issue_against_risk_erm (7 rows)</summary>

| issue_id | risk_id |
|---|---|
| MRA: Annual contingency funding test weaknesses (ISS-2285) | Contingency funding plan not executable (ERM-R2689) |
| Self-identified gap: Third-party due diligence before contract (ISS-2861) | Fintech partner risk not assessed (ERM-R3450) |
| 2LOD review: Third-party due diligence before contract (ISS-4077) | Fintech partner risk not assessed (ERM-R3450) |
| Self-identified gap: Privileged session review (ISS-4180) | Unmonitored privileged access (ERM-R1782) |
| MRA: Role-based access provisioning weaknesses (ISS-5149) | Excessive user access to critical systems (ERM-R2580) |
| MRA: Complaint resolution tracking weaknesses (ISS-7325) | Complaints not captured or resolved (ERM-R4131) |
| 2LOD review: Third-party due diligence before contract (ISS-8558) | Fintech partner risk not assessed (ERM-R3450) |

</details>

<details><summary>issue_against_risk_ia (8 rows)</summary>

| issue_id | risk_id |
|---|---|
| Account activation hold until beneficial ownership is certified not operating as designed (ISS-1283) | Beneficial ownership and CDD refresh (IAR-8993) |
| Central complaint log with 15-day resolution tracking not operating as designed (ISS-4014) | Complaint intake and resolution (IAR-5050) |
| Operational test of FHLB and discount window draws not operating as designed (ISS-4080) | Contingency funding plan testing (IAR-6108) |
| Above- and below-the-line testing of monitoring scenarios not operating as designed (ISS-4944) | AML scenario tuning and coverage (IAR-5757) |
| Operational test of FHLB and discount window draws not operating as designed (ISS-6172) | Contingency funding plan testing (IAR-6108) |
| Central complaint log with 15-day resolution tracking not operating as designed (ISS-8602) | Complaint intake and resolution (IAR-5050) |
| Account activation hold until beneficial ownership is certified not operating as designed (ISS-8888) | Beneficial ownership and CDD refresh (IAR-8993) |
| Above- and below-the-line testing of monitoring scenarios not operating as designed (ISS-9449) | AML scenario tuning and coverage (IAR-5757) |

</details>

<details><summary>issue_owned_by_person (15 rows)</summary>

| issue_id | person_id |
|---|---|
| Account activation hold until beneficial ownership is certified not operating as designed (ISS-1283) | Zelda Lindqvist (P-6147) |
| MRA: Annual contingency funding test weaknesses (ISS-2285) | Corinne Yamamoto (P-1280) |
| Self-identified gap: Third-party due diligence before contract (ISS-2861) | Zelda Lindqvist (P-6147) |
| Central complaint log with 15-day resolution tracking not operating as designed (ISS-4014) | Adaeze Nakamura (P-3378) |
| 2LOD review: Third-party due diligence before contract (ISS-4077) | Marisol Rasmussen (P-2333) |
| Operational test of FHLB and discount window draws not operating as designed (ISS-4080) | Zelda Lindqvist (P-6147) |
| Self-identified gap: Privileged session review (ISS-4180) | Zelda Lindqvist (P-6147) |
| Above- and below-the-line testing of monitoring scenarios not operating as designed (ISS-4944) | Corinne Galloway (P-1755) |
| MRA: Role-based access provisioning weaknesses (ISS-5149) | Adaeze Nakamura (P-3378) |
| Operational test of FHLB and discount window draws not operating as designed (ISS-6172) | Yusuf Whitcombe (P-6927) |
| MRA: Complaint resolution tracking weaknesses (ISS-7325) | Adaeze Eastwick (P-1969) |
| 2LOD review: Third-party due diligence before contract (ISS-8558) | Yusuf Whitcombe (P-6927) |
| Central complaint log with 15-day resolution tracking not operating as designed (ISS-8602) | Marisol Rasmussen (P-2333) |
| Account activation hold until beneficial ownership is certified not operating as designed (ISS-8888) | Corinne Galloway (P-1755) |
| Above- and below-the-line testing of monitoring scenarios not operating as designed (ISS-9449) | Corinne Uriarte (P-4486) |

</details>

<details><summary>process_runs_on_system (21 rows)</summary>

| process_id | system_id |
|---|---|
| User access provisioning (PRC-154) | Okrin Identity Gateway (SYS-879) |
| Customer due diligence (PRC-188) | Corvessa Core Banking (SYS-254) |
| Complaint intake and resolution (PRC-192) | Tessaly Case Manager (SYS-100) |
| Loan application intake (PRC-299) | Halbrook Loan Origination (SYS-772) |
| Mortgage underwriting (PRC-302) | Halbrook Loan Origination (SYS-772) |
| Interest rate risk measurement (PRC-330) | Pellmark ALM (SYS-253) |
| Interest rate risk measurement (PRC-330) | Ylvara Data Warehouse (SYS-526) |
| Manual account adjustments (PRC-407) | Corvessa Core Banking (SYS-254) |
| Wealth client onboarding (PRC-533) | Corvessa Core Banking (SYS-254) |
| Contingency funding planning (PRC-568) | Pellmark ALM (SYS-253) |
| Payment suspense reconciliation (PRC-630) | Quorvane Payments Hub (SYS-533) |
| Payment suspense reconciliation (PRC-630) | Velistra General Ledger (SYS-931) |
| Wire initiation and release (PRC-677) | Corvessa Core Banking (SYS-254) |
| Wire initiation and release (PRC-677) | Brisance Wire Manager (SYS-960) |
| Card dispute processing (PRC-797) | Tessaly Case Manager (SYS-100) |
| Card dispute processing (PRC-797) | Corvessa Core Banking (SYS-254) |
| Credit underwriting and approval (PRC-815) | Halbrook Loan Origination (SYS-772) |
| Transaction monitoring alert review (PRC-869) | Tessaly Case Manager (SYS-100) |
| Transaction monitoring alert review (PRC-869) | Merrow AML Monitor (SYS-170) |
| Access recertification (PRC-954) | Okrin Identity Gateway (SYS-879) |
| ACH file origination (PRC-991) | Quorvane Payments Hub (SYS-533) |

</details>

<details><summary>regulation_requires_control_erm (9 rows)</summary>

| regulation_id | control_id |
|---|---|
| Interagency Guidance on Third-Party Relationships (REG-249) | Third-party due diligence before contract (ERM-C3229) |
| Bank Secrecy Act (REG-542) | Alert aging monitoring (ERM-C2968) |
| Gramm-Leach-Bliley Act (REG-642) | Role-based access provisioning (ERM-C1134) |
| Interagency Policy Statement on Funding and Liquidity Risk Management (REG-693) | Annual contingency funding test (ERM-C3233) |
| Regulation E (Electronic Fund Transfers) (REG-787) | Maker-checker on manual postings (ERM-C3478) |
| OFAC Regulations (REG-852) | Real-time payment sanctions screening (ERM-C1643) |
| Sarbanes-Oxley Act Section 404 (REG-935) | Privileged session review (ERM-C2315) |
| Sarbanes-Oxley Act Section 404 (REG-935) | Daily suspense reconciliation (ERM-C2606) |
| Sarbanes-Oxley Act Section 404 (REG-935) | Quarterly access recertification (ERM-C3504) |

</details>

<details><summary>regulation_requires_control_ia (10 rows)</summary>

| regulation_id | control_id |
|---|---|
| Bank Secrecy Act (REG-542) | Above- and below-the-line testing of monitoring scenarios (IAC-6907) |
| Bank Secrecy Act (REG-542) | Account activation hold until beneficial ownership is certified (IAC-8141) |
| OCC Heightened Standards (REG-589) | Committee sign-off with completed risk assessments before launch (IAC-6349) |
| OCC Heightened Standards (REG-589) | Approval matrix validation in loan origination system (IAC-7297) |
| Gramm-Leach-Bliley Act (REG-642) | Manager and application owner approval of access requests (IAC-5300) |
| Interagency Policy Statement on Funding and Liquidity Risk Management (REG-693) | Operational test of FHLB and discount window draws (IAC-5044) |
| Interagency Policy Statement on Funding and Liquidity Risk Management (REG-693) | Annual challenge of liquidity stress assumptions (IAC-8897) |
| OFAC Regulations (REG-852) | Automated sanctions screening with same-day list updates (IAC-6482) |
| Sarbanes-Oxley Act Section 404 (REG-935) | Quarterly recertification with revocation tracking (IAC-7714) |
| Sarbanes-Oxley Act Section 404 (REG-935) | Daily reconciliation of payment suspense with aged-item escalation (IAC-8814) |

</details>

<details><summary>segment_has_business_unit (12 rows)</summary>

| segment_id | business_unit_id |
|---|---|
| Corporate Functions (SEG-20) | Compliance (BU-215) |
| Corporate Functions (SEG-20) | Finance (BU-990) |
| Consumer Banking (SEG-32) | Card Services (BU-272) |
| Consumer Banking (SEG-32) | Consumer Lending (BU-586) |
| Consumer Banking (SEG-32) | Retail Branch Network (BU-662) |
| Technology (SEG-34) | Enterprise Technology (BU-313) |
| Operations (SEG-55) | Payment Operations (BU-266) |
| Operations (SEG-55) | Deposit Operations (BU-931) |
| Wealth Management (SEG-71) | Private Wealth Advisory (BU-951) |
| Treasury & Markets (SEG-78) | Corporate Treasury (BU-767) |
| Commercial Banking (SEG-80) | Commercial Lending (BU-223) |
| Commercial Banking (SEG-80) | Treasury Management Services (BU-549) |

</details>

<details><summary>taxonomy_node_classifies_risk_erm (15 rows)</summary>

| taxonomy_node_id | risk_id |
|---|---|
| Customer Complaints (ERMT-562) | Complaint trends not analyzed (ERM-R1240) |
| Customer Complaints (ERMT-562) | Complaints not captured or resolved (ERM-R4131) |
| New Products & Initiatives (ERMT-637) | Fintech partner risk not assessed (ERM-R3450) |
| Access & Identity (ERMT-668) | Unmonitored privileged access (ERM-R1782) |
| Access & Identity (ERMT-668) | Inappropriate access not removed (ERM-R1809) |
| Access & Identity (ERMT-668) | Excessive user access to critical systems (ERM-R2580) |
| Contingency Funding (ERMT-751) | Contingency funding plan not executable (ERM-R2689) |
| Banking Book IRR (ERMT-820) | Stale deposit beta assumptions (ERM-R3459) |
| Banking Book IRR (ERMT-820) | Interest rate risk model mis-specification (ERM-R3603) |
| Underwriting & Origination (ERMT-863) | Borrower income not verified (ERM-R4055) |
| Transaction Processing (ERMT-897) | Unreconciled payment suspense balances (ERM-R1512) |
| Transaction Processing (ERMT-897) | Unauthorized ACH originations (ERM-R1647) |
| Transaction Processing (ERMT-897) | Fraudulent wire transfers (ERM-R4982) |
| BSA/AML (ERMT-927) | Alert backlog in AML investigations (ERM-R2069) |
| BSA/AML (ERMT-927) | Sanctions screening failures (ERM-R2184) |

</details>

<details><summary>taxonomy_node_classifies_risk_ia (15 rows)</summary>

| taxonomy_node_id | risk_id |
|---|---|
| Loan Origination (IAT-271) | Appraisal review and independence (IAR-6267) |
| Loan Origination (IAT-271) | Lending authority not enforced at approval (IAR-7771) |
| Project & Change Governance (IAT-391) | New product approval governance (IAR-6295) |
| Interest Rate & Liquidity (IAT-475) | Contingency funding plan testing (IAR-6108) |
| Interest Rate & Liquidity (IAT-475) | Liquidity stress scenario design (IAR-8634) |
| Interest Rate & Liquidity (IAT-475) | ALM model assumptions and validation (IAR-9035) |
| Complaint Handling (IAT-529) | Complaint intake and resolution (IAR-5050) |
| Complaint Handling (IAT-529) | Complaint trend analysis (IAR-8862) |
| AML Monitoring (IAT-548) | Sanctions screening of payments (IAR-5150) |
| AML Monitoring (IAT-548) | AML scenario tuning and coverage (IAR-5757) |
| AML Monitoring (IAT-548) | Beneficial ownership and CDD refresh (IAR-8993) |
| Wire & ACH (IAT-610) | Wire callback verification (IAR-6788) |
| Wire & ACH (IAT-610) | Payment suspense reconciliation (IAR-6809) |
| Access Management (IAT-696) | User access provisioning (IAR-5246) |
| Access Management (IAT-696) | Periodic access recertification (IAR-6395) |

</details>

<details><summary>taxonomy_node_parent_of_taxonomy_node_erm (16 rows)</summary>

| parent_id | child_id |
|---|---|
| Regulatory Compliance (ERMT-149) | BSA/AML (ERMT-927) |
| Operational (ERMT-173) | Technology (ERMT-510) |
| Operational (ERMT-173) | Process & Execution (ERMT-943) |
| Funding Liquidity (ERMT-428) | Contingency Funding (ERMT-751) |
| Technology (ERMT-510) | Access & Identity (ERMT-668) |
| Business Strategy (ERMT-543) | New Products & Initiatives (ERMT-637) |
| Compliance (ERMT-600) | Regulatory Compliance (ERMT-149) |
| Liquidity (ERMT-618) | Funding Liquidity (ERMT-428) |
| Credit Risk Management (ERMT-641) | Underwriting & Origination (ERMT-863) |
| Credit (ERMT-679) | Credit Risk Management (ERMT-641) |
| Interest Rate Risk (ERMT-734) | Banking Book IRR (ERMT-820) |
| Reputational (ERMT-866) | Stakeholder Risk (ERMT-955) |
| Strategic (ERMT-887) | Business Strategy (ERMT-543) |
| Process & Execution (ERMT-943) | Transaction Processing (ERMT-897) |
| Market (ERMT-953) | Interest Rate Risk (ERMT-734) |
| Stakeholder Risk (ERMT-955) | Customer Complaints (ERMT-562) |

</details>

<details><summary>taxonomy_node_parent_of_taxonomy_node_ia (14 rows)</summary>

| parent_id | child_id |
|---|---|
| Operations (IAT-103) | Payments (IAT-355) |
| IT General Controls (IAT-112) | Access Management (IAT-696) |
| Customer (IAT-297) | Complaints (IAT-449) |
| Payments (IAT-355) | Wire & ACH (IAT-610) |
| Asset/Liability Management (IAT-374) | Interest Rate & Liquidity (IAT-475) |
| Commercial Lending (IAT-439) | Loan Origination (IAT-271) |
| Complaints (IAT-449) | Complaint Handling (IAT-529) |
| Corporate Governance (IAT-544) | Governance Oversight (IAT-729) |
| Lending (IAT-674) | Commercial Lending (IAT-439) |
| Governance Oversight (IAT-729) | Project & Change Governance (IAT-391) |
| Information Technology (IAT-767) | IT General Controls (IAT-112) |
| Regulatory Compliance (IAT-889) | Financial Crimes (IAT-968) |
| Treasury (IAT-922) | Asset/Liability Management (IAT-374) |
| Financial Crimes (IAT-968) | AML Monitoring (IAT-548) |

</details>

## Reconciliation pairs (answer key)

Items the answer key says are the same underlying risk or control. Matching these is E2's job; here, check that the pairs look like the same thing described by two different teams.

### risks

| cluster | members |
|---|---|
| RC-001 | ERM: Excessive user access to critical systems (ERM-R2580)<br>IA: User access provisioning (IAR-5246) |
| RC-002 | ERM: Inappropriate access not removed (ERM-R1809)<br>IA: Periodic access recertification (IAR-6395) |
| RC-003 | ERM: Sanctions screening failures (ERM-R2184)<br>IA: Sanctions screening of payments (IAR-5150) |
| RC-004 | ERM: Contingency funding plan not executable (ERM-R2689)<br>IA: Contingency funding plan testing (IAR-6108) |
| RC-005 | ERM: Complaints not captured or resolved (ERM-R4131)<br>IA: Complaint intake and resolution (IAR-5050) |
| RC-006 | ERM: Complaint trends not analyzed (ERM-R1240)<br>IA: Complaint trend analysis (IAR-8862) |
| RC-007 | ERM: Stale deposit beta assumptions (ERM-R3459)<br>ERM: Interest rate risk model mis-specification (ERM-R3603)<br>IA: ALM model assumptions and validation (IAR-9035) |
| RC-008 | ERM: Unreconciled payment suspense balances (ERM-R1512)<br>IA: Payment suspense reconciliation (IAR-6809) |
| RC-009 | ERM: Fraudulent wire transfers (ERM-R4982)<br>IA: Wire callback verification (IAR-6788) |

### controls

| cluster | members |
|---|---|
| CC-001 | ERM: Role-based access provisioning (ERM-C1134)<br>IA: Manager and application owner approval of access requests (IAC-5300) |
| CC-002 | ERM: Quarterly access recertification (ERM-C3504)<br>IA: Quarterly recertification with revocation tracking (IAC-7714) |
| CC-003 | ERM: Real-time payment sanctions screening (ERM-C1643)<br>IA: Automated sanctions screening with same-day list updates (IAC-6482) |
| CC-004 | ERM: Annual contingency funding test (ERM-C3233)<br>IA: Operational test of FHLB and discount window draws (IAC-5044) |
| CC-005 | ERM: Complaint resolution tracking (ERM-C2539)<br>IA: Central complaint log with 15-day resolution tracking (IAC-8207) |
| CC-006 | ERM: Quarterly complaint trend review (ERM-C4997)<br>IA: Quarterly root cause analysis of complaint themes (IAC-6591) |
| CC-007 | ERM: Annual ALM assumption approval (ERM-C1862)<br>IA: Assumption review and back-testing for the ALM model (IAC-5069) |
| CC-008 | ERM: Daily suspense reconciliation (ERM-C2606)<br>IA: Daily reconciliation of payment suspense with aged-item escalation (IAC-8814) |
| CC-009 | ERM: Wire callback verification (ERM-C2452)<br>IA: Independent callback to a number on file before wire release (IAC-5164) |
