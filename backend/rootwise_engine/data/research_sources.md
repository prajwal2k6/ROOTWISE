# M1 reference source register (checked 2026-11-14)

This file lists references used for values stored in `crops.yaml`; values are
*published* agronomic/feed references and are NOT measurements from a Devanahalli farm.
All M2 NASA outputs and crop-specific farm values must be supplied separately.

## Crop water/phenology

- FAO training manual, *Crop Water Needs*, Chapter 3, Table 14: indicative
  seasonal crop water needs; includes category proxies for millet and dry beans.
  https://www.fao.org/4/s2022e/s2022e07.htm
- FAO training manual, Chapter 3, Tables 6/7/8: general season durations,
  water-use stage lengths, and FAO simplified crop Kc values.
  https://www.fao.org/4/s2022e/s2022e07.htm
  **Important**: these are not variety-specific five-stage *phenology*.
- FAO RUSLE explanation (A = R K LS C P):
  https://www.fao.org/land-water/land/land-governance-and-planning/land-resources-planning-toolbox/detail/revised-universal-soil-loss-equation/en
- UAS Bengaluru crop-based technologies, local variety names (not site adaptation):
  https://www.uasbangalore.edu.in/en/crop-based-technologies-approved-for-commercialisation/
- TNAU variety sources: see `variety_profiles.yaml`. Those examples are from
  Tamil Nadu, not Devanahalli; day to 50% flowering is **not** start of flowering.

## Feed-protein laboratory means: Feedipedia

Forage protein is recorded as **% of dry matter, specific stated material**. Its
reported composition is neither an expected farm fodder yield nor nutrient
concentration in a different cultivar or crop part. All values are proxied to
Devanahalli and require a local feed test to confirm.

| Crop | material | published mean crude protein (% DM) | source |
|---|---|---:|---|
| Finger millet | straw | 5.0 | https://www.feedipedia.org/node/447 |
| Groundnut | dry crop residues / haulms | 11.1 | https://www.feedipedia.org/node/695 |
| Horse gram | not quantified | — | Feedipedia draft https://www.feedipedia.org/node/628 explicitly says **DO NOT QUOTE**, so it was not used as numeric evidence |
| Cowpea | haulms | 13.7 | https://www.feedipedia.org/node/17446 |
| Pigeon pea | hay | 14.5 | https://www.feedipedia.org/node/22444 (n=2, very uncertain) |
| Green gram | straw | 9.8 | https://www.feedipedia.org/node/235 |
| Sorghum | straw | 3.7 | https://www.feedipedia.org/node/379 |
| Foxtail millet | stover | 4.2 | https://www.feedipedia.org/node/382 |

## UAS Bangalore variety maturity added to reference duration

The 2025 UAS Bangalore variety compendium explicitly reports **PHG-9 horse gram
100–105 days** and **KKM-3 green gram 65–70 days**; these have been entered
under `reference_duration` for those **named varieties only**. Publication:
https://www.uasbangalore.edu.in/wp-content/uploads/2025/10/Varities-Book.pdf
Do not assume that duration is a full phenology calendar or that every zone
of Bengaluru Rural is suitable. This PDF is large; the extracted document text
was checked, and the web screenshot endpoint could not render its large file.

## Supplementary legitimate published numbers — NOT auto-inserted into crop scores

- TNAU ragi CO(Ra)14, rainfed straw yield **8,503 kg/ha**;
  Paiyur 2 rainfed straw yield **4,200 kg/ha**, from
  https://agritech.tnau.ac.in/agriculture/agri_seasonandvarieties_ragi.html
- TNAU foxtail millet CO(Te)7 straw **5.1 t/ha**, from
  https://agritech.tnau.ac.in/agriculture/agri_seasonandvarieties_tenai.html
- TNAU sorghum CO 30, rainfed fodder **7,000 kg/ha**, from
  https://agritech.tnau.ac.in/agriculture/agri_seasonandvarieties_sorghum.html
- TNAU horse gram Paiyur 2 maturity **100–105 days**, flowering
  **45–50 days to 50% flowering**;
  https://www.agritech.tnau.ac.in/agriculture/CropProduction/Pulses/pulses_horsegram.html
- TNAU green gram CO 6 maturity **62–67 days**, 50% flowering **26–30 days**:
  https://agritech.tnau.ac.in/agriculture/English%20Version/Agriculture/CropProduction/Pulses/pulses_greengram.html
- FAO EcoCrop pigeon pea ecologic requirements: *annual rainfall* optimum
  **600–1,500 mm** and temperature optimum **18–38°C**, not the same as
  seasonal irrigation requirement or heat-damage threshold:
  https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=576
- TNAU redgram drip treatment measured **427 mm used**, conventional surface
  irrigation treatment **523 mm used** in a specific experimental context;
  these should NOT be labelled universal pigeon pea seasonal ETc values:
  https://agritech.tnau.ac.in/Water_requirement.html

## Why some values intentionally remain `null`

- Horse gram lacks a supported general seasonal ETc estimate suitable for the
  current reference database. Pigeon pea is now sourced separately from ICRISAT
  Table 10.7. Rainfall suitability must **not** be substituted for crop ETc.
- Five-stage phenology is not published for the actual UAS varieties in the
  cited catalog. We preserve unknown phase until records of the selected cultivar
  or farmer-observed stage dates are supplied.
- Field-level RUSLE C factor, postharvest retained *dry* biomass, and APMC
  prices are field and time dependent. No source supports hard-coded permanent
  values for all eight crops, so the engine supports these input fields but does
  not fabricate defaults.
- Forage crude protein does not establish the total forage quantity; livestock
  feeding decisions also require digestibility, toxin and feed-management checks.

## Quality and policy notes

The six 0–100 indices are transparent ROOTWISE algorithmic policy rules, not
FAO's published scores. See `criteria.yaml`. Confidence is a **data provenance /
coverage label**, not a frequency or probability of crop success. The cumulative
historical band is a distribution of retrospective *screening indices*, not yield
or future success probabilities.

## ICRISAT 2021 legume reference (Table 10.7)

- URL: https://oar.icrisat.org/11909/1/Chapter-Legumes-2021-Proof.pdf
- Table 10.7 reports general pigeon-pea crop water need **500–800 mm** and duration **140–180 days**, with emergence, flowering, pod formation and pod development as critical stages. The published chapter attributes this table to FAO irrigation and drainage papers 33 and 56. These are not BRG-variety observations in Devanahalli.
- The same table reports green gram/black gram water need **350–400 mm**, duration **65–80 days**, with flowering and pod formation/development critical. For green gram, the source group's water range is labelled a proxy; UAS KKM-3 duration is handled separately in the variety profile.
- Groundnut critical stages are emergence, flowering, pegging and pod development, while the water range agrees with the existing FAO peanut reference **500–700 mm**.
- The public PDF version retrieved was marked **Uncorrected Proof**; treat these as source-reported agronomic references, not local agronomic verification.

## Horse gram observational ET (not a general crop requirement)

- KrishiKosh-hosted research table: https://krishikosh.egranth.ac.in/server/api/core/bitstreams/ed291661-433a-4d6a-83ed-895bfde5a7c9/content
- Experiment-specific total ET reports **182.8–214.3 mm** under different dry-season/tillage/sowing treatments and water-table conditions. This cannot be substituted for the potential seasonal ETc of PHG-9 in Devanahalli; therefore `horse_gram.water_need` remains `null`.
