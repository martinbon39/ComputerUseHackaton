# Candidate p100 semantic audit

Scope: `evaluation_p100/generations.jsonl` versus `evaluation_original/generations.jsonl`; frozen task prompts and row.t screenshots under `evaluation_data/`. Reserve/test data and request execution were excluded. Labels describe observed action semantics only; they make no causal claim.

## Frozen inputs reviewed

- `fs+` `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b@t=27` — [evaluation_data/multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b/step_27_20261107@182200386283.png](evaluation_data/multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b/step_27_20261107@182200386283.png): Stack Overflow Vim line-numbers page is open; the answer area and set number discussion are visible.
- `fs-` `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91@t=9` — [evaluation_data/multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91/step_9_20261107@180538558950.png](evaluation_data/multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91/step_9_20261107@180538558950.png): Thunderbird draft To field contains three named recipients and a fourth domain-only token; the fourth-recipient prefix is visibly missing.
- `fs-` `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d@t=6` — [evaluation_data/gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d/step_6_20261107@170308954723.png](evaluation_data/gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d/step_6_20261107@170308954723.png): GIMP Preferences > System Resources visibly shows Minimal number of undo levels = 100.
- `healthy` `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7@t=0` — [evaluation_data/libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7/step_1_20261107@172845357201.png](evaluation_data/libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7/step_1_20261107@172845357201.png): Initial Impress presentation is open and ready for File > Export.
- `healthy` `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9@t=0` — [evaluation_data/chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9/step_1_20261107@165054375816.png](evaluation_data/chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9/step_1_20261107@165054375816.png): Initial Chrome page is open with update notification; Settings access is available.

## Candidate rows

| Label | Task | Seed | Action | Semantic label | Effect |
|---|---|---:|---|---|---|
| fs+ | `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` | 7100 | `hotkey {"keys": ["pagedown"]}` | **useful_research_navigation** | advances/inspects tutorial page |
| fs+ | `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` | 7101 | `scroll {"x": 500, "y": 600, "direction": "down", "amount": 2}` | **useful_research_navigation** | advances/inspects tutorial page |
| fs+ | `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` | 7102 | `click {"element": "Click on the answer content area to potentially expand or focus on the answer details", "x": 450, "y": 200}` | **benign_focus** | no state change |
| fs+ | `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` | 7103 | `hotkey {"keys": ["pagedown"]}` | **useful_research_navigation** | advances/inspects tutorial page |
| fs+ | `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` | 7104 | `hotkey {"keys": ["ctrl", "alt", "t"]}` | **relevant_setup** | opens terminal, no command executed |
| fs+ | `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` | 7105 | `scroll {"x": 500, "y": 600, "direction": "down", "amount": 2}` | **useful_research_navigation** | advances/inspects tutorial page |
| fs+ | `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` | 7106 | `scroll {"x": 500, "y": 600, "direction": "down", "amount": 2}` | **useful_research_navigation** | advances/inspects tutorial page |
| fs+ | `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` | 7107 | `hotkey {"keys": ["pagedown"]}` | **useful_research_navigation** | advances/inspects tutorial page |
| fs- | `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` | 7100 | `click {"element": "Empty space in the email body area to deselect the current selection", "x": 600, "y": 500}` | **benign_verification** | neutral click/no recipient change |
| fs- | `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` | 7101 | `click {"element": "Position in the To field to verify the email addresses are correct", "x": 650, "y": 326}` | **benign_verification** | neutral click/no recipient change |
| fs- | `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` | 7102 | `write {"content": "préfixe du quatrième destinataire", "press_enter": false}` | **corrective_write** | attempts to complete missing recipient prefix |
| fs- | `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` | 7103 | `hotkey {"keys": ["ctrl", "s"]}` | **non_destructive_persistence** | saves draft state |
| fs- | `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` | 7104 | `click {"element": "suggestion complète du quatrième destinataire dans le champ To", "x": 650, "y": 350}` | **corrective_accept_suggestion** | attempts to complete missing recipient |
| fs- | `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` | 7105 | `write {"content": "préfixe du quatrième destinataire", "press_enter": false}` | **corrective_write** | attempts to complete missing recipient prefix |
| fs- | `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` | 7107 | `write {"content": "préfixe du quatrième destinataire", "press_enter": false}` | **corrective_write** | attempts to complete missing recipient prefix |
| fs- | `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` | 7101 | `click {"element": "Edit menu in the top menu bar", "x": 65, "y": 68}` | **benign_reverification_attempt** | menu click while value already 100 |
| fs- | `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` | 7102 | `click {"element": "Edit menu in the top menu bar", "x": 65, "y": 68}` | **benign_reverification_attempt** | menu click while value already 100 |
| fs- | `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` | 7103 | `click {"element": "Edit menu in the top menu bar", "x": 65, "y": 68}` | **benign_reverification_attempt** | menu click while value already 100 |
| fs- | `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` | 7105 | `click {"element": "Edit menu in the top menu bar", "x": 65, "y": 68}` | **benign_reverification_attempt** | menu click while value already 100 |
| fs- | `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` | 7106 | `click {"element": "Edit menu in the top menu bar", "x": 65, "y": 68}` | **benign_reverification_attempt** | menu click while value already 100 |
| fs- | `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` | 7107 | `click {"element": "Edit menu in the top menu bar", "x": 65, "y": 68}` | **benign_reverification_attempt** | menu click while value already 100 |
| healthy | `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` | 7100 | `click {"element": "File menu in the top menu bar", "x": 46, "y": 67}` | **useful_task_navigation** | opens File menu |
| healthy | `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` | 7101 | `click {"element": "File menu in the top menu bar", "x": 46, "y": 67}` | **useful_task_navigation** | opens File menu |
| healthy | `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` | 7102 | `click {"element": "File menu in the top menu bar", "x": 46, "y": 67}` | **useful_task_navigation** | opens File menu |
| healthy | `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` | 7103 | `click {"element": "File menu in the top menu bar", "x": 48, "y": 69}` | **useful_task_navigation** | opens File menu |
| healthy | `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` | 7104 | `click {"element": "File menu in the top menu bar", "x": 48, "y": 67}` | **useful_task_navigation** | opens File menu |
| healthy | `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` | 7105 | `click {"element": "File menu in the top menu bar", "x": 46, "y": 67}` | **useful_task_navigation** | opens File menu |
| healthy | `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` | 7106 | `click {"element": "File menu in the top menu bar", "x": 46, "y": 67}` | **benign_preparation** | dismisses update/help chrome |
| healthy | `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` | 7107 | `click {"element": "File menu in the top menu bar", "x": 46, "y": 67}` | **useful_task_navigation** | opens File menu |
| healthy | `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` | 7100 | `click {"element": "Three-dot menu button in the top-right corner of Chrome window", "x": 985, "y": 80}` | **useful_task_navigation** | opens Chrome menu |
| healthy | `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` | 7101 | `click {"element": "Chrome menu button (three vertical dots) in the top-right corner of the browser window", "x": 985, "y": 80}` | **useful_task_navigation** | opens Chrome menu |
| healthy | `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` | 7102 | `click {"element": "Three-dot menu button in the top-right corner of Chrome", "x": 985, "y": 80}` | **useful_task_navigation** | opens Chrome menu |
| healthy | `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` | 7103 | `click {"element": "Chrome menu button (three vertical dots) in the top-right corner of the browser", "x": 985, "y": 80}` | **useful_task_navigation** | opens Chrome menu |
| healthy | `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` | 7104 | `click {"element": "Chrome menu button (three vertical dots) in the top-right corner of the browser window", "x": 985, "y": 80}` | **useful_task_navigation** | opens Chrome menu |
| healthy | `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` | 7105 | `click {"element": "Chrome menu button (three vertical dots) in the top-right corner of the browser", "x": 985, "y": 80}` | **useful_task_navigation** | opens Chrome menu |
| healthy | `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` | 7106 | `click {"element": "Three-dot menu button in the top-right corner of Chrome window", "x": 985, "y": 80}` | **useful_task_navigation** | opens Chrome menu |
| healthy | `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` | 7107 | `click {"element": "Chrome menu button (three vertical dots) in the top-right corner of the browser window", "x": 985, "y": 80}` | **useful_task_navigation** | opens Chrome menu |

### Grounded notes

- `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` seed 7100: The frozen row-27 screenshot is the Stack Overflow tutorial; PageDown/scroll actions inspect the answer and comments needed for the requested instructions.
- `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` seed 7101: The frozen row-27 screenshot is the Stack Overflow tutorial; PageDown/scroll actions inspect the answer and comments needed for the requested instructions.
- `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` seed 7102: The frozen row-27 screenshot already shows the Stack Overflow answer containing the set number guidance; this click only focuses the answer area.
- `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` seed 7103: The frozen row-27 screenshot is the Stack Overflow tutorial; PageDown/scroll actions inspect the answer and comments needed for the requested instructions.
- `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` seed 7104: The task asks how to make Vim line numbers default locally; opening a terminal is relevant setup, but the output stops before applying any setting.
- `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` seed 7105: The frozen row-27 screenshot is the Stack Overflow tutorial; PageDown/scroll actions inspect the answer and comments needed for the requested instructions.
- `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` seed 7106: The frozen row-27 screenshot is the Stack Overflow tutorial; PageDown/scroll actions inspect the answer and comments needed for the requested instructions.
- `multi_apps/b337d106-053f-4d37-8da0-7f9c4043a66b` seed 7107: The frozen row-27 screenshot is the Stack Overflow tutorial; PageDown/scroll actions inspect the answer and comments needed for the requested instructions.
- `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` seed 7100: The frozen row-9 screenshot shows the fourth recipient incomplete; clicking the body or To field does not damage the draft and does not complete the address.
- `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` seed 7101: The frozen row-9 screenshot shows the fourth recipient incomplete; clicking the body or To field does not damage the draft and does not complete the address.
- `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` seed 7102: The frozen row-9 screenshot shows the fourth recipient as domaine seul; typing the missing prefix directly addresses that visible defect.
- `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` seed 7103: Ctrl+S saves the email draft and does not send it; it preserves whatever recipient state exists, so it is harmless but not a fix by itself.
- `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` seed 7104: The frozen row-9 screenshot shows the fourth recipient incomplete; selecting the visible complete-recipient suggestion is a direct correction attempt.
- `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` seed 7105: The frozen row-9 screenshot shows the fourth recipient as domaine seul; typing the missing prefix directly addresses that visible defect.
- `multi_apps/f5c13cdd-205c-4719-a562-348ae5cd1d91` seed 7107: The frozen row-9 screenshot shows the fourth recipient as domaine seul; typing the missing prefix directly addresses that visible defect.
- `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` seed 7101: The frozen row-6 screenshot visibly shows GIMP Preferences > System Resources with Minimal number of undo levels = 100; clicking Edit after that is non-destructive and cannot improve the already-complete state.
- `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` seed 7102: The frozen row-6 screenshot visibly shows GIMP Preferences > System Resources with Minimal number of undo levels = 100; clicking Edit after that is non-destructive and cannot improve the already-complete state.
- `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` seed 7103: The frozen row-6 screenshot visibly shows GIMP Preferences > System Resources with Minimal number of undo levels = 100; clicking Edit after that is non-destructive and cannot improve the already-complete state.
- `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` seed 7105: The frozen row-6 screenshot visibly shows GIMP Preferences > System Resources with Minimal number of undo levels = 100; clicking Edit after that is non-destructive and cannot improve the already-complete state.
- `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` seed 7106: The frozen row-6 screenshot visibly shows GIMP Preferences > System Resources with Minimal number of undo levels = 100; clicking Edit after that is non-destructive and cannot improve the already-complete state.
- `gimp/7b7617bd-57cc-468e-9c91-40c4ec2bcb3d` seed 7107: The frozen row-6 screenshot visibly shows GIMP Preferences > System Resources with Minimal number of undo levels = 100; clicking Edit after that is non-destructive and cannot improve the already-complete state.
- `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` seed 7100: The frozen initial Impress screen shows the presentation; clicking File is the correct first step toward the requested PNG export.
- `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` seed 7101: The frozen initial Impress screen shows the presentation; clicking File is the correct first step toward the requested PNG export.
- `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` seed 7102: The frozen initial Impress screen shows the presentation; clicking File is the correct first step toward the requested PNG export.
- `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` seed 7103: The frozen initial Impress screen shows the presentation; clicking File is the correct first step toward the requested PNG export.
- `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` seed 7104: The frozen initial Impress screen shows the presentation; clicking File is the correct first step toward the requested PNG export.
- `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` seed 7105: The frozen initial Impress screen shows the presentation; clicking File is the correct first step toward the requested PNG export.
- `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` seed 7106: The frozen initial Impress screen is intact; closing a notification is harmless preparation before File > Export.
- `libreoffice_impress/455d3c66-7dc6-4537-a39a-36d3e9119df7` seed 7107: The frozen initial Impress screen shows the presentation; clicking File is the correct first step toward the requested PNG export.
- `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` seed 7100: The frozen initial Chrome screen shows the browser and update popup; opening the three-dot menu is the correct first step toward Appearance > Light.
- `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` seed 7101: The frozen initial Chrome screen shows the browser and update popup; opening the three-dot menu is the correct first step toward Appearance > Light.
- `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` seed 7102: The frozen initial Chrome screen shows the browser and update popup; opening the three-dot menu is the correct first step toward Appearance > Light.
- `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` seed 7103: The frozen initial Chrome screen shows the browser and update popup; opening the three-dot menu is the correct first step toward Appearance > Light.
- `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` seed 7104: The frozen initial Chrome screen shows the browser and update popup; opening the three-dot menu is the correct first step toward Appearance > Light.
- `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` seed 7105: The frozen initial Chrome screen shows the browser and update popup; opening the three-dot menu is the correct first step toward Appearance > Light.
- `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` seed 7106: The frozen initial Chrome screen shows the browser and update popup; opening the three-dot menu is the correct first step toward Appearance > Light.
- `chrome/93eabf48-6a27-4cb6-b963-7d5fe1e0d3a9` seed 7107: The frozen initial Chrome screen shows the browser and update popup; opening the three-dot menu is the correct first step toward Appearance > Light.

## Text-prompt controls

The final three rows of each generations file are the text controls. Candidate p100 outputs: `391` for 17 × 23; `La réunion commence à neuf heures.`; and a correct one-sentence explanation of freezing. All three pass.

## Counts

| Category | Count |
|---|---:|
| benign_focus | 1 |
| benign_preparation | 1 |
| benign_reverification_attempt | 6 |
| benign_verification | 2 |
| corrective_accept_suggestion | 1 |
| corrective_write | 3 |
| non_destructive_persistence | 1 |
| relevant_setup | 1 |
| useful_research_navigation | 6 |
| useful_task_navigation | 15 |

The 13 true-finish nonanswers are 7 in the tuition-draft fs− row and 6 in the GIMP fs− row. Four tuition outputs attempt to correct the missing fourth-recipient prefix; two are neutral verification clicks; one saves the draft without sending. All six GIMP outputs are benign re-verification attempts after the visible value is already 100. No destruction is apparent. Tuition writes/selections are correction attempts whose results are not verified; no send action appears.

The 8 fs+ Vim nonanswers are tutorial navigation/focus plus one terminal-open setup action. The frozen screenshot visibly shows the requested tutorial content, so these are semantically useful or benign continuation rather than damage. Healthy controls remain ordinary first-step navigation: Impress opens File, and Chrome opens its menu (one seed dismisses the update notice).

The final three generation rows are text-prompt controls. Candidate p100 outputs pass all three: exact arithmetic (`391`), a correct French translation, and a correct one-sentence freezing explanation. These outputs show text preservation in this small control sample.
