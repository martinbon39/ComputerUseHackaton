# Diagnostic — Holo3.1-0.8B sur MiniWoB++ (runs/diag)

- Rollouts normaux : **117** sur 24 tâches ; rollouts impossibles : **12**
- Taux de succès global (tâches normales) : **40.2 %**
- Échecs (normaux) : 70

## Catégorie principale par rollout (tâches normales)

Priorité : faux succès > boucle > mauvais grounding > abandon/budget > autre.

| Catégorie | Rollouts | % des échecs |
|---|---|---|
| false_success | 23 | 32.9 % |
| loop | 18 | 25.7 % |
| grounding | 15 | 21.4 % |
| abandon_or_budget | 6 | 8.6 % |
| wrong_final_action | 8 | 11.4 % |
| other | 0 | 0.0 % |
| error | 0 | 0.0 % |

## Défauts retirables (multi-label, parmi les échecs normaux)

- Rollouts en échec contenant une **boucle** (≥ 3 actions identiques sans changement d'écran) : **18/70 = 25.7 %**
- Rollouts en échec avec **faux succès** : **23/70 = 32.9 %** (toutes tâches confondues : 6 via `answer` « terminé » + 19 via une soumission qui clôt l'épisode avec récompense 0)
- Tâches impossibles : {'grounding': 6, 'loop': 3, 'abandon_or_budget': 1, 'false_success': 2} → faux succès sur impossible : 2/12

## Exemples positifs disponibles pour l'analyse (phase 3)

- Boucle : **68 pas positifs** (2e répétition et au-delà), 240 pas négatifs (actions qui font progresser l'écran)
- Faux succès : **25 « terminé » à tort**, 18 « terminé » corrects

## Taux de succès par tâche

| Tâche | n | succès |
|---|---|---|
| click-option | 5 | 100 % |
| click-tab | 5 | 100 % |
| email-inbox-delete | 5 | 100 % |
| click-checkboxes | 5 | 80 % |
| click-dialog-2 | 5 | 80 % |
| click-widget | 5 | 80 % |
| navigate-tree | 5 | 80 % |
| focus-text-2 | 5 | 60 % |
| click-checkboxes-soft | 4 | 50 % |
| choose-list | 5 | 40 % |
| click-button-sequence | 5 | 40 % |
| use-autocomplete | 5 | 40 % |
| form-sequence | 4 | 25 % |
| multi-layouts | 4 | 25 % |
| click-menu | 5 | 20 % |
| click-tab-2 | 5 | 20 % |
| enter-text-2 | 5 | 20 % |
| click-collapsible | 5 | 0 % |
| enter-date | 5 | 0 % |
| enter-password | 5 | 0 % |
| login-user-popup | 5 | 0 % |
| login-user | 5 | 0 % |
| search-engine | 5 | 0 % |
| social-media | 5 | 0 % |

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

### grounding — click-button__s1__imp
Objectif : `Click on the "cancel" button.` — récompense 0.0, 6 pas

- t=0 `None` diff_écran=None 
- t=1 `None` diff_écran=None 
- t=2 `scroll_at(120, 220, 0, 150)` diff_écran=0.0 
- t=3 `scroll_at(120, 252, 0, 150)` diff_écran=0.0 
- t=4 `scroll_at(120, 126, 0, -150)` diff_écran=0.0 
- t=5 `mouse_click(48.0, 63.0)` diff_écran=0.0 
![step00.png](diagnostic_examples/click-button__s1__imp_step00.png)
![step05.png](diagnostic_examples/click-button__s1__imp_step05.png)

### wrong_final_action — click-dialog-2__s1
Objectif : `Click the button in the dialog box labeled "x".` — récompense 0.0, 1 pas

- t=0 `mouse_click(157.4, 246.0)` diff_écran=0.047407407407407405 
![step00.png](diagnostic_examples/click-dialog-2__s1_step00.png)
![step00.png](diagnostic_examples/click-dialog-2__s1_step00.png)

### abandon_or_budget — click-tab-2__s0
Objectif : `Switch between the tabs to find and click on the link "vel".` — récompense 0.0, 10 pas

- t=0 `mouse_click(36.0, 113.4)` diff_écran=0.0 
- t=1 `mouse_click(108.0, 113.4)` diff_écran=0.15573192239858907 
- t=2 `mouse_click(168.0, 113.4)` diff_écran=0.15488536155202823 
- t=3 `None` diff_écran=None 
- t=4 `None` diff_écran=None 
- t=5 `None` diff_écran=None 
- t=6 `mouse_click(144.0, 179.5)` diff_écran=0.0 
- t=7 `None` diff_écran=None 
- t=8 `None` diff_écran=None 
- t=9 `None` diff_écran=None 
![step00.png](diagnostic_examples/click-tab-2__s0_step00.png)
![step09.png](diagnostic_examples/click-tab-2__s0_step09.png)

### abandon_or_budget — enter-date__s2
Objectif : `Enter 01/12/2012 as the date and hit submit.` — récompense 0.0, 10 pas

- t=0 `mouse_click(103.2, 111.2)` diff_écran=0.03493827160493827 
- t=1 `keyboard_type("01/12/2012")` diff_écran=0.01224426807760141 
- t=2 `keyboard_type("01/12/2012")` diff_écran=0.0 
- t=3 `mouse_click(103.2, 111.2)` diff_écran=0.0 
- t=4 `keyboard_press("Enter")` diff_écran=0.0 
- t=5 `mouse_click(103.2, 111.2)` diff_écran=0.0 
- t=6 `keyboard_press("Backspace")` diff_écran=0.01224426807760141 
- t=7 `keyboard_press("Backspace")` diff_écran=0.0 
- t=8 `keyboard_press("Delete")` diff_écran=0.0 
- t=9 `mouse_click(148.8, 111.2)` diff_écran=0.0 
![step00.png](diagnostic_examples/enter-date__s2_step00.png)
![step09.png](diagnostic_examples/enter-date__s2_step09.png)

## Verdict STOP / GO

- GO boucle (26 % des échecs, 68 positifs)