# Round 2: approved promote list (coordinator decision, 2026-09-27)

The user delegated the triage approval to the coordinator ("work independently using your own
judgement"). Source: the `<cat>.tsv` files in this directory (live fetches, 2026-09-27).
Rule applied: take every PROMOTE row, except rows whose only case is a signal barely over the
band-3 floor or an unmeasured one, and rows blocked on an unresolved ruling.

| Category | Promote | Cut from the TSV's PROMOTE list, and why |
|---|---|---|
| classic_ml_cv | 34: lightgbm catboost imbalanced-learn pyod umap hdbscan cuml river h2o-3 gensim stanza textblob torchvision detectron2 kornia supervision scikit-image mediapipe monai fastai dlib insightface darts statsforecast pmdarima gluonts flaml pycaret dino depth-anything rt-detr birefnet rmbg segment-anything | skrub, ngboost, neuralforecast (just over the floor; ngboost likely dependency-pulled; neuralforecast same vendor as statsforecast), ml-net (monthly downloads unmeasured), paddledetection (stars only, no download channel), sapiens, eomt, nori (family sums just over the floor, low stars or likely automated downloads) |
| speech_audio | 17: wav2vec xtts vibevoice omnivoice mms speechbrain granite-speech vosk melotts seamless-m4t higgs-audio whisperx personaplex moss-transcribe-diarize moonshine sesame-csm zonos | voxtral: whether the Voxtral TTS member belongs to the governing release is a maintainer ruling; the category note holds it |
| media_generation | 6: open-sora stable-video-diffusion latentsync triposr mmaudio diffsynth-studio | none |
| robotics_embodied | 5: habitat newton robomind interndata-a1 lekiwi | reachy-mini: its placement on the morphology ladder is unresolved |
| multimodal_models | 5: idefics lfm-vl north-vision deepseek-vl cambrian | perception-lm: noncommercial weights and 1.6K/30d; cambrian covers the open-recipe gap |
| datacenter_accelerators | 2: moore-threads-mtt-s5000 huawei-ascend-950 | none |
| assurance_evidence | 1: zkml | none |
| model_hubs | 1: pytorch-hub; plus MOVE openml to benchmark_eval_data (registry row) | none |
| federated_learning | 0 | p2pfl: gap fill blocked on its gating reading, 44 downloads/month; nebula-dfl has the same question |

71 promotions. Rows carrying a license no shared tier names are promoted and deferred with a
hand-placed score, as in round 1 (#739 collects the strings).

## Review fixes folded into the writers (files each writer already touches)
- assurance_evidence: the strapline calls EZKL and DeepProve "the least open products here";
  IBM watsonx.governance and Credo AI score 1/closed. Rewrite it from the scores.
- speech_audio: the comments contradict each other on voxtral (ASR line governs vs TTS member
  governs); state the hold once. The strapline's "only open-weights voice in the arena's top ten"
  claim needs a cited source or goes.
- robotics_embodied: comments still say the promotion places Reachy Mini; AgiBot World is
  described as pooled cross-embodiment while its note bands it 4. Reconcile.
- classic_ml_cv: the note says each rung contains the one below; false at rung 4. Fix the wording.
- multimodal_models: blip is read on BLIP-2 while its github (salesforce/LAVIS) is archived;
  re-read it under the current-release rule and record the governing release.
- federated_learning (no promotions): pysyft and syfthub openness and adoption cite June and
  August fetches; re-fetch and re-cite them. Branch `claude/promote2-federated_learning`.

## Launch (2026-09-27 14:56 UTC)
Eight writer sessions started from main (a4ace94c), one per branch; see sessions.tsv.
The federated_learning evidence-refresh session was NOT started (the session launch was refused
by a permission check); that fix waits for the user.
