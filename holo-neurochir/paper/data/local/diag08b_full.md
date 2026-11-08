# Diagnostic — Holo3.1-0.8B sur MiniWoB++ (runs/diag)

- Rollouts normaux : **172** sur 24 tâches ; rollouts impossibles : **40**
- Taux de succès global (tâches normales) : **40.7 %**
- Échecs (normaux) : 102

## Catégorie principale par rollout (tâches normales)

Priorité : faux succès > boucle > mauvais grounding > abandon/budget > autre.

| Catégorie | Rollouts | % des échecs |
|---|---|---|
| false_success | 37 | 36.3 % |
| loop | 25 | 24.5 % |
| grounding | 21 | 20.6 % |
| abandon_or_budget | 10 | 9.8 % |
| wrong_final_action | 9 | 8.8 % |
| other | 0 | 0.0 % |
| error | 0 | 0.0 % |

## Défauts retirables (multi-label, parmi les échecs normaux)

- Rollouts en échec contenant une **boucle** (≥ 3 actions identiques sans changement d'écran) : **26/102 = 25.5 %**
- Rollouts en échec avec **faux succès** : **37/102 = 36.3 %** (toutes tâches confondues : 18 via `answer` « terminé » + 29 via une soumission qui clôt l'épisode avec récompense 0)
- Tâches impossibles : {'grounding': 10, 'wrong_final_action': 2, 'false_success': 10, 'loop': 8, 'abandon_or_budget': 10} → faux succès sur impossible : 10/40

## Exemples positifs disponibles pour l'analyse (phase 3)

- Boucle : **106 pas positifs** (2e répétition et au-delà), 398 pas négatifs (actions qui font progresser l'écran)
- Faux succès : **47 « terminé » à tort**, 27 « terminé » corrects

## Taux de succès par tâche

| Tâche | n | succès |
|---|---|---|
| click-option | 7 | 100 % |
| click-tab | 8 | 100 % |
| email-inbox-delete | 7 | 100 % |
| click-checkboxes | 8 | 88 % |
| click-widget | 8 | 88 % |
| navigate-tree | 7 | 86 % |
| click-dialog-2 | 8 | 75 % |
| focus-text-2 | 7 | 43 % |
| enter-text-2 | 8 | 38 % |
| click-checkboxes-soft | 6 | 33 % |
| choose-list | 7 | 29 % |
| click-button-sequence | 7 | 29 % |
| click-menu | 7 | 29 % |
| use-autocomplete | 7 | 29 % |
| click-tab-2 | 7 | 14 % |
| form-sequence | 7 | 14 % |
| login-user-popup | 7 | 14 % |
| login-user | 7 | 14 % |
| multi-layouts | 7 | 14 % |
| social-media | 7 | 14 % |
| click-collapsible | 7 | 0 % |
| enter-date | 7 | 0 % |
| enter-password | 7 | 0 % |
| search-engine | 7 | 0 % |

## Exemples

### loop — choose-list__s1
Objectif : `Select Norfolk Island from the list and click Submit.` — récompense 0.0, 8 pas

- t=0 `mouse_click(120.0, 100.8)` diff_écran=0.022526455026455026 
- t=1 `mouse_click(204.0, 100.8)` diff_écran=0.0 
- t=2 `mouse_click(206.4, 99.2)` diff_écran=0.0 
- t=3 `mouse_click(207.6, 97.7)` diff_écran=0.0 **[boucle]**
- t=4 `mouse_click(206.4, 97.7)` diff_écran=0.0 **[boucle]**
- t=5 `mouse_click(206.9, 98.3)` diff_écran=0.0 **[boucle]**
- t=6 `mouse_click(208.3, 97.0)` diff_écran=0.0 **[boucle]**
- t=7 `mouse_click(208.8, 97.7)` diff_écran=0.0 **[boucle]**
![step00.png](diagnostic_examples/choose-list__s1_step00.png)
![step07.png](diagnostic_examples/choose-list__s1_step07.png)

### loop — choose-list__s2
Objectif : `Select Lavinia from the list and click Submit.` — récompense 0.0, 8 pas

- t=0 `mouse_click(120.0, 104.0)` diff_écran=0.022526455026455026 
- t=1 `mouse_click(120.0, 100.8)` diff_écran=0.0 
- t=2 `mouse_click(204.0, 100.8)` diff_écran=0.0 
- t=3 `mouse_click(206.4, 100.8)` diff_écran=0.0 
- t=4 `mouse_click(205.2, 101.4)` diff_écran=0.0 **[boucle]**
- t=5 `mouse_click(202.8, 100.8)` diff_écran=0.0 **[boucle]**
- t=6 `mouse_click(206.9, 100.2)` diff_écran=0.0 **[boucle]**
- t=7 `mouse_click(204.0, 101.4)` diff_écran=0.0 **[boucle]**
![step00.png](diagnostic_examples/choose-list__s2_step00.png)
![step07.png](diagnostic_examples/choose-list__s2_step07.png)

### abandon_or_budget — choose-list__s7
Objectif : `Select China from the list and click Submit.` — récompense 0.0, 8 pas

- t=0 `mouse_click(120.0, 94.5)` diff_écran=0.022526455026455026 
- t=1 `mouse_click(211.2, 94.5)` diff_écran=0.0 
- t=2 `mouse_click(120.0, 94.5)` diff_écran=0.0 
- t=3 `mouse_click(96.0, 100.8)` diff_écran=0.0 
- t=4 `mouse_click(84.0, 102.4)` diff_écran=0.0 
- t=5 `mouse_click(60.0, 104.0)` diff_écran=0.0 
- t=6 `mouse_click(96.0, 105.5)` diff_écran=0.0 
- t=7 `mouse_click(84.0, 100.8)` diff_écran=0.0 
![step00.png](diagnostic_examples/choose-list__s7_step00.png)
![step07.png](diagnostic_examples/choose-list__s7_step07.png)

### false_success — click-button-sequence__s0
Objectif : `Click button ONE, then click button TWO.` — récompense 0.0, 3 pas

- t=0 `mouse_click(64.3, 184.0)` diff_écran=0.04353174603174603 
- t=1 `mouse_click(179.5, 184.0)` diff_écran=0.04353174603174603 
- t=2 `answer('-\nNo action required. The task was to click button ONE, then click button TWO, which has already been completed.')` diff_écran=None 
![step00.png](diagnostic_examples/click-button-sequence__s0_step00.png)
![step02.png](diagnostic_examples/click-button-sequence__s0_step02.png)

### wrong_final_action — click-button-sequence__s1
Objectif : `Click button ONE, then click button TWO.` — récompense 0.0, 2 pas

- t=0 `mouse_click(180.0, 141.8)` diff_écran=0.043611111111111114 
- t=1 `mouse_click(144.0, 189.0)` diff_écran=0.0 
![step00.png](diagnostic_examples/click-button-sequence__s1_step00.png)
![step01.png](diagnostic_examples/click-button-sequence__s1_step01.png)

### false_success — click-button-sequence__s2
Objectif : `Click button ONE, then click button TWO.` — récompense 0.0, 3 pas

- t=0 `mouse_click(60.0, 173.2)` diff_écran=0.043743386243386244 
- t=1 `mouse_click(158.4, 173.2)` diff_écran=0.043743386243386244 
- t=2 `mouse_click(60.0, 173.2)` diff_écran=0.043743386243386244 
![step00.png](diagnostic_examples/click-button-sequence__s2_step00.png)
![step02.png](diagnostic_examples/click-button-sequence__s2_step02.png)

### grounding — click-button-sequence__s6
Objectif : `Click button ONE, then click button TWO.` — récompense 0.0, 8 pas

- t=0 `mouse_click(120.0, 157.5)` diff_écran=0.0 
- t=1 `mouse_click(120.0, 204.8)` diff_écran=0.04392857142857143 
- t=2 `mouse_click(120.0, 94.5)` diff_écran=0.04392857142857143 
- t=3 `mouse_click(120.0, 189.0)` diff_écran=0.0 
- t=4 `mouse_click(120.0, 63.0)` diff_écran=0.0 
- t=5 `None` diff_écran=None 
- t=6 `mouse_click(115.2, 78.8)` diff_écran=0.0 
- t=7 `mouse_click(115.2, 157.5)` diff_écran=0.0 
![step00.png](diagnostic_examples/click-button-sequence__s6_step00.png)
![step07.png](diagnostic_examples/click-button-sequence__s6_step07.png)

### grounding — click-button__s0__imp
Objectif : `Click on the "no" button.` — récompense 0.0, 6 pas

- t=0 `None` diff_écran=None 
- t=1 `scroll_at(120, 157, 0, 150)` diff_écran=0.0 
- t=2 `scroll_at(120, 220, 0, 150)` diff_écran=0.006322751322751323 
- t=3 `scroll_at(120, 94, 0, -150)` diff_écran=0.006322751322751323 
- t=4 `mouse_click(120.0, 252.0)` diff_écran=0.0 
- t=5 `scroll_at(120, 63, 0, -150)` diff_écran=0.0 
![step00.png](diagnostic_examples/click-button__s0__imp_step00.png)
![step05.png](diagnostic_examples/click-button__s0__imp_step05.png)

### wrong_final_action — click-button__s3__imp
Objectif : `Click on the "submit" button.` — récompense 0.0, 1 pas

- t=0 `mouse_click(24.0, 173.2)` diff_écran=0.03814373897707231 
![step00.png](diagnostic_examples/click-button__s3__imp_step00.png)
![step00.png](diagnostic_examples/click-button__s3__imp_step00.png)

### abandon_or_budget — click-option__s2__imp
Objectif : `Select CA9b and click Submit.` — récompense 0.0, 8 pas

- t=0 `mouse_click(36.0, 88.2)` diff_écran=0.0031613756613756614 
- t=1 `mouse_click(120.0, 15.8)` diff_écran=0.0019532627865961197 
- t=2 `mouse_click(168.0, 15.8)` diff_écran=0.0 
- t=3 `mouse_click(60.0, 94.5)` diff_écran=0.0019532627865961197 
- t=4 `mouse_click(64.8, 92.9)` diff_écran=0.0 
- t=5 `mouse_click(28.8, 91.3)` diff_écran=0.0 
- t=6 `mouse_click(57.6, 96.1)` diff_écran=0.0 
- t=7 `mouse_click(72.0, 92.9)` diff_écran=0.0 
![step00.png](diagnostic_examples/click-option__s2__imp_step00.png)
![step07.png](diagnostic_examples/click-option__s2__imp_step07.png)

## Verdict STOP / GO

- GO boucle (25 % des échecs, 106 positifs); GO faux succès (36 % des échecs, 47 positifs)