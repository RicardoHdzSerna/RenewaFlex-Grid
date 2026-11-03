# Phase shifters in the JAO Static Grid Model — inventory, placement, capability (2026-10-06-pst-inventory)

Grid: package run `2026-10-06-stage2-v23-LP-virtual` (1754 buses, 3210 branches). Structure only; no flows, positions or prices read.

## 1. What the file lists

- 61 phase-shifter rows in the Transformers sheet (54 with the same voltage on both sides, i.e. in series with a line; the others are 380/220 kV transformers with phase regulation).
- By operator: TENNETGMBH 14, 50HERTZ 10, PSE 9, ELIA 7, APG 6, AMPRION GMBH 4, CEPS 3, TEL 2, TENNET NL 2, TRANSNETBW 2, ELES 1, HOPS 1.
- 40 have a tap range for remedial actions, i.e. are used as a control in capacity calculation. The Remedial Actions sheet has 131 entries, 44 of them tap changes.
- None of them is in our grid: the build leaves out every same-voltage transformer row (it could not place them by name). 23 are placed on a line here, see section 2.

## 2. Where they sit (placed units)

| corridor | circuits | units | in series per circuit | basis |
|---|---|---|---|---|
| Meeden-Diele (NL-DE) | 2 | PST Meeden PST W; PST Meeden PST Z | 1 | comment: 'Connected to tie-line 10T-DE-NL-00002T and 10T-DE-NL-00001V' |
| Conneforde-Diele (DE, feeds Meeden-Diele) | 2 | PST Diele T441; PST Diele T442 | 1 | comment: line 'Conneforde - Diele rot / weiss' |
| Gronau-Hengelo (DE-NL) | 2 | TR Gronau TR 441 E | 1 | station: Gronau is the terminal of one cross-border corridor; ONE unit for two circuits (taken as acting on both) |
| Van Eyck-Maasbracht (BE-NL) | 2 | TR VAN EYCK PST 1; TR VAN EYCK PST 2 | 1 | station: Van Eyck is the terminal of one cross-border corridor |
| Zandvliet-Rilland (BE-NL) | 2 | TR ZANDVLIET PST 2; TR ZANDVLIET PST 3; TR ZANDVLIET PST 4 | 1 | station: Zandvliet is the terminal of one cross-border corridor; THREE units listed for two circuits (one per circuit assumed) |
| Vierraden-Krajnik (DE-PL) | 2 | PST Vierraden 441; PST Vierraden 442; PST Vierraden 443; PST Vierraden 444 | 2 | station: Vierraden is the terminal of one cross-border corridor; FOUR units for two circuits (two in series per circuit assumed) |
| Mikulowa-Hagenwerder (PL-DE) | 2 | PST MIKULOWA-PF1; PST MIKULOWA-PF2; PST MIKULOWA-PF3; PSTMIKULOWA-PF4 | 2 | comment: 'phase shifting transformer (400) on line Mik…'; FOUR units for two circuits (two in series per circuit assumed) |
| Roehrsdorf-Hradec (DE-CZ), German end | 2 | PST Rohrsdorf 441; PST Rohrsdorf 442 | 1 | station: Roehrsdorf is the terminal of one cross-border corridor |
| Hradec-Roehrsdorf (CZ-DE), Czech end | 2 | PST Hradec 1; PST Hradec 2; PST Hradec 3 | 1 | comment: units 1 and 2 'connected to tieline 10T-CZ-DE-00002U' (circuit V445), unit 3 to 10T-CZ-DE-00003S (circuit V446); THREE units for two circuits (one in series per circuit assumed) |

## 3. What they can move, and the reactance we leave out

Angle = end of the tap range used for remedial actions. Shift = change of the flow on the corridor itself when every circuit is shifted by that angle; the same amount leaves by other paths.

| corridor | angle per circuit, degrees | flow moved per degree, MW | flow moved at that angle, MW | line reactance per circuit, ohm | phase-shifter reactance per circuit, ohm | reactance with / without |
|---|---|---|---|---|---|---|
| Meeden-Diele (NL-DE) | 13.0 | 63 | 824 | 7.6 | 10.0 | 2.3 x |
| Conneforde-Diele (DE, feeds Meeden-Diele) | 7.3 | 60 | 437 | 16.6 | 12.3 | 1.7 x |
| Gronau-Hengelo (DE-NL) | 6.3 | 85 | 536 | 5.8 | 3.3 | 1.6 x |
| Van Eyck-Maasbracht (BE-NL) | 6.7 | 98 | 660 | 3.2 | 10.5 | 4.3 x |
| Zandvliet-Rilland (BE-NL) | 6.7 | 76 | 515 | 2.0 | 11.1 | 6.4 x |
| Vierraden-Krajnik (DE-PL) | 12.2 | 32 | 388 | 7.4 | 24.8 | 4.4 x |
| Mikulowa-Hagenwerder (PL-DE) | 10.2 | 41 | 415 | 4.9 | 23.2 | 5.8 x |
| Roehrsdorf-Hradec (DE-CZ), German end | 6.1 | 58 | 358 | 21.9 | 12.4 | 1.6 x |
| Hradec-Roehrsdorf (CZ-DE), Czech end | 5.6 | 58 | 327 | 21.9 | 25.5 | 2.2 x |

## 4. Effect on the NET flow of each border, at the remedial-action angle (MW; positive = more flow from the first to the second zone)

| corridor | AT-CZ | AT-DE | AT-HU | AT-SI | BE-DE | BE-FR | BE-NL | CZ-DE | CZ-PL | CZ-SK | DE-FR | DE-NL | DE-PL | HR-HU | HR-SI | HU-RO | HU-SI | HU-SK | PL-SK |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Meeden-Diele (NL-DE) | -3 | +4 | -2 | 0 | -10 | -55 | +65 | +2 | -5 | 0 | +55 | -65 | +6 | 0 | 0 | 0 | 0 | -2 | +2 |
| Conneforde-Diele (DE, feeds Meeden-Diele) | -2 | +3 | -1 | 0 | -3 | -18 | +21 | +2 | -4 | 0 | +18 | -21 | +5 | 0 | 0 | 0 | 0 | -1 | +1 |
| Gronau-Hengelo (DE-NL) | +1 | -2 | +1 | 0 | +4 | +23 | -28 | -1 | +2 | 0 | -23 | +28 | -3 | 0 | 0 | 0 | 0 | +1 | -1 |
| Van Eyck-Maasbracht (BE-NL) | -1 | +1 | 0 | 0 | -72 | -193 | +265 | 0 | -1 | 0 | +193 | -265 | +2 | 0 | 0 | 0 | 0 | -1 | 0 |
| Zandvliet-Rilland (BE-NL) | -1 | +1 | -1 | 0 | -19 | -100 | +119 | 0 | -1 | 0 | +100 | -119 | +2 | 0 | 0 | 0 | 0 | -1 | 0 |
| Vierraden-Krajnik (DE-PL) | -3 | +34 | -28 | -2 | 0 | -6 | +6 | +116 | -106 | -14 | +6 | -6 | +150 | -1 | +1 | 0 | +1 | -31 | +44 |
| Mikulowa-Hagenwerder (PL-DE) | +2 | -38 | +34 | +3 | 0 | 0 | 0 | -179 | +183 | -2 | 0 | 0 | -218 | +2 | -2 | 0 | -1 | +37 | -35 |
| Roehrsdorf-Hradec (DE-CZ), German end | -44 | +33 | +10 | +1 | 0 | -4 | +4 | -169 | +111 | +14 | +4 | -4 | -136 | +1 | -1 | 0 | 0 | +11 | -26 |
| Hradec-Roehrsdorf (CZ-DE), Czech end | +40 | -30 | -9 | -1 | 0 | +4 | -4 | +155 | -101 | -13 | -4 | +4 | +125 | -1 | +1 | 0 | 0 | -10 | +23 |

Orientation: a positive angle pushes flow from the first-named station of the corridor to the second.

## 5. Not placed

PST / 380-220kV / Buers / Trafo 37; PST Arad 400/220 3; PST Divaca; PST Ernsthofen EHPST; PST GRUDZIADZ-A3; PST Hamburg/Ost 441; PST Hamburg/Ost 442; PST Hamburg/Ost 443; PST Hamburg/Ost 444; PST JOACHIMOW-TD1; PST JOACHIMOW-TD2; PST Krempermarsch T441A; PST Krempermarsch T441B; PST Krempermarsch T442A; PST Krempermarsch T442B; PST Lienz LIPST; PST MIKULOWA-TD1; PST MIKULOWA-TD2; PST Tauern TAPST; PST Ternitz TEPST; PST Urechesti 400/220 1; PST Wuergau T441A; PST Wuergau T441B; PST Wuergau T442A; PST Wuergau T442B; TR / 380-220kV / Kuehmoos Trafo 401; TR AUBANGE PST 1; TR Doerpen/W T441; TR Doerpen/W T442; TR Doerpen/W T443; TR Doerpen/W T444; TR Hanekenfaher TR 441 E; TR Hanekenfaher TR 442 E; TR MONCEAU PST 1; TR Nauders NRPST21; TR Nauders NRPST22; TR Oberzier TR 442 E; TR4 400/220 kV Zerjavinec.
