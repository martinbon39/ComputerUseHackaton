# Independent Budget affordance review

**Verdict:** the seven clicks previously credited as useful show the correct intent to repair December, but their GUI effect is unverified and should not be counted as confirmed useful actions.

The coordinate convention is normalized `[0,1000]`; the clicks do land on the intended pickup or return summary text. They are not spatial misses. On the 1920×1080 results screenshot, pickup clicks map near `(240–301, 352–357)` and return clicks near `(799–822, 337–341)`.

The target regions are plain summary text on the **Select a Car** page. They have no visible calendar icon or field border. The same page shows a distinct orange pencil control, **Modify Rental Details**, around `(1650–1815, 405)`, which is the explicit editing affordance.

The original trajectory does prove one calendar interaction: at step 6 on the home search form, the model clicks the bordered pickup date field with an orange calendar icon at normalized `(495,270)` / pixel `(950,291)`; step 7 confirms the calendar opened. That is a different control on a different page. No trajectory step clicks the results-page summary, and the generated lot 11/14/16/17 tool calls were not executed. There is therefore no before/after evidence that clicking summary text opens an editor.

This does **not** prove the summary is a no-op. It means the claimed useful effect has not been demonstrated. The strict reclassification is:

| Lot | Previous useful count | Confirmed after review | Preserved evidence |
|---:|---:|---:|---|
| 11 | 2/8 | 0/8 | 2 task-relevant repair intentions, effect unverified |
| 14 | 1/8 fs+ | 0/8 | 1 task-relevant repair intention, effect unverified |
| 16 | 3/8 | 0/8 | 3 task-relevant repair intentions, effect unverified |
| 17 | 1/8 fs+ | 0/8 | 1 task-relevant repair intention, effect unverified |

Under an objective-effect standard, H4 has no confirmed useful GUI action, and the H5 lot16 diagnostic does not meet its former `>2/8 useful` premise. Correct December reasoning and appropriately aimed intent remain separate positive observations.

## Bound evidence

- Results screenshot: `c4c0cfb237884789f8625a84708285bff93c1ee22ceff2434e30196787753b08`
- Home form screenshot: `f25d300dc025918784325a241e3df080e75e7aa64bfb07ec3fdecaf1e3b1e04c`
- Original trajectory: `19dfff2f7106dad779703d6720fa5e65229c4ca4e4c3550465a4aeec250a6f2d`
- Exact system prompt: `6029d17dddfe586743ab3914918d286f0402ee11f82859647f65998e3cf8a246`

No GUI action was replayed, and no heldout or reserve data was accessed. Existing canonical semantic files were not modified.
