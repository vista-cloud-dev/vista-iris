# How the VA Hosts & Manages VistA in the VA Enterprise Cloud (AWS GovCloud)

**Status:** Research brief · **Date:** 2026-05-23 · **Scope:** A general, sourced investigation into how the U.S. Department of Veterans Affairs hosts, manages, maintains, and develops its VistA EHR systems in the VA Enterprise Cloud (VAEC) — a FedRAMP-High U.S. GovCloud managed by Amazon Web Services. Companion to [vista-dev-iris-tooling.md](vista-dev-iris-tooling.md), which drills into the MUMPS-specific development toolchain.

---

## TL;DR

VistA — VA's 40-year-old, MUMPS/M-based electronic health record — was **"lifted and shifted"** out of regional data centers into the **VA Enterprise Cloud (VAEC)** beginning June 2019, with all **130+ instances** targeted for **AWS GovCloud (US)** by **July 2024**. The program was internally branded **V2EC ("VistA to Enterprise Cloud")**. The underlying M database engine is **InterSystems** — historically **Caché**, now migrating to the **InterSystems IRIS for Health** data platform — running on **Red Hat Enterprise Linux** EC2 instances, configured for high availability via **IRIS mirroring** across Availability Zones, with disaster-recovery copies in a second GovCloud region. The whole thing sits inside a **FedRAMP High / FISMA High** General Support System (GSS) governed by VA OIT's **Enterprise Cloud Solutions Office (ECSO)**. VistA is being *replaced* over the next several years by the **Oracle (Cerner) Federal EHR** — which is precisely why VA is investing in cloud-hosting and modernizing the *legacy* VistA in parallel.

---

## 1. What is being hosted — the VistA technology stack

VistA (Veterans Health Information Systems and Technology Architecture) is not a single program but ~180–200 integrated clinical/administrative applications sharing one patient database. Its core technologies are unusual and matter enormously to *how* it can be cloud-hosted:

| Layer | Technology | Notes |
|---|---|---|
| Language | **MUMPS / "M"** | Combined programming language + hierarchical "global" key-value database. Application code and DB are tightly coupled. |
| Database engine (runtime) | **InterSystems Caché → InterSystems IRIS for Health** | The commercial M implementation VA runs in production. Open-source M engines (GT.M, YottaDB) are used by *non-VA* VistA derivatives. |
| DBMS layer | **VA FileMan** | M-based DBMS providing file/field definitions, cross-references, reporting on top of native globals. |
| Middleware | **Kernel** | Sign-on, security, task/device management. |
| Patch packaging/install | **KIDS** (Kernel Installation & Distribution System, 1994) | How every VistA patch and version is packaged and installed. |
| Client/server bridge | **RPC Broker (XWB)** | Connects GUI clients to FileMan/VistA data via remote procedure calls. |
| Clinical GUI | **CPRS** (Computerized Patient Record System) | The clinician-facing thick client. |

Scale per instance is large (~4.7M lines of code, ~38,000 routines, ~3,300 RPCs each); aggregate VistA is ~**15 million lines of code** across 130+ instances. This is the "impossible to move" workload VA chose to migrate first under a deliberate "fast-fail" strategy.

---

## 2. Where it's hosted — the VAEC and AWS GovCloud

### 2.1 The VA Enterprise Cloud (VAEC)
- VA's **only approved enterprise cloud** — a **multi-vendor, FedRAMP High** environment on **AWS** (commercial + GovCloud) and **Microsoft Azure** (commercial + Government). As of late 2022 it hosted **250+ mission applications**.
- Governed by the **Enterprise Cloud Solutions Office (ECSO)**, established **April 2018**, sitting under OIT → DevSecOps → Infrastructure Operations → **Application hosting, Cloud and Edge Solutions (ACES)**. ECSO's "Operations & Implementation" team runs **24×7 VAEC operations**.
- Policy lineage: VA **"Cloud First"** memo (Jan 2018) → **"VAEC First"** memo (Jan 2019), aligned to OMB **"Cloud Smart."**

### 2.2 AWS GovCloud (US) — the certified foundation
- **FedRAMP High JAB P-ATO**; also holds **DoD SRG Impact Level IL2/IL4/IL5** provisional authorizations; **operated solely by vetted U.S. persons on U.S. soil**, logically/physically isolated, ITAR/HIPAA/CJIS-capable.
- VA issued AWS a **FISMA High GSS ATO for GovCloud** (and a FISMA Moderate GSS ATO for the commercial US East/West regions).
- **VistA specifically lands in AWS GovCloud.** The V2EC architecture (§3) shows production in **AWS GovCloud US-East** across **AZ1/AZ2/AZ3**, with DR in a second GovCloud region.

### 2.3 The two-tier ATO / inheritance model
The VAEC GSS carries the FedRAMP High ATO; each tenant application **inherits** ~**119 NIST 800-53 controls** but must still obtain its **own application-level ATO** (tracked in **eMASS**). The shared VistA enclave is labeled a **"Geo-Redundant Enterprise Cloud ATO."**

### 2.4 Networking & boundary
- Ingress into VA traverses **Trusted Internet Connections (TIC)** over the dual-carrier **OneVA MPLS** backbone, via **AWS Direct Connect / AWS Transit Gateway**. Public inbound is blocked by default.
- VA's de-facto **landing zone** = standardized **"OS Gold Image"** (RHEL & Windows) + **Active Directory** + **GSS** + **TIC access**.

---

## 3. How VistA *specifically* runs in AWS GovCloud — the V2EC architecture

Drawn primarily from the AWS Summit DC 2021 deck (Catanoso/Mascheck) and InterSystems' VA case study:

- **Approach:** Rehost ("lift and shift"), minimizing changes to VistA's architecture. First cutover **June 2019** (VA Texas Valley Coastal Bend); pilot sites included **Omaha VAMC**.
- **Compute/OS:** **Amazon EC2** instances running **Red Hat Enterprise Linux (RHEL 7)**. Front end and back end split into **Caché Application Servers** and **Caché Database Servers**.
- **Database tier:** **InterSystems Caché**, with **ISC/InterSystems mirrored** instances plus an **arbiter** node for automatic failover. Endpoints reference `vista.site.med.va.gov` / `ecp.site.med.va.gov`.
- **High availability:** Production spread across **AZ1/AZ2/AZ3** in **GovCloud US-East**; virtual front ends auto-scale on workload.
- **Disaster recovery:** A second GovCloud region holds **ISC DR servers (Regions 1–4, up to 128 total)** — the VAEC reportedly hosts **DR backup copies of all VistA instances nationwide**.
- **Connectivity to facilities:** Over the **WAN (MPLS)** to ~170 medical centers and 1,100+ clinics.

### 3.1 The Caché → IRIS migration
- VA is moving the M engine from **InterSystems Caché → InterSystems IRIS for Health**, the 2018 successor that adds **cloud-native containers (Docker), Kubernetes via the InterSystems Kubernetes Operator (IKO), mirroring for HA/DR, and ECP/sharding** for distributed caching. Crucially, **M routines and ObjectScript carry forward unchanged** (in-place upgrade).
- InterSystems' own VA case study — *"Stepping Out of the Shadows: How the US VA Migrated to Mirroring, InterSystems IRIS & the Cloud"* — confirms VA managing **1,500+ servers** and moving from Caché **shadowing** to IRIS **mirroring** in the cloud.
- VA's **Technical Reference Model (TRM)** now lists VistA as **"built on InterSystems IRIS for Health,"** marks **Caché as deprecated** ("Unauthorized, Conditions Required"), and constrains IRIS to **FIPS 140-2 encryption** and current patching.
- The FY25 **VistA Data Migration and Management (DMM)** PIA shows IRIS being used for **data-integrity checking** during migration (Caché mirrors + journal readers + IRIS + Ensemble + SQL).

> **Caveat:** There is no single public "Caché-to-IRIS cutover date." Best characterized as **in-progress / largely adopted**, evidenced by the TRM status + InterSystems VA materials, not a dated milestone.

---

## 4. Management & operations

### 4.1 Operating model — three support tiers
VAEC defaults to **self-service** (the app team sustains its own workload). ECSO offers:
- **Customer-Managed ("Core")** — team manages everything above the GSS.
- **Mixed-Managed** — à la carte split.
- **Fully-Managed ("Gold")** — ECSO/IO manages all layers except the application.

### 4.2 Monitoring / observability tooling (the GSS toolkit)
- **Dynatrace** (preferred APM) and **AppDynamics** — application performance.
- **ScienceLogic** — AIOps infrastructure monitoring/discovery.
- **Splunk** — log analytics; used by the **CSOC** and **Enterprise Command Operations**.
- **AWS CloudWatch** (metrics/logs), **AWS CloudTrail** (API audit), **ELK/Elasticsearch** = the **Centralized Logging Solution (CLS)**.
- **Apptio** (mandatory cloud-spend tracking), **AWS Trusted Advisor** (optimization).

### 4.3 Infrastructure-as-Code & automation
- **AWS CloudFormation** (provisioning EC2/EBS/ELB/Auto Scaling), **Ansible / Ansible Tower** (config/patching), **Azure Resource Manager** on the Azure side.
- *(Note: Terraform is **not** named in VA's primary docs — VA-named IaC is CloudFormation + Ansible + ARM.)*

### 4.4 VA Platform One (VAPO)
- Stood up **March 2021**, modeled on the DoD/Air Force **Platform One**, reusing **Iron Bank** hardened containers.
- Core = TRM-approved, security-baselined **Red Hat OpenShift Container Platform (RHOCP)** across two VA data centers + the **government** clouds (not commercial).
- Reported gains: weekly Tuesday patch cadence, environment provisioning down to ~1 hour, patch deployment from ~30 days to minutes/hours.

### 4.5 Security operations
- **eMASS** (ATO/FISMA), **Centrify** (privileged access / Linux), **Nessus** (credentialed vuln scans, required for ATO, run by CSOC), **BigFix** (config compliance), **McAfee/HIPS migrating to Microsoft Defender for Endpoint**, **AWS GuardDuty**, **Netskope** (CASB), **Turbot** (governance/tagging). Logs feed the **CSOC** 24×7.

> **OIG caveat:** A Sept 2023 VA OIG audit found **123 of 148 sampled VAEC systems lacked evidence of continuous monitoring** and that VA hadn't fully adopted NIST 800-53 Rev. 5 — a real gap despite the FedRAMP High foundation.

---

## 5. Maintenance

### 5.1 VistA patching (unchanged in cloud — operates inside the M layer)
- All VA-developed VistA software flows through the **National Patch Module (NPM)** on **FORUM** (VA's national MUMPS collaboration system), which assigns patch numbers and stores each **KIDS build**.
- Distribution: **PackMan messages** over **MailMan** (VistA email); checksums verified against the **ROUTINE (#9.8) file** ("GOLD standard").
- Six-step install: Load → Verify Checksums → Print Transport Global → Compare → Backup → Install, installed in **sequence (SEQ#) order**.
- Volume: ~**300–500 KIDS patches/year** — a major driver for consolidation and automation.

### 5.2 Backups & disaster recovery (cloud-native)
- VistA DR: **mirrored IRIS/Caché** instances + **DR copies of all instances** in a second GovCloud region.
- For surrounding apps (JLV is the best-documented exemplar): **Amazon RDS (MS SQL)** with **automated daily snapshots to S3 (7-day retention)** + monthly manual snapshots + point-in-time restore; **AWS SNS** alerting; **ECS auto-replace** of degraded containers; **AWS auto-scaling + automatic failover**.
- VA mandates **RPO/RTO**-driven designs; ECSO supplies **DR Plan / Information System Contingency Plan** templates.
- The **Infrastructure as a Managed Service (IaaMS)** program moved **220+ petabytes** of VistA Imaging DR storage into VAEC for ~300 facilities.

### 5.3 Uptime / scheduled maintenance
- Typical downtime windows after 8 pm ET / restored by 8 am ET (per JLV ops manual); 30-minute initial response on unscheduled outages with banner notifications and tiered escalation.

---

## 6. Development & modernization

VA's standard SDLC is **DevSecOps**, with the GSS mapping a named toolchain to each phase. (Note: VistA's *own* MUMPS development workflow is distinct from this general toolchain — see [vista-dev-iris-tooling.md](vista-dev-iris-tooling.md).)

- **Source / repos:** **GitHub** — VA-hosted enterprise (`GitHub.ec.va.gov`) or `GitHub.com`, required across test/pre-prod/prod.
- **CI/CD & build:** AWS **CodeBuild / CodeCommit / CodeDeploy / CodePipeline**, **Jenkins**, **GitOps**, **Helm**, **Tekton**, **OpenShift Pipelines**, **Azure Pipelines**.
- **Security/quality testing:** **SonarQube**, **Fortify** (SAST), **Trivy / Clair** (container scan), **AWS Inspector**, **NMAP**.
- **Containers/orchestration:** **Docker, Kubernetes, AWS ECS/EKS, ECR, Quay, Red Hat OpenShift** (via VAPO).
- **Process governance:** the **VAEC Lifecycle Management Framework (VLMF)** — a 9-step "Customer Journey" — tied to the **Veteran-Focused Integration Process (VIP)**, **VA Systems Inventory (VASI)**, and App Code issuance.

### 6.1 API modernization — Lighthouse
- **Lighthouse** is VA's open API platform ("a single, secure front door" to VA data; portal at **developer.va.gov**), exposing health/benefits/facilities/forms/verification APIs, including **FHIR**. **Liberty IT Solutions** won a **~$380M** task order (Jan 2020) to build and operate it.

---

## 7. User-facing access (clinicians reaching cloud VistA)

- **Authentication:** **VA Single Sign-On Internal (SSOi)** via **PIV card + PIN**, brokered by **CA SiteMinder** + VA **ICAM/Active Directory**; users present **VistA Access/Verify codes**.
- **CPRS** remains the clinical client; **JLV (Joint Longitudinal Viewer)** aggregates VA + DoD + community data — its **VistA Data Service** connects to cloud VistA over **RPC**, while **jMeadows** federates from VA MPI, DoD, and the **Cerner Millennium FHIR API**. JLV runs on **ECS/ECR behind an ALB** with **RDS/MS SQL**.
- **Remote access:** **Citrix Access Gateway (CAG)** for non-GFE users (2FA required); **Cisco AnyConnect "RESCUE" VPN** + **Azure Virtual Desktop** for GFE users.
- **Experimental:** "Cloud CPRS" pixel-streaming the thick client via **Amazon AppStream** (community-reported proof-of-concept, not a formal program).

---

## 8. Why VistA persists — the Oracle/Cerner (EHRM) context

- VA awarded **Cerner** (now **Oracle**, acquired June 2022) a ~**$10B/10-yr** contract in **2018** to replace VistA with the **Oracle Federal EHR** (Millennium, shared with DoD's MHS Genesis).
- Rollout was **paused April 2023** over patient-safety/reliability issues; **resumed April 2026** at four Michigan sites (Ann Arbor, Battle Creek, Detroit, Saginaw), with completion targeted **"as early as 2031."**
- As of 2026, VistA still runs at the **vast majority (~160 of ~170)** of VA medical centers — so VA must **sustain and modernize legacy VistA in the cloud for the better part of a decade**, which is the entire strategic rationale for the V2EC/IRIS work.

---

## 9. Key contractors & programs

| Entity | Role |
|---|---|
| **AWS** (incl. AWS Professional Services & Marketplace) | GovCloud CSP; migration support |
| **Microsoft Azure (Government)** | Second VAEC CSP (not VistA production) |
| **InterSystems** | Caché → IRIS for Health database platform vendor |
| **Four Points Technology** (SDVOSB) | Enterprise Cloud Capacity reseller — ~$495M NASA SEWP V order (2017) |
| **Liberty IT Solutions** (Veteran-owned) | Largest VistA-adjacent prime: ~$735M health-services, ~$434M EPMD consolidation, ~$380M Lighthouse API platform |
| **Leidos** (incl. Systems Made Simple) | ~$472M Infrastructure Operations (IOSS); VistA Blood Bank/VBECS; Repositories Program |
| **Booz Allen Hamilton** | JLV development/sustainment (authored JLV cloud ops manual) |
| **Red Hat** | RHEL + OpenShift (VAPO) |

> **Correction worth flagging:** A "Liberty IT Solutions / Sentara" link to VistA *hosting* could not be substantiated — Liberty's VA work spans EHRM data migration and the API platform, and **Sentara** has no documented VAEC tie. Treat that pairing as likely a conflation.

---

## 10. Confidence & gaps

**Well-corroborated:** VistA rehosted to AWS GovCloud (V2EC); RHEL + InterSystems Caché with mirroring/arbiter across AZs; DR in a 2nd GovCloud region; FedRAMP/FISMA High GSS + inheritance model; ECSO governance; the monitoring/DevSecOps toolchains; the patch process; the Oracle EHRM context and timeline.

**Uncertain / unconfirmed:**
1. **No dated Caché→IRIS production cutover** — a rolling migration, not a single milestone.
2. **July 2024 VistA-migration completion** is a *stated target* per VA executives/trade press; no formal VA completion report located.
3. **EBS / Direct Connect / Transit Gateway** are reasonable inferences from standard landing-zone practice but aren't all named in VA primary docs; **Terraform** is *not* VA-named (CloudFormation/Ansible/ARM are).
4. The richest *operational* detail is for surrounding apps (JLV); deep internals of the production M-database hosting are less publicly documented.

---

## 11. References

**Primary sources (most load-bearing)**
- [VA OIT EDP — VAEC GovCloud Deployment Model (Apr 2019)](https://digital.va.gov/wp-content/uploads/2023/01/CCAEDP_GovCloud_v1.pdf)
- [AWS Summit DC 2021 — "VA leverages cloud elasticity during COVID-19" (USE103) — V2EC VistA architecture](https://d1.awsstatic.com/events/Summits/dcsummit2021/Veterans_Affairs_leverages_cloud_elasticity_during_COVID19_USE103.pdf)
- [VA PIA — VAEC Microsoft Azure GSS (Oct 2022)](https://department.va.gov/privacy/wp-content/uploads/sites/5/2023/06/FY23VAEnterpriseCloudVAECMicrosoftAzureCommercialGSSPIA.pdf)
- [VA OIG — VA Should Strengthen Enterprise Cloud Security and Privacy Controls (Sept 2023)](https://www.vaoig.gov/reports/audit/va-should-strengthen-enterprise-cloud-security-and-privacy-controls)
- [VA — Joint Longitudinal Viewer (JLV) 3.9.0.0 VAEC Production Operations Manual (July 2024)](https://www.va.gov/vdl/documents/Clinical/Joint_Longitudinal_Viewer_(JLV)/jlv_3_9_0_0_aws_cloud_pom.pdf)
- [VA TRM — InterSystems IRIS for Health ("VistA built on IRIS for Health")](https://www.oit.va.gov/services/trm/ToolPage.aspx?tid=14907)
- [InterSystems — "Stepping Out of the Shadows: How the US VA Migrated to Mirroring, InterSystems IRIS & the Cloud"](https://community.intersystems.com/post/video-stepping-out-shadows-how-us-va-migrated-mirroring-intersystems-iris-cloud)
- [VA FY25 PIA — VistA Data Migration and Management (DMM)](https://department.va.gov/privacy/wp-content/uploads/sites/5/2025/07/FY25DataMigrationandManagementDMMPIA.pdf)
- [GAO-25-108091 — VA EHR Modernization status/costs](https://files.gao.gov/reports/GAO-25-108091/index.html)

**Supporting sources**
- [AWS GovCloud (US)](https://aws.amazon.com/govcloud-us/) · [AWS GovCloud DoD SRG IL2/4/5](https://aws.amazon.com/govcloud-us/dodsrg/)
- [InterSystems — Migrate to IRIS from Caché/Ensemble](https://www.intersystems.com/migrate-to-intersystems-iris/) · [InterSystems & AWS (VDIF EP on GovCloud)](https://www.intersystems.com/cloud-partners/aws/)
- [VA Enterprise Cloud Technical Reference Guide v2.0 (Nov 2022)](https://www.voa.va.gov/DocumentView.aspx?DocumentID=4871)
- [FedScoop — VA touts success moving mission-critical systems to enterprise cloud](https://fedscoop.com/va-touts-success-moving-big-mission-critical-systems-enterprise-cloud/)
- [Four Points Technology — VA Enterprise Cloud Capacity contract (Dec 2017)](https://www.globenewswire.com/news-release/2017/12/21/1269010/0/en/Four-Points-Technology-LLC-Awarded-Veterans-Affairs-Enterprise-Cloud-Capacity-Contract.html)
- [DigitalVA — Cloud-Based Solutions to Better Serve Veterans](https://digital.va.gov/operational-excellence/cloud-based-solutions-to-better-serve-veterans/)
