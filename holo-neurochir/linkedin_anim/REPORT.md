# Report: linkedinviz (LinkedIn animation)

Deliverables (signed links, 30 days):
- MP4 4:5: https://argos.martinbonan.com/artifacts/not-here-linkedin-4x5.mp4?t=mxgg4s4r.iQZ7iQ_MBOYe4dusVoATw09oYvGBBuYA
- HTML (self-contained, live loop): https://argos.martinbonan.com/artifacts/not-here-linkedin.html?t=mxgg4s6j.S8K4MCNGLT1Zjp-2SPTj5b71CYzOdd8d
- MP4 1:1 crop: https://argos.martinbonan.com/artifacts/not-here-linkedin-1x1.mp4?t=mxgg4s8h.PRFRvVl0E1D8fc3EPDhxcMGb3pXTbG2c

ffprobe output:
- not_here_4x5.mp4: h264 High, 1080x1350, yuv420p, bt709, 30/1 fps, 750 frames, 25.000 s, 25,101,017 bytes, faststart (moov before mdat), no audio
- not_here_1x1.mp4: h264 High, 1080x1080, yuv420p, bt709, 30/1 fps, 750 frames, 25.000 s, 26,696,808 bytes, faststart
- Loop seam: the mean absolute luma difference between the first and last frame is 1.13/255.

Captions: "Where does an AI agent know it's wrong?" / "true “done” vs false “done”" / "Not inside." /
"It takes an outside check." / end card "Cogito, Ergo Feci · Holo-3.1-4B · doi 10.5281/zenodo.24061167".
I changed Martin's suggested "Not here." to "Not inside." at the reviewer's request: "Not here." over one layer reads as
"it is somewhere else", while the paper found nothing anywhere it looked.

Hero data: real. The layer-15 dots are the 14 matched false/true "done" pairs of
paper/data/pod_astra/perceive/descriptive_v2.json (previous_z[15] -> terminal_z[15]). Both colours rise, and the
mean lines differ by 0.14 SD. Details in README.md.

Reviewer: a fresh general-purpose subagent that did not build the video. Verdict PASS WITH NITS, all 4 items PASS
(claims, legibility at 360 px, glitches, file spec). It recomputed every README number from the JSON. Applied fixes:
"Not inside.", Holo-3.1-4B on the end card, captions moved off the layer frame and out of the bottom 20 %, a slower
push, brackets kept clear of the 1:1 crop, bt709 tags, README completed (3 infeasible tasks, a repeated pair).
The reviewer did not re-review the final render. I checked it myself on a 1 fps sheet at 360 px.
Not fixed: the camera turn at about 5-7 s is still fast, and LinkedIn's re-encode may soften it.

Practices applied: 4:5 1080x1350, captions 46 px or larger, the top 12 % and bottom 20 % kept clear of text, a
thumbnail-ready first frame, 25 s. Sources: contentin.io LinkedIn video best practices (2026-09),
quso.ai LinkedIn video specs (2026-07), LinkedIn help a565326 (videos autoplay muted).
